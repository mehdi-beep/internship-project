from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.enums import ProjectStatus
from app.repositories import client_repository, project_repository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.pagination import Page
from app.utils.pagination import paginate


def list_projects(
    db: Session, page: int, page_size: int, client_id: int | None, status_filter: ProjectStatus | None, search: str | None
) -> Page:
    stmt = project_repository.list_query(client_id, status_filter, search)
    return paginate(db, stmt, page, page_size)


def get_project(db: Session, project_id: int) -> Project:
    project = project_repository.get(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def create_project(db: Session, payload: ProjectCreate) -> Project:
    if client_repository.get(db, payload.client_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")
    return project_repository.create(db, payload.model_dump())


def update_project(db: Session, project_id: int, payload: ProjectUpdate) -> Project:
    project = get_project(db, project_id)
    return project_repository.update(db, project, payload.model_dump())


def archive_project(db: Session, project_id: int) -> Project:
    project = get_project(db, project_id)
    return project_repository.set_status(db, project, ProjectStatus.ARCHIVED)
