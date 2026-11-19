"""The inventories — applications, data domains and platforms — the target supplies.

Two ways in, one set of rules:

* **the screen** — strict. A value that is not one of a field's options is a 422 with the
  field named, because the analyst is right there to fix it.
* **an uploaded workbook** — tolerant. A value that does not fit is skipped and reported
  as a warning, and the rest of the row still lands. A target's spreadsheet always has
  something in it nobody anticipated, and rejecting forty rows over one cell would push
  the analyst back to retyping.

Uploads **never clear** a value: a blank cell means "not supplied", not "delete what the
analyst typed" — the same rule as the IRL response import.
"""

import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.models.estate import EstateAnswer, InventoryItem
from app.schemas.estate import (
    INVENTORY_KINDS,
    FieldDef,
    InventoryImportResult,
    InventoryImportSummary,
    InventoryItemRead,
    InventoryKind,
    InventoryRead,
    KindDef,
    ProcessRef,
)
from app.services.assess.library import get_process_registry
from app.services.engagements import get_engagement
from app.services.estate.library import get_inventory_definition

_SPLIT = re.compile(r"\s*[,;\n]\s*")


class FieldValueError(ValueError):
    """One value did not fit its field. Carries the field key for the error envelope."""

    def __init__(self, key: str, message: str) -> None:
        super().__init__(message)
        self.key = key


# ------------------------------------------------------------------------ reference data


def process_refs() -> list[ProcessRef]:
    """The business processes an application can claim to support — defined ones only.

    Taken from the Assess registry rather than restated, so an application and the
    business tab always mean the same thing by "Order to Cash".
    """
    return [
        ProcessRef(key=p.key, name=p.name, short_name=p.short_name)
        for p in get_process_registry().processes
        if p.defined
    ]


def _process_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for p in process_refs():
        for alias in (p.key, p.name, p.short_name):
            lookup[alias.strip().lower()] = p.key
    return lookup


def kind_def(kind: InventoryKind) -> KindDef:
    return get_inventory_definition().kinds[kind]


# ------------------------------------------------------------------------ coercion


def _as_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(v).strip() for v in raw if str(v).strip()]
    return [part for part in _SPLIT.split(str(raw).strip()) if part]


def _match_option(value: str, options: list[str]) -> str | None:
    folded = value.strip().lower()
    return next((o for o in options if o.lower() == folded), None)


def coerce_value(field: FieldDef, raw: Any, app_refs: set[str]) -> tuple[Any, list[str]]:
    """Normalise one value to its stored form.

    Returns `(value, rejected)`. `rejected` lists the parts that did not fit; the caller
    decides whether that is an error (the screen) or a warning (an upload). A multi-value
    field keeps the parts that did fit.
    """
    if field.type in ("text", "long_text", "date"):
        return ("" if raw is None else str(raw).strip()), []

    if field.type == "number":
        text = "" if raw is None else str(raw).strip()
        if not text:
            return "", []
        cleaned = re.sub(r"[^\d.\-]", "", text.replace(",", ""))
        try:
            float(cleaned)
        except ValueError:
            return "", [text]
        return text, []

    if field.type == "select":
        text = "" if raw is None else str(raw).strip()
        if not text:
            return "", []
        matched = _match_option(text, field.options)
        return (matched, []) if matched is not None else ("", [text])

    parts = _as_list(raw)
    kept: list[str] = []
    rejected: list[str] = []
    if field.type == "multi_select":
        for part in parts:
            matched = _match_option(part, field.options)
            (kept if matched else rejected).append(matched or part)
    elif field.type == "process_list":
        lookup = _process_lookup()
        for part in parts:
            key = lookup.get(part.lower())
            (kept if key else rejected).append(key or part)
    elif field.type == "app_refs":
        upper = {r.upper(): r for r in app_refs}
        for part in parts:
            ref = upper.get(part.upper())
            (kept if ref else rejected).append(ref or part)
    # De-duplicate, keeping first-seen order.
    return list(dict.fromkeys(kept)), rejected


def _application_refs(db: Session, engagement_id: str) -> set[str]:
    return set(
        db.scalars(
            select(InventoryItem.ref).where(
                InventoryItem.engagement_id == engagement_id,
                InventoryItem.kind == "application",
            )
        )
    )


def clean_fields_strict(db: Session, engagement_id: str, kind: InventoryKind, raw: dict[str, Any]) -> dict[str, Any]:
    """Validate fields from the screen. Unknown keys and unfitting values are errors."""
    fields = {f.key: f for f in kind_def(kind).fields}
    refs = _application_refs(db, engagement_id)
    cleaned: dict[str, Any] = {}
    errors: list[dict[str, str]] = []
    for key, value in raw.items():
        field = fields.get(key)
        if field is None:
            errors.append({"field": key, "message": "Not a field of this inventory."})
            continue
        stored, rejected = coerce_value(field, value, refs)
        if rejected:
            allowed = (
                ", ".join(field.options)
                if field.options
                else (
                    "an application ID from the inventory"
                    if field.type == "app_refs"
                    else "one of the business processes"
                )
            )
            errors.append(
                {
                    "field": key,
                    "message": f"{', '.join(rejected)} is not allowed. Use {allowed}.",
                }
            )
            continue
        cleaned[key] = stored
    if errors:
        raise AppError(
            code="validation_error",
            message="Some values do not fit their fields.",
            status_code=422,
            field_errors=errors,
        )
    return cleaned


# ------------------------------------------------------------------------ reads


def item_to_read(item: InventoryItem) -> InventoryItemRead:
    return InventoryItemRead(
        id=item.id,
        kind=item.kind,
        ref=item.ref,
        fields=dict(item.fields or {}),
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _ref_sort_key(ref: str) -> tuple[str, int, str]:
    match = re.match(r"([A-Za-z]+)(\d+)$", ref)
    return (match.group(1), int(match.group(2)), "") if match else (ref, 0, ref)


def items_of(db: Session, engagement_id: str, kind: InventoryKind | None = None) -> list[InventoryItem]:
    query = select(InventoryItem).where(InventoryItem.engagement_id == engagement_id)
    if kind is not None:
        query = query.where(InventoryItem.kind == kind)
    rows = list(db.scalars(query))
    order: dict[str, int] = {k: i for i, k in enumerate(INVENTORY_KINDS)}
    return sorted(rows, key=lambda r: (order.get(r.kind, 9), _ref_sort_key(r.ref)))


def list_inventory(db: Session, engagement_id: str, kind: InventoryKind | None = None) -> InventoryRead:
    get_engagement(db, engagement_id)
    definition = get_inventory_definition()
    return InventoryRead(
        engagement_id=engagement_id,
        definitions=definition.kinds,
        processes=process_refs(),
        items=[item_to_read(i) for i in items_of(db, engagement_id, kind)],
    )


def get_item(db: Session, engagement_id: str, item_id: str) -> InventoryItem:
    item = db.get(InventoryItem, item_id)
    if item is None or item.engagement_id != engagement_id:
        raise NotFoundError(f"Inventory item {item_id} not found")
    return item


# ------------------------------------------------------------------------ writes


def next_ref(db: Session, engagement_id: str, kind: InventoryKind) -> str:
    prefix = kind_def(kind).ref_prefix
    numbers = [
        int(m.group(1))
        for ref in db.scalars(
            select(InventoryItem.ref).where(InventoryItem.engagement_id == engagement_id, InventoryItem.kind == kind)
        )
        if (m := re.fullmatch(rf"{re.escape(prefix)}(\d+)", ref))
    ]
    return f"{prefix}{(max(numbers) + 1) if numbers else 1:02d}"


def create_item(db: Session, engagement_id: str, kind: InventoryKind, raw: dict[str, Any]) -> InventoryItem:
    get_engagement(db, engagement_id)
    fields = clean_fields_strict(db, engagement_id, kind, raw)
    if not str(fields.get("name", "")).strip():
        raise AppError(
            code="validation_error",
            message="A name is required.",
            status_code=422,
            field_errors=[{"field": "name", "message": "A name is required."}],
        )
    item = InventoryItem(
        engagement_id=engagement_id,
        kind=kind,
        ref=next_ref(db, engagement_id, kind),
        fields=fields,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def update_item(db: Session, engagement_id: str, item_id: str, raw: dict[str, Any]) -> InventoryItem:
    item = get_item(db, engagement_id, item_id)
    fields = clean_fields_strict(db, engagement_id, item.kind, raw)  # type: ignore[arg-type]
    if "name" in fields and not str(fields["name"]).strip():
        raise AppError(
            code="validation_error",
            message="A name is required.",
            status_code=422,
            field_errors=[{"field": "name", "message": "A name is required."}],
        )
    # A fresh dict, not an in-place update: SQLAlchemy does not see mutation inside a
    # JSON column (the `flag_modified` trap recorded in PROJECT_LOG).
    item.fields = {**(item.fields or {}), **fields}
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, engagement_id: str, item_id: str) -> None:
    """Remove an item and the analyst's answers about it.

    Other items that reference it (a data domain's system of record, a platform's hosted
    applications) keep the ref: scoring ignores refs that no longer resolve, and silently
    rewriting the target's own cross-references would hide that something was removed.
    """
    item = get_item(db, engagement_id, item_id)
    for answer in db.scalars(
        select(EstateAnswer).where(EstateAnswer.engagement_id == engagement_id, EstateAnswer.subject_id == item.id)
    ):
        db.delete(answer)
    db.delete(item)
    db.commit()


# ------------------------------------------------------------------------ upload


def apply_rows(
    db: Session,
    engagement_id: str,
    kind: InventoryKind,
    rows: list[tuple[str, dict[str, Any]]],
    sheet: str,
) -> InventoryImportSummary:
    """Create or update items from uploaded rows. Does not commit.

    Each row is `(ref, raw_fields)`. Matching is by ref first, then by exact name — the
    same order of trust as the IRL import: an id is exact, a name is a fallback, and
    nothing fuzzy is ever attempted.
    """
    kdef = kind_def(kind)
    fields_by_key = {f.key: f for f in kdef.fields}
    summary = InventoryImportSummary(kind=kind, sheet=sheet)

    existing = items_of(db, engagement_id, kind)
    by_ref = {i.ref.upper(): i for i in existing}
    by_name = {str((i.fields or {}).get("name", "")).strip().lower(): i for i in existing}
    refs = _application_refs(db, engagement_id)
    prefix = re.escape(kdef.ref_prefix)

    for row_number, (raw_ref, raw) in enumerate(rows, start=2):
        cleaned: dict[str, Any] = {}
        for key, value in raw.items():
            field = fields_by_key.get(key)
            if field is None:
                continue
            stored, rejected = coerce_value(field, value, refs)
            if rejected:
                summary.warnings.append(
                    f"Row {row_number}, {field.label}: '{', '.join(rejected)}' not recognised"
                    + (" and skipped." if stored in ("", []) else "; the rest was kept.")
                )
            if stored not in ("", []):
                cleaned[key] = stored

        ref = raw_ref.strip().upper()
        target = by_ref.get(ref) if ref else None
        name = str(cleaned.get("name", "")).strip()
        if target is None and name:
            target = by_name.get(name.lower())

        if target is not None:
            merged = {**(target.fields or {}), **cleaned}
            if merged == (target.fields or {}):
                summary.unchanged += 1
            else:
                target.fields = merged
                summary.updated += 1
            continue

        if not name:
            if cleaned:
                summary.warnings.append(f"Row {row_number}: no name, so it was not added.")
            continue

        new_ref = ref if re.fullmatch(rf"{prefix}\d+", ref) else ""
        item = InventoryItem(
            engagement_id=engagement_id,
            kind=kind,
            ref=new_ref or "",
            fields=cleaned,
        )
        if not new_ref:
            db.flush()
            item.ref = next_ref(db, engagement_id, kind)
        db.add(item)
        db.flush()
        by_ref[item.ref.upper()] = item
        by_name[name.lower()] = item
        if kind == "application":
            refs.add(item.ref)
        summary.created += 1

    summary.warnings = summary.warnings[:30]
    return summary


def import_workbook(
    db: Session,
    engagement_id: str,
    content: bytes,
    kinds: tuple[InventoryKind, ...] | None = None,
) -> InventoryImportResult:
    """Apply every inventory sheet in an uploaded workbook, applications first.

    Applications go first so a data domain's system of record or a platform's hosted
    applications can name an application added in the same upload.
    """
    from app.services.estate.inventory_xlsx import read_inventory_sheets

    get_engagement(db, engagement_id)
    sheets = read_inventory_sheets(content)
    wanted = kinds or INVENTORY_KINDS
    summaries: list[InventoryImportSummary] = []
    for kind in INVENTORY_KINDS:
        if kind not in wanted or kind not in sheets:
            continue
        sheet, rows = sheets[kind]
        summaries.append(apply_rows(db, engagement_id, kind, rows, sheet))
    db.commit()

    note = ""
    if not summaries:
        expected = ", ".join(get_inventory_definition().kinds[k].sheet for k in wanted)
        note = f"No inventory sheet was found. Expected a sheet named {expected}."
    return InventoryImportResult(summaries=summaries, note=note)
