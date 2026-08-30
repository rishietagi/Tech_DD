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
    deck = get_scope_library().deck("product")
    assert len(deck.rows) == 10
    assert [r.sn for r in deck.rows] == list(range(1, 11))


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
