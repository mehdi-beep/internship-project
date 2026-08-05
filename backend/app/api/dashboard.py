from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.dashboard import AdminDashboard, ChefDashboard, TechnicianDashboard
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/technician", response_model=ApiResponse[TechnicianDashboard])
def technician_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("technician")),
) -> ApiResponse[TechnicianDashboard]:
    return ApiResponse(data=dashboard_service.get_technician_dashboard(db, current_user.id))


@router.get("/supervisor", response_model=ApiResponse[ChefDashboard])
def supervisor_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("chef_technicien")),
) -> ApiResponse[ChefDashboard]:
    return ApiResponse(data=dashboard_service.get_chef_dashboard(db))


@router.get("/admin", response_model=ApiResponse[AdminDashboard])
def admin_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[AdminDashboard]:
    return ApiResponse(data=dashboard_service.get_admin_dashboard(db))
