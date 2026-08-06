from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ApprovalDecision, ApprovalLevel


class ApprovalDecisionInput(BaseModel):
    decision: ApprovalDecision
    comment: str | None = None


class RecentApprovalDecision(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    intervention_id: int
    bi_number: str
    approval_level: ApprovalLevel
    decision: ApprovalDecision
    approval_date: datetime
