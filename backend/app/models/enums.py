import enum


class InterventionStatus(str, enum.Enum):
    """The 9-state lifecycle from project_specifications.md Chapter 9."""

    DRAFT = "draft"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    PENDING_TECHNICAL_APPROVAL = "pending_technical_approval"
    TECHNICAL_APPROVED = "technical_approved"
    PENDING_ADMINISTRATIVE_APPROVAL = "pending_administrative_approval"
    FULLY_APPROVED = "fully_approved"
    REJECTED = "rejected"


class InterventionType(str, enum.Enum):
    STANDARD = "standard"
    CONTRACT = "contract"
    PROJECT = "project"
    WARRANTY = "warranty"


class LocationType(str, enum.Enum):
    SUR_SITE = "sur_site"
    ATELIER = "atelier"


class Priority(str, enum.Enum):
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ApprovalLevel(str, enum.Enum):
    TECHNICAL = "technical"
    ADMINISTRATIVE = "administrative"


class ApprovalDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class ContractStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class PlanningStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AuditAction(str, enum.Enum):
    """Ch.18 / Ch.151 audit trail action types."""

    CREATED = "created"
    DRAFT_SAVED = "draft_saved"
    MODIFIED = "modified"
    SUBMITTED = "submitted"
    TECHNICAL_APPROVED = "technical_approved"
    ADMINISTRATIVE_APPROVED = "administrative_approved"
    REJECTED = "rejected"
    RESUBMITTED = "resubmitted"
