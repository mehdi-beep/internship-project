from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import AuditAction, InterventionStatus, InterventionType
from app.models.intervention import Intervention
from app.models.role import RoleName
from app.repositories import (
    attachment_repository,
    audit_log_repository,
    client_repository,
    client_site_repository,
    contract_repository,
    intervention_repository,
    project_repository,
    travail_repository,
    user_repository,
)
from app.schemas.intervention import InterventionCreate, InterventionUpdate
from app.schemas.pagination import Page
from app.services import business_logic_service, notification_service, status_transition_service
from app.services.status_transition_service import EDITABLE_STATUSES
from app.utils.bi_number import next_bi_number
from app.utils.pagination import paginate


def _validate_colleague_technicians(db: Session, lead_technician_id: int, colleague_technician_ids: list[int]) -> None:
    if lead_technician_id in colleague_technician_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The lead technician cannot also be listed as a colleague."
        )
    if len(set(colleague_technician_ids)) != len(colleague_technician_ids):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate colleague technicians are not allowed.")
    for colleague_id in colleague_technician_ids:
        colleague = user_repository.get(db, colleague_id)
        if colleague is None or not colleague.active or colleague.role.name != RoleName.TECHNICIAN:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Technician {colleague_id} not found.")


def _validate_references(db: Session, payload: InterventionCreate) -> tuple[int | None, int | None, int | None]:
    if client_repository.get(db, payload.client_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found.")

    site = client_site_repository.get(db, payload.site_id)
    if site is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client site not found.")
    if site.client_id != payload.client_id:
        # Rule 2 — the site must belong to the selected client.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Site does not belong to the selected client.")

    contract_id = None
    if payload.intervention_type == InterventionType.CONTRACT:
        contract = contract_repository.get(db, payload.contract_id)  # type: ignore[arg-type]
        if contract is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")
        contract_id = contract.id

    project_id = None
    if payload.intervention_type == InterventionType.PROJECT:
        project = project_repository.get(db, payload.project_id)  # type: ignore[arg-type]
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
        project_id = project.id

    warranty_reference_id = None
    if payload.intervention_type == InterventionType.WARRANTY:
        referenced = intervention_repository.find_by_bi_number(db, payload.warranty_reference_bi)  # type: ignore[arg-type]
        if referenced is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced BI number does not exist.")
        warranty_reference_id = referenced.id

    for travail_id in payload.travail_ids:
        if travail_repository.get(db, travail_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Travail {travail_id} not found.")

    return contract_id, project_id, warranty_reference_id


def list_interventions(
    db: Session,
    current_user_id: int,
    is_privileged: bool,
    page: int,
    page_size: int,
    technician_id: int | None,
    client_id: int | None,
    site_id: int | None,
    status_filter: InterventionStatus | None,
    intervention_type: InterventionType | None,
    date_from: date | None,
    date_to: date | None,
    search: str | None,
    colleague_technician_id: int | None = None,
) -> Page:
    # Ch.16 — a technician may only see their own interventions. A technician
    # requesting the colleague_technician_id filter may only ever request it for
    # themselves (never another technician's participation).
    if not is_privileged:
        if colleague_technician_id is not None:
            colleague_technician_id = current_user_id
            technician_id = None
        else:
            technician_id = current_user_id
    stmt = intervention_repository.list_query(
        technician_id,
        client_id,
        site_id,
        status_filter,
        intervention_type,
        date_from,
        date_to,
        search,
        colleague_technician_id,
    )
    return paginate(db, stmt, page, page_size)


def get_intervention(db: Session, intervention_id: int) -> Intervention:
    intervention = intervention_repository.get_with_details(db, intervention_id)
    if intervention is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention not found.")
    return intervention


def _ensure_visible(intervention: Intervention, current_user_id: int, is_privileged: bool) -> None:
    if not is_privileged and intervention.technician_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")


def get_intervention_for_user(db: Session, intervention_id: int, current_user_id: int, is_privileged: bool) -> Intervention:
    intervention = get_intervention(db, intervention_id)
    _ensure_visible(intervention, current_user_id, is_privileged)
    return intervention


def create_intervention(
    db: Session, payload: InterventionCreate, technician_id: int, submit: bool
) -> Intervention:
    contract_id, project_id, warranty_reference_id = _validate_references(db, payload)
    _validate_colleague_technicians(db, technician_id, payload.colleague_technician_ids)
    net_duration = business_logic_service.calculate_net_duration_minutes(
        payload.start_time, payload.end_time, payload.lunch_break_minutes
    )

    if submit and not payload.travail_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one travail is required to submit.")

    intervention = intervention_repository.create(
        db,
        {
            "bi_number": next_bi_number(db),
            "technician_id": technician_id,
            "client_id": payload.client_id,
            "site_id": payload.site_id,
            "contract_id": contract_id,
            "project_id": project_id,
            "warranty_reference_id": warranty_reference_id,
            "intervention_type": payload.intervention_type,
            "location_type": payload.location_type,
            "intervention_date": payload.intervention_date,
            "start_time": payload.start_time,
            "end_time": payload.end_time,
            "lunch_break_minutes": payload.lunch_break_minutes,
            "net_duration_minutes": net_duration,
            "number_of_technicians": payload.number_of_technicians,
            "technical_report": payload.technical_report,
            "contact_person": payload.contact_person,
            "status": InterventionStatus.DRAFT,
        },
    )
    intervention_repository.replace_tasks(db, intervention.id, payload.travail_ids)
    intervention_repository.replace_colleague_technicians(db, intervention.id, payload.colleague_technician_ids)
    audit_log_repository.create(db, intervention_id=intervention.id, user_id=technician_id, action=AuditAction.CREATED)

    if submit:
        intervention = submit_intervention(db, intervention.id, technician_id, is_privileged=False)
    else:
        audit_log_repository.create(db, intervention_id=intervention.id, user_id=technician_id, action=AuditAction.DRAFT_SAVED)

    return get_intervention(db, intervention.id)


def update_intervention(
    db: Session, intervention_id: int, payload: InterventionUpdate, current_user_id: int
) -> Intervention:
    intervention = get_intervention(db, intervention_id)
    if intervention.technician_id != current_user_id:
        # Ch.15 — only the owning technician may edit; nobody else can modify content.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    status_transition_service.ensure_editable(intervention.status)  # Ch.17 — locked once submitted/approved.

    contract_id, project_id, warranty_reference_id = _validate_references(db, payload)
    _validate_colleague_technicians(db, current_user_id, payload.colleague_technician_ids)
    net_duration = business_logic_service.calculate_net_duration_minutes(
        payload.start_time, payload.end_time, payload.lunch_break_minutes
    )

    was_rejected = intervention.status == InterventionStatus.REJECTED

    intervention = intervention_repository.update(
        db,
        intervention,
        {
            "client_id": payload.client_id,
            "site_id": payload.site_id,
            "contract_id": contract_id,
            "project_id": project_id,
            "warranty_reference_id": warranty_reference_id,
            "intervention_type": payload.intervention_type,
            "location_type": payload.location_type,
            "intervention_date": payload.intervention_date,
            "start_time": payload.start_time,
            "end_time": payload.end_time,
            "lunch_break_minutes": payload.lunch_break_minutes,
            "net_duration_minutes": net_duration,
            "number_of_technicians": payload.number_of_technicians,
            "technical_report": payload.technical_report,
            "contact_person": payload.contact_person,
            # Ch.9 State 9 — correcting a Rejected intervention keeps it editable
            # (Draft) until the technician explicitly resubmits.
            "status": InterventionStatus.DRAFT if was_rejected else intervention.status,
        },
    )
    intervention_repository.replace_tasks(db, intervention.id, payload.travail_ids)
    intervention_repository.replace_colleague_technicians(db, intervention.id, payload.colleague_technician_ids)
    audit_log_repository.create(db, intervention_id=intervention.id, user_id=current_user_id, action=AuditAction.MODIFIED)

    return get_intervention(db, intervention.id)


def submit_intervention(db: Session, intervention_id: int, current_user_id: int, is_privileged: bool) -> Intervention:
    intervention = get_intervention(db, intervention_id)
    if intervention.technician_id != current_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    status_transition_service.ensure_transition_allowed(
        intervention.status, InterventionStatus.PENDING_TECHNICAL_APPROVAL
    )

    # Ch.24 / Rule 7 — at least one attachment is mandatory before submission.
    if attachment_repository.count_for_intervention(db, intervention.id) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one attached image of the signed paper BI is required to submit.",
        )
    if not intervention.tasks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one travail is required to submit.")

    # Status alone can't tell "first submission" from "resubmission-after-
    # rejection" here, since editing a Rejected intervention already resets it
    # to Draft (Ch.9 State 9) before this ever runs — the audit log is checked
    # instead, since it's the one place that history is preserved.
    was_rejected = audit_log_repository.has_ever_been_rejected(db, intervention.id)
    submission_time = datetime.now(timezone.utc)
    intervention = intervention_repository.update(
        db,
        intervention,
        {
            # Ch.24 sets status to Submitted; Ch.9's State 4->5 transition to
            # Pending Technical Approval happens automatically in the same action
            # (mirroring the equally automatic Technical Approved -> Pending
            # Administrative Approval transition in Ch.25), so this is stored
            # directly as the Chef's queue-visible state.
            "status": InterventionStatus.PENDING_TECHNICAL_APPROVAL,
            "submission_date": submission_time,
            # Ch.28 — computed automatically at submission time; technicians
            # cannot influence this (it is never accepted as request input).
            "points_earned": business_logic_service.calculate_points(submission_time),
        },
    )
    action = AuditAction.RESUBMITTED if was_rejected else AuditAction.SUBMITTED
    audit_log_repository.create(db, intervention_id=intervention.id, user_id=current_user_id, action=action)
    notification_service.notify_chefs_of_submission(db, intervention.bi_number, intervention.id)

    return get_intervention(db, intervention.id)


def get_history(db: Session, intervention_id: int, current_user_id: int, is_privileged: bool) -> Intervention:
    return get_intervention_for_user(db, intervention_id, current_user_id, is_privileged)
