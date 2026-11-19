"""The inventory sheets — written into the IRL workbook and the standalone templates, and
read back from whatever the target returns.

**The ID column is visible**, unlike the IRL's hidden Request ID. The target needs it:
a data domain names its system of record as `A03`, and a platform lists the applications it
hosts. It is also what an upload matches on, so an edited name still lands on the right
row. A row with no ID is a new item.

**Guidance rides on header comments, not on a guidance row.** A second header-like row is
the first thing a client deletes, and an importer that has to skip "the row of hints" breaks
the moment they do.

Select fields get an in-cell dropdown sourced from a hidden `Lists` sheet. Excel caps an
inline list at 255 characters, which the category list already exceeds.
"""

import io
from typing import Any

import xlsxwriter
from openpyxl import load_workbook
from xlsxwriter.workbook import Workbook
from xlsxwriter.worksheet import Worksheet

from app.core.errors import AppError
from app.models.estate import InventoryItem
from app.schemas.estate import INVENTORY_KINDS, InventoryKind, KindDef, ProcessRef
from app.services.estate.library import get_inventory_definition

ID_HEADER = "ID"
LISTS_SHEET = "Lists"
_MAX_ROWS = 2_000
_EXTRA_BLANK_ROWS = 30  # rows that carry dropdowns beyond the pre-filled ones

_ID_HEADERS = {"id", "ref", "reference", "app id", "application id"}


def _display(value: Any, field_type: str, processes: dict[str, str]) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        if field_type == "process_list":
            return ", ".join(processes.get(v, v) for v in value)
        return ", ".join(str(v) for v in value)
    return str(value)


def _note(kdef_field_type: str, options: list[str], note: str, processes: list[ProcessRef]) -> str:
    parts = [note] if note else []
    if kdef_field_type == "multi_select":
        parts.append("Any of: " + "; ".join(options) + ". Separate with commas.")
    elif kdef_field_type == "process_list":
        parts.append("Any of: " + "; ".join(p.name for p in processes) + ". Separate with commas.")
    elif kdef_field_type == "app_refs":
        parts.append("IDs from the Application Inventory sheet, e.g. A01, A03.")
    elif kdef_field_type == "date":
        parts.append("A date, e.g. 2027-03-31.")
    return " ".join(parts)


class _Formats:
    def __init__(self, workbook: Workbook) -> None:
        self.header = workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#00338D",
                "valign": "vcenter",
                "text_wrap": True,
                "border": 1,
                "border_color": "#DDE3ED",
            }
        )
        self.id_cell = workbook.add_format({"bold": True, "valign": "top", "border": 1, "border_color": "#DDE3ED"})
        self.cell = workbook.add_format(
            {
                "valign": "top",
                "text_wrap": True,
                "border": 1,
                "border_color": "#DDE3ED",
                "bg_color": "#F4F6FA",
            }
        )


def _write_lists_sheet(workbook: Workbook) -> dict[tuple[str, str], str]:
    """One column per select field across every kind. Returns field → range reference."""
    sheet = workbook.add_worksheet(LISTS_SHEET)
    ranges: dict[tuple[str, str], str] = {}
    column = 0
    for kind, kdef in get_inventory_definition().kinds.items():
        for field in kdef.fields:
            if field.type != "select":
                continue
            sheet.write(0, column, f"{kind}.{field.key}")
            for row, option in enumerate(field.options, start=1):
                sheet.write(row, column, option)
            letter = xlsxwriter.utility.xl_col_to_name(column)
            ranges[(kind, field.key)] = f"='{LISTS_SHEET}'!${letter}$2:${letter}${len(field.options) + 1}"
            column += 1
    sheet.hide()
    return ranges


def _write_kind_sheet(
    workbook: Workbook,
    formats: _Formats,
    kind: InventoryKind,
    kdef: KindDef,
    items: list[InventoryItem],
    processes: list[ProcessRef],
    list_ranges: dict[tuple[str, str], str],
) -> Worksheet:
    sheet = workbook.add_worksheet(kdef.sheet)
    process_names = {p.key: p.name for p in processes}

    sheet.set_column(0, 0, 8)
    sheet.write(0, 0, ID_HEADER, formats.header)
    sheet.write_comment(
        0,
        0,
        f"Leave blank for a new row — an ID ({kdef.ref_prefix}01, {kdef.ref_prefix}02…) "
        "is assigned on upload. Do not change an existing ID.",
        {"x_scale": 2.2, "y_scale": 1.4},
    )
    for column, field in enumerate(kdef.fields, start=1):
        width = 44 if field.type == "long_text" else 30 if field.type in ("multi_select", "process_list") else 22
        sheet.set_column(column, column, width)
        label = field.label + (" *" if field.required else "")
        sheet.write(0, column, label, formats.header)
        note = _note(field.type, field.options, field.template_note, processes)
        if note:
            sheet.write_comment(0, column, note, {"x_scale": 2.6, "y_scale": 1.8})

    for row, item in enumerate(items, start=1):
        sheet.write(row, 0, item.ref, formats.id_cell)
        values = item.fields or {}
        for column, field in enumerate(kdef.fields, start=1):
            sheet.write(row, column, _display(values.get(field.key), field.type, process_names), formats.cell)

    # A checklist inventory (cyber tools) arrives pre-filled with the purposes to answer
    # for, as the request workbooks do. Seeds already recorded are not repeated.
    recorded = {str((i.fields or {}).get("name", "")).strip().lower() for i in items}
    seeds = [name for name in kdef.seed_names if name.lower() not in recorded]
    name_column = 1 + next(i for i, f in enumerate(kdef.fields) if f.key == "name")
    for offset, name in enumerate(seeds, start=len(items) + 1):
        sheet.write(offset, 0, "", formats.id_cell)
        sheet.write(offset, name_column, name, formats.cell)

    last = max(len(items) + len(seeds), 1) + _EXTRA_BLANK_ROWS
    for column, field in enumerate(kdef.fields, start=1):
        source = list_ranges.get((kind, field.key))
        if source:
            sheet.data_validation(
                1,
                column,
                last,
                column,
                {
                    "validate": "list",
                    "source": source,
                    # A warning, not a stop: the importer tolerates the odd unexpected
                    # value and reports it, so blocking the target's typing helps nobody.
                    "error_type": "warning",
                    "error_title": "Not one of the listed values",
                    "error_message": "Pick from the list where you can. Other values are reported back on upload.",
                },
            )
    sheet.set_row(0, 34)
    sheet.freeze_panes(1, 2)
    sheet.autofilter(0, 0, max(len(items), 1), len(kdef.fields))
    return sheet


def write_inventory_sheets(
    workbook: Workbook,
    items: list[InventoryItem],
    processes: list[ProcessRef],
    kinds: tuple[InventoryKind, ...] = INVENTORY_KINDS,
) -> None:
    """Append one sheet per kind, plus the hidden Lists sheet, to an open workbook."""
    definition = get_inventory_definition()
    formats = _Formats(workbook)
    by_kind: dict[str, list[InventoryItem]] = {k: [] for k in kinds}
    for item in items:
        if item.kind in by_kind:
            by_kind[item.kind].append(item)
    pending = [(k, definition.kinds[k]) for k in kinds]
    # Sheets first, Lists last, so the target opens onto content rather than the hidden
    # helper; the ranges are known before any sheet is written.
    list_ranges = _list_ranges()
    for kind, kdef in pending:
        _write_kind_sheet(workbook, formats, kind, kdef, by_kind[kind], processes, list_ranges)
    _write_lists_sheet(workbook)


def _list_ranges() -> dict[tuple[str, str], str]:
    """The same column layout `_write_lists_sheet` produces, computed without writing."""
    ranges: dict[tuple[str, str], str] = {}
    column = 0
    for kind, kdef in get_inventory_definition().kinds.items():
        for field in kdef.fields:
            if field.type != "select":
                continue
            letter = xlsxwriter.utility.xl_col_to_name(column)
            ranges[(kind, field.key)] = f"='{LISTS_SHEET}'!${letter}$2:${letter}${len(field.options) + 1}"
            column += 1
    return ranges


# Inventories that never cross-reference application IDs, so their template stands alone.
STANDALONE_KINDS: tuple[InventoryKind, ...] = ("application", "cyber_tool")


def render_template(kind: InventoryKind, items: list[InventoryItem], processes: list[ProcessRef]) -> bytes:
    """A standalone workbook for one inventory, pre-filled with what is already known.

    A data domain or platform template also carries the Application Inventory sheet, so
    the IDs the target cross-references are in front of them.
    """
    buf = io.BytesIO()
    workbook = xlsxwriter.Workbook(buf, {"in_memory": True})
    kinds: tuple[InventoryKind, ...] = (kind,) if kind in STANDALONE_KINDS else (kind, "application")
    write_inventory_sheets(workbook, items, processes, kinds)
    workbook.close()
    return buf.getvalue()


# ------------------------------------------------------------------------ reading


def _norm(text: Any) -> str:
    return " ".join(str(text or "").replace("*", " ").split()).strip().lower()


def read_inventory_sheets(content: bytes) -> dict[InventoryKind, tuple[str, list[tuple[str, dict[str, Any]]]]]:
    """Every inventory sheet found in a workbook, as `(sheet name, [(ref, raw fields)])`.

    Sheets are found by name, case-insensitively; columns by label or key. A workbook with
    no inventory sheet returns an empty dict — the caller decides whether that is an error.
    """
    try:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001 - any parse failure is the same user error
        raise AppError(
            code="import_failed",
            message=f"That file could not be read as an Excel workbook ({type(exc).__name__}).",
            status_code=400,
        ) from exc

    definition = get_inventory_definition()
    found: dict[InventoryKind, tuple[str, list[tuple[str, dict[str, Any]]]]] = {}
    try:
        names = {name.strip().lower(): name for name in workbook.sheetnames}
        for kind, kdef in definition.kinds.items():
            actual = next((names[n.lower()] for n in [kdef.sheet, *kdef.sheet_aliases] if n.lower() in names), None)
            if actual is None:
                continue
            seeds = {n.lower() for n in kdef.seed_names}
            rows = list(workbook[actual].iter_rows(max_row=_MAX_ROWS, values_only=True))
            if not rows:
                continue
            header = [_norm(cell) for cell in rows[0]]
            columns: dict[str, int] = {}
            for field in kdef.fields:
                for position, label in enumerate(header):
                    if label in (_norm(field.label), _norm(field.key)):
                        columns[field.key] = position
                        break
            id_position = next((i for i, label in enumerate(header) if label in _ID_HEADERS), None)
            if "name" not in columns:
                continue
            parsed: list[tuple[str, dict[str, Any]]] = []
            for row in rows[1:]:
                if not row or all(c is None or str(c).strip() == "" for c in row):
                    continue
                ref = ""
                if id_position is not None and id_position < len(row) and row[id_position] is not None:
                    ref = str(row[id_position]).strip()
                raw: dict[str, Any] = {}
                for key, position in columns.items():
                    if position < len(row) and row[position] is not None:
                        value = row[position]
                        # Excel turns a typed date into a datetime; store the date part.
                        if hasattr(value, "date") and callable(value.date):
                            value = value.date().isoformat()
                        text = str(value).strip()
                        if text:
                            raw[key] = text
                # A seeded checklist row nobody filled in is not an item.
                if not ref and set(raw) == {"name"} and str(raw["name"]).lower() in seeds:
                    continue
                parsed.append((ref, raw))
            found[kind] = (actual, parsed)
    finally:
        workbook.close()
    return found
