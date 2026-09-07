from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.user import User
from app.schemas.app_settings import AppSettingsOut, AppSettingsUpdate
from app.schemas.common import ApiResponse
from app.schemas.point_rule import PointRuleCreate, PointRuleOut, PointRuleUpdate
from app.services import app_settings_service, point_rule_service

router = APIRouter(prefix="/point-rules", tags=["point-rules"])

# Administrator-only: point rules are a Task 2 configuration surface with no
# other reader — unlike travaux/clients/etc., no technician or chef page ever
# needs to fetch this list (calculate_points() reads it server-side, not via
# an API call), so there is no T/C read case to support here.
ADMIN_ONLY = ("admin_supervisor", "ceo")


@router.get("", response_model=ApiResponse[list[PointRuleOut]])
def list_point_rules(
    active_only: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ONLY)),
) -> ApiResponse[list[PointRuleOut]]:
    rules = point_rule_service.list_rules(db, active_only)
    return ApiResponse(data=[PointRuleOut.model_validate(r) for r in rules])


# Company-wide UTC offset used by calculate_points() to convert a submission's
# UTC timestamp before checking it against the rules above — lives on this
# router (rather than a separate one) because it's the same "Point Management"
# admin surface on the frontend and is small enough that a whole new router
# module would be more ceremony than the two endpoints below justify.
# Registered BEFORE /{rule_id} below: FastAPI/Starlette matches routes in
# registration order, and "/settings" would otherwise be swallowed by the
# path-param route first (failing its int conversion) rather than reaching
# these handlers.
@router.get("/settings", response_model=ApiResponse[AppSettingsOut])
def get_point_rule_settings(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ONLY)),
) -> ApiResponse[AppSettingsOut]:
    settings = app_settings_service.get_settings(db)
    return ApiResponse(data=AppSettingsOut.model_validate(settings))


@router.put("/settings", response_model=ApiResponse[AppSettingsOut])
def update_point_rule_settings(
    payload: AppSettingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ONLY)),
) -> ApiResponse[AppSettingsOut]:
    settings = app_settings_service.update_offset(db, payload.company_utc_offset_minutes)
    return ApiResponse(message="Company timezone updated.", data=AppSettingsOut.model_validate(settings))


@router.get("/{rule_id}", response_model=ApiResponse[PointRuleOut])
def get_point_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ONLY)),
) -> ApiResponse[PointRuleOut]:
    rule = point_rule_service.get_rule(db, rule_id)
    return ApiResponse(data=PointRuleOut.model_validate(rule))


@router.post("", response_model=ApiResponse[PointRuleOut])
def create_point_rule(
    payload: PointRuleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ONLY)),
) -> ApiResponse[PointRuleOut]:
    rule = point_rule_service.create_rule(db, payload)
    return ApiResponse(message="Point rule created.", data=PointRuleOut.model_validate(rule))


@router.put("/{rule_id}", response_model=ApiResponse[PointRuleOut])
def update_point_rule(
    rule_id: int,
    payload: PointRuleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ONLY)),
) -> ApiResponse[PointRuleOut]:
    rule = point_rule_service.update_rule(db, rule_id, payload)
    return ApiResponse(message="Point rule updated.", data=PointRuleOut.model_validate(rule))


@router.patch("/{rule_id}/deactivate", response_model=ApiResponse[PointRuleOut])
def deactivate_point_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ONLY)),
) -> ApiResponse[PointRuleOut]:
    rule = point_rule_service.deactivate_rule(db, rule_id)
    return ApiResponse(message="Point rule deactivated.", data=PointRuleOut.model_validate(rule))


@router.patch("/{rule_id}/activate", response_model=ApiResponse[PointRuleOut])
def activate_point_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ONLY)),
) -> ApiResponse[PointRuleOut]:
    rule = point_rule_service.activate_rule(db, rule_id)
    return ApiResponse(message="Point rule reactivated.", data=PointRuleOut.model_validate(rule))


@router.delete("/{rule_id}", response_model=ApiResponse[None])
def delete_point_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ONLY)),
) -> ApiResponse[None]:
    point_rule_service.delete_rule(db, rule_id)
    return ApiResponse(message="Point rule deleted.", data=None)
