from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.dashboard import (
    AdminDashboard,
    AdminDashboardCharts,
    ChefDashboard,
    ChefDashboardCharts,
    TechnicianDashboard,
    TechnicianDashboardCharts,
)
from app.services import dashboard_service
from app.services.dashboard_service import PeriodMode

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/technician", response_model=ApiResponse[TechnicianDashboard])
def technician_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("technician")),
) -> ApiResponse[TechnicianDashboard]:
    return ApiResponse(data=dashboard_service.get_technician_dashboard(db, current_user.id))


@router.get("/technician/charts", response_model=ApiResponse[TechnicianDashboardCharts])
def technician_dashboard_charts(
    mode: PeriodMode = Query(...),
    anchor: date = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("technician")),
) -> ApiResponse[TechnicianDashboardCharts]:
    return ApiResponse(data=dashboard_service.get_technician_dashboard_charts(db, current_user.id, mode, anchor))


@router.get("/supervisor", response_model=ApiResponse[ChefDashboard])
def supervisor_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("chef_technicien")),
) -> ApiResponse[ChefDashboard]:
    return ApiResponse(data=dashboard_service.get_chef_dashboard(db))


@router.get("/supervisor/charts", response_model=ApiResponse[ChefDashboardCharts])
def supervisor_dashboard_charts(
    mode: PeriodMode = Query(...),
    anchor: date = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("chef_technicien")),
) -> ApiResponse[ChefDashboardCharts]:
    return ApiResponse(data=dashboard_service.get_chef_dashboard_charts(db, mode, anchor))


@router.get("/admin", response_model=ApiResponse[AdminDashboard])
def admin_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor", "ceo")),
) -> ApiResponse[AdminDashboard]:
    return ApiResponse(data=dashboard_service.get_admin_dashboard(db))


@router.get("/admin/charts", response_model=ApiResponse[AdminDashboardCharts])
def admin_dashboard_charts(
    mode: PeriodMode = Query(...),
    anchor: date = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor", "ceo")),
) -> ApiResponse[AdminDashboardCharts]:
    return ApiResponse(data=dashboard_service.get_admin_dashboard_charts(db, mode, anchor))
