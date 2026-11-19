"""The findings workbook — one tab's register, or all six together.

Two sheets, deliberately plain so the client team can filter, edit and pass it on:

* **Summary** — each assessment's score and finding counts, then the breakdown under it
  (processes, or the sections of the index).
* **Findings** — one row per finding: ID, assessment, process, diligence area, severity,
  finding, evidence, implication, deal impact, recommended action, and whether the deal
  team edited it.

Edits made in the app are already applied by the time a register reaches here.
"""

import io
import re
from datetime import UTC, datetime

import xlsxwriter

from app.schemas.estate import IMPACT_LABELS
from app.services.findings.registers import INDEX_LABELS, Register

BLUE = "#00338D"
SEVERITY_FILL = {"High": "#F8E1DF", "Medium": "#FBEBD3", "Low": "#ECEEF2"}
FINDINGS_COLUMNS = [
    ("ID", 10),
    ("Assessment", 20),
    ("Process", 18),
    ("Diligence area", 24),
    ("Severity", 10),
    ("Finding", 40),
    ("Evidence", 60),
    ("Implication", 48),
    ("Deal impact", 24),
    ("Recommended action", 52),
    ("Edited", 8),
]


def findings_filename(deal_name: str, key: str | None) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", deal_name.lower()).strip("-") or "engagement"
    tail = re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-") if key else "all"
    return f"{slug}-findings-{tail}.xlsx"


def render(
    registers: list[Register],
    *,
    deal_name: str,
    target_name: str,
    area_titles: dict[str, str],
    title: str,
) -> bytes:
    buffer = io.BytesIO()
    book = xlsxwriter.Workbook(buffer, {"in_memory": True})
    fmt = {
        "title": book.add_format({"bold": True, "font_size": 14, "font_color": BLUE}),
        "meta": book.add_format({"font_color": "#4A5568"}),
        "head": book.add_format(
            {"bold": True, "font_color": "#FFFFFF", "bg_color": BLUE, "valign": "top", "text_wrap": True, "border": 1}
        ),
        "cell": book.add_format({"valign": "top", "text_wrap": True, "border": 1, "border_color": "#D5DAE3"}),
        "num": book.add_format({"valign": "top", "border": 1, "border_color": "#D5DAE3", "num_format": "0"}),
        "section": book.add_format({"bold": True, "font_color": BLUE, "top": 1, "top_color": BLUE}),
        "muted": book.add_format({"font_color": "#8087A0", "italic": True}),
    }
    sev = {
        s: book.add_format({"valign": "top", "border": 1, "border_color": "#D5DAE3", "bold": True, "bg_color": fill})
        for s, fill in SEVERITY_FILL.items()
    }

    # ------------------------------------------------------------------ Summary
    sheet = book.add_worksheet("Summary")
    sheet.set_column(0, 0, 30)
    sheet.set_column(1, 2, 14)
    sheet.set_column(3, 5, 9)
    sheet.set_column(6, 6, 70)
    sheet.write(0, 0, title, fmt["title"])
    sheet.write(1, 0, f"{deal_name}" + (f" · {target_name}" if target_name else ""), fmt["meta"])
    sheet.write(2, 0, f"Exported {datetime.now(UTC):%d %B %Y}. Edits made in the platform are included.", fmt["meta"])
    row = 4
    sheet.write_row(row, 0, ["Assessment", "Score", "Rating", "High", "Medium", "Low", "Summary"], fmt["head"])
    for reg in registers:
        row += 1
        counts = reg.counts()
        sheet.write(row, 0, reg.label, fmt["cell"])
        if reg.index is not None and reg.key != "it_budget":
            sheet.write_number(row, 1, reg.index, fmt["num"])
        else:
            sheet.write(row, 1, "—" if reg.scored else "Not scored", fmt["cell"])
        sheet.write(row, 2, reg.rating, fmt["cell"])
        for col, level in enumerate(("High", "Medium", "Low"), start=3):
            sheet.write_number(row, col, counts[level], fmt["num"])
        sheet.write(row, 6, reg.summary, fmt["cell"])

    for reg in registers:
        if not reg.lines:
            continue
        row += 2
        heading = reg.label + (f" — {INDEX_LABELS[reg.key]}" if INDEX_LABELS.get(reg.key) else "")
        sheet.write(row, 0, heading, fmt["section"])
        row += 1
        score_head = "Variance %" if reg.key == "it_budget" else "Score"
        sheet.write_row(row, 0, ["Item", score_head, "Rating", "", "", "", "Note"], fmt["head"])
        for line in reg.lines:
            row += 1
            sheet.write(row, 0, line.label, fmt["cell"])
            if line.score is None:
                sheet.write(row, 1, "—", fmt["cell"])
            else:
                sheet.write_number(row, 1, line.score, fmt["num"])
            sheet.write(row, 2, line.rating, fmt["cell"])
            sheet.write(row, 6, line.note, fmt["cell"])

    # ------------------------------------------------------------------ Findings
    sheet = book.add_worksheet("Findings")
    for col, (_name, width) in enumerate(FINDINGS_COLUMNS):
        sheet.set_column(col, col, width)
    sheet.write_row(0, 0, [c for c, _ in FINDINGS_COLUMNS], fmt["head"])
    sheet.freeze_panes(1, 0)
    r = 0
    for reg in registers:
        for entry in reg.entries:
            gap = entry.gap
            r += 1
            values = [
                gap.display_id,
                reg.label,
                entry.subject,
                area_titles.get(gap.area, gap.area.replace("_", " ").title()),
                gap.severity,
                gap.headline,
                "\n".join(f"• {line}" for line in gap.evidence),
                gap.implication,
                ", ".join(IMPACT_LABELS.get(i, i) for i in gap.impact),
                gap.action,
                "Yes" if gap.edited else "",
            ]
            for col, value in enumerate(values):
                sheet.write(r, col, value, sev[gap.severity] if col == 4 else fmt["cell"])
    if r == 0:
        sheet.write(1, 0, "No findings yet — score the assessments first.", fmt["muted"])
    else:
        sheet.autofilter(0, 0, r, len(FINDINGS_COLUMNS) - 1)

    book.close()
    return buffer.getvalue()
