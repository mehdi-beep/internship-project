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

Also deletes demo-era Clients, Client Sites, Contracts, and Projects on the
same cutoff, reusing deletion_service.detach_references's exact per-entity
detach logic (inlined here without its internal commit, so everything stays
one transaction) rather than duplicating it.

Travaux cannot use the same created_at cutoff as everything else: both the
58 real catalog entries (TRAVAUX_CATALOG) and the 125 legacy placeholder
entries (LEGACY_PLACEHOLDER_TRAVAUX_CATALOG, seed.py) are inserted in the
same seeding pass, at the same moment, so every travail row shares
essentially the same created_at regardless of which catalog it came from —
a cutoff comparison can't tell them apart. The two catalogs ARE reliably
distinguishable on a different column: every real entry has category=None,
every legacy entry has a real category string ('Network', 'Security',
'Hardware', 'Telephony', 'Infrastructure') — confirmed with zero exceptions
on either side against the actual seed data at the time this was added.
`category` is a normal, freely admin-editable field (schemas/travail.py), so
this is a one-time, data-shape-based selector that matches today's real data
exactly, not a permanent structural guarantee — safe specifically because
this whole feature is itself one-time and gated (see below), not something
that could later misfire against a real travail an admin happens to tag with
a category after this ships.

One entity type is excluded from this feature unconditionally, by explicit
instruction: Users. No user is ever deleted here — the CEO account is
already structurally undeletable (deletion_service.ensure_deletable), and
every other account's fate is a manual decision for later, not an automated
one.

`app_settings.demo_interventions_deleted_at` is the actual gate — set once,
in the same transaction as the deletion, and never cleared. Even though a
second run would also find zero rows before the cutoff (the cutoff cannot
move), the endpoint still refuses outright once this flag is set, as defense
in depth rather than relying solely on the query happening to come back
empty. The name is kept singular/intervention-specific even though the gate
now also covers four more entity types, to avoid an unnecessary migration —
one gate for one indivisible cleanup action is the whole point of a one-time
flag, and there is no scenario where these five entity types' demo data
would ever need to be wiped on separate occasions.
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
from app.models.client import Client
from app.models.client_site import ClientSite
from app.models.contract import Contract
from app.models.intervention import Intervention
from app.models.intervention_task import InterventionTask
from app.models.intervention_technician import InterventionTechnician
from app.models.notification import Notification
from app.models.planning import Planning
from app.models.project import Project
from app.models.travail import Travail
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
    how many rows of each affected type are eligible, and whether this has
    already been done. `eligible_count` is kept as the intervention count
    specifically (the field already existed and other code may read it) —
    the four new counts are additive, not a rename."""

    eligible_count: int
    eligible_client_count: int
    eligible_client_site_count: int
    eligible_contract_count: int
    eligible_project_count: int
    eligible_legacy_travail_count: int
    already_deleted: bool
    deleted_at: datetime | None


def _ids_before_cutoff(db: Session, model, created_at_column) -> list[int]:
    stmt = select(model.id).where(created_at_column < DEMO_DATA_CUTOFF)
    return list(db.scalars(stmt).all())


def _demo_intervention_ids(db: Session) -> list[int]:
    return _ids_before_cutoff(db, Intervention, Intervention.created_at)


def _legacy_travail_ids(db: Session) -> list[int]:
    """Selected by category, not DEMO_DATA_CUTOFF — see this module's
    docstring for why created_at can't distinguish the two travaux catalogs."""
    return list(db.scalars(select(Travail.id).where(Travail.category.is_not(None))).all())


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


def _count_before_cutoff(db: Session, model, created_at_column) -> int:
    return db.scalar(select(func.count()).select_from(model).where(created_at_column < DEMO_DATA_CUTOFF)) or 0


def get_status(db: Session) -> DemoDataStatus:
    settings = _get_settings_without_committing(db)
    legacy_travail_count = db.scalar(
        select(func.count()).select_from(Travail).where(Travail.category.is_not(None))
    ) or 0
    return DemoDataStatus(
        eligible_count=_count_before_cutoff(db, Intervention, Intervention.created_at),
        eligible_client_count=_count_before_cutoff(db, Client, Client.created_at),
        eligible_client_site_count=_count_before_cutoff(db, ClientSite, ClientSite.created_at),
        eligible_contract_count=_count_before_cutoff(db, Contract, Contract.created_at),
        eligible_project_count=_count_before_cutoff(db, Project, Project.created_at),
        eligible_legacy_travail_count=legacy_travail_count,
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
        # No demo interventions doesn't imply no demo reference data (an
        # edge case that shouldn't occur with real seed data, but isn't
        # assumed) — still run the reference-data cleanup before setting the
        # gate, matching "running this twice should be safe" while still
        # permanently closing the door (Ch. one-time-gate requirement).
        _delete_demo_reference_data(db)
        _delete_legacy_travaux(db)
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

    _delete_demo_reference_data(db)
    _delete_legacy_travaux(db)

    app_settings_repository.mark_demo_interventions_deleted(db, settings, datetime.now(timezone.utc))
    db.commit()
    return deleted_count


def _delete_legacy_travaux(db: Session) -> None:
    """The 125 legacy placeholder travaux (category is not None — see this
    module's docstring for why category, not created_at, is the selector
    here). Join rows only, deleted first — same reasoning as
    deletion_service.detach_references's own `travail` branch: an
    intervention_tasks row with no travail carries no information at all.
    By the time this runs, every demo Intervention is already deleted above,
    so in practice this affects zero surviving rows against today's real
    data (confirmed: no real intervention has ever used a legacy travail) —
    handled defensively anyway rather than assumed, matching the same
    caution already applied to every other detach in this module."""
    legacy_ids = _legacy_travail_ids(db)
    if not legacy_ids:
        return
    db.query(InterventionTask).filter(InterventionTask.travail_id.in_(legacy_ids)).delete(synchronize_session=False)
    db.query(Travail).filter(Travail.id.in_(legacy_ids)).delete(synchronize_session=False)


def _delete_demo_reference_data(db: Session) -> None:
    """Clients/Sites/Contracts/Projects created before the cutoff, deleted in
    child-before-parent order (Sites/Contracts/Projects, then Clients last)
    since deleting a Client also detaches its children's client_id — doing
    that before those children have had their own cutoff-based delete would
    make it impossible to tell demo children from real ones afterwards.

    Reuses deletion_service.detach_references's exact per-entity logic,
    inlined without its internal db.commit() (this function must stay inside
    delete_demo_interventions's single transaction), rather than
    reimplementing it separately.

    Deliberately excludes Travaux (the 58 real catalog entries are untouched
    by this feature entirely) and Users (no user is ever deleted here — see
    this module's docstring).

    Runs after every demo Intervention is already deleted above, so the only
    intervention rows that COULD still reference one of these ids are ones
    created after the cutoff (real data) — defensively detached the same way
    Intervention.warranty_reference_id is above, not assumed impossible.
    """
    site_ids = _ids_before_cutoff(db, ClientSite, ClientSite.created_at)
    contract_ids = _ids_before_cutoff(db, Contract, Contract.created_at)
    project_ids = _ids_before_cutoff(db, Project, Project.created_at)
    client_ids = _ids_before_cutoff(db, Client, Client.created_at)

    if site_ids:
        db.query(Intervention).filter(Intervention.site_id.in_(site_ids)).update(
            {Intervention.site_id: None}, synchronize_session=False
        )
        db.query(Planning).filter(Planning.site_id.in_(site_ids)).update(
            {Planning.site_id: None}, synchronize_session=False
        )
        db.query(ClientSite).filter(ClientSite.id.in_(site_ids)).delete(synchronize_session=False)

    if contract_ids:
        db.query(Intervention).filter(Intervention.contract_id.in_(contract_ids)).update(
            {Intervention.contract_id: None}, synchronize_session=False
        )
        db.query(Contract).filter(Contract.id.in_(contract_ids)).delete(synchronize_session=False)

    if project_ids:
        db.query(Intervention).filter(Intervention.project_id.in_(project_ids)).update(
            {Intervention.project_id: None}, synchronize_session=False
        )
        db.query(Project).filter(Project.id.in_(project_ids)).delete(synchronize_session=False)

    if client_ids:
        db.query(Intervention).filter(Intervention.client_id.in_(client_ids)).update(
            {Intervention.client_id: None}, synchronize_session=False
        )
        db.query(Planning).filter(Planning.client_id.in_(client_ids)).update(
            {Planning.client_id: None}, synchronize_session=False
        )
        # Any site/contract/project NOT already deleted above (i.e. created
        # after the cutoff — real data) still gets detached from a demo
        # client being removed, same reasoning as the Intervention detaches.
        db.query(ClientSite).filter(ClientSite.client_id.in_(client_ids)).update(
            {ClientSite.client_id: None}, synchronize_session=False
        )
        db.query(Contract).filter(Contract.client_id.in_(client_ids)).update(
            {Contract.client_id: None}, synchronize_session=False
        )
        db.query(Project).filter(Project.client_id.in_(client_ids)).update(
            {Project.client_id: None}, synchronize_session=False
        )
        db.query(Client).filter(Client.id.in_(client_ids)).delete(synchronize_session=False)
