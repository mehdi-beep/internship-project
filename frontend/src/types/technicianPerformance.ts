import type { ChartPoint } from "./dashboard";

export interface TechnicianPerformanceSummary {
  technician_id: number;
  full_name: string;
  role: string;

  // Technician-only fields — populated for technician rows, left at their
  // defaults (0) for chef/admin rows.
  total_interventions: number;
  completed_interventions: number;
  pending_interventions: number;
  rejected_interventions: number;
  warranty_interventions: number;
  total_points: number;
  average_duration_minutes: number;
  planned_count: number;
  completed_vs_planned_ratio: number;
  colleague_participation_count: number;
  next_planned_date: string | null;
  next_planned_client_name: string | null;

  // Chef/admin-only fields — populated for chef (technical approvals) and
  // admin (administrative approvals) rows, null for technician rows.
  approvals_processed: number | null;
  approvals_rejected: number | null;
  avg_turnaround_minutes: number | null;
}

export interface TechnicianPerformanceDetail extends TechnicianPerformanceSummary {
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  active: boolean;
  monthly_activity_chart: ChartPoint[];
  weekly_activity_chart: ChartPoint[];
}
