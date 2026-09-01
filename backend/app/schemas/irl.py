"""Initial Request List payloads.

The IRL is what the buyer sends the target: every artefact the diligence team needs to
inspect, grouped by the business function that owns it.

Provenance is first-class. A question either came from a scope row's evidence list
(`source="scope"`, carrying `source_row_id`) or was added by the model to cover a
function the tech scope does not reach (`source="llm"`). A reviewer can always tell
which is which, the same way the scope of work distinguishes sourced from extended
content.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

QuestionSource = Literal["scope", "llm"]


class IrlQuestion(BaseModel):
    """One request. `id` is stable within a version and keys the response table."""

    id: str
    # The business function that owns the answer — IT, Finance, HR, Legal, and so on.
    # Model-assigned per target rather than drawn from a fixed list, so a manufacturer
    # can get "Plant Operations" and a bank "Treasury". See docs/PROJECT_LOG.md.
    function: str
    question: str

    source: QuestionSource = "scope"
    # Present only when source == "scope": the KPMG row whose evidence list seeded this.
    source_row_id: str | None = None
    source_row_title: str | None = None
    # Verbatim evidence line the question was expanded from, kept so a reviewer can see
    # what the model was given and judge whether the rewrite is faithful.
    seed_text: str | None = None


class IrlFunction(BaseModel):
    """A function heading, with the questions under it."""

    name: str
    question_ids: list[str] = Field(default_factory=list)


class IrlPayload(BaseModel):
    schema_version: Literal[1] = 1
    generator: str
    prompt_version: str | None = None

    company_name: str | None = None
    # What the IRL was built from, so a reader can tell whether it is still aligned with
    # the current scope.
    source_scope_version: int | None = None
    # True when a research run fed the generation. Recorded because it changes how well
    # the functions fit the target, and a reader deserves to know which they are looking
    # at.
    used_research: bool = False

    intro: str
    questions: list[IrlQuestion]
    # Resolved order of function headings. Stored so a regeneration can be told what the
    # previous run used and reuse the names where they still fit, rather than drifting.
    functions: list[IrlFunction] = Field(default_factory=list)

    generated_at: datetime


class IrlRead(BaseModel):
    id: str
    engagement_id: str
    version: int
    generator: str
    source_scope_version: int | None = None
    payload: dict[str, Any]
    # question_id -> response text. Joined from the separate response table rather than
    # stored in the payload, so regenerating never clobbers typed answers.
    responses: dict[str, str] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class IrlVersionSummary(BaseModel):
    version: int
    generator: str
    created_at: datetime

    model_config = {"from_attributes": True}


class IrlResponseUpdate(BaseModel):
    """Body of the save-one-response endpoint."""

    model_config = {"extra": "forbid"}

    response_text: str = Field(max_length=20_000)


class GenerateIrlRequest(BaseModel):
    model_config = {"extra": "forbid"}

    generator: Literal["rules", "llm"] | None = None


# ---------------------------------------------------------------- LLM contract


class LlmIrlQuestion(BaseModel):
    """One question as the model returns it."""

    model_config = {"extra": "forbid"}

    seed_id: str | None = None
    function: str
    question: str


class LlmIrl(BaseModel):
    """The model's whole response. Validated before any of it is trusted."""

    model_config = {"extra": "forbid"}

    intro: str
    questions: list[LlmIrlQuestion]


class IrlTailoringRejected(RuntimeError):
    """The model's output did not satisfy the structural contract."""
