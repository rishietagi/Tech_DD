"""The company research brief as a Word document (2026-11-19).

Rishi: every page that produces something should export it. The brief is edited in the
platform first (PUT /research), so this renders the latest version as it stands — edits
included — with its citations as numbered references and the source list at the end.
"""

import io
import re
from datetime import UTC, datetime

from docx import Document
from docx.shared import Pt, RGBColor

from app.schemas.research import BusinessBrief, ResearchPayload

BLUE = RGBColor(0x00, 0x33, 0x8D)
MUTED = RGBColor(0x4A, 0x55, 0x68)

SECTIONS = [
    ("executive_summary", "Executive summary"),
    ("what_they_do", "What they do"),
    ("how_they_make_money", "How they make money"),
    ("customers_and_markets", "Customers and markets"),
    ("sector_context", "The sector"),
    ("competitive_position", "Competitive position"),
    ("technology_profile", "Technology they use"),
    ("implications_for_diligence", "What this means for the diligence"),
]


def docx_filename(deal_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", deal_name.lower()).strip("-") or "engagement"
    return f"{slug}-company-research.docx"


def render(payload: ResearchPayload, *, deal_name: str, company_name: str, version: int) -> bytes:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(10.5)

    title = doc.add_heading(f"Company research — {company_name or 'the target'}", level=0)
    for run in title.runs:
        run.font.color.rgb = BLUE
    meta = doc.add_paragraph(f"{deal_name} · version {version} · exported {datetime.now(UTC):%d %B %Y}")
    meta.runs[0].font.color.rgb = MUTED

    number = {s.id: i + 1 for i, s in enumerate(payload.sources)}

    def cite(ids: list[str]) -> str:
        refs = sorted({number[i] for i in ids if i in number})
        return f" [{', '.join(str(r) for r in refs)}]" if refs else ""

    brief = payload.business_brief or BusinessBrief()
    wrote = False
    for key, label in SECTIONS:
        section = getattr(brief, key)
        if not section.text.strip():
            continue
        wrote = True
        heading = doc.add_heading(label, level=1)
        for run in heading.runs:
            run.font.color.rgb = BLUE
        paragraphs = [p.strip() for p in section.text.split("\n") if p.strip()]
        for i, text in enumerate(paragraphs):
            doc.add_paragraph(text + (cite(section.source_ids) if i == len(paragraphs) - 1 else ""))
    if not wrote and payload.summary.strip():
        doc.add_heading("Summary", level=1)
        doc.add_paragraph(payload.summary.strip())

    if payload.findings:
        heading = doc.add_heading("Findings", level=1)
        for run in heading.runs:
            run.font.color.rgb = BLUE
        for finding in payload.findings:
            p = doc.add_paragraph(style="List Bullet")
            p.add_run(f"{finding.topic}: ").bold = True
            p.add_run(finding.detail + cite(finding.source_ids))

    if payload.sources:
        heading = doc.add_heading("Sources", level=1)
        for run in heading.runs:
            run.font.color.rgb = BLUE
        for source in payload.sources:
            line = f"[{number[source.id]}] {source.title}"
            if source.publisher:
                line += f" — {source.publisher}"
            p = doc.add_paragraph(line)
            p.add_run(f"\n{source.url}").font.color.rgb = MUTED

    if payload.disclaimer:
        note = doc.add_paragraph(payload.disclaimer)
        note.runs[0].italic = True
        note.runs[0].font.color.rgb = MUTED

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
