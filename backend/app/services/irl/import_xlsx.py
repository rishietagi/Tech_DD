"""Read responses back out of a completed IRL workbook.

The target fills in the Response column and sends the file back. This scrapes that column
and writes each answer against the right request.

**Matching is by request id first.** `export_xlsx.py` writes a hidden `Request ID` column,
so a row matches exactly even after the client has reordered rows, hidden some, or reworded
a question. Falling back to matching on question text alone would break the moment anyone
edited a cell, and a response landing against the wrong request is worse than one not
landing at all.

Where the id column is missing — someone rebuilt the sheet by hand, or copied the questions
into their own template — it falls back to **exact normalised question text**. Not fuzzy
matching: a near-miss that silently attaches an answer to the wrong request is exactly the
failure this module must not have. Unmatched rows are reported back to the analyst rather
than dropped in silence.

Reading is strictly non-destructive. A blank Response cell never clears an answer already
in the app: the client leaving a cell empty means "not answered yet", not "delete what you
have". Only non-empty cells write.
"""

import io
import re
from typing import Any

from openpyxl import load_workbook

from app.core.errors import AppError
from app.schemas.irl import ImportResponsesResult, IrlPayload

# Header labels the importer will accept, lower-cased. A client may well rename a column
# heading; these are the variants worth tolerating without guessing.
_ID_HEADERS = {"request id", "id", "question id", "ref", "reference"}
_RESPONSE_HEADERS = {"response", "answer", "reply", "client response", "response / comments"}
_QUESTION_HEADERS = {"question", "request", "information requested", "documents requested"}
# "Type" is written by the exporter but never read back: it is fixed by the seed, and a
# client editing it must not be able to change what a request *is*.

# A workbook larger than this is not an IRL response sheet, and parsing it would tie up a
# worker. The largest real list so far is 45 rows.
_MAX_ROWS = 5_000


class ResponseImportError(AppError):
    """The uploaded file could not be read as an IRL response workbook."""

    def __init__(self, message: str) -> None:
        super().__init__(code="import_failed", message=message, status_code=400)


def _normalise(text: Any) -> str:
    """Collapse whitespace and case so trivial edits still match.

    Deliberately conservative: it fixes wrapped cells and stray spaces, nothing more. It
    does not stem, drop punctuation or approximate — those turn a miss into a wrong hit.
    """
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().lower()


def _cell_at(row: tuple[Any, ...], columns: dict[str, int], key: str) -> str:
    """One cell's text, or empty when the column is absent or the row is short.

    A module-level function rather than a closure inside the row loop: defining it in the
    loop captured `row` late, so every call would have read the *last* row (ruff B023).
    """
    position = columns.get(key)
    if position is None or position >= len(row):
        return ""
    value = row[position]
    return "" if value is None else str(value).strip()


def _find_header_row(rows: list[tuple[Any, ...]]) -> tuple[int, dict[str, int]]:
    """Locate the header row and the columns that matter.

    Scans the first few rows rather than assuming row 1: exported sheets sometimes gain a
    title row when a client saves through another tool.
    """
    for index, row in enumerate(rows[:10]):
        labels = {_normalise(cell): position for position, cell in enumerate(row)}
        found: dict[str, int] = {}
        for label, position in labels.items():
            if label in _ID_HEADERS and "id" not in found:
                found["id"] = position
            elif label in _RESPONSE_HEADERS and "response" not in found:
                found["response"] = position
            elif label in _QUESTION_HEADERS and "question" not in found:
                found["question"] = position
        if "response" in found and ("id" in found or "question" in found):
            return index, found

    raise ResponseImportError(
        "Could not find a 'Response' column alongside a 'Request ID' or 'Question' column. "
        "Upload the workbook downloaded from this engagement, with the Response column "
        "filled in."
    )


def import_responses(
    content: bytes, payload: IrlPayload, existing: dict[str, str] | None = None
) -> tuple[dict[str, str], ImportResponsesResult]:
    """Scrape the Response column and return the answers to save, plus what happened.

    Returns `(responses_to_write, result)`. The caller persists the answers; this function
    touches no database, which keeps it testable against a workbook alone.
    """
    already = existing or {}

    try:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001 - any parse failure is the same user error
        raise ResponseImportError(
            f"That file could not be read as an Excel workbook ({type(exc).__name__}). "
            "Save it as .xlsx and try again."
        ) from exc

    try:
        sheet = workbook.active
        if sheet is None:
            raise ResponseImportError("The workbook has no readable sheet.")

        rows = list(sheet.iter_rows(max_row=_MAX_ROWS, values_only=True))
    finally:
        workbook.close()

    if not rows:
        raise ResponseImportError("The workbook is empty.")

    header_index, columns = _find_header_row(rows)
    body = rows[header_index + 1 :]

    by_id = {q.id: q for q in payload.questions}
    by_text = {_normalise(q.question): q.id for q in payload.questions}
    # Also index the seed text: a client working from an older copy may still carry the
    # original evidence wording rather than the model's rewrite.
    for question in payload.questions:
        if question.seed_text:
            by_text.setdefault(_normalise(question.seed_text), question.id)

    responses: dict[str, str] = {}
    matched = skipped_blank = 0
    unmatched: list[str] = []

    for row in body:
        if not row or all(cell is None or str(cell).strip() == "" for cell in row):
            continue

        answer = _cell_at(row, columns, "response")
        question_id = ""

        raw_id = _cell_at(row, columns, "id")
        if raw_id and raw_id in by_id:
            question_id = raw_id
        else:
            text = _normalise(_cell_at(row, columns, "question"))
            if text and text in by_text:
                question_id = by_text[text]

        if not question_id:
            label = _cell_at(row, columns, "question") or raw_id
            if label:
                unmatched.append(label[:120])
            continue

        matched += 1
        if not answer:
            # A blank cell means "not answered yet", never "clear what is already there".
            skipped_blank += 1
            continue
        responses[question_id] = answer

    # Only count a write where the value actually changes, so the reported number means
    # something to the analyst rather than restating the row count.
    updated = sum(1 for qid, text in responses.items() if already.get(qid, "") != text)

    note = ""
    if matched == 0:
        note = (
            "No row in that workbook matched a request in this list. Check it is the "
            "workbook downloaded from this engagement, and that its Request ID or "
            "Question column is intact."
        )
    elif unmatched:
        note = (
            f"{len(unmatched)} row(s) could not be matched to a request and were ignored. "
            "They are listed below."
        )

    result = ImportResponsesResult(
        matched=matched,
        updated=updated,
        skipped_blank=skipped_blank,
        unmatched_rows=unmatched[:20],
        total_rows=sum(
            1 for r in body if r and any(c is not None and str(c).strip() for c in r)
        ),
        note=note,
    )
    return responses, result
