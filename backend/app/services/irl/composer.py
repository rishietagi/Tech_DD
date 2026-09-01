"""Assembles the deterministic IRL from seeds.

This is the floor: what ships when the model is unavailable, rejected, or switched off.
It is a complete, sendable request list — terser than the tailored version, and without
the non-technology functions a tech scope never reaches, but genuinely usable.

Function naming here is the one place the deterministic path has to guess. The LLM path
names functions from the target's actual shape (see `llm.py`); with no model, the DD
workstream codes are the only signal available, so they are mapped to plain business
function names. It is a fallback, not the intended output.
"""

from datetime import UTC, datetime

from app.schemas.irl import IrlFunction, IrlPayload, IrlQuestion
from app.services.irl.seeds import SeedRequest

# DD_master workstream code -> the business function that would own the answer. Used
# only by the deterministic path.
_WORKSTREAM_FUNCTION = {
    "W-APP": "IT Applications",
    "W-INFRA": "IT Infrastructure",
    "W-OPS": "IT Operations",
    "W-SEC": "Information Security",
    "W-DATA": "Data & Analytics",
    "W-PROD": "Engineering & Product",
    "W-STRAT": "Technology Strategy",
    "W-SPEND": "Finance & IT Spend",
    "W-VEN": "Vendor & Contracts",
    "W-PROC": "Legal & Compliance",
    "W-INT": "Integration",
    "W-SEP": "Separation",
}

_DEFAULT_FUNCTION = "Technology"


def function_for(seed: SeedRequest) -> str:
    """First recognised workstream wins; order in the YAML is meaningful (primary first)."""
    for code in seed.workstreams:
        mapped = _WORKSTREAM_FUNCTION.get(code)
        if mapped:
            return mapped
    return _DEFAULT_FUNCTION


def _intro(company: str | None) -> str:
    target = company or "the target"
    return (
        f"This initial request list sets out the information required to complete the "
        f"technology due diligence of {target}. Requests are grouped by the business "
        f"function best placed to answer them. Please provide the document or a short "
        f"written response in the Response column, or note where the information is "
        f"unavailable and why."
    )


def group_functions(questions: list[IrlQuestion]) -> list[IrlFunction]:
    """Function headings in first-appearance order, each listing its question ids.

    First-appearance rather than alphabetical keeps the technology functions that the
    scope drove at the top, which is the order a tech DD reader expects.
    """
    order: list[str] = []
    grouped: dict[str, list[str]] = {}

    for question in questions:
        if question.function not in grouped:
            grouped[question.function] = []
            order.append(question.function)
        grouped[question.function].append(question.id)

    return [IrlFunction(name=name, question_ids=grouped[name]) for name in order]


def compose_irl(
    seeds: list[SeedRequest],
    company_name: str | None,
    source_scope_version: int | None,
    generator: str = "rules",
) -> IrlPayload:
    questions = [
        IrlQuestion(
            id=seed.id,
            function=function_for(seed),
            # The evidence line is an artefact name, not a question. Wrapping it in a
            # request verb is the minimum needed to make it sendable; the LLM path
            # rewrites this properly.
            question=f"Please provide: {seed.text}",
            source="scope",
            source_row_id=seed.row_id,
            source_row_title=seed.row_title,
            seed_text=seed.text,
        )
        for seed in seeds
    ]

    return IrlPayload(
        generator=generator,
        company_name=company_name,
        source_scope_version=source_scope_version,
        used_research=False,
        intro=_intro(company_name),
        questions=questions,
        functions=group_functions(questions),
        generated_at=datetime.now(UTC),
    )
