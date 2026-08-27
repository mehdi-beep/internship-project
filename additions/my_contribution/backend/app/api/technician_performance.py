from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.technician_performance import TechnicianPerformanceDetail, TechnicianPerformanceSummary
from app.services import technician_performance_service

router = APIRouter(prefix="/technician-performance", tags=["technician-performance"])

SUPERVISOR_ROLES = ("chef_technicien", "admin_supervisor")


@router.get("", response_model=ApiResponse[list[TechnicianPerformanceSummary]])
def list_technician_performance(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*SUPERVISOR_ROLES)),
) -> ApiResponse[list[TechnicianPerformanceSummary]]:
    return ApiResponse(data=technician_performance_service.list_technician_performance(db))


@router.get("/me", response_model=ApiResponse[TechnicianPerformanceDetail])
def get_my_technician_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("technician")),
) -> ApiResponse[TechnicianPerformanceDetail]:
    # Self-service profile data — always forces technician_id to the caller's
    # own id, never accepting a client-supplied id, so this is structurally
    # safe to expose to the technician role (unlike GET /{technician_id}
    # below, which is chef/admin only).
    return ApiResponse(data=technician_performance_service.get_technician_performance_detail(db, current_user.id))


@router.get("/{technician_id}", response_model=ApiResponse[TechnicianPerformanceDetail])
def get_technician_performance(
    technician_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*SUPERVISOR_ROLES)),
) -> ApiResponse[TechnicianPerformanceDetail]:
    return ApiResponse(data=technician_performance_service.get_technician_performance_detail(db, technician_id))
