import type { Priority } from "./enums";

export interface ChartPoint {
  label: string;
  value: number;
}

export interface PlanningSummary {
  id: number;
  client_name: string;
  site_name: string;
  planned_start_time: string;
  priority: Priority;
  status: string;
}

export interface NotificationSummary {
  id: number;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}

export interface InterventionSummary {
  id: number;
  bi_number: string;
  client_name: string;
  status: string;
  intervention_date: string;
}

export interface TechnicianDashboard {
  planned_today: number;
  completed_today: number;
  pending_approval: number;
  rejected: number;
  monthly_points: number;
  average_daily_duration_minutes: number;
  today_planning: PlanningSummary[];
  recent_notifications: NotificationSummary[];
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
