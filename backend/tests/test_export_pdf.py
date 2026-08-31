"""PDF export.

A PDF is opaque compared with Markdown, so these tests assert on what can be checked
without a parser: the byte signature, determinism, the download headers, route
precedence, and — via the extracted text layer — that the client-facing/internal split
is actually enforced rather than merely intended.
"""

import re

import reportlab.rl_config
from fastapi.testclient import TestClient

from app.services.scope.export_pdf import pdf_filename, render_pdf, render_pdf_from_payload
from app.services.scope.rules_generator import RulesScopeGenerator
from tests.factories import make_intake
from tests.test_engagement_flow import SECTIONS_PAYLOAD

# ReportLab writes page streams as ASCII85 + Flate by default, which no simple regex can
# read back. Turning compression off for the test session leaves the text as plain
# literals in the file, so the assertions below can check what the document actually
# says. This changes only the byte encoding, never the content or the layout.
reportlab.rl_config.pageCompression = 0

PRODUCT = dict(
    company_name="Meridian Analytics",
    line_of_business="Sells a usage-based analytics platform to mid-market e-commerce retailers.",
    dd_type_preference="Product Tech DD",
    digital_maturity="Digital native",
    data_sensitivity=["Personal data (PII)"],
    compliance_regimes=["SOC 2"],
)

FILED_DEAL_NAME = "Project Redline"


def scope_pdf(**overrides) -> bytes:
    scope = RulesScopeGenerator().generate(make_intake(**{**PRODUCT, **overrides}))
    return render_pdf(scope, deal_name="Project Lighthouse", version=1)


def pdf_text(pdf: bytes) -> str:
    """Best-effort text recovery. Not a PDF parser.

    With compression off (see the module header) ReportLab writes text as
    `(literal) Tj` / `[...] TJ` operators, so pulling the parenthesised literals out
    of the file recovers enough to assert that a phrase is or is not in the document.
    Word boundaries are approximate; substring checks are what this supports.
    """
    body = pdf.decode("latin-1", errors="ignore")
    literals = re.findall(r"\((?:[^()\\]|\\.)*\)", body)
    # Strip the surrounding parens and undo PDF's backslash escaping.
    return " ".join(lit[1:-1] for lit in literals).replace("\\", "")


def _filed_engagement(client: TestClient) -> str:
    response = client.post("/api/v1/engagements", json={"deal_name": "Project Lighthouse"})
    engagement_id = response.json()["id"]
    for section, payload in SECTIONS_PAYLOAD.items():
        client.patch(f"/api/v1/engagements/{engagement_id}/intake/{section}", json=payload)
    client.post(f"/api/v1/engagements/{engagement_id}/submit")
    return engagement_id


# ------------------------------------------------------------------------ renderer


def test_render_produces_a_valid_pdf() -> None:
    pdf = scope_pdf()
    assert pdf.startswith(b"%PDF-")
    assert pdf.rstrip().endswith(b"%%EOF")
    assert len(pdf) > 5_000  # a real document, not an empty shell


def _strip_volatile(pdf: bytes) -> bytes:
    """Mask the two things ReportLab derives from the clock.

    `/CreationDate` and `/ModDate` carry the render time, and the trailer `/ID` is a
    hash seeded from it. Everything else — every byte of actual document content — has
    to match between renders.
    """
    pdf = re.sub(rb"/(CreationDate|ModDate) ?\(D:[^)]*\)", b"", pdf)
    return re.sub(rb"/ID\s*\[<[0-9a-f]+><[0-9a-f]+>\]", b"", pdf)


def test_render_is_deterministic() -> None:
    """Two renders of one payload must be identical apart from the clock-derived bytes."""
    assert _strip_volatile(scope_pdf()) == _strip_volatile(scope_pdf())


def test_the_document_carries_the_deal_and_the_deck() -> None:
    text = pdf_text(scope_pdf())
    assert "Project Lighthouse" in text
    assert "Product Due Diligence" in text


def test_client_facing_sections_are_present() -> None:
    text = pdf_text(scope_pdf())
    for heading in ("Engagement", "Scope of work", "Cost estimation", "Exclusions"):
        assert heading in text, f"missing section: {heading}"


def test_the_internal_audit_trail_is_omitted() -> None:
    """The split that justifies a separate renderer: no signals, no rule provenance.

    If this fails, the PDF has silently become the Markdown export and the
    "client-facing" claim in the module docstring is no longer true.
    """
    text = pdf_text(scope_pdf())
    assert "Provenance" not in text
    assert "Signals" not in text


def test_tier_badges_and_reasons_are_not_shown_on_the_scope_rows() -> None:
    """Depth is an internal decision (Rishi, 2026-08-31) and is not badged on rows.

    The badges are gone entirely, and so is the "core coverage; mandatory at Tier N"
    reason line that sat under each title. "Deep dive" survives only as a sequencing
    phase name, which is why that string is not asserted against here.
    """
    text = pdf_text(scope_pdf())

    # The tier-reason line that used to sit under every title.
    assert "mandatory at Tier" not in text
    assert "core coverage" not in text

    # The badge rendered each tier name as a standalone upper-case token. A plain
    # substring check would be useless — the KPMG source wording legitimately contains
    # "assessment", "screening" and so on — so this matches whole words only.
    from app.schemas.selection import TIER_NAMES

    for tier_name in TIER_NAMES.values():
        badge = tier_name.upper()
        assert not re.search(rf"\b{re.escape(badge)}\b", text), (
            f"tier badge leaked into the PDF: {badge}"
        )


def test_exclusions_are_never_dropped() -> None:
    """DD_master G4 — a scope that does not say what it excludes is not a scope."""
    assert "does not say what it excludes" in pdf_text(scope_pdf())


def test_special_characters_do_not_break_the_render() -> None:
    """`&` and `<` are markup in ReportLab's Paragraph dialect and must be escaped."""
    pdf = render_pdf(
        RulesScopeGenerator().generate(
            make_intake(**{**PRODUCT, "company_name": "Ampersand & Sons <Holdings>"})
        ),
        deal_name="Deal & Co <Alpha>",
        version=1,
    )
    assert pdf.startswith(b"%PDF-")
    assert "Deal & Co <Alpha>" in pdf_text(pdf)


def test_only_schema_v2_is_exportable() -> None:
    try:
        render_pdf_from_payload({"schema_version": 1}, "Project Lighthouse", 1)
    except ValueError as exc:
        assert "schema v2" in str(exc)
    else:
        raise AssertionError("a v1 payload must not be exportable")


def test_filename_is_slugged() -> None:
    assert pdf_filename("Project Redline", 2) == "project-redline-scope-v2.pdf"
    assert pdf_filename("!!!", 1) == "scope-v1.pdf"


# -------------------------------------------------------------------------- route


def test_export_pdf_endpoint_returns_a_pdf_download(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")

    response = client.get(f"/api/v1/engagements/{engagement_id}/scope/export.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")

    disposition = response.headers["content-disposition"]
    assert "attachment" in disposition
    assert "project-redline-scope-v1.pdf" in disposition


def test_export_pdf_route_is_not_shadowed_by_the_version_route(client: TestClient) -> None:
    """`/export.pdf` is declared before `/{version}`; confirm it is not read as one."""
    engagement_id = _filed_engagement(client)
    client.post(f"/api/v1/engagements/{engagement_id}/scope")

    response = client.get(f"/api/v1/engagements/{engagement_id}/scope/export.pdf")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_export_pdf_without_a_scope_returns_404(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    response = client.get(f"/api/v1/engagements/{engagement_id}/scope/export.pdf")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "no_scope"


def test_human_edits_survive_into_the_pdf(client: TestClient) -> None:
    engagement_id = _filed_engagement(client)
    scope = client.post(f"/api/v1/engagements/{engagement_id}/scope").json()
    row_id = scope["payload"]["rows"][0]["id"]

    client.patch(
        f"/api/v1/engagements/{engagement_id}/scope/1/rows/{row_id}",
        json={"tier": 1, "reason": "Client has had this area reviewed externally."},
    )

    response = client.get(f"/api/v1/engagements/{engagement_id}/scope/export.pdf")
    text = pdf_text(response.content)
    assert "Edited by hand" in text
    assert "reviewed externally" in text
