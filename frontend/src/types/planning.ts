import type { Priority } from "./enums";

export type PlanningStatus = "planned" | "in_progress" | "completed" | "cancelled";

export interface Planning {
  id: number;
  // Task 5: nullable — permanently deleting the assigned technician detaches
  // (never deletes) the planning entry; deleted_technician_label carries
  // their name forward once technician_id is cleared.
  technician_id: number | null;
  deleted_technician_label?: string | null;
  // Task 5: nullable — permanently deleting the referenced Client or
  // ClientSite detaches (never deletes) the planning entry.
  client_id: number | null;
  site_id: number | null;
  intervention_id: number | null;
  planned_date: string;
  planned_start_time: string;
  estimated_duration_minutes: number | null;
  priority: Priority;
  status: PlanningStatus;
  notes: string | null;
  // Task 5: nullable — permanently deleting the creator detaches (never
  // deletes) the planning entry; deleted_creator_label carries their name
  // forward once created_by is cleared.
  created_by: number | null;
  deleted_creator_label?: string | null;
  created_at: string;
  updated_at: string;
}

/** Task 3 — the hallway-display calendar's read model: names resolved
 * server-side (see PlanningDisplayOut in the backend), unlike Planning
 * above which only ever carries raw ids. */
export interface PlanningDisplayEntry {
  id: number;
  technician_name: string;
  client_name: string;
  site_name: string;
  city: string;
  planned_date: string;
  planned_start_time: string;
  estimated_duration_minutes: number | null;
  priority: Priority;
  status: PlanningStatus;
}
