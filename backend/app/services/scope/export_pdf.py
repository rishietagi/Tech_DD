"""PDF export of a generated scope — the client-facing document.

Deliberately narrower than `export.py`. The Markdown export is the *internal* artefact
and carries the whole audit trail: every signal that fired, every rule in the
provenance list. This one is what goes to a client, so the internal reasoning layer
(signals, rule provenance) is omitted. What remains is the document a reader is meant
to act on: what is in scope, at what depth, in what order, at what cost, by whom, and
— just as load-bearing — what is excluded.

Deterministic and offline: everything is read off the stored payload, nothing is
recomputed and no network call is made. Two renders of one payload are identical.

House style follows `frontend/src/styles/tokens.css` so the PDF and the screen are
recognisably the same document.
"""

import io
import re
from datetime import date
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.scope import ScopedRow, ScopeOfWorkPayloadV2

# --- house palette, from frontend/src/styles/tokens.css -----------------------------
KPMG_BLUE = colors.HexColor("#00338D")
KPMG_BLUE_DARK = colors.HexColor("#002566")
KPMG_BLUE_LIGHT = colors.HexColor("#0091DA")
TEXT = colors.HexColor("#0A0E1A")
MUTED = colors.HexColor("#4A5568")
MUTED_2 = colors.HexColor("#8087A0")
LINE = colors.HexColor("#DDE3ED")
PAPER_2 = colors.HexColor("#F4F6FA")

_DECK_LABEL = {
    "product": "Product Tech DD",
    "enterprise": "Enterprise IT DD",
    "blended": "Blended",
}

# Tier 0 rows are out of scope. They are NOT dropped: a scope that silently omits what
# it considered is less useful than one that says "looked at, deliberately not opened".
# Their `out_of_scope_note` still carries that, without a coloured tier badge.

_LOGO = Path(__file__).resolve().parents[4] / "assets" / "kpmg-logo-blue.png"

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


def _escape(text: str) -> str:
    """ReportLab's Paragraph parses a mini-HTML dialect, so raw & < > must be escaped.

    Without this a target whose name contains "R&D" or a stack string containing "<T>"
    raises mid-render, which would take out the whole export.
    """
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()["Normal"]

    def mk(**kw: Any) -> ParagraphStyle:
        return ParagraphStyle(parent=base, **kw)

    return {
        "cover_title": mk(
            name="cover_title", fontName="Helvetica-Bold", fontSize=30, leading=36,
            textColor=KPMG_BLUE, spaceAfter=6,
        ),
        "cover_sub": mk(
            name="cover_sub", fontName="Helvetica", fontSize=13, leading=18,
            textColor=MUTED, spaceAfter=2,
        ),
        "cover_deal": mk(
            name="cover_deal", fontName="Helvetica-Bold", fontSize=15, leading=20,
            textColor=TEXT, spaceAfter=4,
        ),
        "eyebrow": mk(
            name="eyebrow", fontName="Helvetica-Bold", fontSize=8.5, leading=12,
            textColor=KPMG_BLUE, spaceAfter=3,
        ),
        "h1": mk(
            name="h1", fontName="Helvetica-Bold", fontSize=16, leading=21,
            textColor=KPMG_BLUE, spaceBefore=2, spaceAfter=8,
        ),
        "h2": mk(
            name="h2", fontName="Helvetica-Bold", fontSize=12, leading=16,
            textColor=KPMG_BLUE_DARK, spaceBefore=10, spaceAfter=5,
        ),
        "row_title": mk(
            name="row_title", fontName="Helvetica-Bold", fontSize=11, leading=15,
            textColor=TEXT, spaceAfter=1,
        ),
        "body": mk(
            name="body", fontName="Helvetica", fontSize=9.5, leading=14,
            textColor=TEXT, alignment=TA_LEFT, spaceAfter=4,
        ),
        "muted": mk(
            name="muted", fontName="Helvetica", fontSize=8.5, leading=12,
            textColor=MUTED, spaceAfter=3,
        ),
        "italic": mk(
            name="italic", fontName="Helvetica-Oblique", fontSize=8.5, leading=12,
            textColor=MUTED, spaceAfter=3,
        ),
        "label": mk(
            name="label", fontName="Helvetica-Bold", fontSize=8.5, leading=12,
            textColor=MUTED, spaceBefore=3, spaceAfter=2,
        ),
    }


def _bullets(items: list[str], st: dict[str, ParagraphStyle], style: str = "body") -> ListFlowable:
    # A positive bulletOffsetY lifts the glyph above the baseline, which left the dots
    # floating level with the ascenders. A small negative value seats them on the
    # text; the size is set relative to the body copy so both stay in proportion.
    return ListFlowable(
        [ListItem(Paragraph(_escape(i), st[style]), leftIndent=10) for i in items],
        bulletType="bullet",
        start="•",
        bulletFontSize=7,
        bulletOffsetY=-1.5,
        leftIndent=12,
        bulletColor=KPMG_BLUE_LIGHT,
        spaceAfter=6,
    )


def _row_block(row: ScopedRow, st: dict[str, ParagraphStyle]) -> list[Any]:
    """One scope row. Kept together so a heading never strands at a page foot.

    No tier badge and no tier reason (Rishi, 2026-08-31): depth is an internal decision
    and the client-facing document states the work, not the engine's grading of it. The
    tier still governs which rows open and how deep — it is simply not shown. The
    Markdown export keeps both, since that is the internal artefact.

    """
    parts: list[Any] = [
        Paragraph(f"{row.sn:02d}.&nbsp;&nbsp;{_escape(row.title)}", st["row_title"])
    ]
    parts.extend(Paragraph(_escape(line.text), st["body"]) for line in row.lines)

    if row.adjustments:
        parts.append(_bullets(row.adjustments, st, "muted"))

    if row.edited_by_human:
        note = "Edited by hand"
        if row.original_tier is not None and row.original_tier != row.tier:
            note += f" — the engine had this at Tier {row.original_tier}"
        if row.override_reason:
            note += f". {row.override_reason}"
        parts.append(Paragraph(_escape(note), st["italic"]))

    if row.evidence_requests:
        parts.append(Paragraph("EVIDENCE REQUESTED", st["label"]))
        parts.append(_bullets(row.evidence_requests, st, "muted"))

    if row.out_of_scope_note:
        parts.append(Paragraph(_escape(row.out_of_scope_note), st["italic"]))

    parts.append(Spacer(1, 5 * mm))
    return [KeepTogether(parts)]


def _cover(
    scope: ScopeOfWorkPayloadV2,
    st: dict[str, ParagraphStyle],
    deal_name: str | None,
    version: int | None,
    content_w: float,
) -> list[Any]:
    out: list[Any] = [Spacer(1, 18 * mm)]

    if _LOGO.exists():
        out.append(Image(str(_LOGO), width=38 * mm, height=38 * mm * 332 / 751))
        out.append(Spacer(1, 16 * mm))

    out.append(Paragraph("SCOPE OF WORK", st["eyebrow"]))
    out.append(Paragraph(_escape(scope.deck_title), st["cover_title"]))
    out.append(Paragraph(_escape(scope.deck_subtitle), st["cover_sub"]))
    out.append(Spacer(1, 12 * mm))

    if deal_name:
        out.append(Paragraph(_escape(deal_name), st["cover_deal"]))

    c = scope.classification
    meta = [
        ["Classification", _DECK_LABEL.get(c.dd_type.value, c.dd_type.value)],
        ["Enterprise / Product mix", f"{c.dd_mix} / 100"],
        ["Confidence", c.confidence.capitalize()],
        ["Areas in scope", str(sum(1 for r in scope.rows if r.tier > 0))],
        ["Date", date.today().strftime("%d %B %Y")],
    ]
    if version is not None:
        meta.append(["Version", str(version)])

    t = Table(meta, colWidths=[46 * mm, content_w - 46 * mm])
    t.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("TEXTCOLOR", (0, 0), (0, -1), MUTED),
            ("TEXTCOLOR", (1, 0), (1, -1), TEXT),
            ("LINEBELOW", (0, 0), (-1, -2), 0.4, LINE),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    out.append(Spacer(1, 4 * mm))
    out.append(t)
    out.append(PageBreak())
    return out


def _decorate(canvas: Any, _doc: Any, deal_name: str | None, footer: str) -> None:
    """Page furniture. The cover (page 1) is left clean.

    `_doc` is unused but required by ReportLab's onPage callback signature.
    """
    canvas.saveState()
    page = canvas.getPageNumber()

    if page == 1:
        canvas.setFillColor(KPMG_BLUE)
        canvas.rect(0, PAGE_H - 6 * mm, PAGE_W, 6 * mm, stroke=0, fill=1)
    else:
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, PAGE_H - MARGIN + 6 * mm, PAGE_W - MARGIN, PAGE_H - MARGIN + 6 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED_2)
        if deal_name:
            canvas.drawString(MARGIN, PAGE_H - MARGIN + 8.5 * mm, deal_name)
        canvas.drawRightString(
            PAGE_W - MARGIN, PAGE_H - MARGIN + 8.5 * mm, "Scope of Work"
        )
        canvas.setFont("Helvetica", 7)
        canvas.drawString(MARGIN, MARGIN - 8 * mm, footer)
        canvas.drawRightString(PAGE_W - MARGIN, MARGIN - 8 * mm, str(page))

    canvas.restoreState()


def render_pdf(
    scope: ScopeOfWorkPayloadV2,
    deal_name: str | None = None,
    version: int | None = None,
) -> bytes:
    """The client-facing scope as a PDF, returned as bytes."""
    st = _styles()
    buf = io.BytesIO()
    content_w = PAGE_W - 2 * MARGIN

    footer = f"Library v{scope.library_version} · rules v{scope.rules_version}"
    if version is not None:
        footer = f"Version {version} · {footer}"

    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=f"{deal_name + ' — ' if deal_name else ''}{scope.deck_title}",
        author="KPMG Tech Diligence Tool",
        subject=scope.deck_subtitle,
    )
    frame = Frame(MARGIN, MARGIN, content_w, PAGE_H - 2 * MARGIN, id="body")
    doc.addPageTemplates([
        PageTemplate(
            id="all",
            frames=[frame],
            onPage=lambda c, d: _decorate(c, d, deal_name, footer),
        )
    ])

    story: list[Any] = []
    story.extend(_cover(scope, st, deal_name, version, content_w))

    # --- engagement -----------------------------------------------------------------
    story.append(Paragraph("Engagement", st["h1"]))
    story.append(Paragraph(_escape(scope.engagement_summary), st["body"]))
    story.append(Spacer(1, 3 * mm))

    if scope.objectives:
        story.append(Paragraph("Objectives", st["h2"]))
        story.append(_bullets(scope.objectives, st))

    # --- scope rows -----------------------------------------------------------------
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Scope of work", st["h1"]))

    product = [r for r in scope.rows if r.deck == "product"]
    enterprise = [r for r in scope.rows if r.deck == "enterprise"]
    is_blended = bool(product) and bool(enterprise)

    for rows, heading in (
        (product, "Product due diligence"),
        (enterprise, "Enterprise IT due diligence"),
    ):
        if not rows:
            continue
        if is_blended:
            story.append(Paragraph(heading, st["h2"]))
        for row in rows:
            story.extend(_row_block(row, st))

    # --- sequencing -----------------------------------------------------------------
    if scope.sequencing:
        story.append(Paragraph("Sequencing", st["h1"]))
        data = [["Phase", "Weeks", "Focus"]]
        for phase in scope.sequencing:
            focus = _escape(phase.focus)
            if phase.output:
                # The handoff between passes is the point of the plan, so it travels
                # with the phase rather than being dropped from the export.
                focus += f'<br/><br/><font color="#0091DA"><b>Output:</b> {_escape(phase.output)}</font>'
            data.append([
                Paragraph(f"<b>{_escape(phase.name)}</b>", st["muted"]),
                Paragraph(_escape(phase.weeks), st["muted"]),
                Paragraph(focus, st["muted"]),
            ])
        t = Table(data, colWidths=[38 * mm, 22 * mm, content_w - 60 * mm], repeatRows=1)
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), KPMG_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAPER_2]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(t)
        story.append(Spacer(1, 6 * mm))

    # --- cost -----------------------------------------------------------------------
    story.append(Paragraph("Cost estimation", st["h1"]))
    story.append(Paragraph(_escape(scope.cost_plan.approach), st["body"]))
    if scope.cost_plan.lines:
        data = [["Type", "Line", "Basis"]]
        for line in scope.cost_plan.lines:
            data.append([
                Paragraph("One-time" if line.category == "one_time" else "Recurring", st["muted"]),
                Paragraph(_escape(line.label), st["muted"]),
                Paragraph(_escape(line.basis), st["muted"]),
            ])
        t = Table(data, colWidths=[24 * mm, 56 * mm, content_w - 80 * mm], repeatRows=1)
        t.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), KPMG_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PAPER_2]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ])
        )
        story.append(t)
        story.append(Spacer(1, 4 * mm))
    if scope.cost_plan.assumptions_register:
        story.append(Paragraph("Assumptions register", st["h2"]))
        story.append(_bullets(scope.cost_plan.assumptions_register, st, "muted"))

    # --- team -----------------------------------------------------------------------
    team = scope.team_shape
    if team.core_team or team.specialists:
        story.append(Paragraph("Team", st["h1"]))
        if team.core_team:
            story.append(_bullets(team.core_team, st))
        if team.specialists:
            story.append(Paragraph("Specialists required", st["h2"]))
            story.append(_bullets(team.specialists, st, "muted"))
        if team.note:
            story.append(Paragraph(_escape(team.note), st["italic"]))

    # --- notes ----------------------------------------------------------------------
    notes = [n for n in scope.notes if n.get("text")]
    if notes:
        story.append(Paragraph("Notes", st["h1"]))
        for note in notes:
            story.append(
                Paragraph(f"<b>{_escape(note['label'])}</b> — {_escape(note['text'])}", st["body"])
            )

    # --- risks ----------------------------------------------------------------------
    if scope.diligence_risks:
        story.append(Paragraph("Risks to the diligence itself", st["h1"]))
        story.append(_bullets(scope.diligence_risks, st))

    # --- exclusions -----------------------------------------------------------------
    # Never dropped from the client document. DD_master G4: a scope that does not say
    # what it excludes is not a scope.
    if scope.exclusions:
        story.append(Paragraph("Exclusions", st["h1"]))
        story.append(
            Paragraph("A scope that does not say what it excludes is not a scope.", st["italic"])
        )
        story.append(
            _bullets(
                [f"{e.subject} — {e.reason}" for e in scope.exclusions],
                st,
            )
        )

    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(_escape(f"Generated by {scope.generator}. {footer}"), st["italic"]))

    doc.build(story)
    return buf.getvalue()


def render_pdf_from_payload(
    payload: dict[str, Any],
    deal_name: str | None = None,
    version: int | None = None,
) -> bytes:
    """Render a stored payload. Only schema v2 is exportable."""
    if payload.get("schema_version") != 2:
        raise ValueError("Only schema v2 scopes can be exported to PDF")
    return render_pdf(ScopeOfWorkPayloadV2.model_validate(payload), deal_name, version)


def pdf_filename(deal_name: str, version: int) -> str:
    """`project-redline-scope-v2.pdf`.

    A deal name that slugs to nothing (punctuation only) falls back to a bare
    `scope-v{n}.pdf` rather than the doubled `scope-scope-v{n}.pdf`.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", deal_name.lower()).strip("-")
    return f"{slug}-scope-v{version}.pdf" if slug else f"scope-v{version}.pdf"
