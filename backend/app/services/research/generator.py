"""Company research grounded in live web search.

One Gemini call with the GoogleSearch tool enabled. The model searches, reads, and
answers; the SDK returns grounding metadata naming the pages it actually used, which
becomes the source list shown beside every finding.

**Grounding is mandatory.** If a response comes back with no grounding metadata, the run
is rejected rather than stored. Ungrounded "research" with invented citations is worse
than no research at all: it looks identical to the real thing and would reach a deal
team carrying the same authority.

Unlike the scope engine there is no deterministic fallback here — research without web
access is not a degraded version of research, it is fabrication. When the model is
unavailable the caller gets a clear error and no stored run.

**Two calls, and the second one is not optional decoration.** Source ids (`S1`, `S2`, …)
are assigned by *this module* from the grounding metadata that comes back with the search
response — so at the moment the model writes its answer, the ids do not exist yet and it
cannot possibly cite them. Every run produced between the module being built and
2026-09-11 therefore carried empty `source_ids` on every finding: the per-claim source
links rendered nothing, and only the list at the foot of the page worked. The second call
fixes that by handing the model its own text alongside the now-numbered sources and asking
only "which of these supports each claim?". It is cheap, it adds no new claims, and if it
fails the run is still stored — uncited, exactly as it was before.
"""

import json
import logging
import re
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.intake import IntakeFull
from app.schemas.research import (
    RESEARCH_DISCLAIMER,
    BriefSection,
    BusinessBrief,
    ResearchFinding,
    ResearchPayload,
    ResearchSource,
)

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "research.md"
ATTRIBUTE_PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "attribute.md"
_VERSION_PATTERN = re.compile(r"prompt_version:\s*([0-9.]+)")


class ResearchUnavailable(RuntimeError):
    """No API key, or the model could not be reached."""


class ResearchRejected(RuntimeError):
    """The model answered, but the answer was not usable."""


@lru_cache(maxsize=1)
def _load_prompt() -> tuple[str, str]:
    text = PROMPT_FILE.read_text(encoding="utf-8")
    match = _VERSION_PATTERN.search(text)
    return text, (match.group(1) if match else "unknown")


@lru_cache(maxsize=1)
def _load_attribute_prompt() -> str:
    return ATTRIBUTE_PROMPT_FILE.read_text(encoding="utf-8")


def _target_brief(intake: IntakeFull) -> dict[str, Any]:
    """What we already know, so the model searches for the right company.

    Sector and line of business are the disambiguators: company names collide, and a
    search for "Meridian" alone will find the wrong business.
    """
    return {
        "company_name": intake.target.company_name,
        "website": intake.target.website,
        "sector": intake.target.sector,
        "line_of_business": intake.target.line_of_business,
        "hq_location": intake.target.hq_location,
        "founded_year": intake.target.founded_year,
        "business_model": intake.target.business_model,
        "headcount": intake.target.headcount,
        "known_tech_stack": intake.technology.known_tech_stack,
    }


def _strip_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _extract_sources(response: Any) -> list[ResearchSource]:
    """Pull the retrieved pages out of the SDK's grounding metadata.

    Shape (google-genai 2.x): candidates[].grounding_metadata.grounding_chunks[].web
    with `uri` and `title`. Defensive throughout — this is provider metadata, not our
    own schema, and a shape change must degrade to "no sources" rather than raise.
    """
    sources: list[ResearchSource] = []
    seen: set[str] = set()

    for candidate in getattr(response, "candidates", None) or []:
        metadata = getattr(candidate, "grounding_metadata", None)
        for chunk in getattr(metadata, "grounding_chunks", None) or []:
            web = getattr(chunk, "web", None)
            uri = getattr(web, "uri", None)
            if not uri or uri in seen:
                continue
            seen.add(uri)
            title = getattr(web, "title", None) or uri
            sources.append(
                ResearchSource(
                    id=f"S{len(sources) + 1}",
                    title=str(title),
                    url=str(uri),
                    publisher=getattr(web, "domain", None),
                )
            )
    return sources


BRIEF_SECTIONS = (
    "executive_summary",
    "what_they_do",
    "how_they_make_money",
    "customers_and_markets",
    "sector_context",
    "competitive_position",
    "technology_profile",
    "implications_for_diligence",
)


def _parse_brief(data: Any, valid_ids: set[str]) -> BusinessBrief | None:
    """Build the business brief from the model's JSON, defensively.

    Three things this does deliberately:

    * **A missing or malformed brief is `None`, never an error.** The findings and the
      summary are still worth storing, and an older prompt version simply will not return
      one. Refusing the whole run over a missing section would throw away good research.
    * **Citations are filtered to sources we actually hold**, exactly as findings are, so
      the UI can never render a dangling reference.
    * **A section the model returned as a placeholder is dropped.** Models asked to omit a
      section sometimes return "N/A" or "Not found in sources" instead of an empty string,
      which would render as content and read as a finding.
    """
    if not isinstance(data, dict):
        return None

    placeholder = {
        "n/a", "na", "none", "not found", "not available", "unknown",
        "not disclosed", "no information", "not found in sources", "-", "—",
    }

    sections: dict[str, BriefSection] = {}
    for name in BRIEF_SECTIONS:
        raw = data.get(name)
        if isinstance(raw, str):
            # Tolerated: the model sometimes flattens a section to a bare string.
            raw = {"text": raw}
        if not isinstance(raw, dict):
            continue
        text = str(raw.get("text") or "").strip()
        if not text or text.lower().rstrip(".") in placeholder:
            continue
        cited = [c for c in (raw.get("source_ids") or []) if c in valid_ids]
        sections[name] = BriefSection(text=text, source_ids=cited)

    if not sections:
        return None
    brief = BusinessBrief(**sections)
    return brief if brief.any_content else None


def _attribute(
    client: Any,
    settings: Settings,
    brief: BusinessBrief | None,
    findings: list[ResearchFinding],
    sources: list[ResearchSource],
) -> None:
    """Fill in `source_ids` on the brief and the findings, in place.

    Best-effort by design. Every failure path here leaves the run exactly as it was —
    uncited but complete — because a research note without per-claim links is degraded,
    while a research note that never got stored is lost.

    Only ids we actually hold survive, so a hallucinated `S99` is dropped the same way it
    is on the first pass.
    """
    claims: dict[str, str] = {}
    if brief is not None:
        for name in BRIEF_SECTIONS:
            text = getattr(brief, name).text.strip()
            if text:
                claims[f"brief:{name}"] = text
    for index, finding in enumerate(findings):
        claims[f"finding:{index}"] = f"{finding.topic} — {finding.detail}"

    if not claims or not sources:
        return

    request = {
        "sources": [
            {"id": s.id, "title": s.title, "url": s.url, "publisher": s.publisher}
            for s in sources
        ],
        "brief": {
            key.split(":", 1)[1]: text
            for key, text in claims.items()
            if key.startswith("brief:")
        },
        "findings": {
            key.split(":", 1)[1]: text
            for key, text in claims.items()
            if key.startswith("finding:")
        },
    }

    contents = (
        f"{_load_attribute_prompt()}\n\n## The note and its sources\n\n"
        f"```json\n{json.dumps(request, indent=2, default=str)}\n```"
    )

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config={
                "temperature": 0.0,
                "max_output_tokens": settings.llm_max_tokens,
                # No search tool on this pass, so JSON output can be forced.
                "response_mime_type": "application/json",
            },
        )
        data = json.loads(_strip_fences(response.text or ""))
    except Exception as exc:  # noqa: BLE001 - attribution must never lose the research
        logger.warning(
            "Source attribution failed (%s: %s); storing the research uncited.",
            type(exc).__name__,
            exc,
        )
        return

    if not isinstance(data, dict):
        return

    valid = {s.id for s in sources}

    def cited(raw: Any) -> list[str]:
        if not isinstance(raw, list):
            return []
        # Deduplicated and capped: a claim citing every source says as little as one
        # citing none, and the prompt asks for one to three.
        out: list[str] = []
        for item in raw:
            if isinstance(item, str) and item in valid and item not in out:
                out.append(item)
        return out[:4]

    raw_brief = data.get("brief")
    brief_map: dict[str, Any] = raw_brief if isinstance(raw_brief, dict) else {}
    if brief is not None:
        for name in BRIEF_SECTIONS:
            section = getattr(brief, name)
            if section.text.strip():
                section.source_ids = cited(brief_map.get(name))

    raw_findings = data.get("findings")
    finding_map: dict[str, Any] = raw_findings if isinstance(raw_findings, dict) else {}
    for index, finding in enumerate(findings):
        finding.source_ids = cited(finding_map.get(str(index)))

    attributed = sum(1 for f in findings if f.source_ids)
    logger.info("Attributed %d of %d findings to sources", attributed, len(findings))


class CompanyResearcher:
    """Runs one grounded research pass over the target."""

    name = "llm+search"

    def __init__(self, settings: Settings | None = None, client: Any | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = client

    @property
    def available(self) -> bool:
        return bool(self._settings.gemini_api_key)

    def _get_client(self) -> Any:
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._settings.gemini_api_key)
        return self._client

    def research(self, intake: IntakeFull) -> ResearchPayload:
        if not self.available:
            raise ResearchUnavailable(
                "Company research needs a Gemini API key. Set GEMINI_API_KEY to enable it."
            )

        company = intake.target.company_name
        if not company:
            raise ResearchRejected(
                "The intake has no target company name, so there is nothing to research."
            )

        prompt, prompt_version = _load_prompt()
        brief = json.dumps(_target_brief(intake), indent=2, default=str)
        contents = f"{prompt}\n\n## The target\n\n```json\n{brief}\n```"

        from google.genai import types

        try:
            response = self._get_client().models.generate_content(
                model=self._settings.gemini_model,
                contents=contents,
                config={
                    "temperature": self._settings.llm_temperature,
                    "max_output_tokens": self._settings.llm_max_tokens,
                    # No response_mime_type here: the search tool and forced JSON output
                    # are mutually exclusive on this API, so the JSON is parsed out of
                    # the text instead.
                    "tools": [types.Tool(google_search=types.GoogleSearch())],
                },
            )
        except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a clean error
            raise ResearchUnavailable(f"{type(exc).__name__}: {exc}") from exc

        sources = _extract_sources(response)
        if not sources:
            raise ResearchRejected(
                "The model returned no web sources, so the result cannot be grounded. "
                "Research is refused rather than stored without citations."
            )

        text = _strip_fences(response.text or "")
        if not text:
            raise ResearchRejected("the model returned an empty response")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ResearchRejected(f"response was not valid JSON: {exc}") from exc

        summary = str(data.get("summary") or "").strip()
        if not summary:
            raise ResearchRejected("the model returned no summary")

        valid_ids = {s.id for s in sources}
        findings: list[ResearchFinding] = []
        for raw in data.get("findings") or []:
            if not isinstance(raw, dict):
                continue
            topic = str(raw.get("topic") or "").strip()
            detail = str(raw.get("detail") or "").strip()
            if not topic or not detail:
                continue
            # The model cites loosely; keep only ids matching a source we actually have,
            # so the UI never renders a dangling citation.
            cited = [c for c in (raw.get("source_ids") or []) if c in valid_ids]
            findings.append(
                ResearchFinding.model_validate(
                    {
                        "topic": topic,
                        "detail": detail,
                        "category": str(raw.get("category") or "other"),
                        "source_ids": cited,
                    }
                )
            )

        business_brief = _parse_brief(data.get("business_brief"), valid_ids)

        # Second pass: the model could not cite ids that did not exist when it wrote.
        _attribute(self._get_client(), self._settings, business_brief, findings, sources)

        if business_brief is None:
            logger.warning(
                "Research for %s returned no usable business brief; storing the summary "
                "and findings alone.",
                company,
            )

        return ResearchPayload(
            generator=self.name,
            prompt_version=prompt_version,
            company_name=company,
            summary=summary,
            business_brief=business_brief,
            findings=findings,
            sources=sources,
            disclaimer=RESEARCH_DISCLAIMER,
            researched_at=datetime.now(UTC),
        )
