import type { Priority } from "./enums";

export interface ChartPoint {
  label: string;
  value: number;
}

export interface PlanningSummary {
  id: number;
  client_id: number;
  client_name: string;
  site_id: number;
  site_name: string;
  planned_date: string;
  planned_start_time: string;
  priority: Priority;
  status: string;
}

export interface InterventionSummary {
  id: number;
  bi_number: string;
  client_name: string;
  status: string;
  intervention_date: string;
}

export interface ActionableInterventionSummary {
  id: number;
  bi_number: string;
  client_name: string;
  intervention_type: string;
  status: string;
  intervention_date: string;
  rejection_reason: string | null;
  rejection_level: string | null;
}

export interface TechnicianDashboard {
  planned_today: number;
  completed_today: number;
  pending_approval: number;
  rejected: number;
  draft_count: number;
  monthly_points: number;
  average_daily_duration_minutes: number;
  today_planning: PlanningSummary[];
  draft_interventions: ActionableInterventionSummary[];
  rejected_interventions: ActionableInterventionSummary[];
  recently_completed: InterventionSummary[];
  weekly_completed_chart: ChartPoint[];
  monthly_points_chart: ChartPoint[];
}

export interface ChefDashboard {
  planned_today: number;
  completed_today: number;
  pending_technical_approvals: number;
  urgent_interventions: number;
  active_technicians: number;
  average_completion_time_minutes: number;
  interventions_by_technician_chart: ChartPoint[];
  interventions_by_client_chart: ChartPoint[];
  daily_activity_chart: ChartPoint[];
  weekly_activity_chart: ChartPoint[];
  today_planning: PlanningSummary[];
  technician_workload: ChartPoint[];
  urgent_queue: PlanningSummary[];
}

export interface AdminDashboard {
  pending_administrative_approvals: number;
  approved_this_month: number;
  rejected_this_month: number;
  average_approval_time_minutes: number;
  monthly_interventions_chart: ChartPoint[];
  approval_rate: number;
  rejection_rate: number;
  points_distribution_chart: ChartPoint[];
  client_activity_chart: ChartPoint[];
  city_activity_chart: ChartPoint[];
}

export interface TechnicianDashboardCharts {
  completed_chart: ChartPoint[];
  points_chart: ChartPoint[];
}

export interface ChefDashboardCharts {
  interventions_by_technician_chart: ChartPoint[];
  interventions_by_client_chart: ChartPoint[];
  activity_chart: ChartPoint[];
  technician_workload: ChartPoint[];
}

export interface AdminDashboardCharts {
  interventions_chart: ChartPoint[];
  points_distribution_chart: ChartPoint[];
  client_activity_chart: ChartPoint[];
  city_activity_chart: ChartPoint[];
}

export interface CeoDashboard {
  total_interventions: number;
  completed_interventions: number;
  pending_interventions: number;
  rejected_interventions: number;
  approval_rate: number;
  rejection_rate: number;
  average_intervention_duration_minutes: number;
  total_clients: number;
  active_clients: number;
  total_technicians: number;
  active_technicians: number;
  active_contracts: number;
  contracts_expiring_soon: number;
  active_projects: number;
  upcoming_planned_interventions: number;
  urgent_planning_count: number;
  monthly_intervention_trend_chart: ChartPoint[];
  completion_trend_chart: ChartPoint[];
  technician_workload_chart: ChartPoint[];
  top_clients_chart: ChartPoint[];
  contract_activity_chart: ChartPoint[];
  project_activity_chart: ChartPoint[];
  priority_distribution_chart: ChartPoint[];
}
