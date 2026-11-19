"""Prose over the deterministic report — never a decision (Phase 7, Part D).

Three skills, each optional, each validated after the call and discarded on any breach:

* `report-executive-summary` rewrites each finding's headline, bullets and implication. It
  is not shown, and cannot change, the risk level, the actions or the investment cell.
* `report-narrative` rewrites the context paragraphs and supporting-section side panels.
* `budget-commentary` rewrites the IT budget side panel.

The one rule checked on every rewrite: **every number in the new text must already appear
in the text it replaces.** A model that writes "three of five" where the rules wrote
"2 of 5" has invented a fact, and the deterministic text is kept.
"""

import json
import logging
import re
from typing import Any

from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.schemas.report import LlmExecutive, LlmNarrative, ReportPayload
from app.services.intelligence.skills import get_skill, skill_text

logger = logging.getLogger(__name__)

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def _numbers(text: str) -> set[str]:
    return {n.replace(",", "") for n in _NUMBER.findall(text)}


def numbers_preserved(original: str, rewritten: str) -> bool:
    return _numbers(rewritten) <= _numbers(original)


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
    return cleaned.strip()


def _plain(text: str) -> str:
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    return cleaned.replace("`", "").strip()


class ReportWriter:
    def __init__(self, settings: Settings | None = None, client: Any | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = client

    def _get_client(self) -> Any:
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._settings.gemini_api_key)
        return self._client

    def _call(self, skill: str, data: dict[str, Any], model: type[BaseModel]) -> Any:
        contents = f"{skill_text(skill)}\n\n## Input\n\n```json\n{json.dumps(data, indent=1, default=str)}\n```"
        response = self._get_client().models.generate_content(
            model=self._settings.gemini_model,
            contents=contents,
            config={
                "temperature": self._settings.llm_temperature,
                "max_output_tokens": self._settings.llm_max_tokens,
                "response_mime_type": "application/json",
            },
        )
        return model.model_validate(json.loads(_strip_fences(response.text or "")))

    # ------------------------------------------------------------------ executive

    def executive(self, payload: ReportPayload) -> int:
        """Rewrite finding headlines, bullets and implications in place. Returns findings changed.

        The model never sees, and cannot change, a finding's risk, its area, its actions or
        the investment cell; a rewrite that adds a bullet or a number is discarded.
        """
        findings = {f.key: f for r in payload.executive if r.include for f in r.findings if f.include}
        if not findings:
            return 0
        data = {
            "target": payload.target_name,
            "dd_type": payload.dd_type,
            "findings": [
                {"key": f.key, "headline": f.headline, "bullets": f.bullets, "implication": f.implication}
                for f in findings.values()
            ],
        }
        try:
            result: LlmExecutive = self._call("report-executive-summary", data, LlmExecutive)
        except Exception as exc:  # noqa: BLE001 - the deterministic text stands
            logger.warning("Executive summary rewrite failed (%s); rules text kept.", exc)
            return 0
        changed = 0
        for new in result.findings:
            finding = findings.get(new.key)
            if finding is None or not new.bullets or not new.headline.strip():
                continue
            original = " ".join([finding.headline, *finding.bullets, finding.implication])
            rewritten = " ".join([new.headline, *new.bullets, new.implication])
            if len(new.bullets) > len(finding.bullets) or not numbers_preserved(original, rewritten):
                logger.warning("Rewrite of %s rejected: added bullets or numbers.", finding.key)
                continue
            finding.headline = _plain(new.headline)
            finding.bullets = [_plain(b) for b in new.bullets if b.strip()]
            finding.implication = _plain(new.implication) or finding.implication
            changed += 1
        return changed

    # ------------------------------------------------------------------ narrative

    def narrative(self, payload: ReportPayload) -> int:
        panels = {s.id: s.panel for s in payload.supporting if s.panel and s.id != "budget"}
        data = {
            "target": payload.target_name,
            "investor": payload.investor_name,
            "context": {
                "objective": payload.context.objective,
                "approach": payload.context.approach,
                "outcome": payload.context.outcome,
            },
            "panels": panels,
        }
        try:
            result: LlmNarrative = self._call("report-narrative", data, LlmNarrative)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Narrative rewrite failed (%s); rules text kept.", exc)
            return 0
        changed = 0
        for field in ("objective", "approach", "outcome"):
            new = getattr(result, field)
            old = getattr(payload.context, field)
            names = [n for n in (payload.target_name, payload.investor_name) if n and n in old]
            if new and numbers_preserved(old, new) and all(n in new for n in names):
                setattr(payload.context, field, _plain(new))
                changed += 1
        for section in payload.supporting:
            new = result.panels.get(section.id)
            if new and section.id in panels and numbers_preserved(section.panel, new):
                section.panel = _plain(new)
                changed += 1
        return changed

    def budget(self, payload: ReportPayload) -> int:
        section = next((s for s in payload.supporting if s.id == "budget"), None)
        if section is None or not section.panel:
            return 0
        data = {
            "panel": section.panel,
            "blocks": [b.model_dump(include={"title", "columns", "rows", "items"}) for b in section.blocks],
        }
        try:
            result: LlmNarrative = self._call("budget-commentary", data, LlmNarrative)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Budget commentary failed (%s); rules text kept.", exc)
            return 0
        new = result.panels.get("budget")
        source = section.panel + " " + json.dumps(data["blocks"])
        # The boundary: revenue never appears, and "benchmark" only where the rules text
        # already used it (to say the section does NOT benchmark).
        crosses = (
            "revenue" in new.lower() or ("benchmark" in new.lower() and "benchmark" not in section.panel.lower())
            if new
            else True
        )
        if new and numbers_preserved(source, new) and not crosses:
            section.panel = _plain(new)
            return 1
        return 0


def skill_versions(names: list[str]) -> dict[str, str]:
    return {n: get_skill(n).version for n in names}
