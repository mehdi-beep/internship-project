import { fetchOne, postOne, putOne, patchOne } from "../api/queryHelpers";
import { apiClient } from "../api/client";
import type { ApiResponse } from "../types/auth";
import type { AppSettings, PointRule } from "../types/pointRule";

export interface PointRuleInput {
  start_time: string;
  end_time: string;
  points: number;
}

export const listPointRules = (activeOnly = false) =>
  fetchOne<PointRule[]>(`/point-rules${activeOnly ? "?active_only=true" : ""}`);
export const getPointRule = (id: number) => fetchOne<PointRule>(`/point-rules/${id}`);
export const createPointRule = (input: PointRuleInput) => postOne<PointRule>("/point-rules", input);
export const updatePointRule = (id: number, input: PointRuleInput) => putOne<PointRule>(`/point-rules/${id}`, input);
export const deactivatePointRule = (id: number) => patchOne<PointRule>(`/point-rules/${id}/deactivate`);
export const activatePointRule = (id: number) => patchOne<PointRule>(`/point-rules/${id}/activate`);

export async function deletePointRule(id: number): Promise<void> {
  const { data } = await apiClient.delete<ApiResponse<null>>(`/point-rules/${id}`);
  if (!data.success) {
    throw new Error(data.message ?? "Delete failed.");
  }
}

// Company-wide UTC offset (GMT-12..GMT+14, in minutes) feeding
// calculate_points()'s local-time conversion — lives on this same service
// file since it's served from /point-rules/settings on the same router.
export const getAppSettings = () => fetchOne<AppSettings>("/point-rules/settings");
export const updateAppSettings = (companyUtcOffsetMinutes: number) =>
  putOne<AppSettings>("/point-rules/settings", { company_utc_offset_minutes: companyUtcOffsetMinutes });
