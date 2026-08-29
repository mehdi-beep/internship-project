"""Task 5 — permanent deletion safety checks.

The project's data model is built around `ON DELETE RESTRICT` and the rule that
audit-sensitive tables (`interventions`, `approval_history`, `audit_log`) are
**never** deleted (DATABASE_SCHEMA.md Ch.49/Ch.50, Rule 9/Ch.20). Permanent
deletion therefore cannot cascade — doing so would destroy exactly the
historical record the application exists to preserve.

The rule implemented here:

    Any entity may be permanently deleted, even when other rows reference it.
    Those referencing rows are never destroyed — the reference is detached
    (its foreign key cleared) instead, and where the reference was to a User
    specifically, that user's name is frozen into a plain text label first,
    since — unlike a client or a site — a user has no other record of their
    own name once their row is gone.

Nothing is ever silently destroyed, and no referencing row ever loses its own
data to make a delete succeed — it only ever loses the one link to the record
that was deleted.
"""

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.approval_history import ApprovalHistory
from app.models.attachment import Attachment
from app.models.audit_log import AuditLog
from app.models.client import Client
from app.models.client_site import ClientSite
from app.models.contract import Contract
from app.models.intervention import Intervention
from app.models.intervention_task import InterventionTask
from app.models.intervention_technician import InterventionTechnician
from app.models.notification import Notification
from app.models.planning import Planning
from app.models.project import Project
from app.models.role import RoleName
from app.models.travail import Travail
from app.models.user import User


@dataclass(frozen=True)
class Blocker:
    """One reason a permanent deletion cannot proceed."""

    label: str  # human-readable, shown to the Administrator
    count: int


def _count(db: Session, model, column, value) -> int:
    return db.scalar(select(func.count()).select_from(model).where(column == value)) or 0


def user_blockers(db: Session, user_id: int) -> list[Blocker]:
    """A user can be referenced from eight places. None of these block a
    delete any more — they're reported as impacts (see check_deletable),
    and detach_references() below freezes this user's name into each
    referencing row before clearing the link, so old approvals, audit
    entries, uploads, interventions and planning entries keep showing who
    did them even after the account is gone."""
    checks = [
        ("interventions where they are the lead technician", Intervention, Intervention.technician_id),
        ("approval decisions they recorded", ApprovalHistory, ApprovalHistory.approved_by),
        ("attachments they uploaded", Attachment, Attachment.uploaded_by),
        ("audit-log entries", AuditLog, AuditLog.user_id),
        ("interventions they assisted on", InterventionTechnician, InterventionTechnician.user_id),
        ("notifications addressed to them", Notification, Notification.user_id),
        ("planning entries assigned to them", Planning, Planning.technician_id),
        ("planning entries they created", Planning, Planning.created_by),
    ]
    return [Blocker(label, n) for label, model, col in checks if (n := _count(db, model, col, user_id)) > 0]


def client_blockers(db: Session, client_id: int) -> list[Blocker]:
    checks = [
        ("interventions", Intervention, Intervention.client_id),
        ("planning entries", Planning, Planning.client_id),
        ("client sites", ClientSite, ClientSite.client_id),
        ("contracts", Contract, Contract.client_id),
        ("projects", Project, Project.client_id),
    ]
    return [Blocker(label, n) for label, model, col in checks if (n := _count(db, model, col, client_id)) > 0]


def client_site_blockers(db: Session, site_id: int) -> list[Blocker]:
    checks = [
        ("interventions performed at this site", Intervention, Intervention.site_id),
        ("planning entries at this site", Planning, Planning.site_id),
    ]
    return [Blocker(label, n) for label, model, col in checks if (n := _count(db, model, col, site_id)) > 0]


def contract_blockers(db: Session, contract_id: int) -> list[Blocker]:
    checks = [("interventions linked to this contract", Intervention, Intervention.contract_id)]
    return [Blocker(label, n) for label, model, col in checks if (n := _count(db, model, col, contract_id)) > 0]


def project_blockers(db: Session, project_id: int) -> list[Blocker]:
    checks = [("interventions linked to this project", Intervention, Intervention.project_id)]
    return [Blocker(label, n) for label, model, col in checks if (n := _count(db, model, col, project_id)) > 0]


def travail_blockers(db: Session, travail_id: int) -> list[Blocker]:
    checks = [("interventions that include this travail", InterventionTask, InterventionTask.travail_id)]
    return [Blocker(label, n) for label, model, col in checks if (n := _count(db, model, col, travail_id)) > 0]


_ENTITY_CHECKS = {
    "user": (User, user_blockers, "user"),
    "client": (Client, client_blockers, "client"),
    "client_site": (ClientSite, client_site_blockers, "client site"),
    "contract": (Contract, contract_blockers, "contract"),
    "project": (Project, project_blockers, "project"),
    "travail": (Travail, travail_blockers, "travail"),
}


def check_deletable(db: Session, entity_key: str, entity_id: int) -> list[Blocker]:
    """Returns what currently references this entity.

    NOTE: for clients/sites/contracts/projects/travaux these are *impacts*,
    not blockers — the deletion proceeds and these references are detached
    (see `detach_references`). They are still reported so the Administrator
    can see the consequences before confirming. For users they remain true
    blockers (see `ensure_deletable`).
    """
    _, blocker_fn, _ = _ENTITY_CHECKS[entity_key]
    return blocker_fn(db, entity_id)


def is_deletable(entity_key: str, blockers: list[Blocker]) -> bool:
    """The single source of truth for the `deletable` flag the `/deletion-
    check` endpoints return to the UI. Every entity, including User, is
    always reported deletable — `blockers` is purely informational, listing
    the impacts the Administrator will see a warning about before confirming,
    never a reason a delete is refused. `_PROTECTED_ENTITIES` is kept as an
    empty set (rather than removed outright) so a future entity type can be
    hard-blocked again without restructuring this function."""
    if entity_key in _PROTECTED_ENTITIES:
        return not blockers
    return True


# No entity is hard-blocked from permanent deletion any more — every
# reference a deleted record leaves behind is detached, not destroyed (see
# detach_references). Users were the one historical exception (they are the
# *actor* in the audit trail, not just a piece of reference data), which is
# why deleting one now specifically freezes their name into a
# deleted_user_label-style column on every row that used to reference them,
# immediately before the link is cleared — unlike a client or a site, a user
# has no other record of their own name once their row is gone.
_PROTECTED_ENTITIES: set[str] = set()


def ensure_deletable(db: Session, entity_key: str, entity_id: int) -> None:
    """A no-op for entity TYPES today (`_PROTECTED_ENTITIES` is empty —
    nothing is hard-blocked any more at that level), kept in place and still
    called by every entity's delete service so a future entity type can be
    hard-blocked again by adding it to `_PROTECTED_ENTITIES` without having
    to re-wire six call sites.

    The one exception isn't an entity type, it's a single specific ROW: the
    CEO account. There can only ever be one (enforced separately, at
    creation, in user_service._ensure_single_ceo), and per explicit
    instruction it must be immune to permanent deletion as well as
    deactivation, unconditionally — not "unless nothing references it," the
    way every other user used to work before Task 6. Checked here rather
    than via _PROTECTED_ENTITIES because that mechanism blocks an entire
    entity TYPE ("user"), and Task 6 deliberately made every OTHER user
    genuinely deletable — only this one specific row is exempt."""
    if entity_key == "user":
        user = db.get(User, entity_id)
        if user is not None and user.role.name == RoleName.CEO:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The CEO account cannot be permanently deleted.",
            )
    if entity_key not in _PROTECTED_ENTITIES:
        return
    _, _, noun = _ENTITY_CHECKS[entity_key]
    blockers = check_deletable(db, entity_key, entity_id)
    if not blockers:
        return
    detail = (
        f"This {noun} cannot be permanently deleted because it is recorded as the actor in "
        + ", ".join(f"{b.count} {b.label}" for b in blockers)
        + ". Removing it would make the audit trail unattributable. Deactivate the account instead —"
        " it will no longer be able to log in, and all history stays intact."
    )
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def detach_references(db: Session, entity_key: str, entity_id: int) -> None:
    """Clears every reference to this entity so it can be deleted **without
    destroying the referencing rows**.

    Interventions, planning entries, approvals and audit-log rows all survive
    with their own data fully intact; only the pointer to the deleted record
    is nulled. The one exception is `intervention_tasks`, which is a pure
    join row — a task line with no travail carries no information at all, so
    those link rows are removed rather than orphaned. No intervention,
    approval or audit row is ever deleted here.
    """
    if entity_key == "client":
        db.query(Intervention).filter(Intervention.client_id == entity_id).update(
            {Intervention.client_id: None}, synchronize_session=False
        )
        db.query(Planning).filter(Planning.client_id == entity_id).update(
            {Planning.client_id: None}, synchronize_session=False
        )
        # Child reference-data rows are detached too, so deleting a client
        # doesn't silently delete its sites/contracts/projects.
        db.query(ClientSite).filter(ClientSite.client_id == entity_id).update(
            {ClientSite.client_id: None}, synchronize_session=False
        )
        db.query(Contract).filter(Contract.client_id == entity_id).update(
            {Contract.client_id: None}, synchronize_session=False
        )
        db.query(Project).filter(Project.client_id == entity_id).update(
            {Project.client_id: None}, synchronize_session=False
        )
    elif entity_key == "client_site":
        db.query(Intervention).filter(Intervention.site_id == entity_id).update(
            {Intervention.site_id: None}, synchronize_session=False
        )
        db.query(Planning).filter(Planning.site_id == entity_id).update(
            {Planning.site_id: None}, synchronize_session=False
        )
    elif entity_key == "contract":
        db.query(Intervention).filter(Intervention.contract_id == entity_id).update(
            {Intervention.contract_id: None}, synchronize_session=False
        )
    elif entity_key == "project":
        db.query(Intervention).filter(Intervention.project_id == entity_id).update(
            {Intervention.project_id: None}, synchronize_session=False
        )
    elif entity_key == "travail":
        # Join rows only — the interventions themselves are untouched.
        db.query(InterventionTask).filter(InterventionTask.travail_id == entity_id).delete(
            synchronize_session=False
        )
    elif entity_key == "user":
        _detach_user_references(db, entity_id)
    db.commit()


def _detach_user_references(db: Session, user_id: int) -> None:
    """The one detach path that needs a value, not just a null, before it can
    clear a link: a client or a site keeps its own name on its own row after
    being detached from, but a user's name only ever lived on the User row
    itself — once that row is gone there is nowhere else to read it from. So
    every referencing row gets that name frozen into a plain text label
    *before* its foreign key is cleared, using the user's live name at the
    moment of deletion (never re-derived afterwards, since after this point
    there is no live row left to re-derive it from).

    `intervention_technicians` (colleague-technician participation) is
    deliberately handled differently, by deletion rather than freezing — see
    its own comment below.
    """
    user = db.get(User, user_id)
    label = f"{user.first_name} {user.last_name}".strip() if user else f"Deleted user #{user_id}"

    db.query(Intervention).filter(Intervention.technician_id == user_id).update(
        {Intervention.technician_id: None, Intervention.deleted_user_label: label}, synchronize_session=False
    )
    db.query(ApprovalHistory).filter(ApprovalHistory.approved_by == user_id).update(
        {ApprovalHistory.approved_by: None, ApprovalHistory.deleted_user_label: label}, synchronize_session=False
    )
    db.query(AuditLog).filter(AuditLog.user_id == user_id).update(
        {AuditLog.user_id: None, AuditLog.deleted_user_label: label}, synchronize_session=False
    )
    db.query(Attachment).filter(Attachment.uploaded_by == user_id).update(
        {Attachment.uploaded_by: None, Attachment.deleted_user_label: label}, synchronize_session=False
    )
    db.query(Planning).filter(Planning.technician_id == user_id).update(
        {Planning.technician_id: None, Planning.deleted_technician_label: label}, synchronize_session=False
    )
    db.query(Planning).filter(Planning.created_by == user_id).update(
        {Planning.created_by: None, Planning.deleted_creator_label: label}, synchronize_session=False
    )
    db.query(Notification).filter(Notification.user_id == user_id).update(
        {Notification.user_id: None, Notification.deleted_user_label: label}, synchronize_session=False
    )
    # A colleague-technician row is a pure join row (intervention_id, user_id,
    # nothing else) — the same shape as intervention_tasks on travail
    # deletion. A frozen name on a row with no working link left isn't
    # meaningful the way a frozen approver name is (an approval's real
    # content is the *decision*; a colleague row's entire content IS the
    # link), so this is removed rather than orphaned, exactly like the
    # travail branch above.
    db.query(InterventionTechnician).filter(InterventionTechnician.user_id == user_id).delete(
        synchronize_session=False
    )
