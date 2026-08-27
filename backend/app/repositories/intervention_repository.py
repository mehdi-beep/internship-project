from datetime import date

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.approval_history import ApprovalHistory
from app.models.client import Client
from app.models.client_site import ClientSite
from app.models.enums import InterventionStatus, InterventionType
from app.models.intervention import Intervention
from app.models.intervention_task import InterventionTask
from app.models.intervention_technician import InterventionTechnician


def list_query(
    technician_id: int | None,
    client_id: int | None,
    site_id: int | None,
    status_filter: InterventionStatus | None,
    intervention_type: InterventionType | None,
    date_from: date | None,
    date_to: date | None,
    search: str | None,
    colleague_technician_id: int | None = None,
    city: str | None = None,
    contract_id: int | None = None,
    project_id: int | None = None,
    status_in: list[InterventionStatus] | None = None,
) -> Select:
    stmt = select(Intervention)
    if technician_id is not None:
        stmt = stmt.where(Intervention.technician_id == technician_id)
    if client_id is not None:
        stmt = stmt.where(Intervention.client_id == client_id)
    if site_id is not None:
        stmt = stmt.where(Intervention.site_id == site_id)
    if status_filter is not None:
        stmt = stmt.where(Intervention.status == status_filter)
    # A separate, independent multi-status filter (not merged into
    # status_filter above) — used by frontend "grouped" tabs like
    # MyInterventionsPage's "Submitted" tab, which spans 4 distinct lifecycle
    # statuses. Keeping it a second parameter rather than overloading
    # status_filter to sometimes be a list avoids changing the meaning of the
    # existing single-status query param for every other caller.
    if status_in:
        stmt = stmt.where(Intervention.status.in_(status_in))
    if intervention_type is not None:
        stmt = stmt.where(Intervention.intervention_type == intervention_type)
    if date_from is not None:
        stmt = stmt.where(Intervention.intervention_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Intervention.intervention_date <= date_to)
    if contract_id is not None:
        stmt = stmt.where(Intervention.contract_id == contract_id)
    if project_id is not None:
        stmt = stmt.where(Intervention.project_id == project_id)
    # `city` and `search` both need ClientSite — joined at most once even if
    # both filters are active together, since SQLAlchemy rejects the same
    # table appearing twice in one FROM clause.
    site_joined = False
    if city:
        stmt = stmt.join(ClientSite, ClientSite.id == Intervention.site_id).where(ClientSite.city == city)
        site_joined = True
    if search:
        # Matches the BI number (the identifier technicians/supervisors actually
        # know by heart) as well as the client/site name, since in practice users
        # searching this list often only remember "the Acme job", not BI000123.
        # Both are OUTER joins (Task 5): a permanently deleted Client/ClientSite
        # detaches (nulls) the link on old interventions rather than deleting
        # them, so an inner join here would make those interventions silently
        # unfindable by name search forever, even though they still legitimately
        # exist and are visible in every other view of this same list.
        pattern = f"%{search}%"
        stmt = stmt.outerjoin(Client, Client.id == Intervention.client_id)
        if not site_joined:
            stmt = stmt.outerjoin(ClientSite, ClientSite.id == Intervention.site_id)
        stmt = stmt.where(
            or_(
                Intervention.bi_number.ilike(pattern),
                Client.client_name.ilike(pattern),
                ClientSite.site_name.ilike(pattern),
            )
        )
    if colleague_technician_id is not None:
        stmt = stmt.join(InterventionTechnician, InterventionTechnician.intervention_id == Intervention.id).where(
            InterventionTechnician.user_id == colleague_technician_id
        )
    return stmt.order_by(Intervention.created_at.desc())


def get(db: Session, intervention_id: int) -> Intervention | None:
    return db.get(Intervention, intervention_id)


def get_with_details(db: Session, intervention_id: int) -> Intervention | None:
    stmt = (
        select(Intervention)
        .options(
            selectinload(Intervention.tasks),
            selectinload(Intervention.attachments),
            selectinload(Intervention.approval_history).selectinload(ApprovalHistory.approver),
            selectinload(Intervention.audit_log),
            selectinload(Intervention.colleague_technicians),
            selectinload(Intervention.warranty_reference),
        )
        .where(Intervention.id == intervention_id)
    )
    return db.scalar(stmt)


def find_by_bi_number(db: Session, bi_number: str) -> Intervention | None:
    return db.scalar(select(Intervention).where(Intervention.bi_number == bi_number))


def create(db: Session, data: dict) -> Intervention:
    intervention = Intervention(**data)
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    return intervention


def update(db: Session, intervention: Intervention, data: dict) -> Intervention:
    for key, value in data.items():
        setattr(intervention, key, value)
    db.commit()
    db.refresh(intervention)
    return intervention


def replace_tasks(db: Session, intervention_id: int, travail_ids: list[int]) -> None:
    db.query(InterventionTask).filter(InterventionTask.intervention_id == intervention_id).delete()
    for travail_id in travail_ids:
        db.add(InterventionTask(intervention_id=intervention_id, travail_id=travail_id))
    db.commit()


def replace_colleague_technicians(db: Session, intervention_id: int, user_ids: list[int]) -> None:
    db.query(InterventionTechnician).filter(InterventionTechnician.intervention_id == intervention_id).delete()
    for user_id in user_ids:
        db.add(InterventionTechnician(intervention_id=intervention_id, user_id=user_id))
    db.commit()


def set_status(db: Session, intervention: Intervention, status_value: InterventionStatus) -> Intervention:
    intervention.status = status_value
    db.commit()
    db.refresh(intervention)
    return intervention
