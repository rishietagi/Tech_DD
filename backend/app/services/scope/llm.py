"""LlmScopeGenerator — rewrites the prose inside a rules-built scope.

The deterministic engine decides what the document contains; this layer only makes the
wording specific to the target. Every response is schema-validated and diffed against
the skeleton, and any mismatch discards the tailoring in favour of the rules output —
so a bad generation degrades to a slightly generic scope, never a wrong one.

An absent API key is not an error: the generator reports itself unavailable and the
factory falls back with a logged warning.
"""

import hashlib
import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.intake import IntakeFull
from app.schemas.scope import ScopeOfWorkPayloadV2
from app.schemas.tailoring import LlmTailoring, TailoringRejected
from app.services.scope.rules_generator import RulesScopeGenerator

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "tailoring.md"
_VERSION_PATTERN = re.compile(r"prompt_version:\s*([0-9.]+)")


@lru_cache(maxsize=1)
def _load_prompt() -> tuple[str, str]:
    """Returns (prompt_text, version)."""
    text = PROMPT_FILE.read_text(encoding="utf-8")
    match = _VERSION_PATTERN.search(text)
    return text, (match.group(1) if match else "unknown")


def _narrative_context(intake: IntakeFull) -> dict[str, Any]:
    """The intake's free-text fields — the only place target-specific colour lives."""
    return {
        "company_name": intake.target.company_name,
        "sector": intake.target.sector,
        "line_of_business": intake.target.line_of_business,
        "business_model": intake.target.business_model,
        "digital_maturity": intake.target.digital_maturity,
        "deal_context": intake.context.context_narrative,
        "deal_rationale": intake.rationale.rationale_narrative,
        "focus_areas": intake.rationale.focus_areas,
        "deal_breakers": intake.rationale.deal_breakers,
        "known_tech_stack": intake.technology.known_tech_stack,
        "core_systems": intake.technology.core_systems,
        "hosting_model": intake.technology.hosting_model,
        "known_incidents": intake.technology.known_incidents,
        "ma_history": intake.target.ma_history,
    }


def _skeleton_for_prompt(scope: ScopeOfWorkPayloadV2) -> list[dict[str, Any]]:
    """Only the fields the model is allowed to touch."""
    return [
        {
            "row_id": row.id,
            "title": row.title,
            "lines": [{"index": i, "text": line.text} for i, line in enumerate(row.lines)],
        }
        for row in scope.rows
    ]


def _cache_key(scope: ScopeOfWorkPayloadV2, narrative: dict[str, Any], settings: Settings) -> str:
    _, prompt_version = _load_prompt()
    material = json.dumps(
        {
            "skeleton": _skeleton_for_prompt(scope),
            "narrative": narrative,
            "model": settings.gemini_model,
            "prompt_version": prompt_version,
        },
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(material.encode()).hexdigest()


def _strip_fences(raw: str) -> str:
    """Models wrap JSON in code fences despite instructions not to."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def validate_tailoring(tailoring: LlmTailoring, scope: ScopeOfWorkPayloadV2) -> None:
    """Diff the model's output against the skeleton. Raises TailoringRejected.

    Order matters (PHASE2_SCOPE_ENGINE §8): identical row id set, then matching line
    counts and indices. Anything else means the model changed something structural.
    """
    if not tailoring.engagement_summary.strip():
        raise TailoringRejected("engagement_summary is empty")

    skeleton_ids = {row.id for row in scope.rows}
    returned_ids = {row.row_id for row in tailoring.rows}

    if returned_ids != skeleton_ids:
        added = returned_ids - skeleton_ids
        dropped = skeleton_ids - returned_ids
        raise TailoringRejected(
            f"row id set changed (added={sorted(added)}, dropped={sorted(dropped)})"
        )

    by_id = {row.id: row for row in scope.rows}
    for tailored in tailoring.rows:
        original = by_id[tailored.row_id]

        if len(tailored.lines) != len(original.lines):
            raise TailoringRejected(
                f"{tailored.row_id}: line count changed "
                f"({len(original.lines)} -> {len(tailored.lines)})"
            )

        indices = [line.index for line in tailored.lines]
        if sorted(indices) != list(range(len(original.lines))):
            raise TailoringRejected(f"{tailored.row_id}: line indices are not 0..n-1 ({indices})")

        if not tailored.title.strip():
            raise TailoringRejected(f"{tailored.row_id}: title is empty")
        if any(not line.text.strip() for line in tailored.lines):
            raise TailoringRejected(f"{tailored.row_id}: a line is empty")


def apply_tailoring(scope: ScopeOfWorkPayloadV2, tailoring: LlmTailoring) -> ScopeOfWorkPayloadV2:
    """Overlay validated prose onto the skeleton. Structure is untouched."""
    tailored_rows = {row.row_id: row for row in tailoring.rows}
    updated = scope.model_copy(deep=True)

    updated.engagement_summary = tailoring.engagement_summary.strip()
    for row in updated.rows:
        replacement = tailored_rows.get(row.id)
        if replacement is None:
            continue
        row.title = replacement.title.strip()
        for line in sorted(replacement.lines, key=lambda line: line.index):
            row.lines[line.index].text = line.text.strip()

    return updated


class LlmScopeGenerator:
    """Rules skeleton + model-authored prose, with fallback on any failure."""

    name = "llm"

    def __init__(self, settings: Settings | None = None, client: Any | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = client
        self._rules = RulesScopeGenerator()
        self._cache: dict[str, LlmTailoring] = {}

    @property
    def available(self) -> bool:
        return bool(self._settings.gemini_api_key)

    def _get_client(self) -> Any:
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._settings.gemini_api_key)
        return self._client

    def _request_tailoring(self, scope: ScopeOfWorkPayloadV2, narrative: dict[str, Any]) -> LlmTailoring:
        prompt, _ = _load_prompt()
        payload = {
            "engagement": narrative,
            "current_engagement_summary": scope.engagement_summary,
            "rows": _skeleton_for_prompt(scope),
        }
        contents = f"{prompt}\n\n## Engagement\n\n```json\n{json.dumps(payload, indent=2, default=str)}\n```"

        response = self._get_client().models.generate_content(
            model=self._settings.gemini_model,
            contents=contents,
            config={
                "temperature": self._settings.llm_temperature,
                "max_output_tokens": self._settings.llm_max_tokens,
                "response_mime_type": "application/json",
            },
        )

        text = _strip_fences(response.text or "")
        if not text:
            raise TailoringRejected("model returned an empty response")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise TailoringRejected(f"response was not valid JSON: {exc}") from exc

        try:
            return LlmTailoring.model_validate(data)
        except Exception as exc:
            raise TailoringRejected(f"response did not match the required shape: {exc}") from exc

    def generate(self, intake: IntakeFull) -> ScopeOfWorkPayloadV2:
        scope = self._rules.generate(intake)
        _, prompt_version = _load_prompt()

        if not self.available:
            logger.warning("GEMINI_API_KEY is not set; returning the deterministic scope.")
            scope.generator = "rules (llm unavailable)"
            return scope

        narrative = _narrative_context(intake)
        key = _cache_key(scope, narrative, self._settings)

        try:
            tailoring = self._cache.get(key)
            if tailoring is None:
                tailoring = self._request_tailoring(scope, narrative)
                self._cache[key] = tailoring

            validate_tailoring(tailoring, scope)
            tailored = apply_tailoring(scope, tailoring)
            tailored.generator = self.name
            tailored.prompt_version = prompt_version
            return tailored

        except TailoringRejected as exc:
            logger.warning("LLM tailoring rejected (%s); shipping the deterministic scope.", exc.reason)
            scope.generator = "rules (llm tailoring rejected)"
            scope.prompt_version = prompt_version
            return scope

        except Exception as exc:  # noqa: BLE001 - the model call must never break generation
            logger.warning(
                "LLM tailoring failed (%s: %s); shipping the deterministic scope.",
                type(exc).__name__,
                exc,
            )
            scope.generator = "rules (llm error)"
            return scope
