import type { ChartPoint } from "./dashboard";

export interface TechnicianPerformanceSummary {
  technician_id: number;
  full_name: string;
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
