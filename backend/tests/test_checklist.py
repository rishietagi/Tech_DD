"""The IRL checklist: ranking, status tracking, and the deferred scanner.

The properties that matter:
- priority is derived from the scope and is explainable;
- the distribution actually discriminates — a scale where everything is critical is
  not a scale;
- statuses default to `not_received` without needing a backfill;
- a human edit is marked as such, so a later scan will not overwrite it.
"""

from collections import Counter

from fastapi.testclient import TestClient

from app.schemas.irl import IrlQuestion
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


def test_the_scanner_is_honestly_not_implemented(client: TestClient) -> None:
    """501 with an explanation beats a missing route or a silent no-op."""
    engagement_id = _engagement_with_irl(client)

    response = client.post(f"/api/v1/engagements/{engagement_id}/checklist/scan")
    assert response.status_code == 501
    detail = response.json()["detail"]
    assert detail["code"] == "scan_not_implemented"
    assert "deployment" in detail["message"]


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
