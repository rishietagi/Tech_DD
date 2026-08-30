from fastapi.testclient import TestClient

SECTIONS_PAYLOAD = {
    "context": {
        "deal_name": "Project Redline",
        "context_narrative": "Target is exploring a sale process after inbound interest from strategics in the space.",
        "deal_stage": "Exclusivity",
        "process_type": "Limited process",
        "investor_firm_name": "Northbridge Capital",
    },
    "rationale": {
        "rationale_narrative": (
            "Buyer believes the product can be cross-sold into its existing enterprise customer base."
        ),
        "value_creation_levers": ["Product expansion", "Cost takeout"],
    },
    "structure": {
        "investment_type": "strategic",
        "stake": "majority",
        "post_close_intent": "Integrate into existing platform",
    },
    "target": {
        "company_name": "Acme Analytics",
        "sector": "SaaS",
        "line_of_business": "Sells usage-based analytics tooling to mid-market e-commerce companies.",
        "business_model": "B2B SaaS",
        "digital_maturity": "Digital native",
        "headcount": 120,
        "revenue_stage": "Growth",
        "hq_location": "Austin, TX",
    },
    "technology": {
        "tech_is_product": "Yes, the software is the product",
        "hosting_model": "Public cloud",
        "ai_ml_dependence": "Embedded in the product",
        "data_sensitivity": ["Personal data (PII)"],
    },
    "objectives": {
        "dd_objectives": ["Validate scalability", "Quantify tech debt"],
        "access_level": "Full (data room and management sessions)",
        "deliverable_format": ["Full diligence report"],
        "timeline_weeks": 4,
        "dd_type_preference": "Product Tech DD",
    },
}


def _create_engagement(client: TestClient) -> str:
    response = client.post("/api/v1/engagements", json={"deal_name": "Project Redline"})
    assert response.status_code == 201
    return response.json()["id"]


def test_full_intake_flow(client: TestClient) -> None:
    engagement_id = _create_engagement(client)

    for section, payload in SECTIONS_PAYLOAD.items():
        response = client.patch(f"/api/v1/engagements/{engagement_id}/intake/{section}", json=payload)
        assert response.status_code == 200, response.text
        saved_section = response.json()["intake"][section]
        first_field = next(iter(payload))
        assert saved_section[first_field] == payload[first_field]

    submit_response = client.post(f"/api/v1/engagements/{engagement_id}/submit")
    assert submit_response.status_code == 200, submit_response.text
    assert submit_response.json()["status"] == "filed"

    list_response = client.get("/api/v1/engagements")
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert list_response.json()["items"][0]["id"] == engagement_id

    scope_response = client.post(f"/api/v1/engagements/{engagement_id}/scope")
    assert scope_response.status_code == 200, scope_response.text
    scope_body = scope_response.json()
    assert scope_body["version"] == 1
    assert scope_body["generator"] == "rules"

    payload = scope_body["payload"]
    assert payload["schema_version"] == 2
    assert payload["is_placeholder"] is False
    # The intake declared "Product Tech DD", so the product deck ships.
    assert payload["classification"]["dd_type"] == "product"
    assert len(payload["rows"]) >= 5
    assert payload["exclusions"], "a scope must state what it excludes (G4)"
    assert payload["provenance"], "a scope must show the rules that fired (G5)"

    latest_response = client.get(f"/api/v1/engagements/{engagement_id}/scope")
    assert latest_response.status_code == 200
    assert latest_response.json()["version"] == 1

    versions_response = client.get(f"/api/v1/engagements/{engagement_id}/scope/versions")
    assert versions_response.status_code == 200
    assert len(versions_response.json()) == 1


def test_full_intake_can_be_filed_with_only_mandatory_fields(client: TestClient) -> None:
    """Every field is optional except target.sector and target.line_of_business."""
    engagement_id = _create_engagement(client)

    minimal_target = {
        "sector": "SaaS",
        "line_of_business": "Sells usage-based analytics tooling to mid-market e-commerce companies.",
    }
    response = client.patch(f"/api/v1/engagements/{engagement_id}/intake/target", json=minimal_target)
    assert response.status_code == 200, response.text

    submit_response = client.post(f"/api/v1/engagements/{engagement_id}/submit")
    assert submit_response.status_code == 200, submit_response.text
    assert submit_response.json()["status"] == "filed"


def test_dd_type_preference_populates_denorm(client: TestClient) -> None:
    """The user's declared archetype is lifted onto denorm.dd_type for filtering."""
    engagement_id = _create_engagement(client)

    client.patch(
        f"/api/v1/engagements/{engagement_id}/intake/objectives",
        json={**SECTIONS_PAYLOAD["objectives"], "dd_type_preference": "Enterprise IT DD"},
    )
    listed = client.get("/api/v1/engagements").json()["items"][0]
    assert listed["denorm"]["dd_type"] == "enterprise"

    # "Let the platform decide" clears it back to Undetermined until the engine runs.
    client.patch(
        f"/api/v1/engagements/{engagement_id}/intake/objectives",
        json={**SECTIONS_PAYLOAD["objectives"], "dd_type_preference": "Let the platform decide"},
    )
    listed = client.get("/api/v1/engagements").json()["items"][0]
    assert listed["denorm"]["dd_type"] is None


def test_partial_draft_can_be_resumed(client: TestClient) -> None:
    engagement_id = _create_engagement(client)

    client.patch(f"/api/v1/engagements/{engagement_id}/intake/context", json=SECTIONS_PAYLOAD["context"])

    fetched = client.get(f"/api/v1/engagements/{engagement_id}")
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["intake"]["context"]["deal_name"] == "Project Redline"
    assert body["intake"]["rationale"] is None or body["intake"]["rationale"] == {}
    assert body["status"] == "draft"


def test_submit_with_incomplete_intake_returns_field_errors(client: TestClient) -> None:
    engagement_id = _create_engagement(client)

    response = client.post(f"/api/v1/engagements/{engagement_id}/submit")
    assert response.status_code == 422
    body = response.json()
    assert body["detail"]["code"] == "incomplete_intake"
    assert isinstance(body["detail"]["field_errors"], list)
    assert len(body["detail"]["field_errors"]) > 0
    assert all("field" in e and "message" in e for e in body["detail"]["field_errors"])


def test_scope_requires_filed_engagement(client: TestClient) -> None:
    engagement_id = _create_engagement(client)
    response = client.post(f"/api/v1/engagements/{engagement_id}/scope")
    assert response.status_code == 409


def test_health_and_enums(client: TestClient) -> None:
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    enums = client.get("/api/v1/meta/enums")
    assert enums.status_code == 200
    assert "sector" in enums.json()["enums"]
    assert "dealStage" in enums.json()["enums"]
    assert "ddTypePreference" in enums.json()["enums"]
    assert "investorType" not in enums.json()["enums"]
    assert "codeAccess" not in enums.json()["enums"]
