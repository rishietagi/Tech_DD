"""Markdown export."""

from fastapi.testclient import TestClient

from app.services.scope.export import render_markdown
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


def scope_markdown(**overrides) -> str:
    scope = RulesScopeGenerator().generate(make_intake(**{**PRODUCT, **overrides}))
    return render_markdown(scope, deal_name="Project Lighthouse", version=1)


# The context step sets deal_name to "Project Redline", which overrides whatever the
# engagement was created with — so that is the name the export uses.
FILED_DEAL_NAME = "Project Redline"


def _filed_engagement(client: TestClient) -> str:
    response = client.post("/api/v1/engagements", json={"deal_name": "Project Lighthouse"})
    engagement_id = response.json()["id"]
    for section, payload in SECTIONS_PAYLOAD.items():
        client.patch(f"/api/v1/engagements/{engagement_id}/intake/{section}", json=payload)
    client.post(f"/api/v1/engagements/{engagement_id}/submit")
    return engagement_id


# ------------------------------------------------------------------------ renderer


def test_markdown_has_a_title_and_the_deal_name() -> None:
    markdown = scope_markdown()
    assert markdown.startswith("# Project Lighthouse — Product Due Diligence")


def test_every_major_section_is_present() -> None:
    markdown = scope_markdown()
    for heading in (
        "## Classification",
        "## Engagement",
        "## Objectives",
        "## Scope of work",
        "## Sequencing",
        "## Cost estimation",
        "## Team",
        "## Exclusions",
        "## Provenance",
    ):
        assert heading in markdown, f"missing {heading}"


def test_rows_carry_their_wording_depth_and_evidence() -> None:
    markdown = scope_markdown()
    assert "#### 01." in markdown
    assert "Deep dive" in markdown or "Assess" in markdown
    assert "**Evidence requested**" in markdown
    assert "Architecture diagrams and system documentation" in markdown


def test_signals_carry_their_rule_ids_and_citations() -> None:
    """The audit trail has to survive the export, or the document cannot be defended."""
    markdown = scope_markdown()
    assert "### Signals" in markdown
    assert "**A1**" in markdown
    assert "Roehl-Anderson 2013" in markdown


def test_cost_language_is_order_of_magnitude() -> None:
    markdown = scope_markdown()
    assert "order-of-magnitude" in markdown
    assert "never as point estimates" in markdown
    assert "## Assumptions register" in markdown


def test_exclusions_are_rendered() -> None:
    markdown = scope_markdown()
    assert "A scope that does not say what it excludes is not a scope." in markdown


def test_override_disagreement_is_rendered() -> None:
    """Declaring enterprise on a product-shaped target must show both views."""
    markdown = scope_markdown(dd_type_preference="Enterprise IT DD")
    assert "Archetype declared in the intake" in markdown
    assert "The engine derived" in markdown


def test_blended_export_labels_both_decks() -> None:
    markdown = scope_markdown(dd_type_preference="Blended")
    assert "### Product due diligence" in markdown
    assert "### Enterprise IT due diligence" in markdown


def test_footer_records_the_versions() -> None:
    markdown = scope_markdown()
    assert "Version 1 ·" in markdown
    assert "library v" in markdown.lower()
    assert "rules v" in markdown.lower()


def test_export_is_deterministic() -> None:
    assert scope_markdown() == scope_markdown()


# ------------------------------------------------------------------------ endpoint


def test_export_endpoint_returns_markdown(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")

    response = client.get(f"/api/v1/engagements/{engagement_id}/scope/export")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/markdown")
    assert response.text.startswith(f"# {FILED_DEAL_NAME}")


def test_export_sets_a_download_filename(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")

    response = client.get(f"/api/v1/engagements/{engagement_id}/scope/export")
    disposition = response.headers["content-disposition"]
    assert "attachment" in disposition
    assert "project-redline-scope-v1.md" in disposition


def test_export_route_is_not_shadowed_by_the_version_route(client: TestClient) -> None:
    """`/export` is declared before `/{version}`; confirm it is not read as a version."""
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")

    response = client.get(f"/api/v1/engagements/{engagement_id}/scope/export")
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"]


def test_export_without_a_scope_returns_404(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    response = client.get(f"/api/v1/engagements/{engagement_id}/scope/export")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "no_scope"


def test_human_edits_survive_into_the_export(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    scope = client.post(f"/api/v1/engagements/{engagement_id}/scope").json()
    row_id = scope["payload"]["rows"][0]["id"]

    client.patch(
        f"/api/v1/engagements/{engagement_id}/scope/1/rows/{row_id}",
        json={"tier": 1, "reason": "Client has had this area reviewed externally."},
    )

    response = client.get(f"/api/v1/engagements/{engagement_id}/scope/export")
    assert "Edited by hand" in response.text
    assert "reviewed externally" in response.text
