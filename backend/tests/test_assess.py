"""Tests for the Assess module — questionnaire, answers and scoring.

The rules that matter most here are the ones that stop the score inventing findings: an
unanswered question is not a zero, an unassessed step drops out of the index, and the
model may move a step by at most ±1 with a stated reason.
"""

from unittest import mock

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
O2C = "order_to_cash"
P2M = "plan_to_make"
H2R = "hire_to_retire"
R2R = "record_to_report"

# Every process in the registry. The whole point of the design is that a new process is
# content, so the library invariants must hold for all of them without a code change —
# and as of 2026-09-14 there is no longer a named-but-undefined process to exclude.
DEFINED = [P2P, O2C, P2M, H2R, R2R]


# --------------------------------------------------------------------------- library


@pytest.mark.parametrize(("key", "steps"), [(P2P, 9), (O2C, 8), (P2M, 8), (H2R, 9), (R2R, 8)])
def test_the_questionnaire_loads_and_its_weights_sum_to_100(key: str, steps: int) -> None:
    questionnaire = get_questionnaire(key)
    assert len(questionnaire.steps) == steps
    assert sum(step.weight for step in questionnaire.steps) == 100


@pytest.mark.parametrize("key", DEFINED)
def test_every_question_and_nudge_id_is_unique(key: str) -> None:
    """They key the answer table — a duplicate would make two questions share an answer."""
    questionnaire = get_questionnaire(key)
    ids: list[str] = []
    for step in questionnaire.steps:
        for question in step.questions:
            ids.append(question.id)
            ids.extend(nudge.id for nudge in question.nudges)
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("key", DEFINED)
def test_every_nudge_fires_on_an_option_that_exists(key: str) -> None:
    """A nudge naming a label that is not an option can never fire — silent dead weight."""
    questionnaire = get_questionnaire(key)
    for step in questionnaire.steps:
        for question in step.questions:
            labels = {option.label for option in question.options}
            for nudge in question.nudges:
                wanted = list(nudge.when.in_ or [])
                if nudge.when.equals:
                    wanted.append(nudge.when.equals)
                for label in wanted:
                    assert label in labels, f"{nudge.id} fires on an unknown option"


def test_every_registered_process_is_now_defined() -> None:
    """Five of five, as of 2026-09-14. No process is named with nothing behind it.

    This test previously asserted the opposite for two of them. Keeping it inverted
    rather than deleting it is deliberate: it pins that the registry and the
    questionnaire files agree, which is the invariant that mattered all along.
    """
    registry = get_process_registry()
    by_key = {entry.key: entry for entry in registry.processes}
    assert set(by_key) == set(DEFINED)
    for key in DEFINED:
        assert by_key[key].defined is True, f"{key} is registered but not defined"


def test_the_undefined_path_still_raises_a_409_rather_than_a_404() -> None:
    """No registered process reaches it any more, but the path must stay correct.

    A 404 would imply the process does not exist. The distinction is what makes adding a
    sixth process safe: register it, and it is listed honestly until its questionnaire is
    written. Exercised against a synthetic registry entry, since there is no longer a real
    one to use.
    """
    from app.services.assess.library import ProcessRegistry, RegistryEntry

    stub = ProcessRegistry(
        processes=[
            RegistryEntry(
                key="idea_to_product",
                name="Idea to Product",
                short_name="I2P",
                defined=False,
                description="A sixth process, registered and not yet written.",
            )
        ]
    )
    with mock.patch(
        "app.services.assess.library.get_process_registry", return_value=stub
    ):
        get_questionnaire.cache_clear()
        with pytest.raises(ProcessNotDefinedError) as exc:
            get_questionnaire("idea_to_product")
    get_questionnaire.cache_clear()
    assert exc.value.status_code == 409
    assert exc.value.code == "process_not_defined"


def test_an_unknown_process_key_is_a_library_error() -> None:
    with pytest.raises(ProcessLibraryError):
        get_questionnaire("not_a_process")


# --------------------------------------------------------------------------- scoring


def _answer_step_fully(step_key: str, score_label_index: int, key: str = P2P) -> dict[str, str]:
    """Answer every scoring question in one step, picking the option at a given rank."""
    questionnaire = get_questionnaire(key)
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


def test_the_process_list_shows_all_five_defined(client) -> None:
    engagement = create_engagement(client)

    response = client.get(f"/api/v1/engagements/{engagement['id']}/assess/processes")
    assert response.status_code == 200

    processes = response.json()["processes"]
    assert len(processes) == 5
    defined = [p for p in processes if p["defined"]]
    assert [p["key"] for p in defined] == DEFINED
    assert not [p for p in processes if not p["defined"]], (
        "no process should render a 'Not yet defined' badge any more"
    )


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


def test_the_409_path_is_no_longer_reachable_through_the_api(client) -> None:
    """Every registered process is now defined, so no API call can produce a 409.

    The path itself is still correct and still covered at the library level by
    test_the_undefined_path_still_raises_a_409_rather_than_a_404 — this asserts only that
    no *real* process reaches it, which is the thing that changed on 2026-09-14.

    An unregistered key is a different matter and is deliberately not asserted here:
    `ProcessLibraryError` is a plain RuntimeError rather than an `AppError`, so it
    surfaces as a 500. That is pre-existing behaviour, unchanged by this work, and it is
    recorded as a known gap in docs/PROJECT_LOG.md rather than fixed inside a
    content-only change.
    """
    engagement = create_engagement(client)
    for key in DEFINED:
        response = client.get(f"/api/v1/engagements/{engagement['id']}/assess/{key}")
        assert response.status_code == 200, f"{key} should serve a questionnaire"


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


# ------------------------------------------------------ answer remarks (2026-09-02)


def test_remarks_save_alongside_the_option(client) -> None:
    engagement = create_engagement(client)
    base = f"/api/v1/engagements/{engagement['id']}/assess/{P2P}"

    questionnaire = get_questionnaire(P2P)
    question = questionnaire.steps[0].questions[0]
    chosen = question.options[2].label

    client.patch(f"{base}/answers/{question.id}", json={"value": chosen})
    client.patch(
        f"{base}/answers/{question.id}",
        json={"remarks": "Catalogue covers MRO only; capex still raised by email."},
    )

    stored = client.get(base).json()["answers"][question.id]
    assert stored["value"] == chosen
    assert stored["remarks"].startswith("Catalogue covers MRO only")


def test_saving_a_remark_never_clears_the_option(client) -> None:
    """The option and the remark are separate controls; one must not wipe the other."""
    engagement = create_engagement(client)
    base = f"/api/v1/engagements/{engagement['id']}/assess/{P2P}"

    questionnaire = get_questionnaire(P2P)
    question = questionnaire.steps[0].questions[0]
    chosen = question.options[1].label

    client.patch(f"{base}/answers/{question.id}", json={"value": chosen})
    client.patch(f"{base}/answers/{question.id}", json={"remarks": "Confirmed verbally."})

    stored = client.get(base).json()["answers"][question.id]
    assert stored["value"] == chosen, "a remark write must not blank the answer"

    # And the reverse: changing the option keeps the remark.
    client.patch(f"{base}/answers/{question.id}", json={"value": question.options[3].label})
    stored = client.get(base).json()["answers"][question.id]
    assert stored["remarks"] == "Confirmed verbally."


def test_a_remark_alone_does_not_count_as_answered(client) -> None:
    """Progress measures answers. A note with no option is evidence, not a decision."""
    engagement = create_engagement(client)
    base = f"/api/v1/engagements/{engagement['id']}/assess/{P2P}"

    questionnaire = get_questionnaire(P2P)
    question = questionnaire.steps[0].questions[0]

    client.patch(f"{base}/answers/{question.id}", json={"remarks": "Chasing a follow-up."})

    assert client.get(base).json()["answered_count"] == 0


def test_remarks_never_move_the_deterministic_score(client) -> None:
    """Scoring reads the selected options alone. Remarks are narrative evidence."""
    engagement = create_engagement(client)
    base = f"/api/v1/engagements/{engagement['id']}/assess/{P2P}"

    questionnaire = get_questionnaire(P2P)
    for question in questionnaire.steps[6].questions:
        if question.scores:
            client.patch(
                f"{base}/answers/{question.id}", json={"value": question.options[2].label}
            )

    first = client.post(f"{base}/score", json={}).json()["payload"]["index"]

    for question in questionnaire.steps[6].questions:
        if question.scores:
            client.patch(
                f"{base}/answers/{question.id}",
                json={"remarks": "Management says this is far worse in practice."},
            )

    second = client.post(f"{base}/score", json={}).json()["payload"]["index"]
    assert first == second


def test_remarks_reach_the_model_as_evidence() -> None:
    """Asserted, not assumed â€” the remark is often the only place a specific is recorded."""
    import json

    questionnaire = get_questionnaire(P2P)
    answers = _answer_step_fully("p2p_invoice", 2)
    remarks = {"P2P-07-01": "4,200 invoices a month keyed by nine AP staff in Rotterdam."}

    generator = _llm_generator(
        json.dumps({"executive_summary": "x", "step_refinements": [], "pointers": []})
    )
    generator.score(questionnaire, answers, None, remarks)

    sent = generator._client.models.last_contents  # type: ignore[attr-defined]
    assert sent is not None
    assert "4,200 invoices a month keyed by nine AP staff" in sent
    assert "consultant_remarks" in sent


# ------------------------------------------------- Order to Cash (2026-09-08)
#
# O2C is the second defined process and the first real test that the module's "a new
# process is pure content" claim holds. The library invariants above are parameterised
# over both; what follows is what is specific to this process — its own step
# decomposition, its own weights, and its own commercial reading of the shape.


def test_the_o2c_steps_carry_the_model_documents_weights() -> None:
    """The weights are the model, so a silent retune must break a test."""
    questionnaire = get_questionnaire(O2C)
    weights = {step.key: step.weight for step in questionnaire.steps}
    assert weights == {
        "o2c_customer_credit": 10,
        "o2c_order_capture": 13,
        "o2c_pricing": 12,
        "o2c_fulfilment": 10,
        "o2c_invoicing": 18,
        "o2c_cash_application": 15,
        "o2c_collections": 12,
        "o2c_disputes": 10,
    }
    # Invoicing is the heaviest step: highest volume, most manual effort, and billing
    # accuracy governs both DSO and disputes. O2C_AUTOMATION_MODEL.md §3.
    assert max(weights, key=lambda k: weights[k]) == "o2c_invoicing"


def test_every_o2c_scoring_option_sits_on_the_shared_ladder() -> None:
    """0-5, and increasing down the option list, or the ladder has been broken."""
    questionnaire = get_questionnaire(O2C)
    for step in questionnaire.steps:
        for question in step.questions:
            if not question.scores:
                continue
            scores = [option.score for option in question.options]
            assert all(0 <= s <= 5 for s in scores), f"{question.id} leaves the ladder"
            assert scores == sorted(scores), f"{question.id} options are not in ladder order"


def test_o2c_free_text_questions_never_score() -> None:
    """They capture DSO, volumes and the caveats the summary draws on — not a level."""
    questionnaire = get_questionnaire(O2C)
    text_questions = [
        q for step in questionnaire.steps for q in step.questions if q.type == "text"
    ]
    assert text_questions, "the evidence questions are what make the number defensible"
    assert all(q.options == [] for q in text_questions)


def test_an_unanswered_o2c_question_is_not_scored_as_zero() -> None:
    """The rule that matters most, asserted against this process rather than inherited."""
    questionnaire = get_questionnaire(O2C)
    answers = _answer_step_fully("o2c_invoicing", 5, O2C)

    payload = score_assessment(questionnaire, answers)
    invoicing = next(s for s in payload.steps if s.key == "o2c_invoicing")
    collections = next(s for s in payload.steps if s.key == "o2c_collections")

    assert invoicing.assessed is True
    assert collections.assessed is False
    assert collections.score is None
    assert payload.steps_assessed == 1
    assert payload.steps_total == 8
    # The one assessed step is the whole index — its weight of 18 is the denominator.
    assert payload.index == pytest.approx((invoicing.score or 0) * 20, abs=0.1)


def test_the_heaviest_o2c_gap_is_the_first_pointer() -> None:
    questionnaire = get_questionnaire(O2C)
    answers: dict[str, str] = {}
    for step in questionnaire.steps:
        for question in step.questions:
            if question.scores:
                answers[question.id] = question.options[0].label

    payload = score_assessment(questionnaire, answers)
    gaps = [p for p in payload.pointers if p.kind == "gap"]
    assert gaps, "an all-manual cycle must produce gaps"
    # Invoicing & billing carries 18%, the heaviest weight in the O2C model.
    assert gaps[0].step_key == "o2c_invoicing"


def _o2c_shaped(front_rank: int, back_rank: int) -> dict[str, str]:
    """Answer O2C with one maturity at the selling end and another at the cash end."""
    questionnaire = get_questionnaire(O2C)
    shape = questionnaire.shape
    assert shape is not None
    answers: dict[str, str] = {}
    for step in questionnaire.steps:
        if step.sn in shape.front_steps:
            rank = front_rank
        elif step.sn in shape.back_steps:
            rank = back_rank
        else:
            continue
        for question in step.questions:
            if question.scores:
                answers[question.id] = question.options[
                    min(rank, len(question.options) - 1)
                ].label
    return answers


def test_a_front_loaded_o2c_cycle_reads_as_a_working_capital_finding() -> None:
    """The shape note must be O2C's own — P2P's talks about accounts payable."""
    questionnaire = get_questionnaire(O2C)
    payload = score_assessment(questionnaire, _o2c_shaped(front_rank=5, back_rank=0))

    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Front-loaded")
    assert "working capital problem grows with revenue" in payload.shape_note
    assert "accounts payable" not in payload.shape_note, "P2P's wording has leaked"
    # The measured means are appended, so the note is evidenced rather than asserted.
    assert "front" in payload.shape_note and "/5" in payload.shape_note


def test_a_back_loaded_o2c_cycle_names_the_upstream_defect() -> None:
    questionnaire = get_questionnaire(O2C)
    payload = score_assessment(questionnaire, _o2c_shaped(front_rank=0, back_rank=5))

    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Back-loaded")
    assert "created at order entry" in payload.shape_note


def test_an_even_o2c_cycle_points_the_reader_at_dso() -> None:
    questionnaire = get_questionnaire(O2C)
    payload = score_assessment(questionnaire, _o2c_shaped(front_rank=2, back_rank=2))

    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Broadly even")
    assert "days sales outstanding" in payload.shape_note


def test_the_p2p_shape_note_is_unchanged_by_the_yaml_shape_block() -> None:
    """P2P declares no `shape` block, so it must say exactly what it said before."""
    questionnaire = get_questionnaire(P2P)
    assert questionnaire.shape is None

    answers: dict[str, str] = {}
    for step in questionnaire.steps:
        rank = 4 if step.sn <= 3 else 0
        for question in step.questions:
            if question.scores:
                answers[question.id] = question.options[
                    min(rank, len(question.options) - 1)
                ].label

    payload = score_assessment(questionnaire, answers)
    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Front-loaded")
    assert "accounts payable" in payload.shape_note


def test_the_o2c_deterministic_score_is_reproducible() -> None:
    questionnaire = get_questionnaire(O2C)
    answers = _answer_step_fully("o2c_invoicing", 2, O2C) | _answer_step_fully(
        "o2c_collections", 3, O2C
    )

    first = score_assessment(questionnaire, answers)
    second = score_assessment(questionnaire, answers)

    assert first.index == second.index
    assert [s.score for s in first.steps] == [s.score for s in second.steps]


def test_an_o2c_refinement_obeys_the_same_one_point_bound() -> None:
    """The +/-1 bound is process-agnostic — asserted here rather than assumed."""
    questionnaire = get_questionnaire(O2C)
    payload = score_assessment(questionnaire, _answer_step_fully("o2c_invoicing", 2, O2C))
    step = next(s for s in payload.steps if s.key == "o2c_invoicing")
    original = step.deterministic_score
    assert original is not None

    payload, applied = apply_refinements(
        payload,
        [
            LlmStepRefinement(
                step_key="o2c_invoicing",
                score=original + 2,
                reason="A long enough reason to pass the length check but too big a jump.",
            )
        ],
    )
    assert applied == 0

    payload, applied = apply_refinements(
        payload,
        [
            LlmStepRefinement(
                step_key="o2c_invoicing",
                score=original + 1,
                reason="Management described manual rework on every recurring billing cycle.",
            )
        ],
    )
    assert applied == 1
    refined = next(s for s in payload.steps if s.key == "o2c_invoicing")
    assert refined.deterministic_score == original, "the rules score must survive"


# ------------------------------------------------------------------ O2C through the API


def test_the_process_list_shows_every_defined_process(client) -> None:
    engagement = create_engagement(client)

    response = client.get(f"/api/v1/engagements/{engagement['id']}/assess/processes")
    assert response.status_code == 200

    processes = response.json()["processes"]
    assert len(processes) == 5
    assert [p["key"] for p in processes if p["defined"]] == DEFINED
    assert [p["key"] for p in processes if not p["defined"]] == []


def test_the_o2c_questionnaire_serves_its_eight_steps(client) -> None:
    engagement = create_engagement(client)
    response = client.get(f"/api/v1/engagements/{engagement['id']}/assess/{O2C}")

    assert response.status_code == 200
    body = response.json()
    assert len(body["steps"]) == 8
    assert body["steps"][0]["key"] == "o2c_customer_credit"
    assert body["answered_count"] == 0


def test_an_o2c_answer_round_trips(client) -> None:
    engagement = create_engagement(client)
    base = f"/api/v1/engagements/{engagement['id']}/assess/{O2C}"

    questionnaire = get_questionnaire(O2C)
    question = questionnaire.steps[1].questions[0]
    chosen = question.options[3].label

    saved = client.patch(f"{base}/answers/{question.id}", json={"value": chosen})
    assert saved.status_code == 200

    # Re-fetched rather than trusting the response — the trap recorded in PROJECT_LOG.
    after = client.get(base).json()
    assert after["answers"][question.id]["value"] == chosen
    assert after["answered_count"] == 1


def test_the_two_processes_keep_separate_answers(client) -> None:
    """One engagement assesses both. An answer to one must never show against the other."""
    engagement = create_engagement(client)
    p2p_base = f"/api/v1/engagements/{engagement['id']}/assess/{P2P}"
    o2c_base = f"/api/v1/engagements/{engagement['id']}/assess/{O2C}"

    p2p_question = get_questionnaire(P2P).steps[0].questions[0]
    o2c_question = get_questionnaire(O2C).steps[0].questions[0]

    client.patch(
        f"{p2p_base}/answers/{p2p_question.id}", json={"value": p2p_question.options[1].label}
    )
    client.patch(
        f"{o2c_base}/answers/{o2c_question.id}", json={"value": o2c_question.options[4].label}
    )

    p2p_body = client.get(p2p_base).json()
    o2c_body = client.get(o2c_base).json()

    assert p2p_body["answered_count"] == 1
    assert o2c_body["answered_count"] == 1
    assert o2c_question.id not in p2p_body["answers"]
    assert p2p_question.id not in o2c_body["answers"]


def test_an_o2c_answer_cannot_be_saved_against_a_p2p_question_id(client) -> None:
    """The ids are namespaced, and the route must enforce it rather than trusting them."""
    engagement = create_engagement(client)
    p2p_question = get_questionnaire(P2P).steps[0].questions[0]

    response = client.patch(
        f"/api/v1/engagements/{engagement['id']}/assess/{O2C}/answers/{p2p_question.id}",
        json={"value": "anything"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "unknown_question"


def test_o2c_scores_and_versions_independently_of_p2p(client) -> None:
    engagement = create_engagement(client)
    o2c_base = f"/api/v1/engagements/{engagement['id']}/assess/{O2C}"
    p2p_base = f"/api/v1/engagements/{engagement['id']}/assess/{P2P}"

    questionnaire = get_questionnaire(O2C)
    invoicing = next(s for s in questionnaire.steps if s.key == "o2c_invoicing")
    for question in invoicing.questions:
        if question.scores:
            client.patch(
                f"{o2c_base}/answers/{question.id}", json={"value": question.options[2].label}
            )

    first = client.post(f"{o2c_base}/score", json={})
    assert first.status_code == 200
    assert first.json()["version"] == 1

    # P2P has its own version sequence and its own emptiness.
    assert client.get(f"{p2p_base}/score").status_code == 404

    second = client.post(f"{o2c_base}/score", json={})
    assert second.json()["version"] == 2
    assert client.get(f"{o2c_base}/score").json()["version"] == 2


def test_a_custom_o2c_question_lands_in_its_own_step(client) -> None:
    engagement = create_engagement(client)
    response = client.post(
        f"/api/v1/engagements/{engagement['id']}/assess/{O2C}/questions",
        json={"step_key": "o2c_collections", "text": "Who owns the aged debtors report?"},
    )
    assert response.status_code == 200

    step = next(s for s in response.json()["steps"] if s["key"] == "o2c_collections")
    custom = [q for q in step["questions"] if q["is_custom"]]
    assert len(custom) == 1
    assert custom[0]["options"] == [], "a custom question has no place on the ladder"


def test_a_p2p_step_key_is_rejected_under_o2c(client) -> None:
    engagement = create_engagement(client)
    response = client.post(
        f"/api/v1/engagements/{engagement['id']}/assess/{O2C}/questions",
        json={"step_key": "p2p_invoice", "text": "Anything"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "unknown_step"


def test_o2c_evidence_reaches_the_model() -> None:
    """The DSO and volume questions are the point of the free text — assert they arrive."""
    import json

    questionnaire = get_questionnaire(O2C)
    answers = _answer_step_fully("o2c_collections", 1, O2C)
    answers["O2C-07-04"] = "DSO is 78 days against 45-day terms, and rising."

    generator = _llm_generator(
        json.dumps({"executive_summary": "x", "step_refinements": [], "pointers": []})
    )
    generator.score(questionnaire, answers)

    sent = generator._client.models.last_contents  # type: ignore[attr-defined]
    assert sent is not None
    assert "DSO is 78 days against 45-day terms" in sent


def test_the_model_may_not_overwrite_an_authored_shape_note() -> None:
    """Found by reading a generated O2C score, not by a test — the note came back as the
    model's own paraphrase, losing both the authored commercial reading and the measured
    front/back means that evidence it. A process that declares a `shape` block has already
    decided what its shape means; the model writes prose, not that judgement.
    """
    import json

    questionnaire = get_questionnaire(O2C)
    answers = _o2c_shaped(front_rank=5, back_rank=0)

    generator = _llm_generator(
        json.dumps(
            {
                "executive_summary": "A summary the model is entitled to write.",
                "shape_note": "The cycle deteriorates from fulfilment onwards.",
                "step_refinements": [],
                "pointers": [],
            }
        )
    )
    payload = generator.score(questionnaire, answers)

    assert payload.generator == "llm"
    assert payload.executive_summary.startswith("A summary the model is entitled to write")
    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Front-loaded")
    assert "working capital problem grows with revenue" in payload.shape_note
    assert "deteriorates from fulfilment" not in payload.shape_note
    # The measured means must survive too — they are the evidence for the claim.
    assert "/5)" in payload.shape_note


def test_the_model_still_writes_the_shape_note_where_none_is_authored() -> None:
    """P2P declares no `shape` block, so the previous behaviour must be untouched."""
    import json

    questionnaire = get_questionnaire(P2P)
    assert questionnaire.shape is None
    answers = _answer_step_fully("p2p_invoice", 2)

    generator = _llm_generator(
        json.dumps(
            {
                "executive_summary": "x",
                "shape_note": "Weak at the back end.",
                "step_refinements": [],
                "pointers": [],
            }
        )
    )
    payload = generator.score(questionnaire, answers)

    assert payload.shape_note == "Weak at the back end."


# --------------------------------------------------- Plan to Make (2026-09-11)
#
# The third defined process. The library invariants above are parameterised over all
# three; what follows is what is specific to P2M — its own decomposition, its own
# weights, and the one thing that makes it different from P2P and O2C: it is a decision
# cycle, not a transaction cycle, and it need not apply in full to every target.


def test_the_p2m_steps_carry_the_model_documents_weights() -> None:
    """The weights are the model, so a silent retune must break a test."""
    questionnaire = get_questionnaire(P2M)
    weights = {step.key: step.weight for step in questionnaire.steps}
    assert weights == {
        "p2m_demand": 14,
        "p2m_sop": 10,
        "p2m_master_data": 13,
        "p2m_mrp": 15,
        "p2m_scheduling": 12,
        "p2m_execution": 12,
        "p2m_quality": 10,
        "p2m_inventory": 14,
    }
    # MRP is the heaviest step: the highest volume of decisions in the cycle, and where a
    # licensed capability most often sits unused. P2M_AUTOMATION_MODEL.md §3.
    assert max(weights, key=lambda k: weights[k]) == "p2m_mrp"


def test_every_p2m_scoring_option_sits_on_the_shared_ladder() -> None:
    """0-5, and increasing down the option list, or the ladder has been broken."""
    questionnaire = get_questionnaire(P2M)
    for step in questionnaire.steps:
        for question in step.questions:
            if not question.scores:
                continue
            scores = [option.score for option in question.options]
            assert all(0 <= s <= 5 for s in scores), f"{question.id} leaves the ladder"
            assert scores == sorted(scores), f"{question.id} options are not in ladder order"


def test_p2m_free_text_questions_never_score() -> None:
    """They capture stock accuracy, forecast accuracy and turns — not a level."""
    questionnaire = get_questionnaire(P2M)
    text_questions = [
        q for step in questionnaire.steps for q in step.questions if q.type == "text"
    ]
    assert text_questions, "the evidence questions are what make the number defensible"
    assert all(q.options == [] for q in text_questions)


def test_the_mrp_spreadsheet_rework_option_scores_as_a_two() -> None:
    """The rule that matters most in this process, pinned.

    A configured MRP run whose output is exported to Excel, reworked and re-entered is
    not integrated: the system proposes and a human decides. Scoring it as a 3 would let
    a licence stand in for a working process, which is the failure this whole module
    exists to catch.
    """
    questionnaire = get_questionnaire(P2M)
    step = next(s for s in questionnaire.steps if s.key == "p2m_mrp")
    question = next(q for q in step.questions if q.id == "P2M-04-01")
    option = next(o for o in question.options if "exported to a spreadsheet" in o.label)
    assert option.score == 2


def test_an_unanswered_p2m_question_is_not_scored_as_zero() -> None:
    questionnaire = get_questionnaire(P2M)
    answers = _answer_step_fully("p2m_mrp", 5, P2M)

    payload = score_assessment(questionnaire, answers)
    mrp = next(s for s in payload.steps if s.key == "p2m_mrp")
    quality = next(s for s in payload.steps if s.key == "p2m_quality")

    assert mrp.assessed is True
    assert quality.assessed is False
    assert quality.score is None
    assert payload.steps_assessed == 1
    assert payload.steps_total == 8
    assert payload.index == pytest.approx((mrp.score or 0) * 20, abs=0.1)


def test_a_non_manufacturing_target_can_be_scored_on_the_steps_that_apply() -> None:
    """The applicability rule from the model document, §1.

    A distributor has no production scheduling, shop floor or quality process. Leaving
    those steps blank must produce a defensible index from the rest rather than dragging
    the score down — otherwise the questionnaire forces an invented answer.
    """
    questionnaire = get_questionnaire(P2M)
    answers: dict[str, str] = {}
    for key in ("p2m_demand", "p2m_sop", "p2m_master_data", "p2m_mrp", "p2m_inventory"):
        answers |= _answer_step_fully(key, 3, P2M)

    payload = score_assessment(questionnaire, answers)

    assert payload.steps_assessed == 5
    assert payload.steps_total == 8
    for key in ("p2m_scheduling", "p2m_execution", "p2m_quality"):
        assert next(s for s in payload.steps if s.key == key).assessed is False
    # The index is built only from the assessed steps, so a distributor still scores well.
    assert payload.index > 50, "unassessed steps must not drag the index down"


def test_the_heaviest_p2m_gap_is_the_first_pointer() -> None:
    questionnaire = get_questionnaire(P2M)
    answers: dict[str, str] = {}
    for step in questionnaire.steps:
        for question in step.questions:
            if question.scores:
                answers[question.id] = question.options[0].label

    payload = score_assessment(questionnaire, answers)
    gaps = [p for p in payload.pointers if p.kind == "gap"]
    assert gaps, "an all-manual cycle must produce gaps"
    # Material requirements planning carries 15%, the heaviest weight in the P2M model.
    assert gaps[0].step_key == "p2m_mrp"


def _p2m_shaped(front_rank: int, back_rank: int) -> dict[str, str]:
    """Answer P2M with one maturity in planning and another on the floor."""
    questionnaire = get_questionnaire(P2M)
    shape = questionnaire.shape
    assert shape is not None
    answers: dict[str, str] = {}
    for step in questionnaire.steps:
        if step.sn in shape.front_steps:
            rank = front_rank
        elif step.sn in shape.back_steps:
            rank = back_rank
        else:
            continue
        for question in step.questions:
            if question.scores:
                answers[question.id] = question.options[
                    min(rank, len(question.options) - 1)
                ].label
    return answers


def test_a_front_loaded_p2m_cycle_points_at_the_floor_not_the_planning_tool() -> None:
    """The shape note must be P2M's own — P2P's talks about accounts payable."""
    questionnaire = get_questionnaire(P2M)
    payload = score_assessment(questionnaire, _p2m_shaped(front_rank=5, back_rank=0))

    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Front-loaded")
    assert "remediation is on the floor" in payload.shape_note
    assert "accounts payable" not in payload.shape_note, "P2P's wording has leaked"
    assert "working capital problem grows" not in payload.shape_note, "O2C's wording has leaked"


def test_a_back_loaded_p2m_cycle_names_efficient_production_of_the_wrong_things() -> None:
    questionnaire = get_questionnaire(P2M)
    payload = score_assessment(questionnaire, _p2m_shaped(front_rank=0, back_rank=5))

    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Back-loaded")
    assert "efficient at making the wrong things" in payload.shape_note


def test_an_even_p2m_cycle_points_the_reader_at_stock_accuracy() -> None:
    questionnaire = get_questionnaire(P2M)
    payload = score_assessment(questionnaire, _p2m_shaped(front_rank=2, back_rank=2))

    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Broadly even")
    assert "stock-record accuracy" in payload.shape_note


def test_the_p2m_deterministic_score_is_reproducible() -> None:
    questionnaire = get_questionnaire(P2M)
    answers = _answer_step_fully("p2m_mrp", 2, P2M) | _answer_step_fully(
        "p2m_inventory", 3, P2M
    )

    first = score_assessment(questionnaire, answers)
    second = score_assessment(questionnaire, answers)

    assert first.index == second.index
    assert [s.score for s in first.steps] == [s.score for s in second.steps]


# ------------------------------------------------------------------ P2M through the API


def test_the_p2m_questionnaire_serves_its_eight_steps(client) -> None:
    engagement = create_engagement(client)
    response = client.get(f"/api/v1/engagements/{engagement['id']}/assess/{P2M}")

    assert response.status_code == 200
    body = response.json()
    assert len(body["steps"]) == 8
    assert body["steps"][0]["key"] == "p2m_demand"
    assert body["answered_count"] == 0


def test_the_three_processes_keep_separate_answers(client) -> None:
    """One engagement can assess all three. An answer to one must not appear on another."""
    engagement = create_engagement(client)
    base = f"/api/v1/engagements/{engagement['id']}/assess"

    first = {key: get_questionnaire(key).steps[0].questions[0] for key in DEFINED}
    for key, question in first.items():
        client.patch(
            f"{base}/{key}/answers/{question.id}",
            json={"value": question.options[1].label},
        )

    for key in first:
        body = client.get(f"{base}/{key}").json()
        assert body["answered_count"] == 1
        others = [q.id for k, q in first.items() if k != key]
        for other in others:
            assert other not in body["answers"]


def test_a_p2m_step_key_is_rejected_under_o2c(client) -> None:
    engagement = create_engagement(client)
    response = client.post(
        f"/api/v1/engagements/{engagement['id']}/assess/{O2C}/questions",
        json={"step_key": "p2m_mrp", "text": "Anything"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "unknown_step"


def test_p2m_evidence_reaches_the_model() -> None:
    """Stock accuracy is the number that governs how much of the rest can be believed."""
    import json

    questionnaire = get_questionnaire(P2M)
    answers = _answer_step_fully("p2m_inventory", 1, P2M)
    answers["P2M-08-04"] = "Inventory is EUR 18.4m at 3.1 turns; provision EUR 2.2m."

    generator = _llm_generator(
        json.dumps({"executive_summary": "x", "step_refinements": [], "pointers": []})
    )
    generator.score(questionnaire, answers)

    sent = generator._client.models.last_contents  # type: ignore[attr-defined]
    assert sent is not None
    assert "EUR 18.4m at 3.1 turns" in sent


# ------------------------------------------------ Hire to Retire (2026-09-14)
#
# The fourth defined process, and the first whose automation gap is also a security
# finding. The library invariants above are parameterised over all five; what follows is
# what is specific to H2R - its own decomposition, weights chosen by exposure rather than
# volume, and the rule that a documented offboarding process with no measured revocation
# lag cannot score as though it were automated.


def test_the_h2r_steps_carry_the_model_documents_weights() -> None:
    """The weights are the model, so a silent retune must break a test."""
    questionnaire = get_questionnaire(H2R)
    weights = {step.key: step.weight for step in questionnaire.steps}
    assert weights == {
        "h2r_recruiting": 9,
        "h2r_onboarding": 14,
        "h2r_employee_data": 13,
        "h2r_payroll": 16,
        "h2r_time": 11,
        "h2r_performance": 8,
        "h2r_learning": 7,
        "h2r_offboarding": 14,
        "h2r_compliance": 8,
    }
    # Payroll is the heaviest: right every period in every jurisdiction, and the payroll
    # system count predicts separation cost. H2R_AUTOMATION_MODEL.md section 3.
    assert max(weights, key=lambda k: weights[k]) == "h2r_payroll"
    # The substantive departure from P2P and O2C: weight follows exposure, not volume.
    # Offboarding processes a trivial number of events and outweighs recruiting, which
    # processes more. If that inverts, the model has been rewritten by accident.
    assert weights["h2r_offboarding"] > weights["h2r_recruiting"]


def test_every_h2r_scoring_option_sits_on_the_shared_ladder() -> None:
    """0-5, and increasing down the option list, or the ladder has been broken."""
    questionnaire = get_questionnaire(H2R)
    for step in questionnaire.steps:
        for question in step.questions:
            if not question.scores:
                continue
            scores = [option.score for option in question.options]
            assert all(0 <= s <= 5 for s in scores), f"{question.id} leaves the ladder"
            assert scores == sorted(scores), f"{question.id} options are not in ladder order"


def test_h2r_free_text_questions_never_score() -> None:
    """They capture the revocation lag, the payroll count and headcount - not a level."""
    questionnaire = get_questionnaire(H2R)
    text_questions = [
        q for step in questionnaire.steps for q in step.questions if q.type == "text"
    ]
    assert text_questions, "the evidence questions are what make the number defensible"
    assert all(q.options == [] for q in text_questions)


def test_a_documented_but_unmeasured_revocation_process_scores_as_a_two() -> None:
    """The rule that matters most in this process, pinned.

    Every management team has an offboarding checklist and it evidences nothing. The
    failure mode here is not the absence of a process but its uneven execution, so the
    score has to turn on whether anyone has counted the lag. Scoring a documented-but-
    unmeasured process as integrated would let a policy document stand in for a control,
    and the finding this process exists to produce - live credentials belonging to people
    who have left - would be scored away. H2R_AUTOMATION_MODEL.md section 2 and 3.1.
    """
    questionnaire = get_questionnaire(H2R)
    step = next(s for s in questionnaire.steps if s.key == "h2r_offboarding")
    question = next(q for q in step.questions if q.id == "H2R-08-02")

    documented = next(
        o for o in question.options if "compliance with it is not measured" in o.label
    )
    assert documented.score == 2

    # And measurement, not tooling, is what lifts it.
    measured = next(
        o for o in question.options if o.label.startswith("The revocation lag is measured")
    )
    assert measured.score == 4
    assert measured.score > documented.score


def test_copying_a_colleagues_access_cannot_score_as_integrated() -> None:
    """The provisioning half of the same rule.

    Access assigned by copying an existing user is where entitlement creep begins, and it
    compounds - the colleague's access was itself copied from someone else. A workflow
    that raises the request does not change what is being granted, so the presence of
    tooling must not lift this above 2.
    """
    questionnaire = get_questionnaire(H2R)
    step = next(s for s in questionnaire.steps if s.key == "h2r_onboarding")
    question = next(q for q in step.questions if q.id == "H2R-02-01")

    copied = next(o for o in question.options if "copied from an existing user" in o.label)
    role_based = next(o for o in question.options if "role-based access profiles" in o.label)

    assert copied.score == 2
    assert role_based.score == 3, "role-based provisioning is what earns the 3"


def test_the_offboarding_step_asks_for_the_lag_as_evidence() -> None:
    """A score without the measured lag beside it has not tested the finding.

    The model document's section 4 says so explicitly; this pins that the questionnaire
    actually carries a free-text question to capture it, rather than only scoring the
    practice.
    """
    questionnaire = get_questionnaire(H2R)
    step = next(s for s in questionnaire.steps if s.key == "h2r_offboarding")
    evidence = [q for q in step.questions if q.type == "text"]
    assert evidence, "offboarding must capture the measured lag as evidence"
    assert any("lag" in q.text.lower() for q in evidence)


def test_the_payroll_step_asks_how_many_payroll_systems_there_are() -> None:
    """The carve-out reading: several countries usually means several payrolls.

    Each is a separate transition service, migration and local compliance obligation, so
    the count is one of the most useful single numbers in this assessment.
    """
    questionnaire = get_questionnaire(H2R)
    step = next(s for s in questionnaire.steps if s.key == "h2r_payroll")
    question = next(q for q in step.questions if q.id == "H2R-04-02")
    assert question.scores, "the payroll estate's fragmentation is scored, not just noted"
    # Fragmentation scores below consolidation, and consolidation tops out at 3: a single
    # payroll is a precondition for an automated one, not evidence of one.
    fragmented = next(o for o in question.options if o.label.startswith("Four or more"))
    single = next(o for o in question.options if o.label.startswith("One country"))
    assert fragmented.score < single.score
    assert single.score == 3


def test_an_unanswered_h2r_question_is_not_scored_as_zero() -> None:
    questionnaire = get_questionnaire(H2R)
    answers = _answer_step_fully("h2r_payroll", 5, H2R)

    payload = score_assessment(questionnaire, answers)
    payroll = next(s for s in payload.steps if s.key == "h2r_payroll")
    learning = next(s for s in payload.steps if s.key == "h2r_learning")

    assert payroll.assessed is True
    assert learning.assessed is False
    assert learning.score is None
    assert payload.steps_assessed == 1
    assert payload.steps_total == 9


def test_a_small_target_can_be_scored_without_the_steps_it_has_outgrown() -> None:
    """The applicability rule from the model document, section 1.

    A 40-person target genuinely does not need a learning management system, and scoring
    step 7 harshly for its absence manufactures a finding. The distinction the analyst
    makes is between too small to need it and too disorganised to have it; the scoring
    must support the first reading.
    """
    questionnaire = get_questionnaire(H2R)
    answers: dict[str, str] = {}
    for key in (
        "h2r_onboarding",
        "h2r_employee_data",
        "h2r_payroll",
        "h2r_offboarding",
    ):
        answers |= _answer_step_fully(key, 3, H2R)

    payload = score_assessment(questionnaire, answers)

    assert payload.steps_assessed == 4
    assert payload.steps_total == 9
    assert next(s for s in payload.steps if s.key == "h2r_learning").assessed is False
    assert payload.index > 50, "unassessed steps must not drag the index down"


def test_the_heaviest_h2r_gap_is_the_first_pointer() -> None:
    questionnaire = get_questionnaire(H2R)
    answers: dict[str, str] = {}
    for step in questionnaire.steps:
        for question in step.questions:
            if question.scores:
                answers[question.id] = question.options[0].label

    payload = score_assessment(questionnaire, answers)
    gaps = [p for p in payload.pointers if p.kind == "gap"]
    assert gaps, "an all-manual lifecycle must produce gaps"
    # Payroll carries 16%, the heaviest weight in the H2R model.
    assert gaps[0].step_key == "h2r_payroll"


def _h2r_shaped(front_rank: int, back_rank: int) -> dict[str, str]:
    """Answer H2R with one maturity at the joining end and another at the leaving end."""
    questionnaire = get_questionnaire(H2R)
    shape = questionnaire.shape
    assert shape is not None
    answers: dict[str, str] = {}
    for step in questionnaire.steps:
        if step.sn in shape.front_steps:
            rank = front_rank
        elif step.sn in shape.back_steps:
            rank = back_rank
        else:
            continue
        for question in step.questions:
            if question.scores:
                answers[question.id] = question.options[
                    min(rank, len(question.options) - 1)
                ].label
    return answers


def test_a_front_loaded_h2r_cycle_reads_as_a_security_finding() -> None:
    """The shape note must be H2R's own, and must name the credential exposure.

    A front-loaded H2R is not an efficiency observation - it is a growing population of
    live accounts belonging to people who have left. If this note reads like P2P's or
    O2C's, the commercial point has been lost.
    """
    questionnaire = get_questionnaire(H2R)
    payload = score_assessment(questionnaire, _h2r_shaped(front_rank=5, back_rank=0))

    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Front-loaded")
    assert "live credentials" in payload.shape_note
    assert "accounts payable" not in payload.shape_note, "P2P's wording has leaked"
    assert "working capital" not in payload.shape_note, "O2C's wording has leaked"
    assert "shop floor" not in payload.shape_note, "P2M's wording has leaked"


def test_a_back_loaded_h2r_cycle_names_controls_operated_on_bad_data() -> None:
    questionnaire = get_questionnaire(H2R)
    payload = score_assessment(questionnaire, _h2r_shaped(front_rank=0, back_rank=5))

    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Back-loaded")
    assert "unreliable data" in payload.shape_note


def test_an_even_h2r_cycle_points_the_reader_at_the_revocation_lag() -> None:
    """An even score is exactly where the two real findings hide behind the number."""
    questionnaire = get_questionnaire(H2R)
    payload = score_assessment(questionnaire, _h2r_shaped(front_rank=2, back_rank=2))

    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Broadly even")
    assert "revocation lag" in payload.shape_note
    assert "payroll systems" in payload.shape_note


def test_the_h2r_deterministic_score_is_reproducible() -> None:
    questionnaire = get_questionnaire(H2R)
    answers = _answer_step_fully("h2r_payroll", 2, H2R) | _answer_step_fully(
        "h2r_offboarding", 3, H2R
    )

    first = score_assessment(questionnaire, answers)
    second = score_assessment(questionnaire, answers)

    assert first.index == second.index
    assert [s.score for s in first.steps] == [s.score for s in second.steps]


# ---------------------------------------------- Record to Report (2026-09-14)
#
# The fifth and last defined process, and the first that is not a flow at all: a periodic
# close, where "volume" barely applies and the currency is days to close, the manual
# journal count and the reconciliation backlog. What follows is what is specific to R2R -
# weights chosen by close effort and misstatement risk, and a shape note that is
# deliberately narrower than the other four because the steps of a close are sequentially
# dependent within one period.


def test_the_r2r_steps_carry_the_model_documents_weights() -> None:
    """The weights are the model, so a silent retune must break a test."""
    questionnaire = get_questionnaire(R2R)
    weights = {step.key: step.weight for step in questionnaire.steps}
    assert weights == {
        "r2r_subledger": 12,
        "r2r_reconciliations": 16,
        "r2r_journals": 15,
        "r2r_intercompany": 11,
        "r2r_consolidation": 14,
        "r2r_external": 10,
        "r2r_tax": 8,
        "r2r_management_reporting": 14,
    }
    # Reconciliations are the heaviest: the largest single consumer of close effort and
    # where an error survives longest. R2R_AUTOMATION_MODEL.md section 3.
    assert max(weights, key=lambda k: weights[k]) == "r2r_reconciliations"
    # Weight follows close effort and misstatement risk, not transaction volume. Tax is
    # the lightest because it is largely annual and adviser-led, so it sits mostly outside
    # the mechanism this model grades - despite being anything but unimportant.
    assert min(weights, key=lambda k: weights[k]) == "r2r_tax"
    # Management reporting is not part of the statutory close at all and still outweighs
    # external reporting, because it is what a buyer experiences from month one.
    assert weights["r2r_management_reporting"] > weights["r2r_external"]


def test_every_r2r_scoring_option_sits_on_the_shared_ladder() -> None:
    """0-5, and increasing down the option list, or the ladder has been broken."""
    questionnaire = get_questionnaire(R2R)
    for step in questionnaire.steps:
        for question in step.questions:
            if not question.scores:
                continue
            scores = [option.score for option in question.options]
            assert all(0 <= s <= 5 for s in scores), f"{question.id} leaves the ladder"
            assert scores == sorted(scores), f"{question.id} options are not in ladder order"


def test_r2r_free_text_questions_never_score() -> None:
    """They capture days to close, manual journals and the backlog - not a level."""
    questionnaire = get_questionnaire(R2R)
    text_questions = [
        q for step in questionnaire.steps for q in step.questions if q.type == "text"
    ]
    assert text_questions, "the evidence questions are what make the number defensible"
    assert all(q.options == [] for q in text_questions)


def test_the_close_asks_for_days_and_manual_journals_as_evidence() -> None:
    """The three numbers the model names as this process's currency, section 4.

    A close cannot be assessed on transaction volume, so the questionnaire has to elicit
    days to close, the manual journal count and the reconciliation backlog explicitly. A
    score reported without days-to-close beside it is missing the figure every reader
    asks for first.
    """
    questionnaire = get_questionnaire(R2R)
    evidence = " ".join(
        q.text.lower()
        for step in questionnaire.steps
        for q in step.questions
        if q.type == "text"
    )
    assert "working days" in evidence, "days to close must be captured"
    assert "manual journals" in evidence, "the manual journal count must be captured"
    assert "unreconciled" in evidence, "the reconciliation backlog must be captured"


def test_a_single_entity_target_can_be_scored_without_consolidation() -> None:
    """The applicability rule from the model document, section 1.

    Intercompany and consolidation do not exist in a single-entity target. Scoring them
    as manual would mark a process deficient for not doing something it has no reason to
    do, which is the same failure the P2M distributor case pins.
    """
    questionnaire = get_questionnaire(R2R)
    answers: dict[str, str] = {}
    for key in (
        "r2r_subledger",
        "r2r_reconciliations",
        "r2r_journals",
        "r2r_external",
        "r2r_tax",
        "r2r_management_reporting",
    ):
        answers |= _answer_step_fully(key, 3, R2R)

    payload = score_assessment(questionnaire, answers)

    assert payload.steps_assessed == 6
    assert payload.steps_total == 8
    for key in ("r2r_intercompany", "r2r_consolidation"):
        assert next(s for s in payload.steps if s.key == key).assessed is False
    assert payload.index > 50, "unassessed steps must not drag the index down"


def test_an_unanswered_r2r_question_is_not_scored_as_zero() -> None:
    questionnaire = get_questionnaire(R2R)
    answers = _answer_step_fully("r2r_reconciliations", 5, R2R)

    payload = score_assessment(questionnaire, answers)
    recs = next(s for s in payload.steps if s.key == "r2r_reconciliations")
    tax = next(s for s in payload.steps if s.key == "r2r_tax")

    assert recs.assessed is True
    assert tax.assessed is False
    assert tax.score is None
    assert payload.steps_assessed == 1
    assert payload.steps_total == 8


def test_the_heaviest_r2r_gap_is_the_first_pointer() -> None:
    questionnaire = get_questionnaire(R2R)
    answers: dict[str, str] = {}
    for step in questionnaire.steps:
        for question in step.questions:
            if question.scores:
                answers[question.id] = question.options[0].label

    payload = score_assessment(questionnaire, answers)
    gaps = [p for p in payload.pointers if p.kind == "gap"]
    assert gaps, "an all-manual close must produce gaps"
    # Reconciliations carry 16%, the heaviest weight in the R2R model.
    assert gaps[0].step_key == "r2r_reconciliations"


def _r2r_shaped(front_rank: int, back_rank: int) -> dict[str, str]:
    """Answer R2R with one maturity in the ledger and another in the reporting."""
    questionnaire = get_questionnaire(R2R)
    shape = questionnaire.shape
    assert shape is not None
    answers: dict[str, str] = {}
    for step in questionnaire.steps:
        if step.sn in shape.front_steps:
            rank = front_rank
        elif step.sn in shape.back_steps:
            rank = back_rank
        else:
            continue
        for question in step.questions:
            if question.scores:
                answers[question.id] = question.options[
                    min(rank, len(question.options) - 1)
                ].label
    return answers


def test_a_front_loaded_close_reads_as_the_cheaper_of_the_two_problems() -> None:
    """R2R inverts the usual reading, and the note must say so.

    In P2P, O2C and H2R a front-loaded shape is the bad news. In a close it is the good
    news: the expensive, risky part - reconciliations and journal control - is already
    right, and what is manual is the reporting layer built on top of trustworthy data.
    A note that treated this as a failure would misdirect the remediation estimate.
    """
    questionnaire = get_questionnaire(R2R)
    payload = score_assessment(questionnaire, _r2r_shaped(front_rank=5, back_rank=0))

    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Front-loaded")
    assert "reporting layer rather than a finance transformation" in payload.shape_note
    assert "accounts payable" not in payload.shape_note, "P2P's wording has leaked"
    assert "live credentials" not in payload.shape_note, "H2R's wording has leaked"
    assert "shop floor" not in payload.shape_note, "P2M's wording has leaked"


def test_a_back_loaded_close_is_named_as_the_more_serious_shape() -> None:
    """A polished pack on an unreconciled ledger, and the note must escalate it.

    This is the shape most likely to surprise a quality-of-earnings team late, because
    the pack ties and the ledger does not.
    """
    questionnaire = get_questionnaire(R2R)
    payload = score_assessment(questionnaire, _r2r_shaped(front_rank=0, back_rank=5))

    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Back-loaded")
    assert "more serious" in payload.shape_note
    assert "cannot be re-performed" in payload.shape_note
    assert "quality-of-earnings" in payload.shape_note


def test_an_even_close_is_reported_as_ordinary_rather_than_as_a_finding() -> None:
    """The judgement recorded in the model document's section 6, pinned.

    The steps of a close are sequentially dependent within one period, so they move
    together and an even profile is the ordinary result. The note says so and redirects
    the reader to days-to-close, rather than inventing a narrative to fill the template.
    That honesty is the thing worth protecting here, so it is asserted.
    """
    questionnaire = get_questionnaire(R2R)
    payload = score_assessment(questionnaire, _r2r_shaped(front_rank=2, back_rank=2))

    assert payload.shape_note is not None
    assert payload.shape_note.startswith("Broadly even")
    assert "ordinary result" in payload.shape_note
    assert "sequentially dependent" in payload.shape_note
    # And it must carry the caution that a fast close is not an automated one.
    assert "manual journal count" in payload.shape_note


def test_the_r2r_deterministic_score_is_reproducible() -> None:
    questionnaire = get_questionnaire(R2R)
    answers = _answer_step_fully("r2r_reconciliations", 2, R2R) | _answer_step_fully(
        "r2r_consolidation", 3, R2R
    )

    first = score_assessment(questionnaire, answers)
    second = score_assessment(questionnaire, answers)

    assert first.index == second.index
    assert [s.score for s in first.steps] == [s.score for s in second.steps]


# ------------------------------------------------------- the last two through the API


def test_the_h2r_and_r2r_questionnaires_serve_their_steps(client) -> None:
    """Both used to 409. Neither does now, and each serves its own decomposition."""
    engagement = create_engagement(client)
    for key, steps, first_step in (
        (H2R, 9, "h2r_recruiting"),
        (R2R, 8, "r2r_subledger"),
    ):
        response = client.get(f"/api/v1/engagements/{engagement['id']}/assess/{key}")
        assert response.status_code == 200, f"{key} should no longer 409"
        body = response.json()
        assert len(body["steps"]) == steps
        assert body["steps"][0]["key"] == first_step
        assert body["answered_count"] == 0


def test_an_r2r_answer_cannot_be_saved_against_an_h2r_question_id(client) -> None:
    engagement = create_engagement(client)
    h2r_question = get_questionnaire(H2R).steps[0].questions[0]
    response = client.patch(
        f"/api/v1/engagements/{engagement['id']}/assess/{R2R}/answers/{h2r_question.id}",
        json={"value": h2r_question.options[0].label},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "unknown_question"


def test_h2r_evidence_reaches_the_model() -> None:
    """The revocation lag is the finding this process exists to produce."""
    import json

    questionnaire = get_questionnaire(H2R)
    answers = _answer_step_fully("h2r_offboarding", 1, H2R)
    answers["H2R-08-05"] = (
        "Last ten leavers: directory disabled a mean of 11 days after last working day, "
        "worst case 38 days; three CRM accounts still enabled."
    )

    generator = _llm_generator(
        json.dumps({"executive_summary": "x", "step_refinements": [], "pointers": []})
    )
    generator.score(questionnaire, answers)

    sent = generator._client.models.last_contents  # type: ignore[attr-defined]
    assert sent is not None
    assert "mean of 11 days" in sent


def test_r2r_evidence_reaches_the_model() -> None:
    """Days to close and the manual journal count are what the summary must use."""
    import json

    questionnaire = get_questionnaire(R2R)
    answers = _answer_step_fully("r2r_journals", 1, R2R)
    answers["R2R-03-03"] = "Close takes 19 working days; 340 manual journals last period."

    generator = _llm_generator(
        json.dumps({"executive_summary": "x", "step_refinements": [], "pointers": []})
    )
    generator.score(questionnaire, answers)

    sent = generator._client.models.last_contents  # type: ignore[attr-defined]
    assert sent is not None
    assert "19 working days" in sent
    assert "340 manual journals" in sent
