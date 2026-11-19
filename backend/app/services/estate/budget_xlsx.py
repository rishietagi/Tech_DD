"""The IT financials sheet — budget and actual technology spend, by line and year.

Written into the IRL workbook and as a standalone template, so the target supplies its own
figures instead of the analyst keying them in (Phase 8, Rishi 2026-11-18). Read back on
upload into the IT budget inputs. The same rules as the inventories: an upload **never
clears a value**, adds what is new, and reports what it changed.

This is the budgeting-process review's input, not a cost model: budget and actual as the
target reports them, nothing estimated (2026-09-14 boundary).
"""

import io
import re
from typing import Any

import xlsxwriter
from openpyxl import load_workbook
from sqlalchemy.orm import Session
from xlsxwriter.workbook import Workbook

from app.core.errors import AppError
from app.schemas.it_budget import BudgetLine, FinancialsImportResult, ItBudgetInputs
from app.services.estate import budget as budget_service
from app.services.estate.library import get_it_budget_config

SHEET = "IT Financials"
SHEET_ALIASES = ("IT Financials Template", "IT Financial", "IT Budget")
KINDS = {"run": "Run", "change": "Change"}
_MAX_ROWS = 200


def write_financials_sheet(workbook: Workbook, inputs: ItBudgetInputs) -> None:
    header = workbook.add_format(
        {"bold": True, "font_color": "#FFFFFF", "bg_color": "#1D3A5F", "text_wrap": True, "valign": "top", "border": 1}
    )
    cell = workbook.add_format({"text_wrap": True, "valign": "top", "border": 1})
    money = workbook.add_format({"num_format": "#,##0", "valign": "top", "border": 1, "bg_color": "#FFF8E1"})
    sheet = workbook.add_worksheet(SHEET)
    sheet.set_column(0, 0, 36)
    sheet.set_column(1, 1, 14)
    sheet.set_column(2, 1 + 2 * len(inputs.years), 15)
    sheet.write(0, 0, "Budget line", header)
    sheet.write_comment(
        0,
        0,
        "One row per line of technology spend. Add rows for lines not listed. Figures in "
        f"{inputs.currency or 'the reporting currency'}{(' ' + inputs.unit) if inputs.unit else ''}.",
        {"x_scale": 2.4, "y_scale": 1.4},
    )
    sheet.write(0, 1, "Run or change", header)
    sheet.write_comment(0, 1, "Run: keeping the lights on. Change: projects and new capability.", {"x_scale": 2.0})
    for i, year in enumerate(inputs.years):
        sheet.write(0, 2 + 2 * i, f"{year} budget", header)
        sheet.write(0, 3 + 2 * i, f"{year} actual", header)
    for row, line in enumerate(inputs.lines, start=1):
        sheet.write(row, 0, line.name, cell)
        sheet.write(row, 1, KINDS[line.kind], cell)
        for i in range(len(inputs.years)):
            for offset, values in ((0, line.budget), (1, line.actual)):
                value = values[i] if i < len(values) else None
                if value is None:
                    sheet.write_blank(row, 2 + 2 * i + offset, None, money)
                else:
                    sheet.write_number(row, 2 + 2 * i + offset, value, money)
    last = len(inputs.lines) + 15
    sheet.data_validation(1, 1, last, 1, {"validate": "list", "source": list(KINDS.values()), "error_type": "warning"})
    for row in range(len(inputs.lines) + 1, last + 1):
        sheet.write_blank(row, 0, None, cell)
        for column in range(2, 2 + 2 * len(inputs.years)):
            sheet.write_blank(row, column, None, money)
    sheet.set_row(0, 30)
    sheet.freeze_panes(1, 1)


def render_template(inputs: ItBudgetInputs) -> bytes:
    buf = io.BytesIO()
    workbook = xlsxwriter.Workbook(buf, {"in_memory": True})
    write_financials_sheet(workbook, inputs)
    workbook.close()
    return buf.getvalue()


def _number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float):
        return float(value)
    cleaned = re.sub(r"[^\d.\-]", "", str(value).replace(",", ""))
    try:
        return float(cleaned) if cleaned not in ("", ".", "-") else None
    except ValueError:
        return None


def read_financials(
    content: bytes,
) -> tuple[str, list[str], list[tuple[str, str, dict[str, tuple[float | None, float | None]]]]] | None:
    """(sheet, years, [(line name, kind, {year: (budget, actual)})]), or None without a sheet."""
    try:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001 - any parse failure is the same user error
        raise AppError(
            code="import_failed",
            message=f"That file could not be read as an Excel workbook ({type(exc).__name__}).",
            status_code=400,
        ) from exc
    try:
        names = {name.strip().lower(): name for name in workbook.sheetnames}
        actual = next((names[n.lower()] for n in (SHEET, *SHEET_ALIASES) if n.lower() in names), None)
        if actual is None:
            return None
        rows = list(workbook[actual].iter_rows(max_row=_MAX_ROWS, values_only=True))
    finally:
        workbook.close()
    if not rows:
        return None
    header = [str(c or "").strip() for c in rows[0]]
    columns: dict[str, dict[str, int]] = {}
    years: list[str] = []
    for position, label in enumerate(header):
        match = re.fullmatch(r"(.+?)\s+(budget|actual)", label, re.I)
        if not match:
            continue
        year = match.group(1).strip()
        if year not in columns:
            columns[year] = {}
            years.append(year)
        columns[year][match.group(2).lower()] = position
    if not years:
        return None
    parsed = []
    for row in rows[1:]:
        if not row or row[0] is None or not str(row[0]).strip():
            continue
        kind_text = str(row[1] or "").strip().lower() if len(row) > 1 else ""
        kind = "change" if kind_text.startswith("change") else "run"
        figures: dict[str, tuple[float | None, float | None]] = {}
        for year, cols in columns.items():
            budget = _number(row[cols["budget"]]) if "budget" in cols and cols["budget"] < len(row) else None
            actual_v = _number(row[cols["actual"]]) if "actual" in cols and cols["actual"] < len(row) else None
            figures[year] = (budget, actual_v)
        parsed.append((str(row[0]).strip(), kind, figures))
    return actual, years, parsed


def import_financials(db: Session, engagement_id: str, content: bytes) -> FinancialsImportResult | None:
    """Merge the sheet into the IT budget inputs. Returns None when there is no sheet."""
    found = read_financials(content)
    if found is None:
        return None
    sheet, years, parsed = found
    read = budget_service.get_budget(db, engagement_id)
    inputs = read.inputs.model_copy(deep=True)
    result = FinancialsImportResult(sheet=sheet)

    for year in years:
        if year not in inputs.years:
            if len(inputs.years) >= 10:
                result.warnings.append(f"{year}: the review period already covers 10 years; column ignored.")
                continue
            inputs.years.append(year)
            for line in inputs.lines:
                line.budget.append(None)
                line.actual.append(None)
            result.years_added += 1

    by_name = {line.name.strip().lower(): line for line in inputs.lines}
    for name, kind, figures in parsed:
        existing = by_name.get(name.lower())
        if existing is not None:
            line = existing
        else:
            line = BudgetLine(
                id=_next_id(inputs),
                name=name,
                kind="change" if kind == "change" else "run",
                budget=[None] * len(inputs.years),
                actual=[None] * len(inputs.years),
            )
            inputs.lines.append(line)
            by_name[name.lower()] = line
            result.lines_added += 1
        for year, (budget, actual) in figures.items():
            if year not in inputs.years:
                continue
            i = inputs.years.index(year)
            for values, value in ((line.budget, budget), (line.actual, actual)):
                if value is None:
                    continue  # a blank cell never clears a figure
                if values[i] is None:
                    result.filled += 1
                elif values[i] != value:
                    result.updated += 1
                else:
                    continue
                values[i] = value

    budget_service.save_budget(db, engagement_id, inputs)
    get_it_budget_config()  # validated on save; keeps the import honest about the content
    changed = result.filled + result.updated
    result.note = (
        f"{changed} figure{'s' if changed != 1 else ''} taken from the {sheet} sheet."
        if changed
        else f"The {sheet} sheet carried no new figures."
    )
    return result


def _next_id(inputs: ItBudgetInputs) -> str:
    used = {line.id for line in inputs.lines}
    n = len(used) + 1
    while f"L{n:02d}" in used:
        n += 1
    return f"L{n:02d}"
