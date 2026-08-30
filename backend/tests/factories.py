"""Intake builders for the scope-engine tests.

`make_intake()` returns a valid IntakeFull with neutral answers; keyword overrides go
to the section they belong to, so a test can say exactly what it is varying:

    make_intake(dd_type_preference="Product Tech DD")
"""

from typing import Any

from app.schemas.intake import (
    DealContextRequired,
    DealStructureRequired,
    DiligenceObjectivesRequired,
    IntakeFull,
    RationaleRequired,
    TargetCompanyRequired,
    TechnologyProfileRequired,
)

_SECTION_FIELDS = {
    "context": set(DealContextRequired.model_fields),
    "rationale": set(RationaleRequired.model_fields),
    "structure": set(DealStructureRequired.model_fields),
    "target": set(TargetCompanyRequired.model_fields),
    "technology": set(TechnologyProfileRequired.model_fields),
    "objectives": set(DiligenceObjectivesRequired.model_fields),
}

# Deliberately neutral: no archetype rule fires except the unconditional ones, so a
# test that sets one field sees only that field's effect.
_NEUTRAL: dict[str, dict[str, Any]] = {
    "context": {
        "deal_name": "Project Neutral",
        "context_narrative": "A neutral baseline engagement used to isolate one rule at a time.",
        "deal_stage": "Exclusivity",
        "process_type": "Limited process",
    },
    "rationale": {
        "rationale_narrative": "The buyer believes the asset is sound and wants confirmation before signing.",
        "value_creation_levers": ["Organic growth"],
    },
    "structure": {
        "investment_type": "financial",
        "stake": "majority",
        "post_close_intent": "Standalone",
    },
    "target": {
        "company_name": "Neutral Co",
        "sector": "Other",
        "line_of_business": "Provides business services to mid-market customers across several regions.",
        "business_model": "Services-led",
        "digital_maturity": "Digitally enabled",
        "headcount": 500,
        "revenue_stage": "Mature",
        "hq_location": "London, UK",
    },
    "technology": {
        "hosting_model": "Hybrid",
        "ai_ml_dependence": "None",
        "data_sensitivity": ["None"],
        "compliance_regimes": ["None known"],
    },
    "objectives": {
        "dd_objectives": ["Validate scalability"],
        "access_level": "Full (data room and management sessions)",
        "deliverable_format": ["Full diligence report"],
        "timeline_weeks": 8,
        "dd_type_preference": "Let the platform decide",
    },
}


def make_intake(**overrides: Any) -> IntakeFull:
    """Build an IntakeFull, routing each override to the section that owns the field."""
    sections = {name: dict(values) for name, values in _NEUTRAL.items()}

    for key, value in overrides.items():
        for section_name, fields in _SECTION_FIELDS.items():
            if key in fields:
                sections[section_name][key] = value
                break
        else:
            raise KeyError(f"no intake section owns field {key!r}")

    return IntakeFull.model_validate(
        {
            "context": DealContextRequired.model_validate(sections["context"]),
            "rationale": RationaleRequired.model_validate(sections["rationale"]),
            "structure": DealStructureRequired.model_validate(sections["structure"]),
            "target": TargetCompanyRequired.model_validate(sections["target"]),
            "technology": TechnologyProfileRequired.model_validate(sections["technology"]),
            "objectives": DiligenceObjectivesRequired.model_validate(sections["objectives"]),
        }
    )
