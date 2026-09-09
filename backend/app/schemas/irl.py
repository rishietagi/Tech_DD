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

from app.schemas.checklist import DocumentStatus, Priority

QuestionSource = Literal["scope", "llm", "manual"]

# What a request actually asks for. A document wants an artefact; a question wants an
# explanation only management can give. DD_master §6 gives every workstream both, and
# until 2026-09-02 this engine produced only the first.
#
# The distinction is not cosmetic: only a document can be "received", only a question can
# be "answered", and they are chased differently.
RequestKind = Literal["document", "question"]


class IrlQuestion(BaseModel):
    """One request. `id` is stable within a version and keys the response table."""

    id: str
    # The business function that owns the answer — IT, Finance, HR, Legal, and so on.
    # Model-assigned per target rather than drawn from a fixed list, so a manufacturer
    # can get "Plant Operations" and a bank "Treasury". See docs/PROJECT_LOG.md.
    function: str
    question: str

    # The scope-of-work heading this request traces to, so the IRL groups by the same
    # areas the SOW opened (Rishi, 2026-09-02). Empty for questions that belong to no
    # scope area — the model's own additions covering HR, Legal and Finance.
    scope_area: str = ""

    # Document or question. Drives what "done" means for this row, and what the client is
    # being asked to do with it.
    kind: RequestKind = "document"
    # For sourced questions: the DD_master page the area of investigation came from, so a
    # question traces to the methodology exactly as a scope row traces to its rule.
    citation: str = ""

    source: QuestionSource = "scope"
    # Present only when source == "scope": the KPMG row whose evidence list seeded this.
    source_row_id: str | None = None
    source_row_title: str | None = None
    # Verbatim evidence line the question was expanded from, kept so a reviewer can see
    # what the model was given and judge whether the rewrite is faithful.
    seed_text: str | None = None

    # Hand-editing (2026-09-02). An analyst may reword any question, add their own, or
    # remove one. The original wording is kept beside the edit rather than replaced, the
    # same pattern the scope rows already use for human overrides.
    edited_by_human: bool = False
    original_question: str | None = None


class IrlFunction(BaseModel):
    """A grouping heading, with the questions under it.

    Since 2026-09-02 the IRL groups by **scope area** — the same headings the scope of
    work uses — so every request traces to the area that asked for it. The owning
    business function moved to its own column on each question.
    """

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


class IrlTracking(BaseModel):
    """What the deal team observes about the document behind one request.

    Merged into the IRL read from 2026-09-02 (Rishi): the analyst works one screen, not
    two. The **storage** stays split — `irl_response` is what the client wrote,
    `irl_document_status` is what the deal team observed — because they have different
    authors and different lifecycles, and the shared-drive scanner will write status
    without touching a client's answer. Only the presentation merges.

    Deliberately **not** exported to the client workbook: status, remarks and priority are
    internal judgements about the target's responsiveness.
    """

    status: DocumentStatus = "not_received"
    document_type: str = ""
    # The deal team's own note on the document — where it sits, what is missing from it,
    # who promised the rest.
    remarks: str = ""
    priority: Priority = "medium"
    priority_reason: str = ""
    set_by_human: bool = False
    updated_at: datetime | None = None

    # --- what the shared-drive scan found. Scan-owned: a human editing the row above
    # --- leaves these alone, and the next scan replaces them.
    #
    # The files the status was inferred from, so a wrong auto-match is visible.
    matched_files: list[str] = Field(default_factory=list)
    # What to go back and ask when what arrived is not enough — the output the scan
    # exists for. Empty where nothing arrived: the request is already outstanding.
    follow_up_questions: list[str] = Field(default_factory=list)
    # Why the scan called the status what it did.
    scan_reasoning: str = ""
    scanned_at: datetime | None = None


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
    # question_id -> tracking. Joined the same way, from the document-status table.
    tracking: dict[str, IrlTracking] = Field(default_factory=dict)
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


class IrlQuestionCreate(BaseModel):
    """An analyst adding a request the generated list did not anticipate."""

    model_config = {"extra": "forbid"}

    question: str = Field(min_length=1, max_length=4000)
    function: str = Field(min_length=1, max_length=120)
    # Which scope area it belongs under. Free text rather than an enum: it must match a
    # heading in the stored scope payload, and those are model-authored per engagement.
    scope_area: str = Field(default="", max_length=200)
    kind: RequestKind = "document"


class IrlQuestionUpdate(BaseModel):
    """Reword a question, or move it to a different function or scope area."""

    model_config = {"extra": "forbid"}

    question: str | None = Field(default=None, min_length=1, max_length=4000)
    function: str | None = Field(default=None, min_length=1, max_length=120)
    scope_area: str | None = Field(default=None, max_length=200)
    kind: RequestKind | None = None


class IrlTrackingUpdate(BaseModel):
    """Set the status, document type or remarks on one request, from the IRL screen."""

    model_config = {"extra": "forbid"}

    status: DocumentStatus | None = None
    document_type: str | None = Field(default=None, max_length=120)
    remarks: str | None = Field(default=None, max_length=4000)


class ImportResponsesResult(BaseModel):
    """What an uploaded response workbook actually changed.

    Reported rather than assumed: an import that silently matched nothing looks identical
    to one that worked, and the analyst would not find out until they read the checklist.
    """

    matched: int
    updated: int
    skipped_blank: int
    unmatched_rows: list[str] = Field(default_factory=list)
    total_rows: int
    note: str = ""


# ---------------------------------------------------------------- LLM contract


class LlmIrlQuestion(BaseModel):
    """One question as the model returns it."""

    model_config = {"extra": "forbid"}

    seed_id: str | None = None
    function: str
    question: str
    # Which scope-of-work heading this belongs under. Seeded questions inherit it from
    # their row regardless of what the model says; only additions rely on this.
    scope_area: str = ""
    # Document or question. For a seeded request the seed's own kind wins — the model may
    # rewrite the wording but must not turn a question into a document request.
    kind: RequestKind = "document"


class LlmIrl(BaseModel):
    """The model's whole response. Validated before any of it is trusted."""

    model_config = {"extra": "forbid"}

    intro: str
    questions: list[LlmIrlQuestion]


class IrlTailoringRejected(RuntimeError):
    """The model's output did not satisfy the structural contract."""
