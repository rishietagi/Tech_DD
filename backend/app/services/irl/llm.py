"""LlmIrlGenerator — turns seeds into a client-ready request list.

Same split as the scope engine: the rules decide *coverage* (which seeds exist, and
therefore which scope areas get asked about), the model decides *wording* and adds the
non-technology functions a tech scope never reaches.

Where this differs from `services/scope/llm.py`: the model is allowed to **add**
questions here, because an IRL that only asks what a technology scope covers is not a
real IRL. What it may not do is drop or invent a seed — every seed id must come back
exactly once. That is the structural contract, and any breach discards the whole
response in favour of the deterministic list.

The model is given the **company research and the engagement context** as input, not
just the seeds. That is what lets it name functions that fit the actual business and ask
about incidents that actually happened.
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
from app.schemas.irl import (
    IrlPayload,
    IrlQuestion,
    IrlTailoringRejected,
    LlmIrl,
)
from app.schemas.research import ResearchPayload
from app.schemas.scope import ScopeOfWorkPayloadV2
from app.services.irl.composer import compose_irl, group_functions
from app.services.irl.seeds import SeedRequest, build_seeds

logger = logging.getLogger(__name__)

PROMPT_FILE = Path(__file__).resolve().parent / "prompts" / "irl.md"
_VERSION_PATTERN = re.compile(r"prompt_version:\s*([0-9.]+)")

# Guard rails on the model's own additions. Too few and the non-tech functions go
# uncovered; too many and the target is buried. The prompt asks for 8-20.
_MAX_ADDED_QUESTIONS = 40
_MAX_FUNCTIONS = 16


@lru_cache(maxsize=1)
def _load_prompt() -> tuple[str, str]:
    text = PROMPT_FILE.read_text(encoding="utf-8")
    match = _VERSION_PATTERN.search(text)
    return text, (match.group(1) if match else "unknown")


def _engagement_context(intake: IntakeFull) -> dict[str, Any]:
    """The deal and the target, so requests can be specific rather than generic."""
    return {
        "deal_context": intake.context.context_narrative,
        "deal_rationale": intake.rationale.rationale_narrative,
        "focus_areas": intake.rationale.focus_areas,
        "deal_breakers": intake.rationale.deal_breakers,
        "investment_type": intake.structure.investment_type,
        "stake": intake.structure.stake,
        "post_close_intent": intake.structure.post_close_intent,
        "company_name": intake.target.company_name,
        "sector": intake.target.sector,
        "line_of_business": intake.target.line_of_business,
        "business_model": intake.target.business_model,
        "headcount": intake.target.headcount,
        "known_tech_stack": intake.technology.known_tech_stack,
        "core_systems": intake.technology.core_systems,
        "hosting_model": intake.technology.hosting_model,
        "data_sensitivity": intake.technology.data_sensitivity,
        "compliance_regimes": intake.technology.compliance_regimes,
        "known_incidents": intake.technology.known_incidents,
    }


def _research_context(research: ResearchPayload | None) -> dict[str, Any] | None:
    """The research summary and findings, trimmed to what shapes the questions."""
    if research is None:
        return None
    return {
        "summary": research.summary,
        "findings": [
            {"topic": f.topic, "category": f.category, "detail": f.detail}
            for f in research.findings
        ],
    }


def _seeds_for_prompt(seeds: list[SeedRequest]) -> list[dict[str, Any]]:
    return [
        {
            "seed_id": seed.id,
            "evidence": seed.text,
            "scope_area": seed.row_title,
        }
        for seed in seeds
    ]


def _strip_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def validate_irl(tailoring: LlmIrl, seeds: list[SeedRequest]) -> None:
    """Diff the model's output against the seeds. Raises IrlTailoringRejected.

    The contract: every seed id back exactly once, no unknown seed ids, and the model's
    own additions kept within sane bounds.
    """
    if not tailoring.intro.strip():
        raise IrlTailoringRejected("intro is empty")
    if not tailoring.questions:
        raise IrlTailoringRejected("no questions returned")

    seed_ids = {seed.id for seed in seeds}
    returned = [q.seed_id for q in tailoring.questions if q.seed_id]

    unknown = set(returned) - seed_ids
    if unknown:
        raise IrlTailoringRejected(f"unknown seed ids returned: {sorted(unknown)}")

    missing = seed_ids - set(returned)
    if missing:
        raise IrlTailoringRejected(f"seed ids dropped: {sorted(missing)}")

    duplicates = {sid for sid in returned if returned.count(sid) > 1}
    if duplicates:
        raise IrlTailoringRejected(f"seed ids returned more than once: {sorted(duplicates)}")

    added = [q for q in tailoring.questions if not q.seed_id]
    if len(added) > _MAX_ADDED_QUESTIONS:
        raise IrlTailoringRejected(
            f"model added {len(added)} questions, more than the {_MAX_ADDED_QUESTIONS} allowed"
        )

    for question in tailoring.questions:
        if not question.question.strip():
            raise IrlTailoringRejected("a question is empty")
        if not question.function.strip():
            raise IrlTailoringRejected("a question has no function")

    functions = {q.function.strip() for q in tailoring.questions}
    if len(functions) > _MAX_FUNCTIONS:
        raise IrlTailoringRejected(
            f"{len(functions)} distinct functions, more than the {_MAX_FUNCTIONS} allowed"
        )


def apply_irl(
    tailoring: LlmIrl,
    seeds: list[SeedRequest],
    company_name: str | None,
    source_scope_version: int | None,
    used_research: bool,
    generator: str,
    prompt_version: str | None,
) -> IrlPayload:
    """Build the payload from validated model output, keeping seed provenance."""
    by_id = {seed.id: seed for seed in seeds}
    questions: list[IrlQuestion] = []

    for index, item in enumerate(tailoring.questions, start=1):
        function = item.function.strip()
        text = item.question.strip()

        if item.seed_id:
            seed = by_id[item.seed_id]
            questions.append(
                IrlQuestion(
                    id=seed.id,
                    function=function,
                    question=text,
                    source="scope",
                    source_row_id=seed.row_id,
                    source_row_title=seed.row_title,
                    seed_text=seed.text,
                )
            )
        else:
            # Model-added: no scope row behind it, and marked as such so a reviewer can
            # tell rule-derived requests from generated ones.
            questions.append(
                IrlQuestion(
                    id=f"ADD-{index:03d}",
                    function=function,
                    question=text,
                    source="llm",
                )
            )

    return IrlPayload(
        generator=generator,
        prompt_version=prompt_version,
        company_name=company_name,
        source_scope_version=source_scope_version,
        used_research=used_research,
        intro=tailoring.intro.strip(),
        questions=questions,
        functions=group_functions(questions),
        generated_at=datetime.now(UTC),
    )


class RulesIrlGenerator:
    """The deterministic floor: seeds, wrapped as requests, grouped by function."""

    name = "rules"

    def generate(
        self,
        intake: IntakeFull,
        scope: ScopeOfWorkPayloadV2,
        research: ResearchPayload | None = None,  # noqa: ARG002 - parity with the LLM path
        source_scope_version: int | None = None,
    ) -> IrlPayload:
        seeds = build_seeds(scope)
        return compose_irl(
            seeds=seeds,
            company_name=intake.target.company_name,
            source_scope_version=source_scope_version,
        )


class LlmIrlGenerator:
    """Seeds plus model-authored wording, with fallback on any failure."""

    name = "llm"

    def __init__(self, settings: Settings | None = None, client: Any | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = client
        self._rules = RulesIrlGenerator()

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
        seeds: list[SeedRequest],
        intake: IntakeFull,
        research: ResearchPayload | None,
        previous_functions: list[str] | None,
    ) -> LlmIrl:
        prompt, _ = _load_prompt()
        payload: dict[str, Any] = {
            "engagement": _engagement_context(intake),
            "research": _research_context(research),
            "previous_functions": previous_functions or [],
            "seeds": _seeds_for_prompt(seeds),
        }
        contents = (
            f"{prompt}\n\n## This engagement\n\n"
            f"```json\n{json.dumps(payload, indent=2, default=str)}\n```"
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
            raise IrlTailoringRejected("model returned an empty response")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise IrlTailoringRejected(f"response was not valid JSON: {exc}") from exc

        try:
            return LlmIrl.model_validate(data)
        except Exception as exc:
            raise IrlTailoringRejected(f"response did not match the required shape: {exc}") from exc

    def generate(
        self,
        intake: IntakeFull,
        scope: ScopeOfWorkPayloadV2,
        research: ResearchPayload | None = None,
        source_scope_version: int | None = None,
        previous_functions: list[str] | None = None,
    ) -> IrlPayload:
        _, prompt_version = _load_prompt()
        seeds = build_seeds(scope)

        def fallback(reason: str) -> IrlPayload:
            payload = self._rules.generate(intake, scope, research, source_scope_version)
            payload.generator = reason
            payload.prompt_version = prompt_version
            return payload

        if not self.available:
            logger.warning("GEMINI_API_KEY is not set; returning the deterministic IRL.")
            return fallback("rules (llm unavailable)")

        try:
            tailoring = self._request(seeds, intake, research, previous_functions)
            validate_irl(tailoring, seeds)
            return apply_irl(
                tailoring,
                seeds,
                company_name=intake.target.company_name,
                source_scope_version=source_scope_version,
                used_research=research is not None,
                generator=self.name,
                prompt_version=prompt_version,
            )

        except IrlTailoringRejected as exc:
            logger.warning("IRL tailoring rejected (%s); shipping the deterministic list.", exc)
            return fallback("rules (llm tailoring rejected)")

        except Exception as exc:  # noqa: BLE001 - the model must never break generation
            logger.warning(
                "IRL tailoring failed (%s: %s); shipping the deterministic list.",
                type(exc).__name__,
                exc,
            )
            return fallback("rules (llm error)")
