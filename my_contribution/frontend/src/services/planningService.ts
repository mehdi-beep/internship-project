import { fetchPage, fetchOne, postOne, putOne } from "../api/queryHelpers";
import { apiClient } from "../api/client";
import type { ApiResponse } from "../types/auth";
import type { Priority } from "../types/enums";
import type { Planning, PlanningStatus } from "../types/planning";

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
