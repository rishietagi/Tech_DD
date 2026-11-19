"""Consultant edits to the report — an overlay keyed on stable element keys.

Everything the report exports is editable before export (Rishi, 2026-11-18). An edit is
stored against a key, not against a version, so regenerating the report keeps every edit
whose element still exists; an edit whose element has gone (a finding area that no longer
has findings) is inert until it comes back.

Key grammar (dots separate parts; ids never contain dots):

    cover.<codename|title|subtitle|date_label>
    context.<objective|approach|outcome|cutoff|key_areas>
    glossary
    in_scope.<area>.<title|considerations|include>
    limitations.<area>.<title|items|include>
    exec.<area>.<title|risk|note|include>
    exec.<area>.<finding>.<headline|bullets|implication|risk|actions|investment|include>
    supporting.<section>.<title|panel|include>
    supporting.<section>.<block>.<title|text|items|columns|rows|include>
    appendix.<...same as supporting>
"""

from typing import Any

from app.core.errors import AppError
from app.schemas.report import RISK_LEVELS

_TEXT = "text"
_LIST = "list"
_BOOL = "bool"
_ROWS = "rows"
_RISK = "risk"
_GLOSSARY = "glossary"

_FIELDS: dict[str, dict[str, str]] = {
    "cover": {"codename": _TEXT, "title": _TEXT, "subtitle": _TEXT, "date_label": _TEXT},
    "context": {"objective": _TEXT, "approach": _TEXT, "outcome": _TEXT, "cutoff": _TEXT, "key_areas": _LIST},
    "in_scope": {"title": _TEXT, "considerations": _LIST, "include": _BOOL},
    "limitations": {"title": _TEXT, "items": _LIST, "include": _BOOL},
    "exec": {"title": _TEXT, "risk": _RISK, "note": _TEXT, "include": _BOOL},
    "finding": {
        "headline": _TEXT,
        "bullets": _LIST,
        "implication": _TEXT,
        "risk": _RISK,
        "actions": _LIST,
        "investment": _TEXT,
        "include": _BOOL,
    },
    "section": {"title": _TEXT, "panel": _TEXT, "include": _BOOL},
    "block": {"title": _TEXT, "text": _TEXT, "items": _LIST, "columns": _LIST, "rows": _ROWS, "include": _BOOL},
}


class EditError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(code="invalid_report_edit", message=message, status_code=422)


def _check(kind: str, value: Any) -> Any:
    if kind == _TEXT:
        if not isinstance(value, str):
            raise EditError("This element takes text.")
        return value.strip()
    if kind == _LIST:
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise EditError("This element takes a list of strings.")
        return [v.strip() for v in value if v.strip()]
    if kind == _BOOL:
        if not isinstance(value, bool):
            raise EditError("This element takes true or false.")
        return value
    if kind == _RISK:
        if value not in RISK_LEVELS:
            raise EditError(f"Risk must be one of {list(RISK_LEVELS)}.")
        return value
    if kind == _ROWS:
        if not isinstance(value, list) or not all(
            isinstance(r, list) and all(isinstance(c, str) for c in r) for r in value
        ):
            raise EditError("A table takes a list of rows, each a list of strings.")
        return value
    if kind == _GLOSSARY:
        if not isinstance(value, list) or not all(
            isinstance(g, dict) and isinstance(g.get("term"), str) and isinstance(g.get("expansion"), str)
            for g in value
        ):
            raise EditError("The glossary takes a list of {term, expansion}.")
        return [{"term": g["term"].strip(), "expansion": g["expansion"].strip()} for g in value if g["term"].strip()]
    raise EditError("Unknown element type.")


def _locate(data: dict[str, Any], key: str) -> tuple[dict[str, Any], str, str] | None:
    """The dict an edit lands in, the field, and its type — or None if absent."""
    parts = key.split(".")
    head = parts[0]
    if head == "glossary" and len(parts) == 1:
        return data, "glossary", _GLOSSARY
    if head in ("cover", "context") and len(parts) == 2:
        kind = _FIELDS[head].get(parts[1])
        return (data[head], parts[1], kind) if kind else None
    if head == "exec" and len(parts) == 4:
        area = next((x for x in data["executive"] if x["area_id"] == parts[1]), None)
        finding = next((f for f in (area or {}).get("findings", []) if f["key"] == parts[2]), None)
        kind = _FIELDS["finding"].get(parts[3])
        return (finding, parts[3], kind) if finding is not None and kind else None
    if head in ("in_scope", "limitations", "exec") and len(parts) == 3:
        collection = data["executive"] if head == "exec" else data[head]
        target = next((x for x in collection if x["area_id"] == parts[1]), None)
        kind = _FIELDS[head].get(parts[2])
        return (target, parts[2], kind) if target is not None and kind else None
    if head in ("supporting", "appendix") and len(parts) in (3, 4):
        section = next((s for s in data[head] if s["id"] == parts[1]), None)
        if section is None:
            return None
        if len(parts) == 3:
            kind = _FIELDS["section"].get(parts[2])
            return (section, parts[2], kind) if kind else None
        block = next((b for b in section["blocks"] if b["id"] == parts[2]), None)
        kind = _FIELDS["block"].get(parts[3])
        return (block, parts[3], kind) if block is not None and kind else None
    return None


def validate(data: dict[str, Any], key: str, value: Any) -> Any:
    """Check an edit against the current report before storing it."""
    located = _locate(data, key)
    if located is None:
        raise EditError(f"{key!r} is not an element of this report.")
    _, _, kind = located
    return _check(kind, value)


def apply(data: dict[str, Any], edits: dict[str, Any]) -> list[str]:
    """Apply stored edits in place; returns the keys that landed."""
    applied = []
    for key, value in edits.items():
        located = _locate(data, key)
        if located is None:
            continue  # the element no longer exists; the edit waits for it
        target, field, kind = located
        try:
            target[field] = _check(kind, value)
        except EditError:
            continue
        applied.append(key)
    return sorted(applied)
