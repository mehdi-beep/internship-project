import type { Priority } from "./enums";

export type PlanningStatus = "planned" | "in_progress" | "completed" | "cancelled";

export interface Planning {
  id: number;
  technician_id: number;
  client_id: number;
  site_id: number;
  intervention_id: number | null;
  planned_date: string;
  planned_start_time: string;
  estimated_duration_minutes: number | null;
  priority: Priority;
  status: PlanningStatus;
  notes: string | null;
  created_by: number;
  created_at: string;
  updated_at: string;
}
