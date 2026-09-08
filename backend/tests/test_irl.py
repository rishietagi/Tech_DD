"""The Initial Request List: seeds, generation, responses and the Excel export.

The load-bearing properties under test:
- seeds come from the scope, deterministically, skipping out-of-scope rows;
- the deterministic list is complete and sendable with the LLM off;
- model output that drops or invents a seed is rejected, and the rules list ships;
- typed responses survive a regeneration.
"""

import io
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.schemas.irl import IrlPayload, IrlTailoringRejected, LlmIrl
from app.services.irl.export_xlsx import render_xlsx, xlsx_filename
from app.services.irl.llm import LlmIrlGenerator, RulesIrlGenerator, validate_irl
from app.services.irl.seeds import build_seeds
from app.services.scope.rules_generator import RulesScopeGenerator
from tests.factories import make_intake
from tests.test_engagement_flow import SECTIONS_PAYLOAD

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

PRODUCT = dict(
    company_name="Meridian Analytics",
    line_of_business="Sells a usage-based analytics platform to mid-market e-commerce retailers.",
    dd_type_preference="Product Tech DD",
    digital_maturity="Digital native",
    data_sensitivity=["Personal data (PII)"],
    compliance_regimes=["SOC 2"],
)


def scope_for(**overrides):
    return RulesScopeGenerator().generate(make_intake(**{**PRODUCT, **overrides}))


def rules_irl(**overrides) -> IrlPayload:
    intake = make_intake(**{**PRODUCT, **overrides})
    scope = RulesScopeGenerator().generate(intake)
    return RulesIrlGenerator().generate(intake, scope, source_scope_version=1)


def _filed_engagement(client: TestClient) -> str:
    response = client.post("/api/v1/engagements", json={"deal_name": "Project Lighthouse"})
    engagement_id = response.json()["id"]
    for section, payload in SECTIONS_PAYLOAD.items():
        client.patch(f"/api/v1/engagements/{engagement_id}/intake/{section}", json=payload)
    client.post(f"/api/v1/engagements/{engagement_id}/submit")
    return engagement_id


def _scoped_engagement(client: TestClient) -> str:
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")
    return engagement_id


# --------------------------------------------------------------------------- seeds


def test_document_seeds_come_from_the_scope_evidence_lists() -> None:
    scope = scope_for()
    seeds = build_seeds(scope)

    assert seeds, "the scope must yield seed requests"
    # Every seed traces back to a row that is actually in scope.
    in_scope_ids = {r.id for r in scope.rows if r.tier > 0}
    assert all(s.row_id in in_scope_ids for s in seeds)

    # And every DOCUMENT seed's text is a real evidence line from its row.
    by_row = {r.id: r.evidence_requests for r in scope.rows}
    documents = [s for s in seeds if s.kind == "document"]
    assert documents
    assert all(s.text in by_row[s.row_id] for s in documents)


def test_the_list_asks_questions_as_well_as_requesting_documents() -> None:
    """An IRL is not a filing exercise.

    DD_master §6 gives every workstream both "areas of investigation" and "evidence
    requests"; until 2026-09-02 the engine used only the second, so the list asked for
    artefacts and never asked management to explain anything.
    """
    seeds = build_seeds(scope_for())

    documents = [s for s in seeds if s.kind == "document"]
    questions = [s for s in seeds if s.kind == "question"]

    assert documents, "the list must still request documents"
    assert questions, "the list must also ask questions"
    # Every sourced question carries the page it came from.
    assert all(s.citation for s in questions)
    assert all(s.source_workstream for s in questions)


def test_a_question_is_never_asked_twice() -> None:
    """Several rows share a workstream. Asking its questions on each would repeat them.

    "avoid repeating questions across sessions" — DD_master p. 84-85.
    """
    questions = [s for s in build_seeds(scope_for()) if s.kind == "question"]
    texts = [s.text.strip().lower() for s in questions]
    assert len(texts) == len(set(texts)), "the same question must not be asked twice"


def test_sourced_questions_carry_no_markdown() -> None:
    """The source formats some questions as bold-labelled bullets. The label is not text
    the client should read."""
    questions = [s for s in build_seeds(scope_for()) if s.kind == "question"]
    assert all("**" not in s.text for s in questions)
    # And each is a single question, not several packed into one row.
    assert all(s.text.count("?") <= 1 for s in questions)


def test_seeds_skip_out_of_scope_rows() -> None:
    """A row the engine deliberately did not open is not worth requesting evidence for."""
    scope = scope_for()
    for row in scope.rows:
        row.tier = 0

    # Neither documents nor questions: an area the engine did not open is not worth
    # requesting evidence for, and not worth management's time either.
    assert build_seeds(scope) == []


def test_seed_ids_are_stable_and_deterministic() -> None:
    """Stable ids are what lets a typed response survive a regeneration."""
    first = [s.id for s in build_seeds(scope_for())]
    second = [s.id for s in build_seeds(scope_for())]
    assert first == second
    assert len(first) == len(set(first)), "seed ids must be unique"


# ------------------------------------------------------------- deterministic list


def test_the_rules_list_is_complete_without_an_llm() -> None:
    """The deterministic floor: a usable IRL with the model entirely absent."""
    payload = rules_irl()

    assert payload.generator == "rules"
    assert payload.questions
    assert payload.intro
    assert payload.functions
    assert all(q.question.strip() for q in payload.questions)
    # Every question is attributable to a scope row.
    assert all(q.source == "scope" and q.source_row_id for q in payload.questions)


def test_every_question_belongs_to_exactly_one_function_group() -> None:
    payload = rules_irl()
    grouped = [qid for f in payload.functions for qid in f.question_ids]

    assert sorted(grouped) == sorted(q.id for q in payload.questions)
    assert len(grouped) == len(set(grouped)), "a question must not appear under two functions"


# ------------------------------------------------------------ the LLM contract


def _seeds():
    return build_seeds(scope_for())


def test_validate_accepts_a_faithful_response() -> None:
    seeds = _seeds()
    tailoring = LlmIrl(
        intro="Please provide the following.",
        questions=[
            {"seed_id": s.id, "function": "IT", "question": f"Provide {s.text}."}
            for s in seeds
        ],
    )
    validate_irl(tailoring, seeds)  # must not raise


def test_a_dropped_seed_is_rejected() -> None:
    """Dropping a seed silently loses a request the scope said was needed."""
    seeds = _seeds()
    tailoring = LlmIrl(
        intro="Intro.",
        questions=[
            {"seed_id": s.id, "function": "IT", "question": "Provide it."}
            for s in seeds[:-1]
        ],
    )
    with pytest.raises(IrlTailoringRejected, match="dropped"):
        validate_irl(tailoring, seeds)


def test_an_invented_seed_id_is_rejected() -> None:
    seeds = _seeds()
    tailoring = LlmIrl(
        intro="Intro.",
        questions=[
            *[{"seed_id": s.id, "function": "IT", "question": "Provide it."} for s in seeds],
            {"seed_id": "MADE-UP-1", "function": "IT", "question": "Provide it."},
        ],
    )
    with pytest.raises(IrlTailoringRejected, match="unknown"):
        validate_irl(tailoring, seeds)


def test_model_added_questions_are_allowed_and_marked() -> None:
    """An IRL that only asks what a tech scope covers is not a real IRL."""
    seeds = _seeds()
    tailoring = LlmIrl(
        intro="Intro.",
        questions=[
            *[{"seed_id": s.id, "function": "IT", "question": "Provide it."} for s in seeds],
            {"seed_id": None, "function": "Human Resources", "question": "Provide the org chart."},
        ],
    )
    validate_irl(tailoring, seeds)  # allowed

    from app.services.irl.llm import apply_irl

    payload = apply_irl(
        tailoring, seeds, "Meridian Analytics", 1, True, "llm", "1.0"
    )
    added = [q for q in payload.questions if q.source == "llm"]
    assert len(added) == 1
    assert added[0].source_row_id is None, "a model-added question has no scope row behind it"
    assert payload.used_research is True


def test_a_rejected_response_falls_back_to_the_rules_list() -> None:
    """A bad generation degrades to a slightly terser list, never to nothing."""

    class _BadClient:
        class models:  # noqa: N801 - mirrors the SDK's shape
            @staticmethod
            def generate_content(**_kwargs: object) -> object:
                class _R:
                    text = '{"intro": "x", "questions": []}'

                return _R()

    intake = make_intake(**PRODUCT)
    scope = RulesScopeGenerator().generate(intake)

    from app.core.config import Settings

    generator = LlmIrlGenerator(
        settings=Settings(gemini_api_key="test-key"), client=_BadClient()
    )
    payload = generator.generate(intake, scope, source_scope_version=1)

    assert payload.generator == "rules (llm tailoring rejected)"
    assert payload.questions, "the deterministic list must still ship"


def test_no_api_key_returns_the_rules_list() -> None:
    from app.core.config import Settings

    intake = make_intake(**PRODUCT)
    scope = RulesScopeGenerator().generate(intake)
    generator = LlmIrlGenerator(settings=Settings(gemini_api_key=None))

    payload = generator.generate(intake, scope, source_scope_version=1)
    assert payload.generator == "rules (llm unavailable)"


# ---------------------------------------------------------------------- export


def _sheet_rows(raw: bytes) -> list[list[str]]:
    """Read the workbook back with openpyxl if present, else assert on the zip."""
    openpyxl = pytest.importorskip("openpyxl", reason="openpyxl is not installed")
    book = openpyxl.load_workbook(io.BytesIO(raw))
    sheet = book.active
    return [[c if c is not None else "" for c in row] for row in sheet.iter_rows(values_only=True)]


def test_export_is_a_valid_workbook() -> None:
    raw = render_xlsx(rules_irl())
    assert raw.startswith(b"PK")  # xlsx is a zip
    assert len(raw) > 2_000


def test_export_columns_and_response_ships_blank() -> None:
    """Four columns since 2026-09-02, plus a hidden id the importer matches on."""
    payload = rules_irl()
    rows = _sheet_rows(render_xlsx(payload))

    assert rows[0] == [
        "Scope Area",
        "Function",
        "Type",
        "Request",
        "Response",
        "Request ID",
    ]
    assert len(rows) == len(payload.questions) + 1
    # Response is the client's column: it must ship blank.
    assert all(row[4] == "" for row in rows[1:])
    # Every row carries its id, or an upload cannot match it back.
    assert all(row[5] for row in rows[1:])
    # And says whether it wants a document or an answer.
    assert {row[2] for row in rows[1:]} <= {"Document", "Question"}


def test_the_workbook_tells_the_client_which_rows_are_questions() -> None:
    """A client needs to know what to attach and what to answer before they start."""
    payload = rules_irl()
    rows = _sheet_rows(render_xlsx(payload))

    kinds = [row[2] for row in rows[1:]]
    assert "Document" in kinds, "the list must still request documents"
    assert "Question" in kinds, "the list must also ask questions"


def test_export_groups_by_scope_area() -> None:
    """The IRL follows the scope of work's headings, so a request traces to its area."""
    payload = rules_irl()
    rows = _sheet_rows(render_xlsx(payload))

    areas = {row[0] for row in rows[1:]}
    row_titles = {q.scope_area for q in payload.questions if q.scope_area}
    assert areas & row_titles, "scope areas must reach the workbook"


def test_export_writes_back_answers_already_typed() -> None:
    payload = rules_irl()
    first = payload.questions[0]
    rows = _sheet_rows(render_xlsx(payload, {first.id: "Attached as Appendix A."}))

    answered = [r for r in rows[1:] if r[4]]
    assert len(answered) == 1
    assert answered[0][4] == "Attached as Appendix A."


def test_filename_is_slugged() -> None:
    assert xlsx_filename("Project Redline", 2) == "project-redline-irl-v2.xlsx"
    assert xlsx_filename("!!!", 1) == "irl-v1.xlsx"


# ------------------------------------------------------------------------ routes


def test_generate_requires_a_scope(client: TestClient) -> None:
    """The IRL is built from the scope's evidence, so that precondition is real."""
    engagement_id = _filed_engagement(client)

    response = client.post(f"/api/v1/engagements/{engagement_id}/irl")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "not_scoped"


def test_generate_and_read_back(client: TestClient) -> None:
    engagement_id = _scoped_engagement(client)

    created = client.post(f"/api/v1/engagements/{engagement_id}/irl")
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["version"] == 1
    assert body["payload"]["questions"]
    assert body["source_scope_version"] == 1

    latest = client.get(f"/api/v1/engagements/{engagement_id}/irl")
    assert latest.status_code == 200
    assert latest.json()["version"] == 1


def test_reading_before_generating_is_404(client: TestClient) -> None:
    engagement_id = _scoped_engagement(client)
    response = client.get(f"/api/v1/engagements/{engagement_id}/irl")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "no_irl"


def test_responses_are_saved_and_returned(client: TestClient) -> None:
    engagement_id = _scoped_engagement(client)
    irl = client.post(f"/api/v1/engagements/{engagement_id}/irl").json()
    question_id = irl["payload"]["questions"][0]["id"]

    saved = client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/responses/{question_id}",
        json={"response_text": "Provided in the data room, folder 3."},
    )
    assert saved.status_code == 200
    assert saved.json()["responses"][question_id] == "Provided in the data room, folder 3."

    # And it survives a re-fetch, not just the mutation response.
    assert (
        client.get(f"/api/v1/engagements/{engagement_id}/irl").json()["responses"][question_id]
        == "Provided in the data room, folder 3."
    )


def test_clearing_a_response_removes_it(client: TestClient) -> None:
    engagement_id = _scoped_engagement(client)
    irl = client.post(f"/api/v1/engagements/{engagement_id}/irl").json()
    question_id = irl["payload"]["questions"][0]["id"]

    client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/responses/{question_id}",
        json={"response_text": "Something"},
    )
    cleared = client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/responses/{question_id}",
        json={"response_text": "   "},
    )
    assert question_id not in cleared.json()["responses"]


def test_an_unknown_question_id_is_404(client: TestClient) -> None:
    engagement_id = _scoped_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/irl")

    response = client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/responses/NOPE-1",
        json={"response_text": "x"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "unknown_question"


def test_responses_survive_a_regeneration(client: TestClient) -> None:
    """The whole reason responses live in their own table."""
    engagement_id = _scoped_engagement(client)
    irl = client.post(f"/api/v1/engagements/{engagement_id}/irl").json()
    question_id = irl["payload"]["questions"][0]["id"]

    client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/responses/{question_id}",
        json={"response_text": "Already answered."},
    )

    regenerated = client.post(f"/api/v1/engagements/{engagement_id}/irl").json()
    assert regenerated["version"] == 2
    assert regenerated["responses"].get(question_id) == "Already answered."


def test_export_endpoint_returns_a_workbook(client: TestClient) -> None:
    engagement_id = _scoped_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/irl")

    response = client.get(f"/api/v1/engagements/{engagement_id}/irl/export.xlsx")
    assert response.status_code == 200
    assert response.headers["content-type"] == XLSX_MEDIA_TYPE
    assert response.content.startswith(b"PK")

    disposition = response.headers["content-disposition"]
    assert "attachment" in disposition
    assert "project-redline-irl-v1.xlsx" in disposition


def test_export_route_is_not_shadowed_by_the_version_route(client: TestClient) -> None:
    """`/export.xlsx` is declared before `/{version}`; confirm it is not read as one."""
    engagement_id = _scoped_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/irl")

    response = client.get(f"/api/v1/engagements/{engagement_id}/irl/export.xlsx")
    assert response.status_code == 200
    assert response.headers["content-type"] == XLSX_MEDIA_TYPE


def test_deleting_an_engagement_removes_its_irl_and_responses(
    client: TestClient, db_session
) -> None:
    from app.models.irl import InformationRequestList, IrlResponse

    engagement_id = _scoped_engagement(client)
    irl = client.post(f"/api/v1/engagements/{engagement_id}/irl").json()
    client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/responses/{irl['payload']['questions'][0]['id']}",
        json={"response_text": "x"},
    )

    db_session.expire_all()
    assert db_session.query(InformationRequestList).filter_by(engagement_id=engagement_id).count() == 1
    assert db_session.query(IrlResponse).count() >= 1

    client.delete(f"/api/v1/engagements/{engagement_id}?permanent=true")

    db_session.expire_all()
    assert db_session.query(InformationRequestList).filter_by(engagement_id=engagement_id).count() == 0
    assert db_session.query(IrlResponse).count() == 0


def test_payload_records_when_research_was_not_used() -> None:
    """A reader deserves to know whether the questions were research-informed."""
    payload = rules_irl()
    assert payload.used_research is False
    assert isinstance(payload.generated_at, datetime)
    assert payload.generated_at.tzinfo is not None
    assert payload.generated_at <= datetime.now(UTC)


# ------------------------------------------------------- research feeds the IRL


def test_research_and_context_reach_the_model() -> None:
    """The IRL prompt must carry the research and the engagement context.

    Without them the model cannot name functions that fit the business or ask about
    things that actually happened — it would write a generic list.
    """
    from types import SimpleNamespace

    from app.core.config import Settings
    from app.schemas.research import ResearchPayload

    captured: dict[str, object] = {}

    class _Client:
        def __init__(self) -> None:
            self.models = SimpleNamespace(generate_content=self._generate)

        def _generate(self, **kwargs: object) -> object:
            captured.update(kwargs)
            # Deliberately invalid, so generation falls back — this test is about what
            # was *sent*, not what came back.
            return SimpleNamespace(text='{"intro": "x", "questions": []}')

    intake = make_intake(**PRODUCT)
    scope = RulesScopeGenerator().generate(intake)
    research = ResearchPayload(
        generator="llm+search",
        company_name="Meridian Analytics",
        summary="Meridian had a six-hour outage in March 2025.",
        findings=[],
        sources=[],
        researched_at=datetime.now(UTC),
    )

    LlmIrlGenerator(settings=Settings(gemini_api_key="k"), client=_Client()).generate(
        intake, scope, research=research, source_scope_version=1
    )

    sent = str(captured.get("contents"))
    assert "six-hour outage in March 2025" in sent, "the research summary must reach the model"
    assert "line_of_business" in sent, "the engagement context must reach the model"
    assert "seeds" in sent, "the scope-derived seeds must reach the model"


# ------------------------------------------------- editing and import (2026-09-02)


def _engagement_with_irl(client: TestClient) -> str:
    """A scoped engagement with a generated request list to edit."""
    engagement_id = _scoped_engagement(client)
    response = client.post(f"/api/v1/engagements/{engagement_id}/irl", json={})
    assert response.status_code == 200, response.text
    return engagement_id


def test_a_question_can_be_added_by_hand(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    before = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()
    count = len(before["payload"]["questions"])

    response = client.post(
        f"/api/v1/engagements/{engagement_id}/irl/questions",
        json={
            "question": "Provide the depot stock-take reconciliation for the last quarter.",
            "function": "Operations",
            "scope_area": "Applications",
        },
    )
    assert response.status_code == 200

    questions = response.json()["payload"]["questions"]
    assert len(questions) == count + 1
    added = [q for q in questions if q["source"] == "manual"]
    assert len(added) == 1
    assert added[0]["function"] == "Operations"
    assert added[0]["scope_area"] == "Applications"


def test_an_edited_question_keeps_the_original_wording(client: TestClient) -> None:
    """The engine's text is kept beside the edit, as the scope rows already do."""
    engagement_id = _engagement_with_irl(client)
    irl = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()
    target = irl["payload"]["questions"][0]

    response = client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/questions/{target['id']}",
        json={"question": "Provide the current architecture diagram set."},
    )
    assert response.status_code == 200

    edited = next(
        q for q in response.json()["payload"]["questions"] if q["id"] == target["id"]
    )
    assert edited["question"] == "Provide the current architecture diagram set."
    assert edited["edited_by_human"] is True
    assert edited["original_question"] == target["question"]


def test_a_question_can_be_deleted_and_takes_its_response(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    irl = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()
    target = irl["payload"]["questions"][0]["id"]

    client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/responses/{target}",
        json={"response_text": "Attached."},
    )

    response = client.delete(
        f"/api/v1/engagements/{engagement_id}/irl/questions/{target}"
    )
    assert response.status_code == 200

    fresh = response.json()
    assert all(q["id"] != target for q in fresh["payload"]["questions"])
    assert target not in fresh["responses"], "an orphan response must not survive"


def test_editing_an_unknown_question_is_rejected(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    response = client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/questions/NOPE-001",
        json={"question": "x"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "unknown_question"


def test_manual_questions_and_edits_survive_a_regeneration(client: TestClient) -> None:
    """Rishi's call: carry them forward, keep the edits."""
    engagement_id = _engagement_with_irl(client)
    irl = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()
    target = irl["payload"]["questions"][0]["id"]

    client.post(
        f"/api/v1/engagements/{engagement_id}/irl/questions",
        json={"question": "Provide the depot stock-take.", "function": "Operations"},
    )
    client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/questions/{target}",
        json={"question": "Provide the architecture diagrams, current versions only."},
    )

    regenerated = client.post(f"/api/v1/engagements/{engagement_id}/irl", json={}).json()
    questions = regenerated["payload"]["questions"]

    manual = [q for q in questions if q["source"] == "manual"]
    assert len(manual) == 1, "an added question must survive regeneration"
    assert manual[0]["question"] == "Provide the depot stock-take."

    carried = next(q for q in questions if q["id"] == target)
    assert carried["question"] == "Provide the architecture diagrams, current versions only."
    assert carried["edited_by_human"] is True


def test_a_completed_workbook_round_trips_into_responses(client: TestClient) -> None:
    """Export, fill in the Response column, upload, and the answers land."""
    import io

    from openpyxl import load_workbook

    engagement_id = _engagement_with_irl(client)
    raw = client.get(f"/api/v1/engagements/{engagement_id}/irl/export.xlsx").content

    workbook = load_workbook(io.BytesIO(raw))
    sheet = workbook.active
    filled: dict[str, str] = {}
    for row in range(2, min(sheet.max_row, 6) + 1):
        question_id = sheet.cell(row=row, column=6).value
        answer = f"Provided - see data room folder {row - 1}."
        sheet.cell(row=row, column=5, value=answer)
        filled[str(question_id)] = answer

    buf = io.BytesIO()
    workbook.save(buf)

    response = client.post(
        f"/api/v1/engagements/{engagement_id}/irl/import",
        files={
            "file": (
                "responses.xlsx",
                buf.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["updated"] == len(filled)

    stored = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()["responses"]
    for question_id, answer in filled.items():
        assert stored[question_id] == answer


def test_a_blank_response_cell_never_clears_an_existing_answer(client: TestClient) -> None:
    """A blank cell means "not answered yet", never "delete what you have"."""
    import io

    from openpyxl import load_workbook

    engagement_id = _engagement_with_irl(client)
    irl = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()
    target = irl["payload"]["questions"][0]["id"]

    client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/responses/{target}",
        json={"response_text": "Already answered in the app."},
    )

    raw = client.get(f"/api/v1/engagements/{engagement_id}/irl/export.xlsx").content
    workbook = load_workbook(io.BytesIO(raw))
    sheet = workbook.active
    for row in range(2, sheet.max_row + 1):
        sheet.cell(row=row, column=5, value=None)
    buf = io.BytesIO()
    workbook.save(buf)

    client.post(
        f"/api/v1/engagements/{engagement_id}/irl/import",
        files={"file": ("blank.xlsx", buf.getvalue(), "application/vnd.ms-excel")},
    )

    stored = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()["responses"]
    assert stored[target] == "Already answered in the app."


def test_an_unreadable_upload_is_a_clear_error(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    response = client.post(
        f"/api/v1/engagements/{engagement_id}/irl/import",
        files={"file": ("notes.txt", b"this is not a workbook", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "import_failed"


def test_an_import_that_matches_nothing_says_so(client: TestClient) -> None:
    """Silence would look identical to success. It must not."""
    import io

    import xlsxwriter

    engagement_id = _engagement_with_irl(client)

    buf = io.BytesIO()
    workbook = xlsxwriter.Workbook(buf, {"in_memory": True})
    sheet = workbook.add_worksheet("Sheet1")
    sheet.write(0, 0, "Question")
    sheet.write(0, 1, "Response")
    sheet.write(1, 0, "A question from an entirely different engagement")
    sheet.write(1, 1, "Some answer")
    workbook.close()

    response = client.post(
        f"/api/v1/engagements/{engagement_id}/irl/import",
        files={"file": ("other.xlsx", buf.getvalue(), "application/vnd.ms-excel")},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["matched"] == 0
    assert result["updated"] == 0
    assert "No row" in result["note"]
    assert result["unmatched_rows"]



# ------------------------------------------- tracking merged into the IRL (2026-09-02)


def test_the_irl_read_carries_tracking_for_every_question(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    irl = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()

    assert irl["tracking"], "tracking must be assembled on read"
    assert set(irl["tracking"]) == {q["id"] for q in irl["payload"]["questions"]}

    first = next(iter(irl["tracking"].values()))
    assert first["status"] == "not_received", "absence of a row means not received"
    assert first["priority"], "priority is computed, not stored"
    assert first["priority_reason"], "a colour with no explanation is not auditable"


def test_tracking_saves_and_reads_back(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    irl = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()
    target = irl["payload"]["questions"][0]["id"]

    response = client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/tracking/{target}",
        json={
            "status": "received_partially",
            "document_type": "Register",
            "remarks": "Summary only; the underlying contracts are still to come.",
        },
    )
    assert response.status_code == 200

    # Re-fetched rather than trusting the response body.
    fresh = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()
    track = fresh["tracking"][target]
    assert track["status"] == "received_partially"
    assert track["document_type"] == "Register"
    assert track["remarks"].startswith("Summary only")
    assert track["set_by_human"] is True, "a scan must not overwrite a human judgement"


def test_saving_one_tracking_field_leaves_the_others_alone(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    irl = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()
    target = irl["payload"]["questions"][0]["id"]
    base = f"/api/v1/engagements/{engagement_id}/irl/tracking/{target}"

    client.patch(base, json={"remarks": "Chased on Tuesday."})
    client.patch(base, json={"status": "received_completely"})

    track = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()["tracking"][target]
    assert track["status"] == "received_completely"
    assert track["remarks"] == "Chased on Tuesday.", "a status change must not wipe remarks"


def test_tracking_never_reaches_the_client_workbook(client: TestClient) -> None:
    """The whole point of the split: status and remarks are the team's own assessment.

    Exporting them would hand the target our view of their responsiveness.
    """
    import io

    from openpyxl import load_workbook

    engagement_id = _engagement_with_irl(client)
    irl = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()
    target = irl["payload"]["questions"][0]["id"]

    client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/tracking/{target}",
        json={
            "status": "received_partially",
            "document_type": "Register",
            "remarks": "SECRET-INTERNAL-NOTE slow to respond",
        },
    )

    raw = client.get(f"/api/v1/engagements/{engagement_id}/irl/export.xlsx").content
    sheet = load_workbook(io.BytesIO(raw)).active

    headers = [sheet.cell(row=1, column=c).value for c in range(1, 9)]
    assert headers[:6] == [
        "Scope Area",
        "Function",
        "Type",
        "Request",
        "Response",
        "Request ID",
    ]
    assert "Status" not in str(headers)
    assert "Remarks" not in str(headers)

    body = " ".join(
        str(sheet.cell(row=r, column=c).value or "")
        for r in range(1, sheet.max_row + 1)
        for c in range(1, 7)
    )
    assert "SECRET-INTERNAL-NOTE" not in body
    assert "received_partially" not in body


def test_tracking_on_an_unknown_question_is_rejected(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    response = client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/tracking/NOPE-001",
        json={"status": "received_completely"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "unknown_question"


def test_the_checklist_and_the_irl_agree_on_status(client: TestClient) -> None:
    """Two views of one dataset. If they disagree, one of them is lying."""
    engagement_id = _engagement_with_irl(client)
    irl = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()
    target = irl["payload"]["questions"][0]["id"]

    client.patch(
        f"/api/v1/engagements/{engagement_id}/irl/tracking/{target}",
        json={"status": "received_completely", "document_type": "Policy"},
    )

    checklist = client.get(f"/api/v1/engagements/{engagement_id}/checklist").json()
    item = next(i for i in checklist["items"] if i["question_id"] == target)
    tracking = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()["tracking"][target]

    assert item["status"] == tracking["status"] == "received_completely"
    assert item["document_type"] == tracking["document_type"] == "Policy"
    assert item["priority"] == tracking["priority"]



# ------------------------------------------ questions as well as documents (2026-09-02)


def test_the_investigation_library_loads_with_its_citations() -> None:
    from app.services.irl.investigation import get_investigation_library

    library = get_investigation_library()
    sourced = {c: w for c, w in library.workstreams.items() if w.questions}

    assert sourced, "DD_master supplies questions for several workstreams"
    for code, entry in sourced.items():
        assert entry.citation.startswith("DD_master"), f"{code} must cite its page"
        assert entry.source == "dd_master"
        for question in entry.questions:
            assert question.text.strip()
            # The source formats some as bold-labelled bullets; the label is not text a
            # client should read.
            assert "**" not in question.text


def test_the_unsourced_workstreams_are_recorded_not_omitted() -> None:
    """A gap the reader can see beats a gap that looks like coverage."""
    from app.services.irl.investigation import get_investigation_library, unsourced_workstreams

    library = get_investigation_library()
    gaps = unsourced_workstreams()

    assert {"W-SEC", "W-DATA", "W-SEP", "W-INT", "W-PROD"} <= gaps
    for code in gaps:
        assert code in library.workstreams, "a gap must still be listed"
        assert library.workstreams[code].source == "none"


def test_questions_are_deduplicated_across_workstreams() -> None:
    """A row carrying two workstreams must not ask the same question twice."""
    from app.services.irl.investigation import questions_for

    both = questions_for(["W-APP", "W-APP"])
    once = questions_for(["W-APP"])
    assert len(both) == len(once)


def test_a_scope_row_inherits_its_workstreams_questions() -> None:
    """Provenance runs the same way as evidence: row -> workstream -> page."""
    seeds = [s for s in build_seeds(scope_for()) if s.kind == "question"]
    assert seeds

    for seed in seeds:
        assert seed.source_workstream in seed.workstreams
        assert seed.citation.startswith("DD_master")


def test_the_rules_list_asks_questions_without_an_llm() -> None:
    """The deterministic floor now includes questions, not only documents."""
    payload = rules_irl()

    kinds = {q.kind for q in payload.questions}
    assert kinds == {"document", "question"}

    asked = [q for q in payload.questions if q.kind == "question"]
    # A question seed is already a question; it must not be prefixed like an artefact.
    assert all(not q.question.startswith("Please provide") for q in asked)
    assert all(q.citation for q in asked)


def test_a_seeds_kind_is_authoritative_over_the_model() -> None:
    """The model may reword a question but not turn it into a document request.

    Flipping the kind would break both the tracking semantics and the citation.
    """
    from app.schemas.irl import LlmIrl, LlmIrlQuestion
    from app.services.irl.llm import apply_irl

    seeds = build_seeds(scope_for())
    question_seed = next(s for s in seeds if s.kind == "question")
    document_seed = next(s for s in seeds if s.kind == "document")

    tailoring = LlmIrl(
        intro="An intro.",
        questions=[
            LlmIrlQuestion(
                seed_id=s.id,
                function="IT",
                question="Rewritten.",
                # The model claims the opposite kind for both.
                kind="document" if s.kind == "question" else "question",
            )
            for s in seeds
        ],
    )

    payload = apply_irl(
        tailoring,
        seeds,
        company_name=None,
        source_scope_version=1,
        used_research=False,
        generator="llm",
        prompt_version="3.0",
    )
    by_id = {q.id: q for q in payload.questions}
    assert by_id[question_seed.id].kind == "question"
    assert by_id[document_seed.id].kind == "document"

