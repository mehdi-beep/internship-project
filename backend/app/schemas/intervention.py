from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.enums import InterventionStatus, InterventionType, LocationType


class InterventionCreate(BaseModel):
    client_id: int
    site_id: int
    contact_person: str | None = None

    intervention_type: InterventionType
    contract_id: int | None = None
    project_id: int | None = None
    warranty_reference_bi: str | None = None

    location_type: LocationType

    intervention_date: date
    start_time: time
    end_time: time
    lunch_break_minutes: int = 0

    number_of_technicians: int = 1
    travail_ids: list[int] = []
    colleague_technician_ids: list[int] = []
    technical_report: str | None = None

    @model_validator(mode="after")
    def _validate_type_fields(self) -> "InterventionCreate":
        if self.intervention_type == InterventionType.CONTRACT and self.contract_id is None:
            raise ValueError("Contract is required for a Contract intervention.")
        if self.intervention_type == InterventionType.PROJECT and self.project_id is None:
            raise ValueError("Project is required for a Project intervention.")
        if self.intervention_type == InterventionType.WARRANTY and not self.warranty_reference_bi:
            raise ValueError("Warranty reference BI number is required for a Warranty intervention.")
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time.")
        return self


class InterventionUpdate(InterventionCreate):
    pass


class InterventionTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    travail_id: int


class InterventionTechnicianOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_path: str
    content_type: str | None
    upload_date: datetime
    # Task 5: nullable because permanently deleting the uploader detaches
    # (never deletes) the attachment — deleted_user_label carries their name
    # forward once uploaded_by is cleared.
    uploaded_by: int | None
    deleted_user_label: str | None = None


class ApprovalHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    approval_level: str
    # Task 5: nullable for the same reason as AttachmentOut.uploaded_by above.
    # approver_name already covers the display fallback (resolved server-side
    # in intervention_service._resolve_display_fields, preferring
    # deleted_user_label once the live approver is gone).
    approved_by: int | None
    approver_name: str | None = None
    decision: str
    comment: str | None
    approval_date: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # Task 5: nullable for the same reason as the fields above.
    user_id: int | None
    deleted_user_label: str | None = None
    action: str
    comment: str | None
    created_at: datetime


class InterventionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bi_number: str
    # Task 5: nullable because permanently deleting the lead technician
    # detaches (never deletes) the intervention — deleted_user_label carries
    # their name forward once technician_id is cleared.
    technician_id: int | None
    deleted_user_label: str | None = None
    # Task 5: client_id/site_id are nullable because permanently deleting a
    # Client, ClientSite, Contract or Project detaches (never deletes) the
    # interventions that reference it — the intervention keeps its BI number,
    # dates, duration, points and full approval/audit history regardless.
    client_id: int | None
    site_id: int | None
    contract_id: int | None
    project_id: int | None
    warranty_reference_id: int | None
    warranty_reference_bi_number: str | None = None
    intervention_type: InterventionType
    location_type: LocationType
    intervention_date: date
    start_time: time
    end_time: time
    lunch_break_minutes: int
    net_duration_minutes: int
    number_of_technicians: int
    technical_report: str | None
    contact_person: str | None
    status: InterventionStatus
    submission_date: datetime | None
    technical_approval_date: datetime | None
    administrative_approval_date: datetime | None
    points_earned: int
    created_at: datetime
    updated_at: datetime


class InterventionDetailOut(InterventionOut):
    tasks: list[InterventionTaskOut] = []
    attachments: list[AttachmentOut] = []
    approval_history: list[ApprovalHistoryOut] = []
    audit_log: list[AuditLogOut] = []
    colleague_technicians: list[InterventionTechnicianOut] = []
