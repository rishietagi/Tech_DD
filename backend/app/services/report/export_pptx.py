"""The report as a .pptx — the client-facing deliverable. docs/reference/REPORT_STRUCTURE.md.

Built from the edit-overlaid payload, so what the consultant sees is what exports. Every
element with `include: false` is left out. The visual conventions follow the sample:
breadcrumb strip and DRAFT stamp on every content slide, numbered context blocks, tables
that paginate "(1/2)", RAG risk markers with a legend, a blue side panel on supporting
slides, section dividers, and the landscape diagram drawn as native shapes.

Reuses the scope deck's theme and primitives so the two documents look like one firm's.
"""

import io
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from app.schemas.report import Block, ExecutiveRow, ReportPayload, ReportSection
from app.services.scope.export_pptx import THEME, Theme, _blank, _table, _textbox, _write

_ASSETS = Path(__file__).resolve().parents[4] / "assets"
_LOGO_BLUE = _ASSETS / "kpmg-logo-blue.png"
_LOGO_WHITE = _ASSETS / "kpmg-logo-white.png"

RISK_COLOURS = {
    "High": RGBColor(0xC0, 0x39, 0x2B),
    "Medium": RGBColor(0xE0, 0xA1, 0x1B),
    "Low": RGBColor(0x2E, 0x8B, 0x3E),
    "Not assessed": RGBColor(0x80, 0x87, 0xA0),
}
CLASSIFICATION = "Document Classification: KPMG Confidential"
LEGAL = "© KPMG. All rights reserved."
BREADCRUMB = [
    ("context", "Context Setting"),
    ("glossary", "Glossary"),
    ("in_scope", "In Scope Areas"),
    ("limitations", "Data Limitations"),
    ("executive", "Executive Summary"),
    ("supporting", "Supporting Analysis"),
    ("appendix", "Appendix"),
]

# Rough capacity of a content slide, in body lines at ~10pt across the table width.
_LINES_PER_SLIDE = 24
_CHARS_PER_LINE = 95


def _lines(text: str, width_chars: int = _CHARS_PER_LINE) -> int:
    return sum(max(1, -(-len(part) // max(width_chars, 20))) for part in (text or " ").split("\n"))


class Deck:
    def __init__(self, payload: ReportPayload, assets: dict[str, tuple[str, bytes]], theme: Theme = THEME) -> None:
        self.p = payload
        self.assets = assets
        self.t = theme
        self.prs = Presentation()
        self.prs.slide_width = Inches(theme.slide_w)
        self.prs.slide_height = Inches(theme.slide_h)
        self.page = 0
        self.starts: dict[str, int] = {}

    # ------------------------------------------------------------------ frame

    def _slide(self) -> Any:
        self.page += 1
        return _blank(self.prs)

    def _rect(
        self,
        slide: Any,
        left: float,
        top: float,
        width: float,
        height: float,
        fill: RGBColor,
        line: RGBColor | None = None,
        shape: Any = MSO_SHAPE.RECTANGLE,
    ) -> Any:
        box = slide.shapes.add_shape(shape, Inches(left), Inches(top), Inches(width), Inches(height))
        box.fill.solid()
        box.fill.fore_color.rgb = fill
        if line is None:
            box.line.fill.background()
        else:
            box.line.color.rgb = line
            box.line.width = Pt(0.75)
        box.shadow.inherit = False
        return box

    def _text_in(
        self, shape: Any, text: str, size: float, color: RGBColor, bold: bool = False, align: Any = PP_ALIGN.CENTER
    ) -> None:
        frame = shape.text_frame
        frame.word_wrap = True
        frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        frame.margin_left = frame.margin_right = Inches(0.05)
        frame.margin_top = frame.margin_bottom = Inches(0.02)
        para = frame.paragraphs[0]
        para.alignment = align
        run = para.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.name = self.t.font
        run.font.color.rgb = color

    def _content(self, section: str, title: str) -> tuple[Any, float]:
        """Breadcrumb, title, DRAFT stamp and footer. Returns the slide and content top."""
        t = self.t
        slide = self._slide()
        crumb = _textbox(slide, t.margin, 0.22, t.content_w - 1.4, 0.25)
        para = crumb.paragraphs[0]
        for i, (key, label) in enumerate(BREADCRUMB):
            run = para.add_run()
            run.text = ("|  " if i else "") + label + "   "
            run.font.size = Pt(7.5)
            run.font.bold = key == section
            run.font.name = t.font
            run.font.color.rgb = t.blue if key == section else t.muted_2
        head = _textbox(slide, t.margin, 0.45, t.content_w - 1.4, 0.7)
        _write(head, title, size=26, color=t.blue, first=True, theme=t)
        stamp = _textbox(slide, t.slide_w - t.margin - 1.2, 0.3, 1.2, 0.35)
        sp = _write(stamp, "DRAFT", size=13, bold=True, color=t.blue_dark, first=True, theme=t)
        sp.alignment = PP_ALIGN.RIGHT
        self._footer(slide)
        return slide, 1.3

    def _footer(self, slide: Any, light: bool = False) -> None:
        t = self.t
        logo = _LOGO_WHITE if light else _LOGO_BLUE
        if logo.exists():
            slide.shapes.add_picture(str(logo), Inches(t.margin), Inches(t.slide_h - 0.48), height=Inches(0.26))
        legal = _textbox(slide, t.margin + 1.0, t.slide_h - 0.44, 6.0, 0.25)
        _write(legal, LEGAL, size=6.5, color=t.white if light else t.muted_2, first=True, theme=t)
        right = _textbox(slide, t.slide_w - t.margin - 4.0, t.slide_h - 0.44, 4.0, 0.25)
        rp = _write(
            right,
            f"{CLASSIFICATION}   |   {self.page}",
            size=6.5,
            color=t.white if light else t.muted_2,
            first=True,
            theme=t,
        )
        rp.alignment = PP_ALIGN.RIGHT

    def _source(self, slide: Any) -> None:
        t = self.t
        frame = _textbox(slide, t.margin, t.slide_h - 0.72, 5.0, 0.2)
        _write(frame, self.p.source_line, size=7, italic=True, color=t.muted, first=True, theme=t)

    # ------------------------------------------------------------------ slides

    def cover(self) -> None:
        t = self.t
        slide = self._slide()
        self._rect(slide, 0, 0, t.slide_w, t.slide_h, t.blue_dark)
        self._rect(slide, t.slide_w * 0.58, 0, t.slide_w * 0.42, t.slide_h, t.blue)
        if _LOGO_WHITE.exists():
            slide.shapes.add_picture(str(_LOGO_WHITE), Inches(t.margin + 0.3), Inches(0.7), height=Inches(0.55))
        frame = _textbox(slide, t.margin + 0.3, 2.0, 7.2, 2.4)
        _write(frame, self.p.cover.codename, size=48, color=t.white, first=True, theme=t)
        frame2 = _textbox(slide, t.margin + 0.3, 4.3, 7.2, 0.9)
        _write(frame2, self.p.cover.title, size=32, color=t.white, first=True, theme=t)
        frame3 = _textbox(slide, t.margin + 0.3, 5.5, 7.2, 1.0)
        _write(frame3, self.p.cover.subtitle, size=16, bold=True, color=t.white, first=True, space_after=10, theme=t)
        _write(frame3, self.p.cover.date_label, size=16, bold=True, color=t.white, theme=t)
        cls = _textbox(slide, t.slide_w - t.margin - 3.5, t.slide_h - 0.5, 3.5, 0.25)
        cp = _write(cls, CLASSIFICATION, size=7, color=t.white, first=True, theme=t)
        cp.alignment = PP_ALIGN.RIGHT

    def toc(self) -> Any:
        slide, top = self._content("", "Table of Contents")
        return slide, top

    def fill_toc(self, slide: Any, top: float) -> None:
        rows = [["#", "Section", "Page"]]
        order = [
            ("context", "Context setting"),
            ("glossary", "Glossary of terms"),
            ("in_scope", "In scope areas"),
            ("limitations", "Data limitations"),
            ("executive", "Executive summary"),
            ("supporting", "Supporting analysis"),
            ("appendix", "Appendix"),
        ]
        n = 0
        for key, label in order:
            if key in self.starts:
                n += 1
                rows.append([str(n), label, f"{self.starts[key]:02d}"])
        _table(slide, rows, [0.6, 6.0, 1.0], top + 0.2, self.t)

    def context(self) -> None:
        t, c = self.t, self.p.context
        self.starts["context"] = self.page + 1
        slide, top = self._content("context", "Setting the context")
        blocks = [("01", "OBJECTIVE", c.objective), ("02", "APPROACH", c.approach), ("03", "OUTCOME", c.outcome)]
        y = top
        for number, label, text in blocks:
            circle = self._rect(slide, t.margin, y, 0.78, 0.78, t.blue_dark, shape=MSO_SHAPE.OVAL)
            self._text_in(circle, number, 20, t.white, bold=True)
            lab = _textbox(slide, t.margin + 0.88, y + 0.24, 1.6, 0.3)
            _write(lab, label, size=11, bold=True, color=t.blue_dark, first=True, theme=t)
            box = self._rect(slide, t.margin + 2.55, y + 0.02, t.content_w - 2.55, 0.74, t.white, line=t.line)
            self._text_in(box, text, 10.5, t.text, align=PP_ALIGN.LEFT)
            y += 0.95
        areas = c.key_areas[:12]
        if areas:
            left = t.margin
            label = self._rect(slide, left, y + 0.1, 1.6, 2.0, t.blue_dark)
            self._text_in(label, "Key Assessment Areas", 12, t.white, bold=True)
            cols = 4
            w = (t.content_w - 1.75) / cols - 0.12
            for i, area in enumerate(areas):
                r, col = divmod(i, cols)
                box = self._rect(
                    slide, left + 1.75 + col * (w + 0.12), y + 0.1 + r * 0.7, w, 0.58, t.paper_2, line=t.line
                )
                self._text_in(box, area, 9.5, t.text)
        note = _textbox(slide, t.margin, t.slide_h - 0.85, t.content_w, 0.25)
        _write(note, f"* {c.cutoff}", size=8.5, color=t.text, first=True, theme=t)

    def glossary(self) -> None:
        entries = self.p.glossary
        if not entries:
            return
        t = self.t
        self.starts["glossary"] = self.page + 1
        per_slide = 44
        for start in range(0, len(entries), per_slide):
            chunk = entries[start : start + per_slide]
            slide, top = self._content("glossary", "Glossary of terms")
            half = -(-len(chunk) // 2)
            for col, part in enumerate((chunk[:half], chunk[half:])):
                frame = _textbox(slide, t.margin + col * (t.content_w / 2), top, t.content_w / 2 - 0.2, 5.4)
                for i, g in enumerate(part):
                    para = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
                    term = para.add_run()
                    term.text = f"{g.term}\t"
                    term.font.size = Pt(10)
                    term.font.bold = True
                    term.font.name = t.font
                    term.font.color.rgb = t.blue_dark
                    exp = para.add_run()
                    exp.text = g.expansion
                    exp.font.size = Pt(10)
                    exp.font.name = t.font
                    exp.font.color.rgb = t.text
                    para.space_after = Pt(2)

    def _paged_table(
        self,
        section: str,
        title: str,
        header: list[str],
        rows: list[list[str]],
        widths: list[float],
        weight: Callable[[list[str]], int],
        after: Callable[[Any], None] | None = None,
    ) -> None:
        pages: list[list[list[str]]] = []
        current: list[list[str]] = []
        used = 0
        for row in rows:
            need = weight(row)
            if current and used + need > _LINES_PER_SLIDE:
                pages.append(current)
                current, used = [], 0
            current.append(row)
            used += need
        if current:
            pages.append(current)
        for i, page_rows in enumerate(pages):
            suffix = f" ({i + 1}/{len(pages)})" if len(pages) > 1 else ""
            slide, top = self._content(section, title + suffix)
            _table(slide, [header, *page_rows], widths, top, self.t)
            if after:
                after(slide)

    def _bullets(self, items: list[str]) -> str:
        return "\n".join(f"•  {i}" for i in items)

    def in_scope(self) -> None:
        areas = [a for a in self.p.in_scope if a.include]
        if not areas:
            return
        self.starts["in_scope"] = self.page + 1
        rows = [[a.title, self._bullets(a.considerations)] for a in areas]
        self._paged_table(
            "in_scope",
            "In scope areas",
            ["Focus Area", "Key considerations"],
            rows,
            [3.0, self.t.content_w - 3.0],
            lambda r: _lines(r[1], 110) + 1,
        )

    def limitations(self) -> None:
        rows_in = [lim for lim in self.p.limitations if lim.include and lim.items]
        if not rows_in:
            return
        self.starts["limitations"] = self.page + 1
        rows = [[lim.title, self._bullets(lim.items)] for lim in rows_in]
        self._paged_table(
            "limitations",
            "Data Limitations",
            ["Focus Area", "Data Limitations"],
            rows,
            [3.0, self.t.content_w - 3.0],
            lambda r: _lines(r[1], 110) + 1,
        )

    def executive(self) -> None:
        rows_in: list[ExecutiveRow] = [r for r in self.p.executive if r.include]
        if not rows_in:
            return
        t = self.t
        self.starts["executive"] = self.page + 1
        widths = [0.55, 1.55, 5.0, 0.85, 2.85, 1.3]

        def findings_text(r: ExecutiveRow) -> str:
            text = self._bullets(r.findings)
            return text + (f"\n•  Implication: {r.implication}" if r.implication else "")

        pages: list[list[ExecutiveRow]] = []
        current: list[ExecutiveRow] = []
        used = 0
        for r in rows_in:
            # Measured on the rendered deck: ~90 characters a line in the findings column,
            # ~42 in the actions column, ~30 lines between header and footnote.
            need = max(_lines(findings_text(r), 90), _lines(self._bullets(r.actions), 42)) + 1
            if current and used + need > 30:
                pages.append(current)
                current, used = [], 0
            current.append(r)
            used += need
        if current:
            pages.append(current)

        for i, page_rows in enumerate(pages):
            suffix = f" ({i + 1}/{len(pages)})" if len(pages) > 1 else ""
            slide, top = self._content("executive", self.p.executive_title + suffix)
            # Legend, as in the sample: Low / Medium / High.
            for j, level in enumerate(("Low", "Medium", "High")):
                x = t.slide_w - t.margin - 3.0 + j * 1.0
                self._rect(slide, x, top - 0.25, 0.9, 0.08, RISK_COLOURS[level])
                lf = _textbox(slide, x, top - 0.15, 0.9, 0.2)
                _write(lf, level, size=7, color=t.muted, first=True, theme=t)
            body = [
                [
                    str(r.sn),
                    r.title,
                    findings_text(r),
                    r.risk if r.risk == "Not assessed" else "●",
                    self._bullets(r.actions) or "—",
                    r.investment,
                ]
                for r in page_rows
            ]
            table = _table(
                slide,
                [
                    [
                        "S.no.",
                        "Diligence Area",
                        "Key Findings",
                        "Risk level",
                        "Recommended actions",
                        "Investment impact",
                    ],
                    *body,
                ],
                widths,
                top + 0.1,
                t,
            )
            for r_index, r in enumerate(page_rows, start=1):
                cell = table.cell(r_index, 3)
                para = cell.text_frame.paragraphs[0]
                para.alignment = PP_ALIGN.CENTER
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                for run in para.runs:
                    run.font.color.rgb = RISK_COLOURS.get(r.risk, t.muted)
                    run.font.size = Pt(26 if r.risk != "Not assessed" else 8)
                # One paragraph per finding, then the implication in italics with its
                # label bold — as the sample sets it. Written fresh rather than styled
                # after the fact: the table helper writes the cell as one run.
                self._findings_cell(table.cell(r_index, 2), r)
            note = _textbox(slide, t.margin, t.slide_h - 0.72, t.content_w, 0.2)
            _write(
                note,
                "*The estimated investment is to be completed by the engagement team; actual costs "
                "may vary with the final technical configuration and other factors.",
                size=7,
                italic=True,
                color=t.muted,
                first=True,
                theme=t,
            )

    def _findings_cell(self, cell: Any, row: ExecutiveRow) -> None:
        t = self.t
        frame = cell.text_frame
        for paragraph in list(frame.paragraphs)[1:]:
            paragraph._p.getparent().remove(paragraph._p)
        first = frame.paragraphs[0]
        for run in list(first.runs):
            run._r.getparent().remove(run._r)
        lines = [(f, False) for f in row.findings] + ([(row.implication, True)] if row.implication else [])
        for i, (text, implication) in enumerate(lines):
            para = first if i == 0 else frame.add_paragraph()
            para.space_after = Pt(2)
            bullet = para.add_run()
            bullet.text = "•  "
            if implication:
                label = para.add_run()
                label.text = "Implication: "
                label.font.bold = True
                label.font.italic = True
            body = para.add_run()
            body.text = text
            body.font.italic = implication
            for run in para.runs:
                run.font.size = Pt(8.5)
                run.font.name = t.font
                run.font.color.rgb = t.text

    def divider(self, number: str, title: str) -> None:
        t = self.t
        slide = self._slide()
        self._rect(slide, 0, 0, t.slide_w, t.slide_h, t.paper_2)
        box = self._rect(slide, 1.4, 1.2, 7.6, 5.0, t.blue)
        frame = box.text_frame
        frame.word_wrap = True
        frame.vertical_anchor = MSO_ANCHOR.TOP
        frame.margin_left = Inches(0.5)
        frame.margin_top = Inches(0.5)
        _write(frame, number, size=40, bold=True, color=t.white, first=True, space_after=18, theme=t)
        _write(frame, title, size=48, color=t.white, theme=t)
        self._footer(slide)

    # ------------------------------------------------------------------ supporting

    def _panel(self, slide: Any, top: float, text: str) -> None:
        t = self.t
        box = self._rect(slide, t.margin, top, 2.6, t.slide_h - top - 0.85, t.blue)
        frame = box.text_frame
        frame.word_wrap = True
        frame.vertical_anchor = MSO_ANCHOR.TOP
        frame.margin_left = frame.margin_right = Inches(0.14)
        frame.margin_top = Inches(0.14)
        para = _write(frame, text, size=10, color=t.white, first=True, theme=t)
        para.alignment = PP_ALIGN.LEFT

    def section(self, key: str, section: ReportSection, with_panel: bool) -> None:
        t = self.t
        blocks = [b for b in section.blocks if b.include]
        left = t.margin + (2.8 if with_panel else 0)
        width = t.slide_w - t.margin - left
        slide, top = self._content(key, section.title)
        if with_panel and section.panel:
            self._panel(slide, top, section.panel)
        self._source(slide)
        y = top
        bottom = t.slide_h - 0.85
        for block in blocks:
            need = self._block_height(block, width)
            if y > top and y + min(need, bottom - top) > bottom:
                slide, top = self._content(key, section.title)
                if with_panel and section.panel:
                    self._panel(slide, top, section.panel)
                self._source(slide)
                y = top
            y = self._draw_block(slide, block, left, y, width, bottom)

    def _block_height(self, block: Block, width: float) -> float:
        chars = int(width * 13)
        if block.kind == "paragraph":
            return 0.3 + _lines(block.text, chars) * 0.2
        if block.kind == "bullets":
            return 0.3 + sum(_lines(i, chars) for i in block.items) * 0.2
        if block.kind == "table":
            return 0.35 + 0.3 * (1 + len(block.rows))
        return 4.8

    def _heading(self, slide: Any, text: str, left: float, y: float, width: float) -> float:
        if not text:
            return y
        frame = _textbox(slide, left, y, width, 0.28)
        _write(frame, text, size=11, bold=True, color=self.t.blue_dark, first=True, theme=self.t)
        return y + 0.3

    def _draw_block(self, slide: Any, block: Block, left: float, y: float, width: float, bottom: float) -> float:
        t = self.t
        y = self._heading(slide, block.title, left, y, width)
        if block.kind == "paragraph":
            frame = _textbox(slide, left, y, width, bottom - y)
            _write(frame, block.text, size=10, first=True, theme=t)
            return y + _lines(block.text, int(width * 13)) * 0.2 + 0.15
        if block.kind == "bullets":
            frame = _textbox(slide, left, y, width, bottom - y)
            for i, item in enumerate(block.items):
                _write(frame, item, size=10, bullet=True, first=i == 0, space_after=3, theme=t)
            return y + sum(_lines(i, int(width * 13)) for i in block.items) * 0.2 + 0.15
        if block.kind == "table":
            cols = max(len(block.columns), 1)
            widths = _widths(block.columns, block.rows, width)
            rows = block.rows[:18]
            _table_at(slide, [block.columns, *rows], widths, left, y, t)
            if len(block.rows) > 18:
                frame = _textbox(slide, left, bottom - 0.25, width, 0.2)
                _write(
                    frame,
                    f"{len(block.rows) - 18} further rows in the appendix.",
                    size=8,
                    italic=True,
                    color=t.muted,
                    first=True,
                    theme=t,
                )
            return y + 0.3 * (1 + len(rows)) + 0.25 + 0 * cols
        if block.kind == "diagram" and block.diagram:
            return self._diagram(slide, block.diagram, left, y, width, bottom)
        if block.kind == "image" and block.asset_id in self.assets:
            _, data = self.assets[block.asset_id]
            picture = slide.shapes.add_picture(io.BytesIO(data), Inches(left), Inches(y), width=Inches(width))
            max_h = Inches(bottom - y - 0.3)
            if picture.height > max_h:
                ratio = max_h / picture.height
                picture.height = int(picture.height * ratio)
                picture.width = int(picture.width * ratio)
            if block.text:
                cap = _textbox(slide, left, bottom - 0.25, width, 0.2)
                _write(cap, block.text, size=8, italic=True, color=t.muted, first=True, theme=t)
            return bottom
        return y

    def _diagram(self, slide: Any, model: dict[str, Any], left: float, y: float, width: float, bottom: float) -> float:
        """Applications panel left, infrastructure panel right — the sample's layout."""
        t = self.t
        app_w = width * 0.6
        infra_l = left + app_w + 0.15
        infra_w = width - app_w - 0.15
        height = bottom - y - 0.1

        head = self._rect(slide, left, y, app_w, 0.3, t.blue_dark)
        self._text_in(head, "IT Applications", 10, t.white, bold=True)
        cy = y + 0.38
        erp = model.get("erp")
        if erp:
            band = self._rect(slide, left, cy, app_w, 0.26, t.paper_2, line=t.line)
            self._text_in(band, f"Functions managed in ERP: {erp['name']}", 8.5, t.blue_dark, bold=True)
            cy += 0.32
            functions = erp.get("functions") or ["—"]
            fw = (app_w - 0.1 * (len(functions) - 1)) / len(functions)
            for i, fn in enumerate(functions):
                box = self._rect(slide, left + i * (fw + 0.1), cy, fw, 0.42, t.white, line=t.blue)
                self._text_in(box, fn, 8, t.text, bold=True)
            cy += 0.52
        groups = model.get("app_groups", [])
        rows_available = max(1, int((y + height - cy) / 0.36))
        for group in groups[:rows_available]:
            label = self._rect(slide, left, cy, 1.55, 0.3, t.blue)
            self._text_in(label, group["label"], 7.5, t.white, bold=True)
            items = group["items"][:4]
            iw = (app_w - 1.65 - 0.06 * max(len(items) - 1, 0)) / max(len(items), 1)
            for i, item in enumerate(items):
                box = self._rect(slide, left + 1.65 + i * (iw + 0.06), cy, iw, 0.3, t.paper_2, line=t.line)
                self._text_in(
                    box,
                    item["name"] + (f" (+{len(group['items']) - 4})" if i == 3 and len(group["items"]) > 4 else ""),
                    7.5,
                    t.text,
                )
            cy += 0.36

        head = self._rect(slide, infra_l, y, infra_w, 0.3, t.blue_dark)
        self._text_in(head, "IT Infrastructure", 10, t.white, bold=True)
        cy = y + 0.38
        backup = model.get("backup") or []
        if backup:
            label = self._rect(slide, infra_l, cy, 1.2, 0.3 * min(len(backup), 3), t.paper_2, line=t.line)
            self._text_in(label, "Backup and restoration", 7.5, t.blue_dark, bold=True)
            for i, name in enumerate(backup[:3]):
                box = self._rect(slide, infra_l + 1.3, cy + i * 0.3, infra_w - 1.3, 0.27, t.white, line=t.line)
                self._text_in(box, name, 7.5, t.text)
            cy += 0.3 * min(len(backup), 3) + 0.15
        for group in model.get("infra_groups", []):
            if cy > bottom - 0.6:
                break
            band = self._rect(slide, infra_l, cy, infra_w, 0.26, t.paper_2, line=t.line)
            self._text_in(band, group["label"], 8, t.blue_dark, bold=True)
            cy += 0.3
            for item in group["items"]:
                if cy > bottom - 0.4:
                    break
                hosts = ", ".join(item.get("hosts") or [])
                box = self._rect(slide, infra_l, cy, infra_w, 0.34 if hosts else 0.27, t.white, line=t.line)
                self._text_in(
                    box, item["name"] + (f"  —  hosts {hosts}" if hosts else ""), 7.5, t.text, align=PP_ALIGN.LEFT
                )
                cy += 0.38 if hosts else 0.31
        return bottom

    # ------------------------------------------------------------------ build

    def build(self) -> bytes:
        self.cover()
        toc_slide, toc_top = self.toc()
        self.context()
        self.glossary()
        self.in_scope()
        self.limitations()
        self.executive()
        supporting = [s for s in self.p.supporting if s.include]
        if supporting:
            self.divider("05", "Supporting Analysis")
            self.starts["supporting"] = self.page + 1
            for s in supporting:
                self.section("supporting", s, with_panel=True)
        appendix = [s for s in self.p.appendix if s.include]
        if appendix:
            self.divider("06", "Appendix")
            self.starts["appendix"] = self.page + 1
            for s in appendix:
                self.section("appendix", s, with_panel=False)
        self.fill_toc(toc_slide, toc_top)
        buf = io.BytesIO()
        self.prs.save(buf)
        return buf.getvalue()


# Inches per character at the 8pt table font, measured on the rendered deck.
_CHAR_IN = 0.075


def _widths(columns: list[str], rows: list[list[str]], total: float) -> list[float]:
    """Column widths: never narrower than the longest word, the rest by content length.

    Pure proportion squeezed short columns ("#", "Users") until PowerPoint wrapped them a
    character per line (found rendering the Kiln report, 2026-11-18).
    """
    n = max(len(columns), 1)
    floors, weights = [], []
    for i in range(n):
        cells = [columns[i] if i < len(columns) else ""] + [r[i] if i < len(r) else "" for r in rows[:30]]
        longest_word = max((len(w) for c in cells for w in c.split()), default=1)
        floors.append(longest_word * _CHAR_IN + 0.2)
        weights.append(max(4, min(60, max(len(c) for c in cells))))
    spare = total - sum(floors)
    if spare <= 0:
        scale = total / sum(floors)
        return [f * scale for f in floors]
    return [f + spare * w / sum(weights) for f, w in zip(floors, weights, strict=True)]


def _table_at(slide: Any, rows: list[list[str]], widths: list[float], left: float, top: float, theme: Theme) -> None:
    """`_table` at an arbitrary left edge (the scope helper anchors at the margin)."""
    table = _table(slide, rows, widths, top, theme)
    frame = table._graphic_frame if hasattr(table, "_graphic_frame") else None
    if frame is not None:
        frame.left = Inches(left)
    else:
        # python-pptx: the shape is the table's parent graphic frame.
        shape = slide.shapes[-1]
        shape.left = Inches(left)
    for r in range(len(rows)):
        for c in range(len(widths)):
            for para in table.cell(r, c).text_frame.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(8 if r else 8.5)


def render(payload: ReportPayload, assets: dict[str, tuple[str, bytes]]) -> bytes:
    return Deck(payload, assets).build()


def filename(deal_name: str, version: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", deal_name.lower()).strip("-")
    return f"{slug}-it-dd-report-v{version}.pptx" if slug else f"it-dd-report-v{version}.pptx"
