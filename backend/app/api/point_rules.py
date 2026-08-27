from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.point_rule import PointRuleCreate, PointRuleOut, PointRuleUpdate
from app.services import point_rule_service

router = APIRouter(prefix="/point-rules", tags=["point-rules"])

# Administrator-only: point rules are a Task 2 configuration surface with no
# other reader — unlike travaux/clients/etc., no technician or chef page ever
# needs to fetch this list (calculate_points() reads it server-side, not via
# an API call), so there is no T/C read case to support here.
ADMIN_ONLY = ("admin_supervisor",)


@router.get("", response_model=ApiResponse[list[PointRuleOut]])
def list_point_rules(
    active_only: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ADMIN_ONLY)),
) -> ApiResponse[list[PointRuleOut]]:
    rules = point_rule_service.list_rules(db, active_only)
    return ApiResponse(data=[PointRuleOut.model_validate(r) for r in rules])


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
