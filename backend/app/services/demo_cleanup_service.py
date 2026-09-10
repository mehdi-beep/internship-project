"""One-time demo-data cleanup — CEO-only, irreversible, and structurally
incapable of ever touching a real intervention.

Rule 9 (Ch.20) / Intervention's own class docstring: interventions are never
deleted, only status-transitioned — every other deletion feature in this
codebase (deletion_service.py) deliberately respects that by detaching
references rather than ever removing an Intervention row. This module is the
one deliberate, narrow exception, and it is not a general-purpose override of
Rule 9: it deletes rows only when `created_at` predates DEMO_DATA_CUTOFF, a
constant fixed once at the moment this feature shipped — not `datetime.now()`,
which would let the boundary drift forward on every server restart and
eventually swallow real data. Everything before the cutoff was seeded/created
during development, before this system had any real intervention in it;
nothing created after it can ever be reached by this code path, by any role,
including the CEO.

`app_settings.demo_interventions_deleted_at` is the actual gate — set once,
in the same transaction as the deletion, and never cleared. Even though a
second run would also find zero rows before the cutoff (the cutoff cannot
move), the endpoint still refuses outright once this flag is set, as defense
in depth rather than relying solely on the query happening to come back
empty.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.approval_history import ApprovalHistory
from app.models.attachment import Attachment
from app.models.audit_log import AuditLog
from app.models.intervention import Intervention
from app.models.intervention_task import InterventionTask
from app.models.intervention_technician import InterventionTechnician
from app.models.notification import Notification
from app.models.planning import Planning
from app.repositories import app_settings_repository
from config import get_settings

# Fixed once, at the moment this feature was built (2026-09-10) — the real
# UTC "now" read while writing this module, rounded forward a few minutes so
# nothing legitimately created while finishing this feature is excluded. Every
# row in dev.db at that time predates this (latest recorded created_at was
# 2026-09-09 21:49:11), so the entire pre-existing dataset is demo data.
# Intentionally NOT datetime.now(): that would recompute "now" on every import
# / server restart, permanently defeating the "fixed once" guarantee this
# feature depends on.
DEMO_DATA_CUTOFF = datetime(2026, 9, 10, 19, 45, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class DemoDataStatus:
    """What the frontend confirmation dialog needs before the CEO commits:
    how many rows are eligible, and whether this has already been done."""

    eligible_count: int
    already_deleted: bool
    deleted_at: datetime | None


def _demo_intervention_ids(db: Session) -> list[int]:
    stmt = select(Intervention.id).where(Intervention.created_at < DEMO_DATA_CUTOFF)
    return list(db.scalars(stmt).all())


def _get_settings_without_committing(db: Session):
    # Prefers the plain, non-creating read: delete_demo_interventions below
    # needs the settings row available WITHOUT an early db.commit() splitting
    # its single transaction (get_or_create commits immediately if the row is
    # missing). In every real deployment the row already exists — seeded
    # unconditionally by the app_settings migration itself — so this always
    # takes the plain-read path in practice; get_or_create is kept only as a
    # fallback for a database that somehow predates that migration, where its
    # one-time bootstrap commit (creating a settings row with
    # demo_interventions_deleted_at still None) is harmless on its own even if
    # something later in the same call fails.
    settings = app_settings_repository.get(db)
    if settings is None:
        settings = app_settings_repository.get_or_create(db)
    return settings


def get_status(db: Session) -> DemoDataStatus:
    settings = _get_settings_without_committing(db)
    count = db.scalar(
        select(func.count()).select_from(Intervention).where(Intervention.created_at < DEMO_DATA_CUTOFF)
    ) or 0
    return DemoDataStatus(
        eligible_count=count,
        already_deleted=settings.demo_interventions_deleted_at is not None,
        deleted_at=settings.demo_interventions_deleted_at,
    )


def _delete_attachment_files(db: Session, intervention_ids: list[int]) -> None:
    """Removes the uploaded files from disk before their Attachment rows are
    deleted — mirrors attachment_service.delete_attachment's own
    unlink-if-exists pattern, the only existing precedent in this codebase for
    cleaning up an attachment's file alongside its row."""
    upload_folder = Path(get_settings().upload_folder)
    stmt = select(Attachment.file_path).where(Attachment.intervention_id.in_(intervention_ids))
    for (file_path,) in db.execute(stmt):
        absolute_path = upload_folder / file_path
        if absolute_path.exists():
            absolute_path.unlink()


def delete_demo_interventions(db: Session) -> int:
    """Permanently deletes every intervention created before DEMO_DATA_CUTOFF,
    and everything that exists solely because of it. Returns the count of
    interventions deleted (0 on an already-empty or already-run cleanup).

    Single transaction: every statement below uses the session's pending
    (uncommitted) state, with exactly one db.commit() at the very end — the
    same shape deletion_service.detach_references uses for its own bulk
    updates, and for the same reason: any exception before that final commit
    leaves the session's pending changes uncommitted, and get_db's teardown
    (app/database/session.py) closes the connection without ever committing
    them, so nothing partial is ever persisted.
    """
    settings = _get_settings_without_committing(db)
    if settings.demo_interventions_deleted_at is not None:
        # Structural gate, independent of whether any rows would even match —
        # see this module's docstring. Never a silent no-op: the CEO must see
        # this was already done, not get an empty success.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Demo intervention cleanup has already been performed on "
                f"{settings.demo_interventions_deleted_at.isoformat()} and cannot be run again."
            ),
        )

    intervention_ids = _demo_intervention_ids(db)
    if not intervention_ids:
        # Idempotent no-op path: nothing to delete, but the gate still needs
        # to be set so this can never be attempted again once the feature has
        # been exercised — matches "running this twice should be safe" while
        # still permanently closing the door (Ch. one-time-gate requirement).
        app_settings_repository.mark_demo_interventions_deleted(db, settings, datetime.now(timezone.utc))
        db.commit()
        return 0

    # Defensive detach, done first: a demo intervention's warranty_reference_id
    # could in principle point at an intervention that does NOT fall before
    # the cutoff (this shouldn't happen given a fixed forward-only cutoff and
    # was verified against real data, but is not assumed here). Nulling every
    # self-reference among the batch before any row is deleted means the
    # DELETE statements below can never trip a live FK constraint, regardless.
    db.query(Intervention).filter(Intervention.id.in_(intervention_ids)).update(
        {Intervention.warranty_reference_id: None}, synchronize_session=False
    )

    # DETACH (nullable FKs) — these rows have their own independent meaning
    # and are never destroyed just because the intervention they referenced
    # is gone. Matches deletion_service.py's own detach-not-destroy rule for
    # every nullable FK it handles.
    db.query(Notification).filter(Notification.related_intervention_id.in_(intervention_ids)).update(
        {Notification.related_intervention_id: None}, synchronize_session=False
    )
    db.query(Planning).filter(Planning.intervention_id.in_(intervention_ids)).update(
        {Planning.intervention_id: None}, synchronize_session=False
    )

    # DELETE (rows that exist solely to record something about the
    # intervention itself, and are meaningless without it).
    _delete_attachment_files(db, intervention_ids)
    db.query(Attachment).filter(Attachment.intervention_id.in_(intervention_ids)).delete(synchronize_session=False)
    db.query(ApprovalHistory).filter(ApprovalHistory.intervention_id.in_(intervention_ids)).delete(
        synchronize_session=False
    )
    db.query(AuditLog).filter(AuditLog.intervention_id.in_(intervention_ids)).delete(synchronize_session=False)
    db.query(InterventionTask).filter(InterventionTask.intervention_id.in_(intervention_ids)).delete(
        synchronize_session=False
    )
    db.query(InterventionTechnician).filter(InterventionTechnician.intervention_id.in_(intervention_ids)).delete(
        synchronize_session=False
    )

    deleted_count = (
        db.query(Intervention)
        .filter(Intervention.id.in_(intervention_ids))
        .delete(synchronize_session=False)
    )

    app_settings_repository.mark_demo_interventions_deleted(db, settings, datetime.now(timezone.utc))
    db.commit()
    return deleted_count
