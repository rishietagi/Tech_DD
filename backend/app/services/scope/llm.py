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
from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.intake import IntakeFull
from app.schemas.scope import ScopeOfWorkPayloadV2
from app.schemas.tailoring import LlmTailoring, TailoringRejected
from app.services.intelligence.skills import skill_text
from app.services.scope.rules_generator import RulesScopeGenerator

logger = logging.getLogger(__name__)

_VERSION_PATTERN = re.compile(r"prompt_version:\s*([0-9.]+)")


@lru_cache(maxsize=1)
def _load_prompt() -> tuple[str, str]:
    """Returns (prompt_text, version)."""
    text = skill_text("scope-tailoring")
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

    Order matters (PHASE2_SPEC §8): identical row id set, then matching line
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


# --------------------------------------------------------------------------- house rules
#
# The prompt (v2.0) states these, but a prompt is guidance and a deck that names the
# client is a real problem, so they are enforced in code as well. Rishi's instruction,
# 2026-09-02: never name the target or the investor, and open every bullet with an
# examination verb.
#
# Scrubbing rather than rejecting is deliberate. A single leaked name should not throw
# away an otherwise good scope and fall back to the generic deterministic text — that
# would be a worse document, not a safer one.

# Openers the model reaches for that are not examination verbs. Mapped to the verb that
# carries the same meaning. Order matters: longest phrase first, so "Gain an overview of"
# is matched before "Gain".
_VERB_REWRITES: list[tuple[str, str]] = [
    ("Gain an overview of the", "Review the"),
    ("Gain an overview of", "Review"),
    ("Gain overview of the", "Review the"),
    ("Gain overview of", "Review"),
    ("Gain an understanding of the", "Understand the"),
    ("Gain an understanding of", "Understand"),
    ("Gain insight into", "Review"),
    ("Gain visibility of", "Review"),
    ("Gain visibility into", "Review"),
    ("Obtain an overview of", "Review"),
    ("Obtain", "Review"),
    ("Look at", "Review"),
    ("Explore", "Review"),
    ("Deep dive into", "Assess"),
    ("Consider", "Review"),
]

# Generic replacements for the parties. Used when a name leaks through.
_TARGET_WORD = "the Target"
_ACQUIRER_WORD = "the Acquirer"


def _name_variants(name: str | None) -> list[str]:
    """A company name plus the shorter forms a model tends to use instead.

    "Kiln Industrial Supply" also leaks as "Kiln" and as the possessive "Kiln's", so the
    first token is treated as a name in its own right when it is distinctive enough. Short
    or generic first tokens (The, A, Group) are skipped — scrubbing those would mangle
    ordinary prose.
    """
    if not name or not name.strip():
        return []
    cleaned = name.strip()
    variants = {cleaned}

    suffixes = (
        " Limited", " Ltd", " Ltd.", " Inc", " Inc.", " LLC", " PLC", " Plc",
        " GmbH", " BV", " B.V.", " NV", " N.V.", " Group", " Holdings", " Corporation",
        " Corp", " Corp.", " Company", " Co", " Co.",
    )
    trimmed = cleaned
    for suffix in suffixes:
        if trimmed.endswith(suffix):
            trimmed = trimmed[: -len(suffix)].strip()
            variants.add(trimmed)

    first = trimmed.split()[0] if trimmed.split() else ""
    _TOO_GENERIC = {"the", "a", "an", "group", "holdings", "global", "national", "first"}
    if len(first) >= 4 and first.lower() not in _TOO_GENERIC:
        variants.add(first)

    # Longest first, so "Kiln Industrial Supply" is replaced before the bare "Kiln".
    return sorted((v for v in variants if v), key=len, reverse=True)


def _scrub_names(text: str, target_names: list[str], acquirer_names: list[str]) -> str:
    """Replace any party name with its generic equivalent, possessives included."""
    result = text
    for names, replacement in ((target_names, _TARGET_WORD), (acquirer_names, _ACQUIRER_WORD)):
        for name in names:
            escaped = re.escape(name)
            # Possessive first: "Kiln's estate" -> "the Target's estate", not
            # "the Target 's estate".
            result = re.sub(rf"\b{escaped}’s\b", f"{replacement}'s", result)
            result = re.sub(rf"\b{escaped}'s\b", f"{replacement}'s", result)
            result = re.sub(rf"\b{escaped}\b", replacement, result)

    # "The the Target" reads badly when the model already wrote an article.
    result = re.sub(r"\b[Tt]he the Target\b", "the Target", result)
    result = re.sub(r"\b[Tt]he the Acquirer\b", "the Acquirer", result)
    # A scrubbed name at the start of a sentence should keep its capital.
    result = re.sub(r"(^|(?<=[.!?] ))the Target", "The Target", result)
    result = re.sub(r"(^|(?<=[.!?] ))the Acquirer", "The Acquirer", result)
    return result


def _enforce_verb(text: str) -> str:
    """Rewrite a bullet that opens with a non-examination verb."""
    stripped = text.strip()
    for bad, good in _VERB_REWRITES:
        if stripped.lower().startswith(bad.lower()):
            return good + stripped[len(bad) :]
    return stripped


def _strip_names_from_title(title: str, target_names: list[str], acquirer_names: list[str]) -> str:
    """Headings must be generic (Rule 2), so a name is removed rather than replaced.

    "Kiln's Standalone IT Cost Model" should become "Standalone IT Cost Model", not
    "the Target's Standalone IT Cost Model" — a heading naming a party is wrong even
    when the party is anonymised.
    """
    result = title
    for name in [*target_names, *acquirer_names]:
        escaped = re.escape(name)
        result = re.sub(rf"\b{escaped}’s\s+", "", result)
        result = re.sub(rf"\b{escaped}'s\s+", "", result)
        result = re.sub(rf"\s*\b{escaped}\b\s*", " ", result)
    # Tidy what removal leaves behind: doubled spaces, a dangling "for"/"at"/"of".
    result = re.sub(r"\s{2,}", " ", result).strip()
    result = re.sub(r"\s+(for|at|of|in|and)$", "", result).strip()
    result = re.sub(r"^(for|at|of|in|and)\s+", "", result).strip()
    return result


def enforce_house_rules(
    scope: ScopeOfWorkPayloadV2,
    target_name: str | None = None,
    investor_name: str | None = None,
) -> ScopeOfWorkPayloadV2:
    """Apply the rules a prompt alone cannot guarantee.

    Names are scrubbed from the summary, every title and every bullet; titles have them
    removed outright; and each bullet is forced to open with an examination verb.
    """
    target_names = _name_variants(target_name)
    acquirer_names = _name_variants(investor_name)

    if not target_names and not acquirer_names:
        # Still worth enforcing the verb rule.
        for row in scope.rows:
            for line in row.lines:
                line.text = _enforce_verb(line.text)
        return scope

    scope.engagement_summary = _scrub_names(
        scope.engagement_summary, target_names, acquirer_names
    )
    for row in scope.rows:
        row.title = _strip_names_from_title(row.title, target_names, acquirer_names)
        for line in row.lines:
            line.text = _enforce_verb(_scrub_names(line.text, target_names, acquirer_names))

    return scope


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
            # The prompt states these rules, but a prompt is guidance and a deck naming
            # the client is a real problem — so they are enforced here too.
            tailored = enforce_house_rules(
                tailored,
                target_name=intake.target.company_name,
                investor_name=intake.context.investor_firm_name,
            )
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
