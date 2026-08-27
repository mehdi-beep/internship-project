export interface ReportTypeInfo {
  key: string;
  label: string;
}

export interface InterventionReportRow {
  bi_number: string;
  intervention_date: string;
  technician_name: string;
  client_name: string;
  site_name: string;
  intervention_type: string;
  status: string;
  net_duration_minutes: number;
  points_earned: number;
}

export interface InterventionReportSummary {
  total_interventions: number;
  total_duration_minutes: number;
  total_points: number;
  fully_approved_count: number;
  rejected_count: number;
}

export interface InterventionReport {
  report_type: string;
  date_from: string | null;
  date_to: string | null;
  summary: InterventionReportSummary;
  rows: InterventionReportRow[];
}

export interface ApprovalReportRow {
  bi_number: string;
  approval_level: string;
  approver_name: string;
  decision: string;
  comment: string | null;
  approval_date: string;
}

export interface ApprovalReport {
  date_from: string | null;
  date_to: string | null;
  total_approved: number;
  total_rejected: number;
  rows: ApprovalReportRow[];
}

export interface PlanningReportRow {
  technician_name: string;
  client_name: string;
  site_name: string;
  planned_date: string;
  priority: string;
  status: string;
}

export interface PlanningReport {
  date_from: string | null;
  date_to: string | null;
  total_planned: number;
  total_cancelled: number;
  rows: PlanningReportRow[];
}

export interface ComparisonPeriodResult {
  label: string;
  total_interventions: number;
  total_duration_minutes: number;
  total_points: number;
  fully_approved_count: number;
  rejected_count: number;
}

export interface ComparisonReport {
  period_a: ComparisonPeriodResult;
  period_b: ComparisonPeriodResult;
}
