"""Tests for the Assess module — questionnaire, answers and scoring.

The rules that matter most here are the ones that stop the score inventing findings: an
unanswered question is not a zero, an unassessed step drops out of the index, and the
model may move a step by at most ±1 with a stated reason.
"""

import pytest

from app.schemas.assess import StepScore, band_for_index
from app.services.assess.library import (
    ProcessLibraryError,
    ProcessNotDefinedError,
    get_process_registry,
    get_questionnaire,
)
from app.services.assess.llm import LlmStepRefinement, apply_refinements
from app.services.assess.scoring import compute_index, score_assessment
from tests.test_engagement_flow import SECTIONS_PAYLOAD


def create_engagement(client) -> dict:
    """A filed engagement. Assess needs no scope — it is the analyst's own fieldwork."""
    response = client.post("/api/v1/engagements", json={"deal_name": "Project Lighthouse"})
    engagement = response.json()
    for section, payload in SECTIONS_PAYLOAD.items():
        client.patch(f"/api/v1/engagements/{engagement['id']}/intake/{section}", json=payload)
    client.post(f"/api/v1/engagements/{engagement['id']}/submit")
    return engagement

P2P = "procure_to_pay"


# --------------------------------------------------------------------------- library


def test_the_questionnaire_loads_and_its_weights_sum_to_100() -> None:
    questionnaire = get_questionnaire(P2P)
    assert len(questionnaire.steps) == 9
    assert sum(step.weight for step in questionnaire.steps) == 100


def test_every_question_and_nudge_id_is_unique() -> None:
    """They key the answer table — a duplicate would make two questions share an answer."""
    questionnaire = get_questionnaire(P2P)
    ids: list[str] = []
    for step in questionnaire.steps:
        for question in step.questions:
            ids.append(question.id)
            ids.extend(nudge.id for nudge in question.nudges)
    assert len(ids) == len(set(ids))


def test_every_nudge_fires_on_an_option_that_exists() -> None:
    """A nudge naming a label that is not an option can never fire — silent dead weight."""
    questionnaire = get_questionnaire(P2P)
    for step in questionnaire.steps:
        for question in step.questions:
            labels = {option.label for option in question.options}
            for nudge in question.nudges:
                wanted = list(nudge.when.in_ or [])
                if nudge.when.equals:
                    wanted.append(nudge.when.equals)
                for label in wanted:
                    assert label in labels, f"{nudge.id} fires on an unknown option"


def test_the_four_other_processes_are_named_but_not_defined() -> None:
    registry = get_process_registry()
    by_key = {entry.key: entry for entry in registry.processes}
    assert by_key[P2P].defined is True
    for key in ("order_to_cash", "plan_to_make", "hire_to_retire", "record_to_report"):
        assert by_key[key].defined is False


def test_asking_for_an_undefined_process_is_a_409_not_a_404() -> None:
    """404 would imply the process does not exist. It does; its questions do not."""
    with pytest.raises(ProcessNotDefinedError) as exc:
        get_questionnaire("order_to_cash")
    assert exc.value.status_code == 409


def test_an_unknown_process_key_is_a_library_error() -> None:
    with pytest.raises(ProcessLibraryError):
        get_questionnaire("not_a_process")


# --------------------------------------------------------------------------- scoring


def _answer_step_fully(step_key: str, score_label_index: int) -> dict[str, str]:
    """Answer every scoring question in one step, picking the option at a given rank."""
    questionnaire = get_questionnaire(P2P)
    step = next(s for s in questionnaire.steps if s.key == step_key)
    answers: dict[str, str] = {}
    for question in step.questions:
        if question.scores:
            index = min(score_label_index, len(question.options) - 1)
            answers[question.id] = question.options[index].label
    return answers


def test_an_unanswered_question_is_not_scored_as_zero() -> None:
    """A blank is an absence of evidence, not evidence of manual working."""
    questionnaire = get_questionnaire(P2P)

    # One step answered at the top of each question's ladder, everything else blank.
    # Not every question reaches 5 — the ladder is per-question — so the expected index
    # is computed from the options actually chosen rather than assumed to be 100.
    step = questionnaire.steps[0]
    scoring = [q for q in step.questions if q.scores]
    top = {q.id: q.options[-1].label for q in scoring}
    expected = round(sum(q.options[-1].score for q in scoring) / len(scoring), 1) * 20

    payload = score_assessment(questionnaire, top)

    # The one answered step is the whole index. If blanks were scored as zero, eight
    # empty steps would drag this to a fraction of it.
    assert payload.index == pytest.approx(expected, abs=0.1)
    assert payload.index > 80, "blank steps must not drag the index down"
    assert payload.steps_assessed == 1
    assert payload.steps_total == 9


def test_an_unassessed_step_drops_out_and_its_weight_is_redistributed() -> None:
    questionnaire = get_questionnaire(P2P)
    answers = _answer_step_fully("p2p_invoice", 3)

    payload = score_assessment(questionnaire, answers)
    invoice = next(s for s in payload.steps if s.key == "p2p_invoice")
    payment = next(s for s in payload.steps if s.key == "p2p_payment")

    assert invoice.assessed is True
    assert payment.assessed is False
    assert payment.score is None
    # Only one step is assessed, so the index is that step's score alone — its weight of
    # 17 has become the whole denominator.
    assert payload.index == pytest.approx((invoice.score or 0) * 20, abs=0.1)


def test_nothing_answered_produces_a_zero_index_and_says_so() -> None:
    questionnaire = get_questionnaire(P2P)
    payload = score_assessment(questionnaire, {})

    assert payload.index == 0.0
    assert payload.steps_assessed == 0
    assert "not yet been assessed" in payload.executive_summary
    assert all(not step.assessed for step in payload.steps)


def test_a_stale_answer_label_is_ignored_rather_than_raising() -> None:
    """The questionnaire can change under a stored answer. Reduced coverage beats a crash."""
    questionnaire = get_questionnaire(P2P)
    answers = {"P2P-07-01": "An option that no longer exists"}

    payload = score_assessment(questionnaire, answers)
    invoice = next(s for s in payload.steps if s.key == "p2p_invoice")
    assert invoice.assessed is False


def test_the_index_is_the_weighted_mean_normalised_to_100() -> None:
    steps = [
        StepScore(key="a", sn=1, title="A", weight=75, score=4.0, deterministic_score=4.0),
        StepScore(key="b", sn=2, title="B", weight=25, score=2.0, deterministic_score=2.0),
    ]
    # (4*75 + 2*25) / 100 = 3.5 -> 70
    assert compute_index(steps) == 70.0


def test_the_bands_map_as_the_model_document_states() -> None:
    assert band_for_index(0) == "manual"
    assert band_for_index(20) == "manual"
    assert band_for_index(21) == "emerging"
    assert band_for_index(40) == "emerging"
    assert band_for_index(41) == "standardised"
    assert band_for_index(60) == "standardised"
    assert band_for_index(61) == "integrated"
    assert band_for_index(80) == "integrated"
    assert band_for_index(81) == "optimised"
    assert band_for_index(100) == "optimised"


def test_a_front_loaded_cycle_is_named_as_such() -> None:
    """The shape is the finding; the index alone hides it."""
    questionnaire = get_questionnaire(P2P)
    answers: dict[str, str] = {}
    for step in questionnaire.steps:
        # Strong at the front (steps 1-3), weak at the back (7-9).
        rank = 4 if step.sn <= 3 else 0
        for question in step.questions:
            if question.scores:
                answers[question.id] = question.options[
                    min(rank, len(question.options) - 1)
                ].label

    payload = score_assessment(questionnaire, answers)
    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Front-loaded")


def test_the_heaviest_gap_is_the_first_pointer() -> None:
    """Pointers rank by weight, so they name what matters commercially."""
    questionnaire = get_questionnaire(P2P)
    answers: dict[str, str] = {}
    for step in questionnaire.steps:
        for question in step.questions:
            if question.scores:
                answers[question.id] = question.options[0].label

    payload = score_assessment(questionnaire, answers)
    gaps = [p for p in payload.pointers if p.kind == "gap"]
    assert gaps, "an all-manual process must produce gaps"
    # Invoice capture & matching carries 17%, the heaviest weight in the model.
    assert gaps[0].step_key == "p2p_invoice"


def test_thin_coverage_is_flagged_on_the_step() -> None:
    questionnaire = get_questionnaire(P2P)
    supplier = next(s for s in questionnaire.steps if s.key == "p2p_supplier_master")
    scoring_qs = [q for q in supplier.questions if q.scores]
    # One of three answered — below the half-coverage threshold.
    answers = {scoring_qs[0].id: scoring_qs[0].options[0].label}

    payload = score_assessment(questionnaire, answers)
    step = next(s for s in payload.steps if s.key == "p2p_supplier_master")
    assert "thin coverage" in step.reason


def test_the_deterministic_score_is_reproducible() -> None:
    """Two runs over the same answers must agree, or the audit trail means nothing."""
    questionnaire = get_questionnaire(P2P)
    answers = _answer_step_fully("p2p_invoice", 2) | _answer_step_fully("p2p_payment", 3)

    first = score_assessment(questionnaire, answers)
    second = score_assessment(questionnaire, answers)

    assert first.index == second.index
    assert [s.score for s in first.steps] == [s.score for s in second.steps]


# --------------------------------------------------------------------------- refinement


def _invoice_payload() -> tuple:
    """A payload with the invoice step assessed and the payment step untouched."""
    questionnaire = get_questionnaire(P2P)
    answers = _answer_step_fully("p2p_invoice", 2)
    payload = score_assessment(questionnaire, answers)
    return payload, next(s for s in payload.steps if s.key == "p2p_invoice")


def test_a_refinement_within_one_point_is_applied_and_records_its_reason() -> None:
    payload, step = _invoice_payload()
    original = step.deterministic_score
    assert original is not None

    payload, applied = apply_refinements(
        payload,
        [
            LlmStepRefinement(
                step_key="p2p_invoice",
                score=original + 1,
                reason="Management stated tolerances are set so wide the match is nominal.",
            )
        ],
    )

    assert applied == 1
    refined = next(s for s in payload.steps if s.key == "p2p_invoice")
    assert refined.score == original + 1
    assert refined.refined is True
    assert refined.deterministic_score == original, "the rules score must survive"
    assert refined.refinement_reason


def test_a_refinement_beyond_one_point_is_rejected() -> None:
    payload, step = _invoice_payload()
    original = step.deterministic_score
    assert original is not None

    payload, applied = apply_refinements(
        payload,
        [
            LlmStepRefinement(
                step_key="p2p_invoice",
                score=original + 2,
                reason="A long enough reason to pass the length check but too big a jump.",
            )
        ],
    )

    assert applied == 0
    assert next(s for s in payload.steps if s.key == "p2p_invoice").score == original


def test_a_refinement_without_a_reason_is_rejected() -> None:
    payload, step = _invoice_payload()
    original = step.deterministic_score
    assert original is not None

    payload, applied = apply_refinements(
        payload,
        [LlmStepRefinement(step_key="p2p_invoice", score=original + 1, reason="better")],
    )

    assert applied == 0
    assert next(s for s in payload.steps if s.key == "p2p_invoice").score == original


def test_a_refinement_to_an_unassessed_step_is_rejected() -> None:
    """No evidence means no score, not a guessed one."""
    payload, _ = _invoice_payload()
    payment = next(s for s in payload.steps if s.key == "p2p_payment")
    assert payment.assessed is False

    payload, applied = apply_refinements(
        payload,
        [
            LlmStepRefinement(
                step_key="p2p_payment",
                score=3.0,
                reason="This step has no recorded answers at all, so this must be refused.",
            )
        ],
    )

    assert applied == 0
    assert next(s for s in payload.steps if s.key == "p2p_payment").score is None


def test_refining_too_many_steps_drops_all_of_them() -> None:
    """Moving many steps means second-guessing the ladder, not reading evidence."""
    questionnaire = get_questionnaire(P2P)
    answers: dict[str, str] = {}
    for step in questionnaire.steps:
        answers |= _answer_step_fully(step.key, 2)
    payload = score_assessment(questionnaire, answers)
    before = [s.score for s in payload.steps]

    refinements = [
        LlmStepRefinement(
            step_key=step.key,
            score=(step.score or 0) + 1,
            reason="A plausible-looking reason that is long enough to pass validation.",
        )
        for step in payload.steps[:5]
    ]
    payload, applied = apply_refinements(payload, refinements)

    assert applied == 0
    assert [s.score for s in payload.steps] == before


def test_the_deterministic_index_survives_refinement() -> None:
    """Both numbers are kept, so a reader can put the rules score back."""
    payload, step = _invoice_payload()
    original_index = payload.deterministic_index
    assert step.deterministic_score is not None

    payload, applied = apply_refinements(
        payload,
        [
            LlmStepRefinement(
                step_key="p2p_invoice",
                score=step.deterministic_score + 1,
                reason="The free text describes controls plainly better than the option chosen.",
            )
        ],
    )

    assert applied == 1
    assert payload.deterministic_index == original_index
    assert payload.index != original_index


# --------------------------------------------------------------------------- API


def test_the_process_list_shows_all_five_with_four_undefined(client) -> None:
    engagement = create_engagement(client)

    response = client.get(f"/api/v1/engagements/{engagement['id']}/assess/processes")
    assert response.status_code == 200

    processes = response.json()["processes"]
    assert len(processes) == 5
    defined = [p for p in processes if p["defined"]]
    assert [p["key"] for p in defined] == [P2P]


def test_an_answer_round_trips_and_moves_the_progress_count(client) -> None:
    engagement = create_engagement(client)
    base = f"/api/v1/engagements/{engagement['id']}/assess/{P2P}"

    before = client.get(base).json()
    assert before["answered_count"] == 0

    questionnaire = get_questionnaire(P2P)
    question = questionnaire.steps[0].questions[0]
    chosen = question.options[2].label

    response = client.patch(f"{base}/answers/{question.id}", json={"value": chosen})
    assert response.status_code == 200
    assert response.json()["answered_count"] == 1

    # Re-fetched rather than trusting the response — the trap recorded in PROJECT_LOG.
    after = client.get(base).json()
    assert after["answers"][question.id]["value"] == chosen


def test_an_unknown_question_id_is_rejected(client) -> None:
    """A typo would otherwise create an orphan row that never renders and never scores."""
    engagement = create_engagement(client)
    response = client.patch(
        f"/api/v1/engagements/{engagement['id']}/assess/{P2P}/answers/NOT-A-QUESTION",
        json={"value": "x"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "unknown_question"


def test_a_custom_question_appears_in_its_step_and_never_scores(client) -> None:
    engagement = create_engagement(client)
    base = f"/api/v1/engagements/{engagement['id']}/assess/{P2P}"

    response = client.post(
        f"{base}/questions",
        json={"step_key": "p2p_invoice", "text": "Who owns the AP mailbox?"},
    )
    assert response.status_code == 200

    step = next(s for s in response.json()["steps"] if s["key"] == "p2p_invoice")
    custom = [q for q in step["questions"] if q["is_custom"]]
    assert len(custom) == 1
    assert custom[0]["text"] == "Who owns the AP mailbox?"
    assert custom[0]["options"] == [], "a custom question has no place on the ladder"
    assert custom[0]["type"] == "text"


def test_a_custom_question_under_an_unknown_step_is_rejected(client) -> None:
    engagement = create_engagement(client)
    response = client.post(
        f"/api/v1/engagements/{engagement['id']}/assess/{P2P}/questions",
        json={"step_key": "not_a_step", "text": "Anything"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "unknown_step"


def test_scoring_stores_a_version_and_reads_back(client) -> None:
    engagement = create_engagement(client)
    base = f"/api/v1/engagements/{engagement['id']}/assess/{P2P}"

    questionnaire = get_questionnaire(P2P)
    for question in questionnaire.steps[6].questions:
        if question.scores:
            client.patch(f"{base}/answers/{question.id}", json={"value": question.options[3].label})

    first = client.post(f"{base}/score", json={})
    assert first.status_code == 200
    assert first.json()["version"] == 1

    second = client.post(f"{base}/score", json={})
    assert second.json()["version"] == 2, "re-scoring versions rather than mutating"

    latest = client.get(f"{base}/score")
    assert latest.status_code == 200
    assert latest.json()["version"] == 2


def test_an_unscored_process_404s_with_a_named_code(client) -> None:
    engagement = create_engagement(client)
    response = client.get(f"/api/v1/engagements/{engagement['id']}/assess/{P2P}/score")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "no_score"


def test_an_undefined_process_409s_through_the_api(client) -> None:
    engagement = create_engagement(client)
    response = client.get(f"/api/v1/engagements/{engagement['id']}/assess/order_to_cash")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "process_not_defined"


def test_the_processes_route_is_not_shadowed_by_the_process_key_route(client) -> None:
    """FastAPI matches in declaration order — the same trap already hit by export.pdf."""
    engagement = create_engagement(client)
    response = client.get(f"/api/v1/engagements/{engagement['id']}/assess/processes")
    assert response.status_code == 200
    assert "processes" in response.json()


def test_answers_survive_a_rescore(client) -> None:
    """Scoring must never touch the analyst's recorded answers."""
    engagement = create_engagement(client)
    base = f"/api/v1/engagements/{engagement['id']}/assess/{P2P}"

    questionnaire = get_questionnaire(P2P)
    question = questionnaire.steps[0].questions[0]
    chosen = question.options[1].label
    client.patch(f"{base}/answers/{question.id}", json={"value": chosen})

    client.post(f"{base}/score", json={})

    after = client.get(base).json()
    assert after["answers"][question.id]["value"] == chosen


def test_deleting_the_engagement_takes_the_assessment_with_it(client) -> None:
    engagement = create_engagement(client)
    base = f"/api/v1/engagements/{engagement['id']}/assess/{P2P}"

    questionnaire = get_questionnaire(P2P)
    question = questionnaire.steps[0].questions[0]
    client.patch(f"{base}/answers/{question.id}", json={"value": question.options[0].label})
    client.post(f"{base}/score", json={})

    deleted = client.delete(f"/api/v1/engagements/{engagement['id']}?permanent=true")
    assert deleted.status_code == 204

    assert client.get(base).status_code == 404


# --------------------------------------------------------------------------- LLM path


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeModels:
    def __init__(self, text: str) -> None:
        self._text = text
        self.last_contents: str | None = None

    def generate_content(self, **kwargs: object) -> _FakeResponse:
        self.last_contents = str(kwargs.get("contents", ""))
        return _FakeResponse(self._text)


class _FakeClient:
    """Stands in for the Gemini client. Tests never call the live API."""

    def __init__(self, text: str) -> None:
        self.models = _FakeModels(text)


def _llm_generator(text: str):
    from app.core.config import Settings
    from app.services.assess.llm import LlmScoreGenerator

    settings = Settings(gemini_api_key="test-key")
    return LlmScoreGenerator(settings=settings, client=_FakeClient(text))


def test_the_model_writes_the_summary_but_the_arithmetic_stays_deterministic() -> None:
    import json

    questionnaire = get_questionnaire(P2P)
    answers = _answer_step_fully("p2p_invoice", 2)
    rules_payload = score_assessment(questionnaire, answers)

    generator = _llm_generator(
        json.dumps(
            {
                "executive_summary": "Accounts payable carries nine FTEs against 4,200 invoices a month.",
                "shape_note": "Weak at the back end.",
                "step_refinements": [],
                "pointers": [{"kind": "gap", "step_key": "p2p_invoice", "text": "Matching is manual."}],
            }
        )
    )
    payload = generator.score(questionnaire, answers)

    assert payload.generator == "llm"
    assert payload.executive_summary.startswith("Accounts payable carries nine FTEs")
    # The index is the rules' arithmetic — the model wrote prose, not numbers.
    assert payload.index == rules_payload.index
    assert payload.pointers[0].text == "Matching is manual."


def test_a_model_failure_falls_back_to_the_deterministic_score() -> None:
    questionnaire = get_questionnaire(P2P)
    answers = _answer_step_fully("p2p_invoice", 2)
    rules_payload = score_assessment(questionnaire, answers)

    payload = _llm_generator("not json at all").score(questionnaire, answers)

    assert payload.generator == "rules (llm rejected)"
    assert payload.index == rules_payload.index
    assert payload.executive_summary, "the deterministic summary must still be present"


def test_the_evidence_actually_reaches_the_model() -> None:
    """Asserted rather than trusting the wiring — the lesson from the IRL build."""
    import json

    questionnaire = get_questionnaire(P2P)
    answers = _answer_step_fully("p2p_invoice", 2)
    answers["P2P-07-04"] = "4,200 invoices a month against nine AP FTEs."

    generator = _llm_generator(
        json.dumps({"executive_summary": "x", "step_refinements": [], "pointers": []})
    )
    generator.score(questionnaire, answers)

    sent = generator._client.models.last_contents  # type: ignore[attr-defined]
    assert sent is not None
    assert "4,200 invoices a month against nine AP FTEs." in sent
    assert "deterministic" in sent


def test_nothing_answered_does_not_spend_a_model_call() -> None:
    questionnaire = get_questionnaire(P2P)
    generator = _llm_generator("{}")

    payload = generator.score(questionnaire, {})

    assert payload.generator == "rules (nothing assessed)"
    assert generator._client.models.last_contents is None  # type: ignore[attr-defined]
