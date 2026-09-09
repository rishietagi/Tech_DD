"""Shared-drive scanning — walk the folder the client drops documents into.

Match each file to an IRL request, decide whether what arrived is actually enough, and
update the checklist so the consultant does not maintain it by hand.

**The four rules this was always going to have to follow** (recorded in the stub long
before it was built, and kept):

1. **A scan never overwrites a human-set status.** `IrlDocumentStatus.set_by_human`
   exists for exactly this. Someone who has looked at a document and made a judgement
   outranks a filename match.
2. **Record what was matched.** `matched_files` holds the filenames a status was inferred
   from, so a wrong call is visible and correctable rather than silent.
3. **Below the confidence threshold, propose nothing.** Leaving a request as
   `not_received` is honest; marking it received on a weak filename match is not.
4. **Never delete or move client files.** Read-only over the drive, always.

## How it decides

Two stages, and the split matters:

* **Deterministic shortlisting.** Token overlap between the filename, its folder and the
  request's own text picks a handful of candidate files per request. This is cheap,
  reproducible, and it is what bounds the prompt — the model never sees 50 files against
  90 requests.
* **A model judgement per shortlisted request.** Given the request and its candidates'
  names and content excerpts, the model decides the status, names the document type, and
  — the point of the exercise — **writes the follow-up questions** when what arrived is
  partial. A quarter of monitoring data against a twelve-month request is not a missing
  document; it is an incomplete one, and the useful output is the question that closes
  the gap.

With no API key, or when the model fails, the deterministic shortlist alone still writes
statuses. It cannot tell partial from complete — that judgement needs the content — so it
only ever says `received_completely` on a strong match and leaves everything else alone.

## What it deliberately does not do

**Only `kind == "document"` requests are scanned.** An IRL also asks questions, and a
question is answered in a meeting, not by a file appearing on a drive. Scanning them
would mark them received the moment any loosely related document arrived.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.models.irl import InformationRequestList, IrlDocumentStatus
from app.schemas.irl import IrlPayload, IrlQuestion
from app.services.checklist.extract import ExtractedFile, extract_excerpt

logger = logging.getLogger(__name__)

# Folders that are scaffolding rather than client material.
SKIP_DIRS = {".git", "__pycache__", ".ds_store", "node_modules", ".trash"}
SKIP_FILES = {"readme.md", ".ds_store", "thumbs.db", "desktop.ini"}

# Tokens that appear in so many filenames and requests that they carry no signal.
STOPWORDS = {
    "the", "and", "for", "with", "of", "a", "an", "to", "in", "on", "at", "by", "or",
    "provide", "please", "detail", "details", "including", "current", "copy", "copies",
    "any", "all", "list", "latest", "target", "document", "documents", "its", "from",
    "over", "per", "into", "that", "this", "which", "each", "most", "recent", "last",
    "department", "dept", "team", "kiln", "lighthouse", "project",
}

# Abbreviations that recur in diligence filenames, expanded so a file called
# "IT-Org-Chart" meets a request that says "organization chart". Only pairs where the
# short form is genuinely unambiguous in this domain — an over-eager synonym list would
# manufacture matches, which is the failure this whole module is written to avoid.
SYNONYMS: dict[str, set[str]] = {
    "org": {"organisation", "organization"},
    "orgchart": {"organisation", "organization", "chart"},
    "hr": {"human", "resources"},
    "dr": {"disaster", "recovery"},
    "bcp": {"business", "continuity"},
    "sla": {"service", "level", "agreement"},
    "slas": {"service", "level", "agreement"},
    "tsa": {"transition", "service", "agreement"},
    "eol": {"end", "life"},
    "capex": {"capital", "expenditure"},
    "opex": {"operating", "expenditure"},
    "pii": {"personal", "identifiable", "information", "personally"},
    "rpa": {"robotic", "process", "automation"},
    "sdlc": {"software", "development", "lifecycle"},
    "dc": {"data", "centre", "center"},
    "licence": {"license"},
    "licences": {"license"},
    "centre": {"center"},
    "spend": {"expenditure"},
    "headcount": {"staff", "employees"},
    "vendor": {"supplier", "third"},
    "vendors": {"supplier", "third"},
}

# Below this share of the request's own distinctive tokens, a file is not a candidate.
# Deliberately generous: this stage shortlists, the model decides.
CANDIDATE_THRESHOLD = 0.34
# Without the model, only a match this strong is allowed to write a status on its own.
DETERMINISTIC_THRESHOLD = 0.55
MAX_CANDIDATES_PER_REQUEST = 4


class ScanError(AppError):
    """The drive could not be scanned — a bad path, rather than a bad match."""

    def __init__(self, message: str) -> None:
        super().__init__(code="scan_failed", message=message, status_code=400)


@dataclass
class ScanOutcome:
    """What one scan did, for the caller to report."""

    files_seen: int
    requests_considered: int
    updated: int
    skipped_human: int
    follow_ups: int
    generator: str
    # Files nothing on the list claimed — see ScanResult.unmatched_files.
    unmatched_files: list[str] = field(default_factory=list)


def _tokenise(text: str) -> set[str]:
    """Words worth matching on: lowercase, de-punctuated, stopwords and noise removed."""
    words = re.split(r"[^a-z0-9]+", text.lower())
    tokens: set[str] = set()
    for word in words:
        if len(word) < 3 or word in STOPWORDS:
            continue
        # Numeric-only tokens are years and quarters; they say when, not what.
        if word.isdigit():
            continue
        tokens.add(word)
        # Crude singularisation so "policies"/"policy" and "diagrams"/"diagram" meet.
        if word.endswith("ies") and len(word) > 4:
            tokens.add(word[:-3] + "y")
        elif word.endswith("s") and not word.endswith("ss"):
            tokens.add(word[:-1])
        tokens |= SYNONYMS.get(word, set())
    return tokens


def walk_drive(root: Path) -> list[ExtractedFile]:
    """Every client file under `root`, with a content excerpt. Read-only."""
    if not root.exists():
        raise ScanError(
            f"The shared drive path does not exist: {root}. Set SHARED_DRIVE_ROOT to the "
            "folder the client drops documents into."
        )
    if not root.is_dir():
        raise ScanError(f"The shared drive path is not a folder: {root}")

    files: list[ExtractedFile] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.lower() in SKIP_FILES:
            continue
        if any(part.lower() in SKIP_DIRS for part in path.relative_to(root).parts[:-1]):
            continue

        excerpt, error = extract_excerpt(path)
        relative = path.relative_to(root).as_posix()
        folder = path.parent.name if path.parent != root else ""
        files.append(
            ExtractedFile(
                path=path,
                relative_path=relative,
                name=path.name,
                folder=folder,
                suffix=path.suffix.lower(),
                size_bytes=path.stat().st_size,
                excerpt=excerpt,
                extract_error=error,
                # The folder is part of the file's identity for matching: "01-Finance"
                # is the strongest hint that a file answers a Finance request.
                tokens=_tokenise(f"{path.stem} {folder}"),
            )
        )
    return files


def _request_tokens(question: IrlQuestion) -> set[str]:
    """What this request is distinctively about.

    `seed_text` is the scope row's own phrasing of the evidence it wants, which is
    tighter than the client-facing question, so both are used.
    """
    return _tokenise(f"{question.question} {question.seed_text or ''}")


def _score(request: set[str], file_tokens: set[str]) -> float:
    """How strongly a file's name and folder answer a request.

    Measured against the **smaller** of the two token sets rather than against the
    request alone. A request is a sentence and a filename is three or four words, so
    dividing by the request's length punishes exactly the filenames that are most
    obviously right: "Application-Inventory-SAP-and-Bolt-ons.xlsx" shares only
    "application" and "inventory" with a request that also says complete, business,
    function, version, licensing and owner — 25% by that measure, and plainly the file
    being asked for.

    Two distinctive words in common is a real match, so the overlap count is also floored
    in directly: two hits carry the score over the candidate threshold on their own.
    """
    if not request or not file_tokens:
        return 0.0
    overlap = request & file_tokens
    if not overlap:
        return 0.0
    coverage = len(overlap) / min(len(request), len(file_tokens))
    # A second and third shared term each add real confidence; beyond that the filename
    # has said all it can.
    density = min(len(overlap), 3) / 3
    return round(max(coverage, density * 0.6), 4)


@dataclass
class Candidate:
    file: ExtractedFile
    score: float


def shortlist(
    questions: list[IrlQuestion], files: list[ExtractedFile]
) -> dict[str, list[Candidate]]:
    """Candidate files per request id. Deterministic, and the same inputs always agree."""
    out: dict[str, list[Candidate]] = {}
    for question in questions:
        tokens = _request_tokens(question)
        scored = [
            Candidate(file=f, score=_score(tokens, f.tokens))
            for f in files
        ]
        keep = sorted(
            (c for c in scored if c.score >= CANDIDATE_THRESHOLD),
            key=lambda c: (-c.score, c.file.relative_path),
        )[:MAX_CANDIDATES_PER_REQUEST]
        if keep:
            out[question.id] = keep
    return out


def _scannable(payload: IrlPayload) -> list[IrlQuestion]:
    """Only document requests. A question is answered in a meeting, not by a file."""
    return [q for q in payload.questions if q.kind == "document"]


def scan_shared_drive(
    db: Session,
    irl: InformationRequestList,
    payload: IrlPayload,
    *,
    root: Path | None = None,
    settings: Settings | None = None,
) -> ScanOutcome:
    """Walk the drive and update the statuses on `irl`. Returns what it did.

    Never raises on a single bad file or a model failure — only on a drive path that
    cannot be read at all, which is a configuration fault the caller must see.
    """
    settings = settings or get_settings()
    root = root or Path(settings.shared_drive_root)

    files = walk_drive(root)
    requests = _scannable(payload)
    candidates = shortlist(requests, files)

    existing = {s.question_id: s for s in irl.document_statuses}
    # Rule 1: a human's judgement outranks anything found on the drive.
    protected = {qid for qid, row in existing.items() if row.set_by_human}

    judgements: dict[str, _Judgement] = {}
    generator = "rules"
    scannable_with_candidates = [q for q in requests if q.id in candidates and q.id not in protected]

    if settings.llm_enabled and scannable_with_candidates:
        from app.services.checklist.scan_llm import judge_documents

        try:
            judgements = judge_documents(scannable_with_candidates, candidates, settings)
            generator = "llm"
        except Exception as exc:  # noqa: BLE001 - a model failure must not lose the walk
            logger.warning(
                "Scan narrative failed (%s: %s); falling back to deterministic matching.",
                type(exc).__name__,
                exc,
            )
            generator = "rules (llm failed)"

    if not judgements:
        judgements = _deterministic_judgements(scannable_with_candidates, candidates)

    now = datetime.now(UTC)
    updated = 0
    follow_ups = 0
    for question in requests:
        if question.id in protected:
            continue
        judgement = judgements.get(question.id)
        if judgement is None:
            continue

        row = existing.get(question.id)
        if row is None:
            row = IrlDocumentStatus(irl_id=irl.id, question_id=question.id)
            db.add(row)
            irl.document_statuses.append(row)
            existing[question.id] = row

        row.status = judgement.status
        if judgement.document_type:
            row.document_type = judgement.document_type
        row.matched_files = judgement.matched_files
        row.follow_up_questions = judgement.follow_up_questions or None
        row.scan_reasoning = judgement.reasoning
        row.scanned_at = now
        # Rule 1's other half: a scan-written row stays scan-owned, so the next scan may
        # correct itself. Only the checklist's own edit endpoint sets this true.
        row.set_by_human = False

        updated += 1
        follow_ups += len(judgement.follow_up_questions)

    # A file is "claimed" only where the judgement actually kept it, so a candidate the
    # model rejected still counts as unmatched — which is the honest reading.
    claimed = {f for j in judgements.values() for f in j.matched_files}
    unmatched = sorted(f.relative_path for f in files if f.relative_path not in claimed)

    db.commit()
    logger.info(
        "Scanned %s: %d files, %d document requests, %d updated, %d protected, %d follow-ups (%s)",
        root,
        len(files),
        len(requests),
        updated,
        len(protected),
        follow_ups,
        generator,
    )
    return ScanOutcome(
        files_seen=len(files),
        requests_considered=len(requests),
        updated=updated,
        skipped_human=len(protected),
        follow_ups=follow_ups,
        generator=generator,
        unmatched_files=unmatched,
    )


@dataclass
class _Judgement:
    """One request's outcome — the shape both the model and the fallback produce."""

    status: str
    document_type: str
    matched_files: list[str]
    follow_up_questions: list[str]
    reasoning: str


def _deterministic_judgements(
    questions: list[IrlQuestion], candidates: dict[str, list[Candidate]]
) -> dict[str, _Judgement]:
    """Statuses from filename matching alone, for when the model is off or failed.

    Rule 3 is what shapes this: without reading the documents there is no way to tell a
    complete register from a one-quarter extract, so this only ever claims
    `received_completely` on a strong match and stays silent otherwise. It writes no
    follow-up questions at all — inventing one from a filename would be guesswork.
    """
    out: dict[str, _Judgement] = {}
    for question in questions:
        best = candidates.get(question.id, [])
        if not best or best[0].score < DETERMINISTIC_THRESHOLD:
            continue
        matched = [c.file.relative_path for c in best if c.score >= DETERMINISTIC_THRESHOLD]
        out[question.id] = _Judgement(
            status="received_completely",
            document_type="",
            matched_files=matched,
            follow_up_questions=[],
            reasoning=(
                f"Filename match only ({best[0].score:.0%} of the request's terms). "
                "No document content was read, so completeness is not assessed."
            ),
        )
    return out
