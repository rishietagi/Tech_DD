"""Prose over a computed estate result — never a number (D4, PHASE6_PLAN §1).

The ±1 step refinement Rishi allowed on 2026-09-02 is specific to business processes and
is deliberately **not** extended here. The model writes the executive summary and the
pointers; everything it is shown is already decided. A rules summary is always produced
first, so a failed or absent model leaves a usable — if terser — write-up.
"""

import json
import logging
import re
from functools import lru_cache
from typing import Any

from app.core.config import Settings, get_settings
from app.schemas.estate import Gap, LlmEstateSummary
from app.services.intelligence.skills import skill_text

logger = logging.getLogger(__name__)

_MAX_POINTERS = 5
DOMAIN_LABELS = {
    "applications": "application assessment",
    "data_tech": "data and technology assessment",
}


@lru_cache(maxsize=1)
def _prompt() -> str:
    return skill_text("estate-summary")


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
    return cleaned.strip()


def _plain(text: str) -> str:
    """Strip the markdown a model adds anyway. The screen renders text, not markdown, and
    `**SAP ECC 6.0:**` would show its asterisks (the leak recorded in PROJECT_LOG)."""
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    cleaned = re.sub(r"(?<!\w)\*(\S.*?\S|\S)\*(?!\w)", r"\1", cleaned)
    cleaned = re.sub(r"^\s*[-•]\s+", "", cleaned)
    return cleaned.replace("`", "").strip()


# ------------------------------------------------------------------ the rules floor


def rules_summary(domain: str, payload: dict[str, Any], gaps: list[Gap]) -> tuple[str, list[str]]:
    """A terse, fully deterministic write-up. Always computed; the model may replace it."""
    high = [g for g in gaps if g.severity == "High"]
    sentences: list[str] = []
    if domain == "applications":
        counts = payload["counts"]
        if not counts["applications"]:
            return "No applications are in the inventory yet.", []
        dispositions = ", ".join(
            f"{n} {d.lower()}" for d, n in sorted(counts["by_disposition"].items(), key=lambda kv: -kv[1])
        )
        sentences.append(
            f"{counts['applications']} applications are inventoried and {counts['assessed']} "
            f"have a disposition ({dispositions})."
        )
        if payload.get("index") is not None:
            sentences.append(
                f"The criticality-weighted automation index is {payload['index']:.0f}/100 "
                f"({payload['band_label']})."
            )
        flags = []
        if counts["high_debt"]:
            flags.append(f"{counts['high_debt']} carry high technical debt")
        if counts["spof"]:
            flags.append(f"{counts['spof']} are single points of failure")
        if counts["scalability_risk"]:
            flags.append(f"{counts['scalability_risk']} are at risk at peak load")
        if flags:
            sentences.append("Of these, " + ", ".join(flags) + ".")
    else:
        scored = [s for s in payload["sections"] if s["score"] is not None]
        if payload.get("index") is not None:
            sentences.append(
                f"The data and technology index is {payload['index']:.0f}/100 "
                f"({payload['band_label']}), across {len(scored)} of "
                f"{len(payload['sections'])} sections with evidence."
            )
        else:
            sentences.append("No data and technology evidence has been recorded yet.")
        weakest = min(scored, key=lambda s: s["score"], default=None)
        if weakest is not None:
            sentences.append(f"The weakest section is {weakest['label'].lower()} at {weakest['score']:.0f}/100.")
    if high:
        sentences.append(
            f"{len(high)} high-severity gap{'s' if len(high) != 1 else ''}: "
            + "; ".join(g.title for g in high[:4])
            + ("…" if len(high) > 4 else "")
            + "."
        )
    if payload.get("coverage_note"):
        sentences.append(payload["coverage_note"])
    pointers = [f"{g.display_id} — {g.title}: {g.findings[0]}" for g in high[:_MAX_POINTERS]]
    return " ".join(sentences), pointers


# ------------------------------------------------------------------ the model


def _evidence(domain: str, payload: dict[str, Any], remarks: list[dict[str, str]]) -> dict[str, Any]:
    trimmed = {k: v for k, v in payload.items() if k not in ("executive_summary", "pointers")}
    trimmed["gaps"] = [
        {
            "id": g["display_id"],
            "title": g["title"],
            "severity": g["severity"],
            "findings": g["findings"],
        }
        for g in payload.get("gaps", [])
    ]
    return {"domain": domain, "result": trimmed, "consultant_remarks": remarks}


class EstateSummariser:
    def __init__(self, settings: Settings | None = None, client: Any | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = client

    @property
    def available(self) -> bool:
        return bool(self._settings.gemini_api_key) or self._client is not None

    def _get_client(self) -> Any:
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._settings.gemini_api_key)
        return self._client

    def summarise(self, domain: str, payload: dict[str, Any], remarks: list[dict[str, str]]) -> LlmEstateSummary | None:
        """The model's summary, or None — the caller keeps the rules summary on None."""
        if not self.available:
            return None
        prompt = _prompt().replace("{domain_label}", DOMAIN_LABELS.get(domain, domain))
        contents = (
            f"{prompt}\n\n## This assessment\n\n```json\n"
            f"{json.dumps(_evidence(domain, payload, remarks), indent=1, default=str)}\n```"
        )
        try:
            response = self._get_client().models.generate_content(
                model=self._settings.gemini_model,
                contents=contents,
                config={
                    "temperature": self._settings.llm_temperature,
                    "max_output_tokens": self._settings.llm_max_tokens,
                    "response_mime_type": "application/json",
                },
            )
            data = json.loads(_strip_fences(response.text or ""))
            summary = LlmEstateSummary.model_validate(data)
        except Exception as exc:  # noqa: BLE001 - any failure falls back to the rules text
            logger.warning("Estate summary fell back to rules (%s).", exc)
            return None
        if len(summary.executive_summary.strip()) < 40:
            logger.warning("Estate summary too short to use; kept the rules summary.")
            return None
        summary.executive_summary = _plain(summary.executive_summary)
        summary.pointers = [_plain(p) for p in summary.pointers if p.strip()][:_MAX_POINTERS]
        return summary
