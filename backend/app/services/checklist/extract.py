"""Read a little text out of a client's document, for the scanner to reason over.

Deliberately shallow. The scanner's job is to decide *which request a file answers* and
*whether it looks complete* — not to read the document properly. A few hundred
characters of the top of a spreadsheet or the first paragraphs of a policy is enough to
tell a licence register from an org chart, and cheap enough to do across a whole drive.

Three rules this module keeps:

1. **Read-only, always.** `scanner.py` promises never to modify or move client files.
   Nothing here opens a file for writing.
2. **Never raise on a bad file.** A corrupt, password-protected or half-uploaded
   document is a normal thing to find on a client drive. Extraction failure degrades to
   "no excerpt" and the scanner falls back to the filename, which is what it had before
   this module existed.
3. **Cap what comes back.** A 40,000-row spreadsheet must not blow up the prompt. Every
   path through here returns at most `MAX_EXCERPT_CHARS`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Enough to identify a document, not enough to summarise it. Raising this raises the
# prompt cost on every file of every scan.
MAX_EXCERPT_CHARS = 600

# Spreadsheets: read the top-left corner of the first sheets only. A register's identity
# is in its headers and first rows, and the rest is volume.
MAX_SHEETS = 3
MAX_ROWS = 12
MAX_COLS = 8

# Documents: the title and opening paragraphs carry the type.
MAX_PARAGRAPHS = 15

# Anything larger is skipped rather than parsed. A file this size on a diligence drive is
# a data extract, and opening it costs more than the identification is worth.
MAX_FILE_BYTES = 25 * 1024 * 1024

TEXT_SUFFIXES = {".txt", ".md", ".csv"}
EXCEL_SUFFIXES = {".xlsx", ".xlsm"}
WORD_SUFFIXES = {".docx"}
# Known-but-unreadable: identified by name, no text extracted. Listing them explicitly
# keeps "we chose not to read this" distinct from "we failed to read this".
OPAQUE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ppt", ".pptx", ".doc", ".xls", ".zip"}


@dataclass
class ExtractedFile:
    """One file on the drive, as the scanner sees it."""

    path: Path
    # Path relative to the drive root, e.g. "01-IT-Department/IT-Policy-Index.docx".
    relative_path: str
    name: str
    # The immediate containing folder — the strong hint for function matching.
    folder: str
    suffix: str
    size_bytes: int
    excerpt: str = ""
    # Set when extraction was attempted and failed. Kept so a drive full of unreadable
    # files is visible rather than looking like a drive full of empty ones.
    extract_error: str = ""

    # Tokens from the filename and folder, for the deterministic pre-match.
    tokens: set[str] = field(default_factory=set)


def _truncate(text: str) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= MAX_EXCERPT_CHARS:
        return cleaned
    return cleaned[:MAX_EXCERPT_CHARS].rstrip() + "…"


def _from_excel(path: Path) -> str:
    from openpyxl import load_workbook

    # read_only + data_only: never evaluate formulas, never hold the whole book in memory.
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        parts: list[str] = []
        for sheet in book.worksheets[:MAX_SHEETS]:
            parts.append(f"[sheet: {sheet.title}]")
            for row in sheet.iter_rows(max_row=MAX_ROWS, max_col=MAX_COLS, values_only=True):
                cells = [str(c).strip() for c in row if c is not None and str(c).strip()]
                if cells:
                    parts.append(" | ".join(cells))
            if sum(len(p) for p in parts) > MAX_EXCERPT_CHARS:
                break
        return "\n".join(parts)
    finally:
        book.close()


def _from_word(path: Path) -> str:
    import docx

    document = docx.Document(str(path))
    parts: list[str] = []
    for paragraph in document.paragraphs[:MAX_PARAGRAPHS]:
        text = paragraph.text.strip()
        if text:
            parts.append(text)
        if sum(len(p) for p in parts) > MAX_EXCERPT_CHARS:
            break
    # A policy document is often mostly tables, with the paragraphs nearly empty.
    if not parts:
        for table in document.tables[:2]:
            for row in table.rows[:MAX_ROWS]:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))
            if parts:
                break
    return "\n".join(parts)


def _from_text(path: Path) -> str:
    # errors="replace" rather than a guessed encoding: this is identification, not
    # ingestion, and a mangled character costs nothing here.
    return path.read_text(encoding="utf-8", errors="replace")[: MAX_EXCERPT_CHARS * 2]


def _recover_as_text(path: Path) -> str:
    """Last resort for a file whose extension does not match its contents.

    Returns an excerpt only if the bytes look like text. The printable-ratio check is
    what stops a genuinely binary file (a real .xlsx that failed to parse for some other
    reason) being handed to the model as mojibake.
    """
    try:
        raw = path.read_bytes()[: MAX_EXCERPT_CHARS * 4]
    except OSError:
        return ""
    if not raw:
        return ""
    decoded = raw.decode("utf-8", errors="replace")
    printable = sum(1 for c in decoded if c.isprintable() or c in "\r\n\t")
    if printable / len(decoded) < 0.9:
        return ""
    return _truncate(decoded)


def extract_excerpt(path: Path) -> tuple[str, str]:
    """Return `(excerpt, error)` for one file. Never raises.

    An empty excerpt with an empty error means the file type is deliberately not read
    (an image, a PDF) — the filename is the only signal and that is expected, not a
    failure.
    """
    suffix = path.suffix.lower()
    if suffix in OPAQUE_SUFFIXES:
        return "", ""

    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return "", "file too large to parse"
        if suffix in EXCEL_SUFFIXES:
            return _truncate(_from_excel(path)), ""
        if suffix in WORD_SUFFIXES:
            return _truncate(_from_word(path)), ""
        if suffix in TEXT_SUFFIXES:
            return _truncate(_from_text(path)), ""
    except Exception as exc:  # noqa: BLE001 - a bad client file must not stop the scan
        # A file whose extension lies about its format is ordinary on a client drive:
        # someone renames a CSV to .xlsx, or exports "Word" that is really RTF or plain
        # text. Before giving up, try reading it as text — if it turns out to be readable
        # prose we get the excerpt anyway, and if it is binary the guard below rejects it.
        recovered = _recover_as_text(path)
        if recovered:
            return recovered, ""
        logger.warning("Could not read %s (%s: %s)", path.name, type(exc).__name__, exc)
        return "", f"{type(exc).__name__}: {exc}"

    return "", ""
