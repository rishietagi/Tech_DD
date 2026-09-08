"""LLM layer for process assessment scoring.

This module makes a deliberate, recorded exception to the platform's usual split. Every
other module lets the model write prose only; here it may also **refine step scores**,
because the multiple-choice answers alone cannot see that an analyst chose "configured
3-way matching" and then noted the tolerances make it meaningless.

Rishi asked for this explicitly on 2026-09-02, knowing the trade: a refined index is no
longer perfectly reproducible from the answers. The cost is contained rather than
accepted wholesale:

* the **deterministic score is always computed and always stored** alongside the refined
  one, on the payload and on every step;
* an adjustment may move a step by **at most ±1** and must carry a reason;
* an adjustment to an unassessed step, or one without a reason, is **rejected**;
* rejection is per-adjustment, not per-response — one bad refinement does not throw away
  a good summary.

So a reader always sees that the model moved a step from 2 to 3, and why, and can put the
deterministic number back by reading it off the same page.
"""

import json
import logging
import re
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.schemas.assess import (
    BAND_LABELS,
    BAND_MEANINGS,
    AssessmentScorePayload,
    ProcessQuestionnaire,
    ScorePointer,
    band_for_index,
    level_label_for,
)
from app.services.assess.scoring import compute_index, score_assessment

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "scoring.md"
_VERSION_PATTERN = re.compile(r"prompt_version:\s*([0-9.]+)")

# The model may move a step by at most this much. Larger disagreement means the answers
# are wrong, which is a probe for the analyst rather than a silent adjustment.
_MAX_ADJUSTMENT = 1.0
# Adjusting more than this many steps means the model is second-guessing the ladder
# rather than reading evidence. The whole refinement set is dropped.
_MAX_REFINED_STEPS = 3
_MIN_REASON_CHARS = 20


class ScoringRejected(Exception):
    """The model's response could not be trusted. The deterministic score stands."""


class LlmStepRefinement(BaseModel):
    model_config = {"extra": "ignore"}

    step_key: str
    score: float = Field(ge=0, le=5)
    reason: str = ""


class LlmPointer(BaseModel):
    model_config = {"extra": "ignore"}

    kind: str = "probe"
    step_key: str | None = None
    text: str


class LlmScoring(BaseModel):
    model_config = {"extra": "ignore"}

    executive_summary: str
    shape_note: str | None = None
    step_refinements: list[LlmStepRefinement] = Field(default_factory=list)
    pointers: list[LlmPointer] = Field(default_factory=list)


@lru_cache(maxsize=1)
def _load_prompt() -> tuple[str, str]:
    text = PROMPT_FILE.read_text(encoding="utf-8")
    match = _VERSION_PATTERN.search(text)
    return text, (match.group(1) if match else "unknown")


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
    return cleaned.strip()


def _evidence_for_prompt(
    questionnaire: ProcessQuestionnaire,
    answers: dict[str, str],
    remarks: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """The analyst's answers, grouped by step, with the questions they answer.

    Unanswered questions are omitted rather than sent as blanks: a model shown thirty
    empty fields tends to comment on the emptiness instead of the evidence.
    """
    steps: list[dict[str, Any]] = []
    for step in questionnaire.steps:
        recorded: list[dict[str, Any]] = []
        for question in step.questions:
            value = (answers.get(question.id) or "").strip()
            remark = (remarks or {}).get(question.id, "").strip()
            if value or remark:
                entry: dict[str, Any] = {
                    "question": question.text,
                    "answer": value,
                    "scores": question.scores,
                }
                # The consultant's own note on what they were told. Often the only place
                # a volume, a system name or a caveat is recorded, so it is exactly what
                # makes the summary specific rather than generic.
                if remark:
                    entry["consultant_remarks"] = remark
                recorded.append(entry)
            for nudge in question.nudges:
                nudge_value = (answers.get(nudge.id) or "").strip()
                if nudge_value:
                    recorded.append(
                        {
                            "follow_up": nudge.ask,
                            "answer": nudge_value,
                            "scores": False,
                        }
                    )
        if recorded:
            steps.append(
                {
                    "step_key": step.key,
                    "title": step.title,
                    "weight": step.weight,
                    "intent": step.intent,
                    "recorded": recorded,
                }
            )
    return steps


def _deterministic_for_prompt(payload: AssessmentScorePayload) -> list[dict[str, Any]]:
    return [
        {
            "step_key": step.key,
            "title": step.title,
            "weight": step.weight,
            "deterministic_score": step.score,
            "assessed": step.assessed,
            "answered": step.answered,
            "scoreable": step.scoreable,
        }
        for step in payload.steps
    ]


def apply_refinements(
    payload: AssessmentScorePayload, refinements: list[LlmStepRefinement]
) -> tuple[AssessmentScorePayload, int]:
    """Apply the model's step adjustments, rejecting any that break the contract.

    Returns the payload and how many adjustments survived. The deterministic score is
    preserved on every step regardless, so nothing is lost by a refinement being applied.
    """
    if not refinements:
        return payload, 0

    if len(refinements) > _MAX_REFINED_STEPS:
        logger.warning(
            "Model tried to refine %d steps (limit %d); dropping all refinements.",
            len(refinements),
            _MAX_REFINED_STEPS,
        )
        return payload, 0

    by_key = {step.key: step for step in payload.steps}
    applied = 0

    for refinement in refinements:
        step = by_key.get(refinement.step_key)
        if step is None:
            logger.warning("Refinement names unknown step %r; ignored.", refinement.step_key)
            continue
        if not step.assessed or step.deterministic_score is None:
            logger.warning(
                "Refinement targets unassessed step %r; ignored — no evidence means no score.",
                refinement.step_key,
            )
            continue
        if len(refinement.reason.strip()) < _MIN_REASON_CHARS:
            logger.warning(
                "Refinement of %r carries no usable reason; ignored.", refinement.step_key
            )
            continue

        delta = refinement.score - step.deterministic_score
        if abs(delta) > _MAX_ADJUSTMENT + 1e-9:
            logger.warning(
                "Refinement of %r moves the score by %.1f, beyond the ±%.1f bound; ignored.",
                refinement.step_key,
                delta,
                _MAX_ADJUSTMENT,
            )
            continue
        if abs(delta) < 1e-9:
            continue

        step.score = round(refinement.score, 1)
        step.level_label = level_label_for(step.score)
        step.refined = True
        step.refinement_reason = refinement.reason.strip()
        step.reason = (
            f"{step.level_label} ({step.score}/5), adjusted from "
            f"{step.deterministic_score}/5 on the recorded evidence"
        )
        applied += 1

    if applied:
        payload.index = compute_index(payload.steps)
        payload.band = band_for_index(payload.index)
        payload.band_label = BAND_LABELS[payload.band]
        payload.band_meaning = BAND_MEANINGS[payload.band]

    return payload, applied


class RulesScoreGenerator:
    """The deterministic floor: the arithmetic and a terse written summary."""

    name = "rules"

    def score(
        self,
        questionnaire: ProcessQuestionnaire,
        answers: dict[str, str],
        context: dict[str, Any] | None = None,  # noqa: ARG002 - parity with the LLM path
        remarks: dict[str, str] | None = None,  # noqa: ARG002 - remarks never move a score
    ) -> AssessmentScorePayload:
        return score_assessment(questionnaire, answers)


class LlmScoreGenerator:
    """Deterministic arithmetic, model-written summary, bounded step refinement."""

    name = "llm"

    def __init__(self, settings: Settings | None = None, client: Any | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = client
        self._rules = RulesScoreGenerator()

    @property
    def available(self) -> bool:
        return bool(self._settings.gemini_api_key)

    def _get_client(self) -> Any:
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self._settings.gemini_api_key)
        return self._client

    def _request(
        self,
        questionnaire: ProcessQuestionnaire,
        answers: dict[str, str],
        deterministic: AssessmentScorePayload,
        context: dict[str, Any] | None,
        remarks: dict[str, str] | None = None,
    ) -> LlmScoring:
        prompt, _ = _load_prompt()
        request_payload: dict[str, Any] = {
            "process": {
                "key": questionnaire.process_key,
                "name": questionnaire.name,
                "description": questionnaire.description,
            },
            "engagement": context or {},
            "deterministic": {
                "index": deterministic.index,
                "band": deterministic.band_label,
                "coverage_note": deterministic.coverage_note,
                "steps": _deterministic_for_prompt(deterministic),
            },
            "evidence": _evidence_for_prompt(questionnaire, answers, remarks),
        }
        contents = (
            f"{prompt}\n\n## This assessment\n\n"
            f"```json\n{json.dumps(request_payload, indent=2, default=str)}\n```"
        )

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
            raise ScoringRejected("model returned an empty response")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ScoringRejected(f"response was not valid JSON: {exc}") from exc

        try:
            return LlmScoring.model_validate(data)
        except Exception as exc:
            raise ScoringRejected(f"response did not match the required shape: {exc}") from exc

    def score(
        self,
        questionnaire: ProcessQuestionnaire,
        answers: dict[str, str],
        context: dict[str, Any] | None = None,
        remarks: dict[str, str] | None = None,
    ) -> AssessmentScorePayload:
        _, prompt_version = _load_prompt()
        payload = score_assessment(questionnaire, answers)

        def fallback(reason: str) -> AssessmentScorePayload:
            payload.generator = reason
            return payload

        if not self.available:
            logger.warning("GEMINI_API_KEY is not set; returning the deterministic score.")
            return fallback("rules (llm unavailable)")

        # Nothing answered means nothing to summarise. Calling the model here would spend
        # a request to have it observe the questionnaire is empty.
        if payload.questions_scored == 0:
            return fallback("rules (nothing assessed)")

        try:
            scoring = self._request(questionnaire, answers, payload, context, remarks)
        except ScoringRejected as exc:
            logger.warning("Scoring narrative rejected (%s); keeping the deterministic score.", exc)
            return fallback("rules (llm rejected)")
        except Exception as exc:  # noqa: BLE001 - the model must never break scoring
            logger.warning(
                "Scoring narrative failed (%s: %s); keeping the deterministic score.",
                type(exc).__name__,
                exc,
            )
            return fallback("rules (llm error)")

        payload, applied = apply_refinements(payload, scoring.step_refinements)

        summary = scoring.executive_summary.strip()
        if summary:
            payload.executive_summary = summary
        if scoring.shape_note and scoring.shape_note.strip():
            payload.shape_note = scoring.shape_note.strip()

        valid_kinds = {"gap", "strength", "probe"}
        pointers = [
            ScorePointer(
                kind=p.kind if p.kind in valid_kinds else "probe",
                step_key=p.step_key,
                text=p.text.strip(),
            )
            for p in scoring.pointers
            if p.text and p.text.strip()
        ]
        if pointers:
            payload.pointers = pointers

        payload.generator = self.name
        payload.generated_at = datetime.now(UTC)
        if applied:
            logger.info("Model refined %d step score(s) within the ±1 bound.", applied)
        return payload
