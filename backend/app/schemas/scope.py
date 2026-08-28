from datetime import datetime

from pydantic import BaseModel

from app.reference.enums import DdType


class Workstream(BaseModel):
    name: str
    summary: str
    objectives: list[str]
    key_questions: list[str]
    evidence_requests: list[str]


class ScopeOfWorkPayload(BaseModel):
    dd_type: DdType | None = None
    dd_mix: int | None = None
    is_placeholder: bool
    placeholder_notice: str | None = None
    workstreams: list[Workstream]


class ScopeOfWorkRead(BaseModel):
    id: str
    engagement_id: str
    version: int
    generator: str
    dd_type: str | None = None
    dd_mix: int | None = None
    payload: ScopeOfWorkPayload
    created_at: datetime

    model_config = {"from_attributes": True}


class ScopeOfWorkVersionSummary(BaseModel):
    version: int
    generator: str
    created_at: datetime

    model_config = {"from_attributes": True}
