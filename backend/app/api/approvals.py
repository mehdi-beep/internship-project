from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.user import User
from app.schemas.approval import ApprovalDecisionInput, RecentApprovalDecision
from app.schemas.common import ApiResponse
from app.schemas.intervention import InterventionDetailOut, InterventionOut
from app.schemas.pagination import Page
from app.services import approval_service

router = APIRouter(tags=["approvals"])


@router.get("/approvals/my-recent-decisions", response_model=ApiResponse[list[RecentApprovalDecision]])
def my_recent_decisions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chef_technicien", "admin_supervisor", "ceo")),
) -> ApiResponse[list[RecentApprovalDecision]]:
    return ApiResponse(data=approval_service.list_my_recent_decisions(db, current_user.id))


@router.get("/approvals/technical-pending", response_model=ApiResponse[Page[InterventionOut]])
def list_technical_pending(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("chef_technicien", "ceo")),
) -> ApiResponse[Page[InterventionOut]]:
    result = approval_service.list_technical_pending(db, page, page_size)
    return ApiResponse(
        data=Page(
            items=[InterventionOut.model_validate(i) for i in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            pages=result.pages,
        )
    )


@router.get("/approvals/administrative-pending", response_model=ApiResponse[Page[InterventionOut]])
def list_administrative_pending(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor", "ceo")),
) -> ApiResponse[Page[InterventionOut]]:
    result = approval_service.list_administrative_pending(db, page, page_size)
    return ApiResponse(
        data=Page(
            items=[InterventionOut.model_validate(i) for i in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            pages=result.pages,
        )
    )


@router.post("/interventions/{intervention_id}/technical-approval", response_model=ApiResponse[InterventionDetailOut])
def technical_approval(
    intervention_id: int,
    payload: ApprovalDecisionInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("chef_technicien", "ceo")),
) -> ApiResponse[InterventionDetailOut]:
    intervention = approval_service.decide_technical_approval(db, intervention_id, payload, current_user.id)
    message = "Technical approval completed." if payload.decision.value == "approved" else "Intervention rejected."
    return ApiResponse(message=message, data=InterventionDetailOut.model_validate(intervention))


@router.post("/interventions/{intervention_id}/administrative-approval", response_model=ApiResponse[InterventionDetailOut])
def administrative_approval(
    intervention_id: int,
    payload: ApprovalDecisionInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin_supervisor", "ceo")),
) -> ApiResponse[InterventionDetailOut]:
    intervention = approval_service.decide_administrative_approval(db, intervention_id, payload, current_user.id)
    message = "Administrative approval completed." if payload.decision.value == "approved" else "Intervention rejected."
    return ApiResponse(message=message, data=InterventionDetailOut.model_validate(intervention))
