from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.enums import InterventionStatus, InterventionType
from app.models.role import RoleName
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.intervention import (
    AuditLogOut,
    DemoDataStatusOut,
    InterventionCreate,
    InterventionDetailOut,
    InterventionOut,
    InterventionUpdate,
)
from app.schemas.pagination import Page
from app.services import demo_cleanup_service, intervention_service

router = APIRouter(prefix="/interventions", tags=["interventions"])

ALL_ROLES = ("technician", "chef_technicien", "admin_supervisor", "ceo")


def _is_privileged(user: User) -> bool:
    return user.role.name in (RoleName.CHEF_TECHNICIEN, RoleName.ADMIN_SUPERVISOR, RoleName.CEO)


# Registered BEFORE "/{intervention_id}" below, same reason point_rules.py's
# "/settings" is registered before its own "/{rule_id}" — FastAPI/Starlette
# matches routes in registration order, and "demo-data"/"demo-data-count"
# would otherwise be swallowed by the path-param route first (failing its int
# conversion) rather than reaching these handlers.
#
# CEO-only, not ALL_ROLES / admin_supervisor — this is a one-time, irreversible
# cleanup of pre-cutoff seeded data (see demo_cleanup_service.py's module
# docstring for why this exists and why it can never broaden to real
# interventions), matching the CEO-exclusive gating already established by
# GET /dashboard/ceo/charts (require_roles("ceo") alone, not the shared
# admin_supervisor pattern used elsewhere).
@router.get("/demo-data-count", response_model=ApiResponse[DemoDataStatusOut])
def get_demo_data_status(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ceo")),
) -> ApiResponse[DemoDataStatusOut]:
    return ApiResponse(data=DemoDataStatusOut.model_validate(demo_cleanup_service.get_status(db)))


@router.delete("/demo-data", response_model=ApiResponse[dict])
def delete_demo_data(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ceo")),
) -> ApiResponse[dict]:
    deleted_count = demo_cleanup_service.delete_demo_interventions(db)
    return ApiResponse(
        message=f"Deleted {deleted_count} demo intervention(s) and all their dependent records.",
        data={"deleted_count": deleted_count},
    )


@router.get("", response_model=ApiResponse[Page[InterventionOut]])
def list_interventions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    technician_id: int | None = None,
    client_id: int | None = None,
    site_id: int | None = None,
    status_filter: InterventionStatus | None = Query(None, alias="status"),
    intervention_type: InterventionType | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    colleague_technician_id: int | None = None,
    city: str | None = None,
    contract_id: int | None = None,
    project_id: int | None = None,
    status_in: list[InterventionStatus] | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[Page[InterventionOut]]:
    result = intervention_service.list_interventions(
        db,
        current_user.id,
        _is_privileged(current_user),
        page,
        page_size,
        technician_id,
        client_id,
        site_id,
        status_filter,
        intervention_type,
        date_from,
        date_to,
        search,
        colleague_technician_id,
        city,
        contract_id,
        project_id,
        status_in,
    )
    return ApiResponse(
        data=Page(
            items=[InterventionOut.model_validate(i) for i in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            pages=result.pages,
        )
    )


@router.get("/{intervention_id}", response_model=ApiResponse[InterventionDetailOut])
def get_intervention(
    intervention_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[InterventionDetailOut]:
    intervention = intervention_service.get_intervention_for_user(
        db, intervention_id, current_user.id, _is_privileged(current_user)
    )
    return ApiResponse(data=InterventionDetailOut.model_validate(intervention))


@router.post("", response_model=ApiResponse[InterventionDetailOut])
def create_intervention(
    payload: InterventionCreate,
    submit: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("technician")),
) -> ApiResponse[InterventionDetailOut]:
    intervention = intervention_service.create_intervention(db, payload, current_user.id, submit)
    message = "Intervention submitted." if submit else "Intervention saved as draft."
    return ApiResponse(message=message, data=InterventionDetailOut.model_validate(intervention))


@router.put("/{intervention_id}", response_model=ApiResponse[InterventionDetailOut])
def update_intervention(
    intervention_id: int,
    payload: InterventionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("technician")),
) -> ApiResponse[InterventionDetailOut]:
    intervention = intervention_service.update_intervention(db, intervention_id, payload, current_user.id)
    return ApiResponse(message="Intervention updated.", data=InterventionDetailOut.model_validate(intervention))


@router.post("/{intervention_id}/submit", response_model=ApiResponse[InterventionDetailOut])
def submit_intervention(
    intervention_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("technician")),
) -> ApiResponse[InterventionDetailOut]:
    intervention = intervention_service.submit_intervention(db, intervention_id, current_user.id, is_privileged=False)
    return ApiResponse(message="Intervention submitted.", data=InterventionDetailOut.model_validate(intervention))


@router.get("/{intervention_id}/history", response_model=ApiResponse[list[AuditLogOut]])
def get_history(
    intervention_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[list[AuditLogOut]]:
    intervention = intervention_service.get_history(db, intervention_id, current_user.id, _is_privileged(current_user))
    return ApiResponse(data=[AuditLogOut.model_validate(a) for a in intervention.audit_log])
