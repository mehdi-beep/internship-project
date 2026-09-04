from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import require_roles
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.report import (
    ApprovalReport,
    ComparisonReport,
    InterventionReport,
    PlanningReport,
    ReportTypeInfo,
)
from app.services import export_service, report_service

router = APIRouter(prefix="/reports", tags=["reports"])

ROLES = ("chef_technicien", "admin_supervisor", "ceo")


@router.get("", response_model=ApiResponse[list[ReportTypeInfo]])
def list_report_types(_: User = Depends(require_roles(*ROLES))) -> ApiResponse[list[ReportTypeInfo]]:
    return ApiResponse(data=report_service.list_report_types())


@router.get("/interventions", response_model=ApiResponse[InterventionReport])
def interventions_report(
    type: str = Query(..., description="daily|weekly|monthly|yearly|technician|client|project|contract"),
    date_from: date | None = None,
    date_to: date | None = None,
    technician_id: int | None = None,
    client_id: int | None = None,
    project_id: int | None = None,
    contract_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ROLES)),
) -> ApiResponse[InterventionReport]:
    report = report_service.generate_intervention_report(
        db, type, date_from, date_to, technician_id, client_id, project_id, contract_id
    )
    return ApiResponse(data=report)


@router.get("/approval", response_model=ApiResponse[ApprovalReport])
def approval_report(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ROLES)),
) -> ApiResponse[ApprovalReport]:
    return ApiResponse(data=report_service.generate_approval_report(db, date_from, date_to))


@router.get("/planning", response_model=ApiResponse[PlanningReport])
def planning_report(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ROLES)),
) -> ApiResponse[PlanningReport]:
    return ApiResponse(data=report_service.generate_planning_report(db, date_from, date_to))


@router.get("/comparison", response_model=ApiResponse[ComparisonReport])
def comparison_report(
    period_a_from: date,
    period_a_to: date,
    period_b_from: date,
    period_b_to: date,
    technician_id: int | None = None,
    client_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ROLES)),
) -> ApiResponse[ComparisonReport]:
    report = report_service.generate_comparison_report(
        db, period_a_from, period_a_to, period_b_from, period_b_to, technician_id, client_id
    )
    return ApiResponse(data=report)


def _rows_for_export(
    db: Session,
    report: str,
    type: str | None,
    date_from: date | None,
    date_to: date | None,
    technician_id: int | None,
    client_id: int | None,
    project_id: int | None,
    contract_id: int | None,
) -> tuple[str, str, list[dict]]:
    if report == "interventions":
        if not type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="'type' is required when report=interventions.")
        data = report_service.generate_intervention_report(
            db, type, date_from, date_to, technician_id, client_id, project_id, contract_id
        )
        label = next((t.label for t in report_service.REPORT_TYPES if t.key == type), type.title())
        subtitle = f"{data.date_from or 'all time'} to {data.date_to or 'present'} — {data.summary.total_interventions} interventions"
        return label, subtitle, [row.model_dump() for row in data.rows]
    if report == "approval":
        data = report_service.generate_approval_report(db, date_from, date_to)
        subtitle = f"{data.date_from or 'all time'} to {data.date_to or 'present'} — {data.total_approved} approved, {data.total_rejected} rejected"
        return "Approval Report", subtitle, [row.model_dump() for row in data.rows]
    if report == "planning":
        data = report_service.generate_planning_report(db, date_from, date_to)
        subtitle = f"{data.date_from or 'all time'} to {data.date_to or 'present'} — {data.total_planned} planned, {data.total_cancelled} cancelled"
        return "Planning Report", subtitle, [row.model_dump() for row in data.rows]
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown report.")


@router.get("/export.pdf")
def export_pdf(
    report: str = Query(..., description="interventions|approval|planning"),
    type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    technician_id: int | None = None,
    client_id: int | None = None,
    project_id: int | None = None,
    contract_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ROLES)),
) -> Response:
    title, subtitle, rows = _rows_for_export(
        db, report, type, date_from, date_to, technician_id, client_id, project_id, contract_id
    )
    pdf_bytes = export_service.render_pdf(title, subtitle, rows)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{title.replace(" ", "_")}.pdf"'},
    )


@router.get("/export.xlsx")
def export_excel(
    report: str = Query(..., description="interventions|approval|planning"),
    type: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    technician_id: int | None = None,
    client_id: int | None = None,
    project_id: int | None = None,
    contract_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*ROLES)),
) -> Response:
    title, _subtitle, rows = _rows_for_export(
        db, report, type, date_from, date_to, technician_id, client_id, project_id, contract_id
    )
    excel_bytes = export_service.render_excel(title, rows)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{title.replace(" ", "_")}.xlsx"'},
    )
