"""Guards the KPMG scope library.

The client-facing wording is transcribed verbatim from the source deck. These tests
fail if an edit drifts from that wording or breaks the schema, so the library stays
editable by a practitioner without becoming editable by accident.
"""

import pytest

from app.schemas.kpmg_library import ScopeDeck, ScopeRow
from app.services.scope.library import get_scope_library


def test_library_loads_and_has_both_decks() -> None:
    lib = get_scope_library()
    assert set(lib.decks) == {"product", "enterprise"}
    assert lib.manifest.library_version == "1.0"


def test_product_deck_has_all_ten_source_objectives() -> None:
    """The ten verbatim KPMG objectives are rows 1-10 and must all still be there.

    Rows 11 and 12 (product financials, artificial intelligence readiness) were added on
    2026-09-14 at Rishi's request: the source deck has neither, and a product diligence
    that covers neither is incomplete. They are additions, not source text, and the
    split is asserted here so a future edit cannot quietly drop a sourced objective while
    the row count still looks right.
    """
    deck = get_scope_library().deck("product")
    assert len(deck.rows) == 12
    assert [r.sn for r in deck.rows] == list(range(1, 13))

    source_rows = [r for r in deck.rows if r.sn <= 10]
    assert len(source_rows) == 10
    assert [r.id for r in source_rows] == [f"PD-{n:02d}" for n in range(1, 11)]

    added = {r.id: r for r in deck.rows if r.sn > 10}
    assert set(added) == {"PD-11", "PD-12"}
    assert added["PD-11"].objective == "Product financials"
    assert added["PD-12"].objective == "Artificial intelligence readiness"


def test_the_ai_row_opens_only_where_ai_is_material() -> None:
    """A product with no AI must not carry a section explaining that it has none.

    PD-12 is deliberately not always_in_scope: it opens on rule A11, which fires when
    ai_ml_dependence is "Embedded in the product" or "Core to the value proposition".
    """
    deck = get_scope_library().deck("product")
    ai_row = next(r for r in deck.rows if r.id == "PD-12")
    assert ai_row.always_in_scope is False
    assert "A11" in ai_row.triggers


def test_the_product_financials_row_reviews_budgeting_not_a_cost_model() -> None:
    """Rishi, 2026-09-14: we review the budgeting process, never a cost model.

    Pinned on both decks because the boundary is the engagement's, not one deck's.
    """
    library = get_scope_library()
    product = next(r for r in library.deck("product").rows if r.id == "PD-11")
    enterprise = next(r for r in library.deck("enterprise").rows if r.id == "EN-05")

    product_text = (product.scope_of_work or "").lower()
    enterprise_text = " ".join(enterprise.considerations or []).lower()

    for text, label in ((product_text, "PD-11"), (enterprise_text, "EN-05")):
        assert "cost model" not in text, f"{label} offers a cost model"
        assert "budget" in text, f"{label} must review the budgeting process"
        # The financial review period is stated so the client knows what is being asked.
        assert "three financial years" in text, f"{label} must state the review period"


def test_enterprise_deck_has_all_nine_source_focus_areas() -> None:
    deck = get_scope_library().deck("enterprise")
    assert len(deck.rows) == 9
    assert [r.focus_area for r in deck.rows] == [
        "Applications",
        "IT Strategy and Roadmap",
        "IT Org and Governance",
        "IT Infrastructure",
        "IT Financials",
        "IT Projects",
        "Software Development Lifecycle for internal apps",
        "Emerging Tech",
        "Contracts and Licenses",
    ]


def test_verbatim_wording_is_preserved() -> None:
    """Spot-check lines that must match the source deck exactly."""
    product = get_scope_library().deck("product")
    row1 = next(r for r in product.rows if r.id == "PD-01")
    assert row1.objective == "Review product tech stack and architecture for scalability constraints"
    assert "legacy languages/ frameworks" in (row1.scope_of_work or "")

    row5 = next(r for r in product.rows if r.id == "PD-05")
    assert row5.objective == "IT Regulatory aspects"
    assert "SAR audit report" in (row5.scope_of_work or "")

    enterprise = get_scope_library().deck("enterprise")
    apps = next(r for r in enterprise.rows if r.id == "EN-01")
    assert apps.considerations is not None
    assert "ERP, CRM, timesheet system, HRMS" in apps.considerations[0]


def test_every_row_carries_an_audit_trail() -> None:
    """A row with no workstream or trigger cannot be justified to a reviewer."""
    for deck_id in ("product", "enterprise"):
        for row in get_scope_library().deck(deck_id).rows:
            assert row.workstreams, f"{row.id} has no workstreams"
            assert row.triggers, f"{row.id} has no triggers"
            assert row.evidence, f"{row.id} has no evidence requests"
            assert row.dd_master_ref, f"{row.id} has no DD_master reference"


def test_every_row_yields_client_facing_text() -> None:
    for deck_id in ("product", "enterprise"):
        for row in get_scope_library().deck(deck_id).rows:
            assert row.title.strip()
            assert row.body_lines
            assert all(line.strip() for line in row.body_lines)


def test_core_rows_are_always_in_scope() -> None:
    """DD_master G3: the 80% core is never dropped to make room for tailoring."""
    enterprise = {r.id: r for r in get_scope_library().deck("enterprise").rows}
    for row_id in ("EN-01", "EN-03", "EN-04", "EN-05"):  # apps, org, infra, financials
        assert enterprise[row_id].always_in_scope, f"{row_id} must always be in scope"


def test_row_rejects_mixed_product_and_enterprise_shape() -> None:
    with pytest.raises(ValueError, match="not both and not neither"):
        ScopeRow(
            sn=1,
            id="BAD-01",
            objective="an objective",
            scope_of_work="some work",
            focus_area="a focus area",
            considerations=["a consideration"],
        )


def test_row_rejects_missing_both_shapes() -> None:
    with pytest.raises(ValueError, match="not both and not neither"):
        ScopeRow(sn=1, id="BAD-02")


def test_deck_rejects_duplicate_row_ids() -> None:
    row = {"sn": 1, "id": "DUP", "objective": "o", "scope_of_work": "s"}
    with pytest.raises(ValueError, match="duplicate row ids"):
        ScopeDeck.model_validate(
            {
                "deck": "product",
                "deck_title": "t",
                "deck_subtitle": "s",
                "library_version": "1.0",
                "source": "x",
                "rows": [row, {**row, "sn": 2}],
            }
        )


# ------------------------------------------- scope boundaries (Rishi, 2026-09-14)
#
# Four instructions that narrow or widen what the generated scope of work says. Each is
# content in YAML, but each is also a promise to a client about what is being sold, so
# each is pinned here rather than left to the prompt.


def test_no_deck_offers_to_review_or_build_a_cost_model() -> None:
    """We review the budgeting process. We do not review or build a cost model.

    Asserted across every client-facing string in both decks, not only the financials
    rows, because the phrase could reappear anywhere - the separation and infrastructure
    rows are the likely places.
    """
    library = get_scope_library()
    for deck_id in ("product", "enterprise"):
        for row in library.deck(deck_id).rows:
            client_text = " ".join(
                [row.objective or "", row.scope_of_work or "", row.focus_area or ""]
                + list(row.considerations or [])
            ).lower()
            assert "cost model" not in client_text, f"{row.id} offers a cost model"


def test_no_deck_offers_to_scope_a_transitional_service_agreement() -> None:
    """On a separation we review contracts and their expiry, not TSAs.

    The two rules that injected TSA language (M4, C7) have been dormant since the intake
    field was removed on 2026-08-30, so nothing generated carries it - but the decks are
    the place it would come back, and this is cheaper than finding it in a client deck.
    """
    library = get_scope_library()
    for deck_id in ("product", "enterprise"):
        for row in library.deck(deck_id).rows:
            client_text = " ".join(
                [row.objective or "", row.scope_of_work or "", row.focus_area or ""]
                + list(row.considerations or [])
            ).lower()
            assert "tsa" not in client_text.split(), f"{row.id} names a TSA"
            assert "transitional service" not in client_text, f"{row.id} scopes a TSA"
            assert "transition service" not in client_text, f"{row.id} scopes a TSA"


def test_the_contracts_row_asks_for_expiry_and_change_of_control() -> None:
    """What replaced the TSA framing: what is committed, when it ends, does it transfer."""
    row = next(r for r in get_scope_library().deck("enterprise").rows if r.id == "EN-09")
    text = " ".join(row.considerations or []).lower()
    assert "expiry" in text
    assert "change-of-control" in text or "change of control" in text
    evidence = " ".join(row.evidence).lower()
    assert "notice period" in evidence


def test_both_org_rows_ask_for_the_in_house_versus_outsourced_mix() -> None:
    """Rishi, 2026-09-14: how much is in-house, what skills, how many vendors.

    On both decks, because the question is the same one whichever archetype the deal is:
    a 12-person IT function with four managed-service providers behind it is a different
    asset from a 40-person one doing the same work, and neither an organisation chart nor
    a headcount number distinguishes them.
    """
    library = get_scope_library()

    enterprise = next(r for r in library.deck("enterprise").rows if r.id == "EN-03")
    ent_text = " ".join(enterprise.considerations or []).lower()
    assert "in-house" in ent_text and "outsourced" in ent_text
    assert "third-party vendors" in ent_text
    assert "role structure" in ent_text
    ent_evidence = " ".join(enterprise.evidence).lower()
    assert "in-house versus outsourced" in ent_evidence

    product = next(r for r in library.deck("product").rows if r.id == "PD-06")
    prod_text = (product.scope_of_work or "").lower()
    assert "skill sets" in prod_text, "the development team's skills must be in scope"
    assert "in-house" in prod_text and "outsourced" in prod_text


def test_the_first_ten_product_objectives_are_still_verbatim_source_text() -> None:
    """The additions must not have disturbed the transcribed KPMG wording.

    The deck's value is that rows 1-10 are quoted exactly from the source. A test that
    only counted rows would not notice an edit to one of them.
    """
    deck = get_scope_library().deck("product")
    by_id = {r.id: r for r in deck.rows}
    assert by_id["PD-01"].objective == (
        "Review product tech stack and architecture for scalability constraints"
    )
    assert by_id["PD-05"].objective == "IT Regulatory aspects"
    assert by_id["PD-09"].objective == "Technology vendors"
    assert by_id["PD-10"].objective == "Tech outages and disclosures"
