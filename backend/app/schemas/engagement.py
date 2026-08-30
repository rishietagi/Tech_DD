from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.reference.enums import EngagementStatus
from app.schemas.intake import SECTION_JSON_COLUMNS, IntakeDraft

if TYPE_CHECKING:
    from app.models.engagement import Engagement


class EngagementCreate(BaseModel):
    deal_name: str = Field(min_length=1, max_length=255)


class EngagementDenormRead(BaseModel):
    company_name: str | None = None
    sector: str | None = None
    investment_type: str | None = None
    stake: str | None = None
    digital_maturity: str | None = None
    dd_type: str | None = None
    dd_mix: int | None = None

    model_config = {"from_attributes": True}


class EngagementSummary(BaseModel):
    id: str
    deal_name: str
    status: EngagementStatus
    current_step: str
    created_at: datetime
    updated_at: datetime
    filed_at: str | None = None
    denorm: EngagementDenormRead | None = None

    model_config = {"from_attributes": True}


class EngagementRead(EngagementSummary):
    intake: IntakeDraft

    model_config = {"from_attributes": True}

    @classmethod
    def from_engagement(cls, engagement: "Engagement") -> "EngagementRead":
        intake_row = engagement.intake
        section_data = {section: getattr(intake_row, column) for section, column in SECTION_JSON_COLUMNS.items()}
        return cls(
            id=engagement.id,
            deal_name=engagement.deal_name,
            status=EngagementStatus(engagement.status),
            current_step=engagement.current_step,
            created_at=engagement.created_at,
            updated_at=engagement.updated_at,
            filed_at=engagement.filed_at,
            denorm=EngagementDenormRead.model_validate(engagement.denorm) if engagement.denorm else None,
            intake=IntakeDraft.model_validate(section_data),
        )


class EngagementUpdate(BaseModel):
    deal_name: str | None = Field(default=None, min_length=1, max_length=255)
    current_step: str | None = None


class EngagementListResponse(BaseModel):
    items: list[EngagementSummary]
    total: int


class FieldErrorOut(BaseModel):
    field: str
    message: str


class SubmitErrorResponse(BaseModel):
    code: str = "incomplete_intake"
    message: str
    field_errors: list[FieldErrorOut]
