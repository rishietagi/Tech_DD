"""The IRL checklist: ranking, status tracking, and the deferred scanner.

The properties that matter:
- priority is derived from the scope and is explainable;
- the distribution actually discriminates — a scale where everything is critical is
  not a scale;
- statuses default to `not_received` without needing a backfill;
- a human edit is marked as such, so a later scan will not overwrite it.
"""

import json
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.schemas.irl import IrlQuestion
from app.services.checklist import scan_llm, scanner
from app.services.checklist import service as checklist_service
from app.services.checklist.ranking import rank_questions
from app.services.scope.rules_generator import RulesScopeGenerator
from tests.factories import make_intake
from tests.test_engagement_flow import SECTIONS_PAYLOAD

PRODUCT = dict(
    company_name="Meridian Analytics",
    line_of_business="Sells a usage-based analytics platform to mid-market e-commerce retailers.",
    dd_type_preference="Product Tech DD",
    digital_maturity="Digital native",
    data_sensitivity=["Personal data (PII)"],
    compliance_regimes=["SOC 2"],
)


def _scope():
    return RulesScopeGenerator().generate(make_intake(**PRODUCT))


def _filed_engagement(client: TestClient) -> str:
    response = client.post("/api/v1/engagements", json={"deal_name": "Project Lighthouse"})
    engagement_id = response.json()["id"]
    for section, payload in SECTIONS_PAYLOAD.items():
        client.patch(f"/api/v1/engagements/{engagement_id}/intake/{section}", json=payload)
    client.post(f"/api/v1/engagements/{engagement_id}/submit")
    return engagement_id


def _engagement_with_irl(client: TestClient) -> str:
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")
    client.post(f"/api/v1/engagements/{engagement_id}/irl")
    return engagement_id


# -------------------------------------------------------------------------- ranking


def test_security_evidence_is_critical_whatever_the_tier() -> None:
    """A gap in security or regulatory evidence is a deal issue, not a depth question."""
    scope = _scope()
    security_row = next(r for r in scope.rows if "W-SEC" in r.workstreams)

    question = IrlQuestion(
        id="Q1",
        function="Information Security",
        question="Provide the penetration test report.",
        source="scope",
        source_row_id=security_row.id,
    )
    priority, reason = rank_questions([question], scope)["Q1"]

    assert priority == "critical"
    assert "security" in reason.lower() or "regulatory" in reason.lower()


def test_depth_alone_is_high_not_critical() -> None:
    """Calibration guard: deep dive is important, but not automatically critical.

    An earlier version made every deep-dive request critical, which put over half a real
    45-request list in one bucket and left the colour meaningless.
    """
    scope = _scope()
    row = next(
        r
        for r in scope.rows
        if r.tier >= 3 and not ({"W-SEC", "W-PROC", "W-DATA"} & set(r.workstreams))
    )

    question = IrlQuestion(
        id="Q1", function="Engineering", question="Provide it.", source="scope",
        source_row_id=row.id,
    )
    assert rank_questions([question], scope)["Q1"][0] == "high"


def test_the_scale_actually_discriminates() -> None:
    """No single level may swallow the list — that is what makes the colours useful."""
    from app.services.irl.llm import RulesIrlGenerator

    intake = make_intake(**PRODUCT)
    scope = RulesScopeGenerator().generate(intake)
    payload = RulesIrlGenerator().generate(intake, scope, source_scope_version=1)

    ranked = rank_questions(payload.questions, scope)
    spread = Counter(priority for priority, _ in ranked.values())

    assert len(spread) >= 2, "a scale with one level is not a scale"
    biggest = max(spread.values())
    assert biggest < len(ranked), "one level must not swallow every request"


def test_model_added_legal_and_finance_outrank_supporting_context() -> None:
    """A missing IP assignment matters more than a nice-to-have overview."""
    legal = IrlQuestion(id="A1", function="Legal", question="Provide the licences.", source="llm")
    other = IrlQuestion(id="A2", function="Engineering", question="Provide an overview.", source="llm")

    ranked = rank_questions([legal, other], _scope())
    assert ranked["A1"][0] == "high"
    assert ranked["A2"][0] == "low"


def test_a_question_whose_scope_row_vanished_still_ranks() -> None:
    """The scope can be regenerated under an existing IRL. It must not crash the view."""
    question = IrlQuestion(
        id="Q1", function="IT", question="Provide it.", source="scope",
        source_row_id="NO-SUCH-ROW",
    )
    priority, reason = rank_questions([question], _scope())["Q1"]

    assert priority == "medium"
    assert "no longer" in reason.lower()


def test_ranking_without_a_scope_degrades_rather_than_failing() -> None:
    question = IrlQuestion(
        id="Q1", function="IT", question="Provide it.", source="scope", source_row_id="PD-01"
    )
    assert rank_questions([question], None)["Q1"][0] == "medium"


# --------------------------------------------------------------------------- routes


def test_checklist_needs_a_request_list(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")

    response = client.get(f"/api/v1/engagements/{engagement_id}/checklist")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "no_irl"


def test_every_request_starts_not_received(client: TestClient) -> None:
    """No backfill needed: absence of a status row means not received."""
    engagement_id = _engagement_with_irl(client)

    body = client.get(f"/api/v1/engagements/{engagement_id}/checklist").json()
    assert body["items"], "the checklist must cover the request list"
    assert all(i["status"] == "not_received" for i in body["items"])
    assert body["summary"]["not_received"] == body["summary"]["total"]
    assert body["summary"]["received_completely"] == 0


def test_every_item_carries_a_priority_and_a_reason(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    body = client.get(f"/api/v1/engagements/{engagement_id}/checklist").json()

    assert all(i["priority"] in {"critical", "high", "medium", "low"} for i in body["items"])
    assert all(i["priority_reason"].strip() for i in body["items"])


def test_items_are_ordered_most_important_first(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    items = client.get(f"/api/v1/engagements/{engagement_id}/checklist").json()["items"]

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    ranks = [order[i["priority"]] for i in items]
    assert ranks == sorted(ranks), "a consultant reads top-down; the urgent work is at the top"


def test_setting_a_status_persists_and_updates_the_summary(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    items = client.get(f"/api/v1/engagements/{engagement_id}/checklist").json()["items"]
    question_id = items[0]["question_id"]

    updated = client.patch(
        f"/api/v1/engagements/{engagement_id}/checklist/{question_id}",
        json={"status": "received_completely", "document_type": "Report"},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["summary"]["received_completely"] == 1

    row = next(i for i in body["items"] if i["question_id"] == question_id)
    assert row["status"] == "received_completely"
    assert row["document_type"] == "Report"

    # And it survives a re-fetch, not just the mutation response.
    refetched = client.get(f"/api/v1/engagements/{engagement_id}/checklist").json()
    assert next(
        i for i in refetched["items"] if i["question_id"] == question_id
    )["status"] == "received_completely"


def test_a_human_edit_is_marked_so_a_scan_cannot_overwrite_it(client: TestClient) -> None:
    """`set_by_human` is what will protect a judgement from the future scanner."""
    engagement_id = _engagement_with_irl(client)
    items = client.get(f"/api/v1/engagements/{engagement_id}/checklist").json()["items"]
    question_id = items[0]["question_id"]

    body = client.patch(
        f"/api/v1/engagements/{engagement_id}/checklist/{question_id}",
        json={"status": "received_partially"},
    ).json()

    assert next(i for i in body["items"] if i["question_id"] == question_id)["set_by_human"] is True


def test_partial_counts_separately_from_received(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    items = client.get(f"/api/v1/engagements/{engagement_id}/checklist").json()["items"]

    client.patch(
        f"/api/v1/engagements/{engagement_id}/checklist/{items[0]['question_id']}",
        json={"status": "received_partially"},
    )
    summary = client.get(f"/api/v1/engagements/{engagement_id}/checklist").json()["summary"]

    assert summary["received_partially"] == 1
    assert summary["received_completely"] == 0


def test_an_unknown_question_id_is_404(client: TestClient) -> None:
    engagement_id = _engagement_with_irl(client)
    response = client.patch(
        f"/api/v1/engagements/{engagement_id}/checklist/NOPE-1",
        json={"status": "received_completely"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "unknown_question"


def test_the_scan_route_returns_a_checklist_and_says_what_it_did(
    client: TestClient, tmp_path: Path
) -> None:
    """Was a 501 until 2026-09-09. The route now walks the drive for real."""
    engagement_id = _engagement_with_irl(client)
    root = tmp_path / "empty-drive"
    root.mkdir()

    settings = Settings(shared_drive_root=str(root), gemini_api_key=None)
    with patch.object(checklist_service, "get_settings", return_value=settings):
        response = client.post(f"/api/v1/engagements/{engagement_id}/checklist/scan")

    assert response.status_code == 200
    body = response.json()
    assert body["items"], "a scan returns the rebuilt checklist"
    assert body["scan"]["scanned_path"] == str(root)
    assert body["scan"]["files_seen"] == 0


def test_deleting_an_engagement_removes_its_statuses(client: TestClient, db_session) -> None:
    from app.models.irl import IrlDocumentStatus

    engagement_id = _engagement_with_irl(client)
    items = client.get(f"/api/v1/engagements/{engagement_id}/checklist").json()["items"]
    client.patch(
        f"/api/v1/engagements/{engagement_id}/checklist/{items[0]['question_id']}",
        json={"status": "received_completely"},
    )

    db_session.expire_all()
    assert db_session.query(IrlDocumentStatus).count() >= 1

    client.delete(f"/api/v1/engagements/{engagement_id}?permanent=true")

    db_session.expire_all()
    assert db_session.query(IrlDocumentStatus).count() == 0


def _filename_matching(question: dict) -> str:
    """A filename built from the tokens the matcher actually scores on.

    The IRL is model-generated, so its exact wording changes between runs. Deriving the
    filename from `scanner._tokenise` rather than from the prose keeps these tests about
    the scanner instead of about what the model happened to write today.
    """
    tokens = sorted(scanner._tokenise(f"{question['question']} {question.get('seed_text') or ''}"))
    return "-".join(tokens[:5]) or "Document"


def _first_document(client: TestClient, engagement_id: str) -> dict:
    irl = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()
    documents = [q for q in irl["payload"]["questions"] if q["kind"] == "document"]
    assert documents, "the IRL must contain document requests for this to test anything"
    return documents[0]


class _FakeGemini:
    """Stands in for the Gemini client. Tests never call the live API."""

    class _Models:
        def __init__(self, text: str) -> None:
            self._text = text
            self.last_contents: str | None = None

        def generate_content(self, **kwargs: object):
            self.last_contents = str(kwargs.get("contents", ""))
            return type("R", (), {"text": self._text})()

    def __init__(self, text: str) -> None:
        self.models = self._Models(text)



# ------------------------------------------------- shared-drive scanner (2026-09-09)
#
# The scanner writes statuses on its own, so the tests that matter are the ones that
# pin what it must NOT do: overwrite a human, invent a document, or mark a question
# received because a file turned up nearby.


def _drive(tmp_path: Path, layout: dict[str, str]) -> Path:
    """Build a throwaway shared drive. Keys are relative paths, values file contents."""
    root = tmp_path / "drive"
    for relative, content in layout.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    root.mkdir(parents=True, exist_ok=True)
    return root


def _question(qid: str, text: str, *, kind: str = "document", seed: str = "") -> IrlQuestion:
    return IrlQuestion(
        id=qid, function="IT", question=text, kind=kind, seed_text=seed or None
    )


# ------------------------------------------------------------------ walking the drive


def test_the_walk_reads_files_and_skips_scaffolding(tmp_path: Path) -> None:
    root = _drive(
        tmp_path,
        {
            "01-IT/Application-Inventory.xlsx": "Application inventory with owners.",
            "01-IT/README.md": "not client material",
            ".git/config": "scaffolding",
        },
    )

    files = scanner.walk_drive(root)

    assert [f.name for f in files] == ["Application-Inventory.xlsx"]
    assert files[0].folder == "01-IT"
    assert files[0].relative_path == "01-IT/Application-Inventory.xlsx"
    # Contents are read, not just filenames — that is what partial detection needs.
    assert "owners" in files[0].excerpt


def test_a_missing_drive_is_a_stated_error_not_a_crash(tmp_path: Path) -> None:
    with pytest.raises(scanner.ScanError) as exc:
        scanner.walk_drive(tmp_path / "nothing-here")
    assert exc.value.status_code == 400
    assert "does not exist" in exc.value.message


def test_an_unreadable_file_does_not_stop_the_walk(tmp_path: Path) -> None:
    """A corrupt or binary file is normal on a client drive; it degrades to no excerpt."""
    root = tmp_path / "drive"
    (root / "01-IT").mkdir(parents=True)
    (root / "01-IT" / "Corrupt-Inventory.xlsx").write_bytes(bytes(range(256)) * 8)
    (root / "01-IT" / "Good-Policy.docx").write_text("Backup policy.", encoding="utf-8")

    files = scanner.walk_drive(root)

    assert len(files) == 2
    corrupt = next(f for f in files if f.name.startswith("Corrupt"))
    assert corrupt.excerpt == ""
    assert corrupt.extract_error, "an unreadable file must say so rather than look empty"


def test_an_image_is_identified_by_name_without_an_error(tmp_path: Path) -> None:
    """No excerpt and no error: not reading a .png is a decision, not a failure."""
    root = _drive(tmp_path, {"01-IT/Architecture-Diagram.png": "binary-ish"})
    diagram = scanner.walk_drive(root)[0]
    assert diagram.excerpt == ""
    assert diagram.extract_error == ""


# ----------------------------------------------------------------------- shortlisting


def test_a_short_filename_still_matches_a_long_request() -> None:
    """The bug that made the first build match 1 request in 35.

    A request is a sentence and a filename is three words. Scoring the overlap against
    the request's length punishes exactly the filenames that are obviously right.
    """
    root_questions = [
        _question(
            "EN-01-E1",
            "Provide a complete application inventory, including version and owner.",
            seed="Application inventory with business function, version and licensing",
        )
    ]
    files = [
        scanner.ExtractedFile(
            path=Path("x"),
            relative_path="01-IT/Application-Inventory-SAP-and-Bolt-ons.xlsx",
            name="Application-Inventory-SAP-and-Bolt-ons.xlsx",
            folder="01-IT",
            suffix=".xlsx",
            size_bytes=10,
            tokens=scanner._tokenise("Application-Inventory-SAP-and-Bolt-ons 01-IT"),
        )
    ]

    shortlisted = scanner.shortlist(root_questions, files)
    assert "EN-01-E1" in shortlisted


def test_an_abbreviated_filename_meets_a_spelled_out_request() -> None:
    """"IT-Org-Chart" must reach a request that says "organization chart"."""
    tokens = scanner._tokenise("IT-Org-Chart-2026 04-Human-Resources")
    assert {"organisation", "organization"} & tokens


def test_an_unrelated_file_is_not_shortlisted() -> None:
    questions = [_question("EN-01-E1", "Provide the data backup and disaster recovery policy.")]
    files = [
        scanner.ExtractedFile(
            path=Path("x"),
            relative_path="06-Commercial/Top-Customer-Contracts.docx",
            name="Top-Customer-Contracts.docx",
            folder="06-Commercial",
            suffix=".docx",
            size_bytes=10,
            tokens=scanner._tokenise("Top-Customer-Contracts 06-Commercial"),
        )
    ]
    assert scanner.shortlist(questions, files) == {}


# --------------------------------------------------------------- what a scan must not do


def test_a_scan_never_overwrites_a_human_set_status(client: TestClient, tmp_path: Path) -> None:
    """Rule 1 of scanner.py. Someone who looked at the document outranks a filename."""
    engagement_id = _engagement_with_irl(client)
    document = _first_document(client, engagement_id)
    target = document["id"]

    client.patch(
        f"/api/v1/engagements/{engagement_id}/checklist/{target}",
        json={"status": "received_completely", "notes": "Seen it, it is fine."},
    )

    # A file that would certainly match this request, were the row not protected.
    root = _drive(tmp_path, {f"01-IT/{_filename_matching(document)}.xlsx": "content"})
    with patch.object(checklist_service, "get_settings", return_value=Settings(shared_drive_root=str(root))):
        response = client.post(f"/api/v1/engagements/{engagement_id}/checklist/scan")

    assert response.status_code == 200
    after = {i["question_id"]: i for i in response.json()["items"]}
    assert after[target]["status"] == "received_completely"
    assert after[target]["notes"] == "Seen it, it is fine."
    assert after[target]["set_by_human"] is True
    assert response.json()["scan"]["skipped_human"] >= 1


def test_a_question_kind_request_is_never_scanned(client: TestClient, tmp_path: Path) -> None:
    """A question is answered in a meeting, not by a file appearing on a drive."""
    engagement_id = _engagement_with_irl(client)
    irl = client.get(f"/api/v1/engagements/{engagement_id}/irl").json()
    question_ids = {q["id"] for q in irl["payload"]["questions"] if q["kind"] == "question"}
    assert question_ids, "the fixture IRL must contain questions for this to test anything"

    root = _drive(tmp_path, {"01-IT/Everything-Inventory-Policy-Register.xlsx": "everything"})
    with patch.object(checklist_service, "get_settings", return_value=Settings(shared_drive_root=str(root))):
        response = client.post(f"/api/v1/engagements/{engagement_id}/checklist/scan")

    items = {i["question_id"]: i for i in response.json()["items"]}
    for qid in question_ids:
        assert items[qid]["status"] == "not_received", f"{qid} is a question, not a document"
        assert items[qid]["matched_files"] == []


def test_an_empty_folder_is_not_evidence_that_anything_arrived(
    client: TestClient, tmp_path: Path
) -> None:
    """The fixture's empty Commercial folder exists to catch exactly this."""
    engagement_id = _engagement_with_irl(client)
    root = tmp_path / "drive"
    (root / "06-Commercial-Department").mkdir(parents=True)

    with patch.object(checklist_service, "get_settings", return_value=Settings(shared_drive_root=str(root))):
        response = client.post(f"/api/v1/engagements/{engagement_id}/checklist/scan")

    body = response.json()
    assert body["scan"]["files_seen"] == 0
    assert body["scan"]["updated"] == 0
    assert all(i["status"] == "not_received" for i in body["items"])


def test_the_model_may_not_name_a_file_it_was_not_given() -> None:
    """The guard that stops an invented document becoming a receipt."""
    questions = [_question("EN-01-E1", "Provide the application inventory.")]
    candidates = {
        "EN-01-E1": [
            scanner.Candidate(
                file=scanner.ExtractedFile(
                    path=Path("x"),
                    relative_path="01-IT/Application-Inventory.xlsx",
                    name="Application-Inventory.xlsx",
                    folder="01-IT",
                    suffix=".xlsx",
                    size_bytes=10,
                ),
                score=0.9,
            )
        ]
    }

    judgements = scan_llm.judge_documents(
        questions,
        candidates,
        Settings(gemini_api_key="test-key"),
        client=_FakeGemini(
            json.dumps(
                {
                    "judgements": [
                        {
                            "request_id": "EN-01-E1",
                            "status": "received_completely",
                            "document_type": "Inventory",
                            "matched_files": ["01-IT/A-File-That-Does-Not-Exist.xlsx"],
                            "follow_up_questions": [],
                            "reasoning": "Invented.",
                        }
                    ]
                }
            )
        ),
    )

    # The invented filename is dropped, and a receipt with no surviving file is not one.
    assert judgements["EN-01-E1"].matched_files == []
    assert judgements["EN-01-E1"].status == "not_received"


def test_a_not_received_request_carries_no_follow_up() -> None:
    """The checklist already says it is outstanding; a follow-up would restate the ask."""
    questions = [_question("EN-01-E1", "Provide the application inventory.")]
    candidates = {
        "EN-01-E1": [
            scanner.Candidate(
                file=scanner.ExtractedFile(
                    path=Path("x"),
                    relative_path="01-IT/Something-Else.xlsx",
                    name="Something-Else.xlsx",
                    folder="01-IT",
                    suffix=".xlsx",
                    size_bytes=10,
                ),
                score=0.4,
            )
        ]
    }

    judgements = scan_llm.judge_documents(
        questions,
        candidates,
        Settings(gemini_api_key="test-key"),
        client=_FakeGemini(
            json.dumps(
                {
                    "judgements": [
                        {
                            "request_id": "EN-01-E1",
                            "status": "not_received",
                            "matched_files": [],
                            "follow_up_questions": ["Please send the inventory."],
                            "reasoning": "Not a match.",
                        }
                    ]
                }
            )
        ),
    )

    assert judgements["EN-01-E1"].follow_up_questions == []


def test_a_partial_receipt_keeps_its_follow_up_questions() -> None:
    """The output the whole feature exists for."""
    questions = [_question("EN-04-E4", "Provide twelve months of monitoring reports.")]
    candidates = {
        "EN-04-E4": [
            scanner.Candidate(
                file=scanner.ExtractedFile(
                    path=Path("x"),
                    relative_path="01-IT/Monitoring-2026Q1-ONLY.xlsx",
                    name="Monitoring-2026Q1-ONLY.xlsx",
                    folder="01-IT",
                    suffix=".xlsx",
                    size_bytes=10,
                    excerpt="Monitoring extract, Q1 2026 only.",
                ),
                score=0.8,
            )
        ]
    }

    judgements = scan_llm.judge_documents(
        questions,
        candidates,
        Settings(gemini_api_key="test-key"),
        client=_FakeGemini(
            json.dumps(
                {
                    "judgements": [
                        {
                            "request_id": "EN-04-E4",
                            "status": "received_partially",
                            "document_type": "Monitoring report",
                            "matched_files": ["01-IT/Monitoring-2026Q1-ONLY.xlsx"],
                            "follow_up_questions": [
                                "The report covers Q1 2026 only; please provide the full "
                                "twelve months, or confirm earlier data is not retained."
                            ],
                            "reasoning": "Explicitly one quarter of the period requested.",
                        }
                    ]
                }
            )
        ),
    )

    judgement = judgements["EN-04-E4"]
    assert judgement.status == "received_partially"
    assert judgement.document_type == "Monitoring report"
    assert len(judgement.follow_up_questions) == 1
    assert "Q1 2026" in judgement.follow_up_questions[0]


def test_more_than_three_follow_ups_are_trimmed() -> None:
    questions = [_question("EN-01-E1", "Provide the application inventory.")]
    candidates = {
        "EN-01-E1": [
            scanner.Candidate(
                file=scanner.ExtractedFile(
                    path=Path("x"),
                    relative_path="01-IT/Inventory.xlsx",
                    name="Inventory.xlsx",
                    folder="01-IT",
                    suffix=".xlsx",
                    size_bytes=10,
                ),
                score=0.9,
            )
        ]
    }
    judgements = scan_llm.judge_documents(
        questions,
        candidates,
        Settings(gemini_api_key="test-key"),
        client=_FakeGemini(
            json.dumps(
                {
                    "judgements": [
                        {
                            "request_id": "EN-01-E1",
                            "status": "received_partially",
                            "matched_files": ["01-IT/Inventory.xlsx"],
                            "follow_up_questions": [f"Question {n}?" for n in range(8)],
                            "reasoning": "Partial.",
                        }
                    ]
                }
            )
        ),
    )
    assert len(judgements["EN-01-E1"].follow_up_questions) == 3


# ------------------------------------------------------------------ without a model


def test_without_a_model_the_scan_still_matches_but_claims_less(
    client: TestClient, tmp_path: Path
) -> None:
    """No key means no content judgement, so it may not claim partial — only a strong match."""
    engagement_id = _engagement_with_irl(client)
    document = _first_document(client, engagement_id)

    # Name a file after a real request so the deterministic threshold is cleared.
    root = _drive(tmp_path, {f"01-IT/{_filename_matching(document)}.xlsx": "content"})

    settings = Settings(shared_drive_root=str(root), gemini_api_key=None)
    with patch.object(checklist_service, "get_settings", return_value=settings):
        response = client.post(f"/api/v1/engagements/{engagement_id}/checklist/scan")

    body = response.json()
    assert body["scan"]["generator"] == "rules"
    # Rule 3: filename matching cannot see completeness, so it never says "partial"...
    assert all(i["status"] != "received_partially" for i in body["items"])
    # ...and it invents no follow-up questions from a filename.
    assert body["scan"]["follow_ups"] == 0


def test_a_model_failure_falls_back_rather_than_losing_the_walk(
    client: TestClient, tmp_path: Path
) -> None:
    engagement_id = _engagement_with_irl(client)
    # The model is only consulted when the shortlist found something, so the drive has to
    # contain a real match for the fallback path to be exercised at all.
    document = _first_document(client, engagement_id)
    root = _drive(tmp_path, {f"01-IT/{_filename_matching(document)}.xlsx": "content"})

    settings = Settings(shared_drive_root=str(root), gemini_api_key="test-key")
    with (
        patch.object(checklist_service, "get_settings", return_value=settings),
        patch("app.services.checklist.scan_llm.judge_documents", side_effect=RuntimeError("boom")),
    ):
        response = client.post(f"/api/v1/engagements/{engagement_id}/checklist/scan")

    assert response.status_code == 200
    assert response.json()["scan"]["generator"] == "rules (llm failed)"


# ------------------------------------------------------------------------ round trip


def test_a_scan_records_what_it_matched_and_why(client: TestClient, tmp_path: Path) -> None:
    """Rule 2: a wrong call must be visible and correctable, not silent."""
    engagement_id = _engagement_with_irl(client)
    document = _first_document(client, engagement_id)
    root = _drive(tmp_path, {f"01-IT/{_filename_matching(document)}.xlsx": "content"})

    settings = Settings(shared_drive_root=str(root), gemini_api_key=None)
    with patch.object(checklist_service, "get_settings", return_value=settings):
        first = client.post(f"/api/v1/engagements/{engagement_id}/checklist/scan").json()

    matched = [i for i in first["items"] if i["matched_files"]]
    assert matched, "a strong filename match must be recorded"
    assert matched[0]["scan_reasoning"], "an automatic status needs a stated reason"
    assert matched[0]["scanned_at"] is not None
    assert matched[0]["set_by_human"] is False
    assert first["last_scanned_at"] is not None

    # A scan-written row is scan-owned, so a second scan may correct itself.
    with patch.object(checklist_service, "get_settings", return_value=settings):
        second = client.post(f"/api/v1/engagements/{engagement_id}/checklist/scan").json()
    assert second["scan"]["skipped_human"] == 0


def test_files_nothing_asked_for_are_reported(client: TestClient, tmp_path: Path) -> None:
    """A target sending something nobody requested is a fact about the deal."""
    engagement_id = _engagement_with_irl(client)
    root = _drive(tmp_path, {"09-Misc/Chairmans-Holiday-Photos.xlsx": "unrelated"})

    settings = Settings(shared_drive_root=str(root), gemini_api_key=None)
    with patch.object(checklist_service, "get_settings", return_value=settings):
        body = client.post(f"/api/v1/engagements/{engagement_id}/checklist/scan").json()

    assert body["scan"]["unmatched_files"] == ["09-Misc/Chairmans-Holiday-Photos.xlsx"]


def test_a_bad_drive_path_is_a_400_through_the_api(client: TestClient, tmp_path: Path) -> None:
    engagement_id = _engagement_with_irl(client)
    settings = Settings(shared_drive_root=str(tmp_path / "no-such-drive"))
    with patch.object(checklist_service, "get_settings", return_value=settings):
        response = client.post(f"/api/v1/engagements/{engagement_id}/checklist/scan")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "scan_failed"
