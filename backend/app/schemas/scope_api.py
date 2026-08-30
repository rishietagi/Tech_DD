"""Request and response models for the scope endpoints."""

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.classification import Classification


class GenerateScopeRequest(BaseModel):
    """POST /engagements/{id}/scope"""

    generator: Literal["rules", "llm"] | None = Field(
        default=None,
        description="Override the configured generator for this run. None uses SCOPE_GENERATOR.",
    )
    force_regenerate: bool = Field(
        default=False,
        description="Create a new version even when the intake has not changed since the last one.",
    )


class ScopePreviewResponse(BaseModel):
    """POST /engagements/{id}/scope/preview

    Classification only, from a possibly-incomplete draft intake. Powers the live
    signal panel, so it must tolerate a half-filled intake and return low confidence
    rather than erroring (PHASE2_SPEC §9.1).
    """

    classification: Classification
    row_count: int = Field(description="How many scope rows would open at this point")
    deck: str = Field(description="Which KPMG deck the engagement is heading toward")
    is_complete: bool = Field(description="False when the intake is still too sparse to file")


class WorkstreamOverrideRequest(BaseModel):
    """PATCH /engagements/{id}/scope/{version}/rows/{row_id}

    A human edit to one row. DD_master G6: the human overrides the engine, and the
    original is preserved rather than replaced.
    """

    tier: int | None = Field(default=None, ge=0, le=3)
    title: str | None = None
    reason: str | None = Field(
        default=None, description="Why the override was made. Recorded alongside the change."
    )


class LibraryRowSummary(BaseModel):
    id: str
    sn: int
    deck: str
    title: str
    lines: list[str]
    workstreams: list[str]
    base_tier: int
    always_in_scope: bool
    dd_master_ref: str | None = None


class WorkstreamLibraryResponse(BaseModel):
    """GET /meta/workstreams — the library, for the methodology page."""

    library_version: str
    source_document: str
    source_owner: str
    decks: dict[str, list[LibraryRowSummary]]
