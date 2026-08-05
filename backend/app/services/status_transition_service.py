from fastapi import HTTPException, status

from app.models.enums import InterventionStatus

# Ch.9 lifecycle + Ch.17 locking rules, expressed as the single source of truth
# for which status transitions are legal. Every status-changing action in the
# app (submit, technical/administrative approve or reject) must go through
# `ensure_transition_allowed` rather than setting `.status` directly, so this
# table is the only place the state machine needs to be read to understand it.
#
# Two states from Ch.9's literal 9-state list — Submitted (State 4) and
# Technical Approved (State 6) — are never actually stored as a standalone
# `status` value here. Both of Ch.9's own diagrams show them auto-advancing
# to the very next state in the same action (State 4->5, State 6->7), so the
# transition tables below jump straight to the queue-visible state a
# Chef/Admin would actually query on, while `technical_approval_date` /
# `submission_date` still record that the intermediate step happened.
ALLOWED_TRANSITIONS: dict[InterventionStatus, set[InterventionStatus]] = {
    InterventionStatus.DRAFT: {InterventionStatus.PENDING_TECHNICAL_APPROVAL},
    InterventionStatus.PLANNED: {InterventionStatus.PENDING_TECHNICAL_APPROVAL},
    InterventionStatus.IN_PROGRESS: {InterventionStatus.PENDING_TECHNICAL_APPROVAL},
    InterventionStatus.SUBMITTED: {InterventionStatus.PENDING_TECHNICAL_APPROVAL},
    InterventionStatus.PENDING_TECHNICAL_APPROVAL: {
        InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL,
        InterventionStatus.REJECTED,
    },
    InterventionStatus.TECHNICAL_APPROVED: {InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL},
    InterventionStatus.PENDING_ADMINISTRATIVE_APPROVAL: {
        InterventionStatus.FULLY_APPROVED,
        InterventionStatus.REJECTED,
    },
    InterventionStatus.FULLY_APPROVED: set(),  # Ch.9 State 8 — permanently locked, terminal.
    InterventionStatus.REJECTED: {InterventionStatus.PENDING_TECHNICAL_APPROVAL},
}

# Ch.17 — statuses in which the owning technician may still edit content.
EDITABLE_STATUSES = (InterventionStatus.DRAFT, InterventionStatus.REJECTED)

# Statuses that represent "no decision has ever been made yet" for a fresh
# Draft-to-submission path vs. a Rejected-to-resubmission path, used only for
# audit-log wording (both funnel through the same transition rule above).
RESUBMISSION_SOURCE_STATUSES = (InterventionStatus.REJECTED,)


def ensure_transition_allowed(current: InterventionStatus, target: InterventionStatus) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition intervention from '{current.value}' to '{target.value}'.",
        )


def ensure_editable(current: InterventionStatus) -> None:
    if current not in EDITABLE_STATUSES:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Intervention is locked and cannot be edited.")
