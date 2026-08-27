import { fetchPage, fetchOne, postOne, putOne } from "../api/queryHelpers";
import { apiClient } from "../api/client";
import type { ApiResponse } from "../types/auth";
import type { Priority } from "../types/enums";
import type { Planning, PlanningDisplayEntry, PlanningStatus } from "../types/planning";

export interface PlanningListParams {
  page?: number;
  page_size?: number;
  technician_id?: number;
  date_from?: string;
  date_to?: string;
  priority?: Priority;
  status?: PlanningStatus;
  created_by?: number;
}

export interface PlanningCreateInput {
  technician_id: number;
  client_id: number;
  site_id: number;
  planned_date: string;
  planned_start_time: string;
  estimated_duration_minutes?: number | null;
  priority: Priority;
  notes?: string | null;
}

export interface PlanningUpdateInput {
  technician_id: number;
  planned_date: string;
  planned_start_time: string;
  estimated_duration_minutes?: number | null;
  priority: Priority;
  notes?: string | null;
}

export const listPlanning = (params: PlanningListParams = {}) => fetchPage<Planning>("/planning", params);

export interface PlanningDisplayParams {
  date_from?: string;
  date_to?: string;
}

// Task 3 — the hallway-display calendar's dedicated read model: names
// already resolved server-side, so this is the display role's ONLY API
// call (no separate /clients or /users lookup needed, unlike every other
// calendar page). fetchOne is used (not fetchPage) since this returns a
// plain array, not a paginated Page<T> — the display always wants the
// whole visible range at once.
export const listPlanningForDisplay = (params: PlanningDisplayParams = {}) =>
  apiClient.get<ApiResponse<PlanningDisplayEntry[]>>("/planning/display", { params }).then((res) => {
    if (!res.data.data) {
      throw new Error(res.data.message ?? "Request failed.");
    }
    return res.data.data;
  });
export const getPlanning = (id: number) => fetchOne<Planning>(`/planning/${id}`);
export const createPlanning = (input: PlanningCreateInput) => postOne<Planning>("/planning", input);
export const updatePlanning = (id: number, input: PlanningUpdateInput) => putOne<Planning>(`/planning/${id}`, input);
export const markPlanningUrgent = (id: number) => postOne<Planning>(`/planning/${id}/urgent`);

export const reorderUrgentQueue = (orderedIds: number[]) =>
  apiClient.put("/planning/urgent-queue/reorder", { ordered_ids: orderedIds });

export async function cancelPlanning(id: number): Promise<Planning> {
  const { data } = await apiClient.delete<ApiResponse<Planning>>(`/planning/${id}`);
  if (!data.data) {
    throw new Error(data.message ?? "Request failed.");
  }
  return data.data;
}
