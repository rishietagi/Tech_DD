"""Checklist payloads — what has actually arrived against each IRL request.

The checklist is **assembled on read**, never stored: IRL questions + their statuses +
computed priorities. There is nothing to regenerate and nothing that can drift out of
step with the request list it tracks.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DocumentStatus = Literal["not_received", "received_partially", "received_completely"]
Priority = Literal["critical", "high", "medium", "low"]

STATUS_LABELS: dict[str, str] = {
    "not_received": "Not yet received",
    "received_partially": "Received partially",
    "received_completely": "Received completely",
}

PRIORITY_LABELS: dict[str, str] = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}


class ChecklistItem(BaseModel):
    """One requested document and where it has got to."""

    question_id: str
    function: str
    # The request itself — what the client is being asked to supply.
    document_requested: str
    document_type: str = ""
    status: DocumentStatus = "not_received"
    notes: str = ""

    priority: Priority
    # Why the priority is what it is. A colour with no explanation is not auditable.
    priority_reason: str

    # Provenance, carried through from the IRL so a reader can trace a request back to
    # the scope area that asked for it.
    source_row_id: str | None = None
    source_row_title: str | None = None

    # Filenames the scanner matched. Empty until the shared-drive walk is built.
    matched_files: list[str] = Field(default_factory=list)
    set_by_human: bool = False
    updated_at: datetime | None = None


class ChecklistSummary(BaseModel):
    """Counts for the header and the reminder preview."""

    total: int
    received_completely: int
    received_partially: int
    not_received: int
    outstanding_critical: int
    outstanding_high: int


class ChecklistRead(BaseModel):
    engagement_id: str
    irl_id: str
    irl_version: int
    company_name: str | None = None
    items: list[ChecklistItem]
    summary: ChecklistSummary
    # When the shared drive was last walked. None until the scanner exists.
    last_scanned_at: datetime | None = None


class ChecklistItemUpdate(BaseModel):
    """Body of the update endpoint. Every field is optional — a caller may set only one."""

    model_config = {"extra": "forbid"}

    status: DocumentStatus | None = None
    document_type: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=4000)
