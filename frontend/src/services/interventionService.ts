import { apiClient } from "../api/client";
import { fetchOne, fetchPage, postOne, putOne } from "../api/queryHelpers";
import type { ApiResponse } from "../types/auth";
import type { InterventionStatus, InterventionType, LocationType } from "../types/enums";
import type { Attachment, AuditLogEntry, Intervention, InterventionDetail } from "../types/intervention";

export interface InterventionListParams {
  page?: number;
  page_size?: number;
  technician_id?: number;
  client_id?: number;
  site_id?: number;
  status?: InterventionStatus;
  intervention_type?: InterventionType;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface InterventionInput {
  client_id: number;
  site_id: number;
  contact_person?: string | null;
  intervention_type: InterventionType;
  contract_id?: number | null;
  project_id?: number | null;
  warranty_reference_bi?: string | null;
  location_type: LocationType;
  intervention_date: string;
  start_time: string;
  end_time: string;
  lunch_break_minutes: number;
  number_of_technicians: number;
  travail_ids: number[];
  technical_report?: string | null;
}

export const listInterventions = (params: InterventionListParams = {}) =>
  fetchPage<Intervention>("/interventions", params);

export const getIntervention = (id: number) => fetchOne<InterventionDetail>(`/interventions/${id}`);

export const getInterventionHistory = (id: number) => fetchOne<AuditLogEntry[]>(`/interventions/${id}/history`);

export const createIntervention = (input: InterventionInput, submit = false) =>
  postOne<InterventionDetail>(`/interventions?submit=${submit}`, input);

export const updateIntervention = (id: number, input: InterventionInput) =>
  putOne<InterventionDetail>(`/interventions/${id}`, input);

export const submitIntervention = (id: number) => postOne<InterventionDetail>(`/interventions/${id}/submit`);

export async function uploadAttachment(interventionId: number, file: File): Promise<Attachment> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<ApiResponse<Attachment>>(
    `/attachments?intervention_id=${interventionId}`,
    form,
  );
  if (!data.data) {
    throw new Error(data.message ?? "Upload failed.");
  }
  return data.data;
}

export async function deleteAttachment(attachmentId: number): Promise<void> {
  await apiClient.delete(`/attachments/${attachmentId}`);
}

export function attachmentDownloadUrl(attachmentId: number): string {
  return `${apiClient.defaults.baseURL}/attachments/${attachmentId}/download`;
}
