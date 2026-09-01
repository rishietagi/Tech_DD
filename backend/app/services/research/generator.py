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
    ResearchFinding,
    ResearchPayload,
    ResearchSource,
)

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "research.md"
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

        return ResearchPayload(
            generator=self.name,
            prompt_version=prompt_version,
            company_name=company,
            summary=summary,
            findings=findings,
            sources=sources,
            disclaimer=RESEARCH_DISCLAIMER,
            researched_at=datetime.now(UTC),
        )
