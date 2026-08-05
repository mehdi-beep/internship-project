from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.enums import ProjectStatus
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.pagination import Page
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services import project_service

router = APIRouter(tags=["projects"])

ALL_ROLES = ("technician", "chef_technicien", "admin_supervisor")


def _to_page(result) -> Page[ProjectOut]:
    return Page(
        items=[ProjectOut.model_validate(p) for p in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        pages=result.pages,
    )


@router.get("/projects", response_model=ApiResponse[Page[ProjectOut]])
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    client_id: int | None = None,
    status_filter: ProjectStatus | None = Query(None, alias="status"),
    search: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[Page[ProjectOut]]:
    result = project_service.list_projects(db, page, page_size, client_id, status_filter, search)
    return ApiResponse(data=_to_page(result))


@router.get("/clients/{client_id}/projects", response_model=ApiResponse[Page[ProjectOut]])
def list_projects_for_client(
    client_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[Page[ProjectOut]]:
    result = project_service.list_projects(db, page, page_size, client_id, ProjectStatus.ACTIVE, None)
    return ApiResponse(data=_to_page(result))


@router.get("/projects/{project_id}", response_model=ApiResponse[ProjectOut])
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ALL_ROLES)),
) -> ApiResponse[ProjectOut]:
    project = project_service.get_project(db, project_id)
    return ApiResponse(data=ProjectOut.model_validate(project))


@router.post("/projects", response_model=ApiResponse[ProjectOut])
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ProjectOut]:
    project = project_service.create_project(db, payload)
    return ApiResponse(message="Project created.", data=ProjectOut.model_validate(project))


@router.put("/projects/{project_id}", response_model=ApiResponse[ProjectOut])
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ProjectOut]:
    project = project_service.update_project(db, project_id, payload)
    return ApiResponse(message="Project updated.", data=ProjectOut.model_validate(project))


@router.patch("/projects/{project_id}/archive", response_model=ApiResponse[ProjectOut])
def archive_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("admin_supervisor")),
) -> ApiResponse[ProjectOut]:
    project = project_service.archive_project(db, project_id)
    return ApiResponse(message="Project archived.", data=ProjectOut.model_validate(project))
