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


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_path: str
    content_type: str | None
    upload_date: datetime
    uploaded_by: int


class ApprovalHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    approval_level: str
    approved_by: int
    decision: str
    comment: str | None
    approval_date: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    action: str
    comment: str | None
    created_at: datetime


class InterventionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bi_number: str
    technician_id: int
    client_id: int
    site_id: int
    contract_id: int | None
    project_id: int | None
    warranty_reference_id: int | None
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
