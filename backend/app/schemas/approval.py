from pydantic import BaseModel

from app.models.enums import ApprovalDecision


class ApprovalDecisionInput(BaseModel):
    decision: ApprovalDecision
    comment: str | None = None
