"""full schema: clients, sites, contracts, projects, travaux, interventions, tasks, attachments, planning, notifications, approval_history, audit_log

Revision ID: 2fb0de52b5f8
Revises: e893da397596
Create Date: 2026-08-02 12:47:26.124967

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2fb0de52b5f8'
down_revision: Union[str, None] = 'e893da397596'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Enum definitions — kept alongside the tables that use them, mirroring DATABASE_SCHEMA.md.
contract_status_enum = sa.Enum("active", "archived", name="contract_status")
project_status_enum = sa.Enum("active", "archived", name="project_status")
intervention_type_enum = sa.Enum("standard", "contract", "project", "warranty", name="intervention_type")
location_type_enum = sa.Enum("sur_site", "atelier", name="location_type")
intervention_status_enum = sa.Enum(
    "draft",
    "planned",
    "in_progress",
    "submitted",
    "pending_technical_approval",
    "technical_approved",
    "pending_administrative_approval",
    "fully_approved",
    "rejected",
    name="intervention_status",
)
priority_enum = sa.Enum("normal", "high", "urgent", name="priority")
planning_status_enum = sa.Enum("planned", "in_progress", "completed", "cancelled", name="planning_status")
approval_level_enum = sa.Enum("technical", "administrative", name="approval_level")
approval_decision_enum = sa.Enum("approved", "rejected", name="approval_decision")
audit_action_enum = sa.Enum(
    "created",
    "draft_saved",
    "modified",
    "submitted",
    "technical_approved",
    "administrative_approved",
    "rejected",
    "resubmitted",
    name="audit_action",
)


def upgrade() -> None:

    # --- clients (Ch.37) ---
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # --- client_sites (Ch.38) ---
    op.create_table(
        "client_sites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("site_name", sa.String(length=200), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=300), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_client_sites_client_id", "client_sites", ["client_id"])
    op.create_index("ix_client_sites_city", "client_sites", ["city"])

    # --- contracts (Ch.39) ---
    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("contract_name", sa.String(length=200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", contract_status_enum, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_contracts_client_id", "contracts", ["client_id"])

    # --- projects (Ch.40) ---
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("project_name", sa.String(length=200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", project_status_enum, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_projects_client_id", "projects", ["client_id"])

    # --- travaux (Ch.41) ---
    op.create_table(
        "travaux",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("travail_code", sa.String(length=20), nullable=False),
        sa.Column("travail_name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("travail_code", name="uq_travaux_travail_code"),
    )
    op.create_index("ix_travaux_travail_code", "travaux", ["travail_code"])

    # --- interventions (Ch.42 — central table) ---
    op.create_table(
        "interventions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("bi_number", sa.String(length=20), nullable=False),
        sa.Column("technician_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("client_sites.id"), nullable=False),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id"), nullable=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("warranty_reference_id", sa.Integer(), sa.ForeignKey("interventions.id"), nullable=True),
        sa.Column("intervention_type", intervention_type_enum, nullable=False),
        sa.Column("location_type", location_type_enum, nullable=False),
        sa.Column("intervention_date", sa.Date(), nullable=False, server_default=sa.func.current_date()),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("lunch_break_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("net_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("number_of_technicians", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("technical_report", sa.Text(), nullable=True),
        sa.Column("contact_person", sa.String(length=200), nullable=True),
        sa.Column("status", intervention_status_enum, nullable=False, server_default="draft"),
        sa.Column("submission_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("technical_approval_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("administrative_approval_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("points_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint("bi_number", name="uq_interventions_bi_number"),
    )
    op.create_index("ix_interventions_bi_number", "interventions", ["bi_number"])
    op.create_index("ix_interventions_technician_id", "interventions", ["technician_id"])
    op.create_index("ix_interventions_client_id", "interventions", ["client_id"])
    op.create_index("ix_interventions_site_id", "interventions", ["site_id"])
    op.create_index("ix_interventions_status", "interventions", ["status"])
    op.create_index("ix_interventions_submission_date", "interventions", ["submission_date"])

    # --- intervention_tasks (Ch.43 — join table) ---
    op.create_table(
        "intervention_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("intervention_id", sa.Integer(), sa.ForeignKey("interventions.id"), nullable=False),
        sa.Column("travail_id", sa.Integer(), sa.ForeignKey("travaux.id"), nullable=False),
        sa.UniqueConstraint("intervention_id", "travail_id", name="uq_intervention_travail"),
    )
    op.create_index("ix_intervention_tasks_intervention_id", "intervention_tasks", ["intervention_id"])

    # --- attachments (Ch.44) ---
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("intervention_id", sa.Integer(), sa.ForeignKey("interventions.id"), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=50), nullable=True),
        sa.Column("upload_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
    )
    op.create_index("ix_attachments_intervention_id", "attachments", ["intervention_id"])

    # --- planning (Ch.45) ---
    op.create_table(
        "planning",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("technician_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("client_sites.id"), nullable=False),
        sa.Column("intervention_id", sa.Integer(), sa.ForeignKey("interventions.id"), nullable=True),
        sa.Column("planned_date", sa.Date(), nullable=False),
        sa.Column("planned_start_time", sa.Time(), nullable=False),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("priority", priority_enum, nullable=False, server_default="normal"),
        sa.Column("status", planning_status_enum, nullable=False, server_default="planned"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_planning_technician_id", "planning", ["technician_id"])
    op.create_index("ix_planning_planned_date", "planning", ["planned_date"])
    op.create_index("ix_planning_priority", "planning", ["priority"])

    # --- notifications (Ch.46) ---
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("related_intervention_id", sa.Integer(), sa.ForeignKey("interventions.id"), nullable=True),
        sa.Column("read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_read", "notifications", ["read"])

    # --- approval_history (Ch.47) ---
    op.create_table(
        "approval_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("intervention_id", sa.Integer(), sa.ForeignKey("interventions.id"), nullable=False),
        sa.Column("approval_level", approval_level_enum, nullable=False),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", approval_decision_enum, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("approval_date", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_approval_history_intervention_id", "approval_history", ["intervention_id"])
    op.create_index("ix_approval_history_approval_date", "approval_history", ["approval_date"])

    # --- audit_log (Ch.18, Ch.151) ---
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("intervention_id", sa.Integer(), sa.ForeignKey("interventions.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", audit_action_enum, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_log_intervention_id", "audit_log", ["intervention_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_intervention_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_approval_history_approval_date", table_name="approval_history")
    op.drop_index("ix_approval_history_intervention_id", table_name="approval_history")
    op.drop_table("approval_history")

    op.drop_index("ix_notifications_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_planning_priority", table_name="planning")
    op.drop_index("ix_planning_planned_date", table_name="planning")
    op.drop_index("ix_planning_technician_id", table_name="planning")
    op.drop_table("planning")

    op.drop_index("ix_attachments_intervention_id", table_name="attachments")
    op.drop_table("attachments")

    op.drop_index("ix_intervention_tasks_intervention_id", table_name="intervention_tasks")
    op.drop_table("intervention_tasks")

    op.drop_index("ix_interventions_submission_date", table_name="interventions")
    op.drop_index("ix_interventions_status", table_name="interventions")
    op.drop_index("ix_interventions_site_id", table_name="interventions")
    op.drop_index("ix_interventions_client_id", table_name="interventions")
    op.drop_index("ix_interventions_technician_id", table_name="interventions")
    op.drop_index("ix_interventions_bi_number", table_name="interventions")
    op.drop_table("interventions")

    op.drop_index("ix_travaux_travail_code", table_name="travaux")
    op.drop_table("travaux")

    op.drop_index("ix_projects_client_id", table_name="projects")
    op.drop_table("projects")

    op.drop_index("ix_contracts_client_id", table_name="contracts")
    op.drop_table("contracts")

    op.drop_index("ix_client_sites_city", table_name="client_sites")
    op.drop_index("ix_client_sites_client_id", table_name="client_sites")
    op.drop_table("client_sites")

    op.drop_table("clients")

    bind = op.get_bind()
    for enum in (
        audit_action_enum,
        approval_decision_enum,
        approval_level_enum,
        planning_status_enum,
        priority_enum,
        intervention_status_enum,
        location_type_enum,
        intervention_type_enum,
        project_status_enum,
        contract_status_enum,
    ):
        enum.drop(bind, checkfirst=True)
