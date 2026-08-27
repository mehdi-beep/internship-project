from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.enums import ProjectStatus


def list_query(
    client_id: int | None,
    status_filter: ProjectStatus | None,
    search: str | None,
    start_date_from: date | None = None,
    start_date_to: date | None = None,
) -> Select:
    stmt = select(Project)
    if client_id is not None:
        stmt = stmt.where(Project.client_id == client_id)
    if status_filter is not None:
        stmt = stmt.where(Project.status == status_filter)
    if start_date_from is not None:
        stmt = stmt.where(Project.start_date >= start_date_from)
    if start_date_to is not None:
        stmt = stmt.where(Project.start_date <= start_date_to)
    if search:
        stmt = stmt.where(Project.project_name.ilike(f"%{search}%"))
    return stmt.order_by(Project.project_name)


def get(db: Session, project_id: int) -> Project | None:
    return db.get(Project, project_id)


def create(db: Session, data: dict) -> Project:
    project = Project(**data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update(db: Session, project: Project, data: dict) -> Project:
    for key, value in data.items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


def set_status(db: Session, project: Project, status_value: ProjectStatus) -> Project:
    project.status = status_value
    db.commit()
    db.refresh(project)
    return project


def delete(db: Session, project: Project) -> None:
    """Hard delete. Callers MUST run deletion_service.ensure_deletable first —
    the model's foreign keys are ON DELETE RESTRICT by design, so this is only
    ever reached for a row nothing references."""
    db.delete(project)
    db.commit()
