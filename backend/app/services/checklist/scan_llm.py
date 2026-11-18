"""The model's half of the shared-drive scan.

The deterministic shortlist in `scanner.py` decides *which files are worth looking at*
for each request. This module decides *whether what arrived is actually enough*, and
writes the follow-up question when it is not — which is the judgement a filename cannot
support and the reason the model is here at all.

The split is the same one the rest of the platform uses: the rules bound the problem,
the model reads. What is different from the scope and IRL modules is that here the model
does change a stored value — the checklist status. Three things contain that:

* **it can only touch requests the shortlist already found candidates for**, so it never
  invents a document out of an empty drive;
* **every filename it returns is checked against the candidates it was given** — one it
  invented is dropped, and a judgement left with no files cannot claim receipt;
* **a human-set row never reaches it**, filtered out before the prompt is built.
"""

from __future__ import annotations

import json
import logging
import re
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings
from app.schemas.irl import IrlQuestion
from app.services.intelligence.skills import skill_text

if TYPE_CHECKING:  # pragma: no cover - import cycle, types only
    from app.services.checklist.scanner import Candidate, _Judgement

logger = logging.getLogger(__name__)

_VERSION_PATTERN = re.compile(r"prompt_version:\s*([0-9.]+)")

VALID_STATUSES = {"not_received", "received_partially", "received_completely"}
MAX_FOLLOW_UPS = 3
# One request's worth of candidates is small; this bounds a pathological drive.
MAX_REQUESTS_PER_CALL = 60


@lru_cache(maxsize=1)
def _load_prompt() -> tuple[str, str]:
    text = skill_text("drive-scan")
    match = _VERSION_PATTERN.search(text)
    return text, (match.group(1) if match else "unknown")


class LlmJudgement(BaseModel):
    """One request's verdict, as the model returns it."""

    model_config = {"extra": "ignore"}

    request_id: str
    status: str
    document_type: str = ""
    matched_files: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    reasoning: str = ""


class LlmScanResponse(BaseModel):
    model_config = {"extra": "ignore"}

    judgements: list[LlmJudgement] = Field(default_factory=list)


def _strip_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z]*\n", "", stripped)
        stripped = re.sub(r"\n```$", "", stripped)
    return stripped.strip()


def _request_block(question: IrlQuestion, candidates: list[Candidate]) -> dict[str, Any]:
    """One request and its candidate files, as the model sees them."""
    return {
        "request_id": question.id,
        "function": question.function,
        "request": question.question,
        "evidence_wanted": question.seed_text or "",
        "candidate_files": [
            {
                "path": c.file.relative_path,
                "folder": c.file.folder,
                "filename": c.file.name,
                "size_bytes": c.file.size_bytes,
                # An empty excerpt is meaningful — say which kind of empty it is, so the
                # model does not read "unreadable" as "blank document".
                "content_excerpt": c.file.excerpt
                or (
                    f"(not readable: {c.file.extract_error})"
                    if c.file.extract_error
                    else "(no text extracted — image or binary; judge on the filename)"
                ),
                "filename_match_score": round(c.score, 2),
            }
            for c in candidates
        ],
    }


def judge_documents(
    questions: list[IrlQuestion],
    candidates: dict[str, list[Candidate]],
    settings: Settings,
    client: Any | None = None,
) -> dict[str, _Judgement]:
    """Ask the model to judge each request against its candidate files.

    Raises on a model or parsing failure so `scanner.py` can fall back to deterministic
    matching — a scan that half-worked is worse than one that says it used the rules.
    """
    from app.services.checklist.scanner import _Judgement

    prompt, prompt_version = _load_prompt()
    considered = questions[:MAX_REQUESTS_PER_CALL]
    blocks = [_request_block(q, candidates.get(q.id, [])) for q in considered]

    contents = (
        f"{prompt}\n\n## The requests and what was found\n\n"
        f"```json\n{json.dumps({'requests': blocks}, indent=2, default=str)}\n```"
    )

    if client is None:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=contents,
        config={
            "temperature": settings.llm_temperature,
            "max_output_tokens": settings.llm_max_tokens,
            "response_mime_type": "application/json",
        },
    )

    text = _strip_fences(response.text or "")
    if not text:
        raise ValueError("model returned an empty response")

    try:
        parsed = LlmScanResponse.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValueError(f"model response did not parse: {exc}") from exc

    by_id = {q.id: q for q in considered}
    out: dict[str, _Judgement] = {}
    for judgement in parsed.judgements:
        question = by_id.get(judgement.request_id)
        if question is None:
            # A request id nobody asked about. Dropping it individually is right: one
            # hallucinated row must not discard the judgements that were sound.
            logger.warning("Scan: model returned unknown request id %r", judgement.request_id)
            continue

        status = judgement.status if judgement.status in VALID_STATUSES else "not_received"

        # Only filenames the model was actually shown. This is the guard that stops an
        # invented document becoming a receipt.
        offered = {c.file.relative_path for c in candidates.get(question.id, [])}
        matched = [f for f in judgement.matched_files if f in offered]
        if len(matched) != len(judgement.matched_files):
            logger.warning(
                "Scan: dropped %d filename(s) the model was not given, on %s",
                len(judgement.matched_files) - len(matched),
                question.id,
            )

        # A receipt with no surviving file is not a receipt.
        if status != "not_received" and not matched:
            status = "not_received"

        follow_ups = [q.strip() for q in judgement.follow_up_questions if q and q.strip()]
        if status == "not_received":
            # The request is already outstanding; a follow-up here restates the ask.
            follow_ups = []
        follow_ups = follow_ups[:MAX_FOLLOW_UPS]

        out[question.id] = _Judgement(
            status=status,
            document_type=judgement.document_type.strip()[:120] if status != "not_received" else "",
            matched_files=matched,
            follow_up_questions=follow_ups,
            reasoning=judgement.reasoning.strip(),
        )

    logger.info(
        "Scan judged %d of %d requests (prompt v%s)", len(out), len(considered), prompt_version
    )
    return out
