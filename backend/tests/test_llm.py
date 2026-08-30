"""The LLM tailoring layer.

Every test mocks the client. The spec forbids live API calls in tests, and a test that
depends on a model's wording is not a test.
"""

import json
from typing import Any

import pytest

from app.core.config import Settings
from app.schemas.tailoring import LlmTailoring, TailoringRejected
from app.services.scope.llm import (
    LlmScopeGenerator,
    apply_tailoring,
    validate_tailoring,
)
from app.services.scope.rules_generator import RulesScopeGenerator
from tests.factories import make_intake

INTAKE = dict(
    company_name="Meridian Analytics",
    line_of_business="Sells a usage-based analytics platform to mid-market e-commerce retailers.",
    dd_type_preference="Product Tech DD",
    tech_is_product="Yes, the software is the product",
    digital_maturity="Digital native",
)


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeModels:
    def __init__(self, payload: str | Exception) -> None:
        self._payload = payload
        self.calls = 0

    def generate_content(self, **kwargs: Any) -> FakeResponse:  # noqa: ARG002 - fake mirrors the real signature
        self.calls += 1
        if isinstance(self._payload, Exception):
            raise self._payload
        return FakeResponse(self._payload)


class FakeClient:
    def __init__(self, payload: str | Exception) -> None:
        self.models = FakeModels(payload)


def settings_with_key() -> Settings:
    return Settings(gemini_api_key="test-key-not-real", gemini_model="gemini-2.5-flash")


def base_scope():
    return RulesScopeGenerator().generate(make_intake(**INTAKE))


def faithful_tailoring(scope) -> dict[str, Any]:
    """A well-formed response that respects the skeleton."""
    return {
        "engagement_summary": "Meridian Analytics operates a usage-based analytics platform.",
        "rows": [
            {
                "row_id": row.id,
                "title": f"{row.title} (tailored)",
                "lines": [
                    {"index": i, "text": f"Review the analytics platform: {line.text}"}
                    for i, line in enumerate(row.lines)
                ],
            }
            for row in scope.rows
        ],
    }


def generator_for(payload: str | Exception) -> LlmScopeGenerator:
    return LlmScopeGenerator(settings=settings_with_key(), client=FakeClient(payload))


# ----------------------------------------------------------------------- happy path


def test_valid_tailoring_is_applied() -> None:
    scope = base_scope()
    generator = generator_for(json.dumps(faithful_tailoring(scope)))
    result = generator.generate(make_intake(**INTAKE))

    assert result.generator == "llm"
    assert result.prompt_version
    assert "Meridian Analytics" in result.engagement_summary
    assert all("(tailored)" in row.title for row in result.rows)


def test_tailoring_never_changes_structure() -> None:
    """The model rewrites wording; depth, evidence and provenance are the engine's."""
    scope = base_scope()
    generator = generator_for(json.dumps(faithful_tailoring(scope)))
    result = generator.generate(make_intake(**INTAKE))

    assert [r.id for r in result.rows] == [r.id for r in scope.rows]
    assert [r.tier for r in result.rows] == [r.tier for r in scope.rows]
    assert [r.evidence_requests for r in result.rows] == [r.evidence_requests for r in scope.rows]
    assert result.classification.dd_mix == scope.classification.dd_mix
    assert len(result.provenance) == len(scope.provenance)
    assert result.exclusions == scope.exclusions


def test_response_wrapped_in_code_fences_is_still_accepted() -> None:
    scope = base_scope()
    fenced = f"```json\n{json.dumps(faithful_tailoring(scope))}\n```"
    result = generator_for(fenced).generate(make_intake(**INTAKE))
    assert result.generator == "llm"


def test_identical_requests_are_cached() -> None:
    scope = base_scope()
    generator = generator_for(json.dumps(faithful_tailoring(scope)))

    generator.generate(make_intake(**INTAKE))
    generator.generate(make_intake(**INTAKE))

    assert generator._client.models.calls == 1, "re-opening a scope must not re-bill"


# ------------------------------------------------------------------------ rejection


def test_added_row_is_rejected() -> None:
    scope = base_scope()
    payload = faithful_tailoring(scope)
    payload["rows"].append({"row_id": "PD-99", "title": "Invented", "lines": []})

    result = generator_for(json.dumps(payload)).generate(make_intake(**INTAKE))
    assert result.generator == "rules (llm tailoring rejected)"
    assert not any(r.id == "PD-99" for r in result.rows)


def test_dropped_row_is_rejected() -> None:
    scope = base_scope()
    payload = faithful_tailoring(scope)
    payload["rows"].pop()

    result = generator_for(json.dumps(payload)).generate(make_intake(**INTAKE))
    assert result.generator == "rules (llm tailoring rejected)"
    assert len(result.rows) == len(scope.rows)


def test_changed_line_count_is_rejected() -> None:
    scope = base_scope()
    payload = faithful_tailoring(scope)
    payload["rows"][0]["lines"].append({"index": 99, "text": "An extra line."})

    result = generator_for(json.dumps(payload)).generate(make_intake(**INTAKE))
    assert result.generator == "rules (llm tailoring rejected)"


def test_malformed_json_is_rejected() -> None:
    result = generator_for("{not valid json").generate(make_intake(**INTAKE))
    assert result.generator == "rules (llm tailoring rejected)"


def test_response_missing_required_fields_is_rejected() -> None:
    result = generator_for(json.dumps({"rows": []})).generate(make_intake(**INTAKE))
    assert result.generator == "rules (llm tailoring rejected)"


def test_empty_response_is_rejected() -> None:
    result = generator_for("").generate(make_intake(**INTAKE))
    assert result.generator == "rules (llm tailoring rejected)"


def test_a_rejected_tailoring_still_yields_a_publishable_scope() -> None:
    """Degrading must produce a slightly generic scope, never a broken one."""
    result = generator_for("{broken").generate(make_intake(**INTAKE))
    assert result.rows
    assert result.engagement_summary
    assert result.exclusions
    assert result.provenance
    assert result.cost_plan.assumptions_register


# -------------------------------------------------------------------------- errors


def test_api_error_falls_back_without_raising() -> None:
    result = generator_for(RuntimeError("503 upstream unavailable")).generate(make_intake(**INTAKE))
    assert result.generator == "rules (llm error)"
    assert result.rows


def test_missing_api_key_falls_back_cleanly() -> None:
    generator = LlmScopeGenerator(settings=Settings(gemini_api_key=None))
    assert generator.available is False

    result = generator.generate(make_intake(**INTAKE))
    assert result.generator == "rules (llm unavailable)"
    assert result.rows


def test_missing_key_never_constructs_a_client() -> None:
    """No key must mean no network attempt at all."""
    generator = LlmScopeGenerator(settings=Settings(gemini_api_key=None))
    generator.generate(make_intake(**INTAKE))
    assert generator._client is None


# ---------------------------------------------------------------------- validation


def test_validate_accepts_a_faithful_response() -> None:
    scope = base_scope()
    validate_tailoring(LlmTailoring.model_validate(faithful_tailoring(scope)), scope)


def test_validate_rejects_an_empty_summary() -> None:
    scope = base_scope()
    payload = faithful_tailoring(scope)
    payload["engagement_summary"] = "   "

    with pytest.raises(TailoringRejected, match="engagement_summary"):
        validate_tailoring(LlmTailoring.model_validate(payload), scope)


def test_validate_rejects_out_of_range_line_indices() -> None:
    """Indices must be exactly 0..n-1, so a rewritten line cannot land in the wrong slot."""
    scope = base_scope()
    payload = faithful_tailoring(scope)
    payload["rows"][0]["lines"][0]["index"] = 7

    with pytest.raises(TailoringRejected, match="indices"):
        validate_tailoring(LlmTailoring.model_validate(payload), scope)


def test_validate_rejects_duplicate_line_indices() -> None:
    """Two lines claiming the same slot would silently drop one of them."""
    enterprise = RulesScopeGenerator().generate(
        make_intake(dd_type_preference="Enterprise IT DD")
    )
    payload = faithful_tailoring(enterprise)
    multi = next(r for r in payload["rows"] if len(r["lines"]) > 1)
    multi["lines"][1]["index"] = multi["lines"][0]["index"]

    with pytest.raises(TailoringRejected, match="indices"):
        validate_tailoring(LlmTailoring.model_validate(payload), enterprise)


def test_validate_rejects_an_empty_line() -> None:
    scope = base_scope()
    payload = faithful_tailoring(scope)
    payload["rows"][0]["lines"][0]["text"] = "   "

    with pytest.raises(TailoringRejected, match="empty"):
        validate_tailoring(LlmTailoring.model_validate(payload), scope)


def test_apply_leaves_the_original_scope_untouched() -> None:
    scope = base_scope()
    original_title = scope.rows[0].title
    apply_tailoring(scope, LlmTailoring.model_validate(faithful_tailoring(scope)))
    assert scope.rows[0].title == original_title, "apply must not mutate its input"
