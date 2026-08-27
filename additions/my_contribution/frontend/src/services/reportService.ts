import { apiClient } from "../api/client";
import { fetchOne } from "../api/queryHelpers";
import type {
  ApprovalReport,
  ComparisonReport,
  InterventionReport,
  PlanningReport,
  ReportTypeInfo,
} from "../types/report";

export interface InterventionReportParams {
  type: string;
  date_from?: string;
  date_to?: string;
  technician_id?: number;
  client_id?: number;
  project_id?: number;
  contract_id?: number;
}

export const listReportTypes = () => fetchOne<ReportTypeInfo[]>("/reports");

export async function fetchInterventionReport(params: InterventionReportParams): Promise<InterventionReport> {
  const { data } = await apiClient.get("/reports/interventions", { params });
  return data.data;
}

export async function fetchApprovalReport(params: { date_from?: string; date_to?: string }): Promise<ApprovalReport> {
  const { data } = await apiClient.get("/reports/approval", { params });
  return data.data;
}

export async function fetchPlanningReport(params: { date_from?: string; date_to?: string }): Promise<PlanningReport> {
  const { data } = await apiClient.get("/reports/planning", { params });
  return data.data;
}

export async function fetchComparisonReport(params: {
  period_a_from: string;
  period_a_to: string;
  period_b_from: string;
  period_b_to: string;
  technician_id?: number;
  client_id?: number;
}): Promise<ComparisonReport> {
  const { data } = await apiClient.get("/reports/comparison", { params });
  return data.data;
}

export async function downloadExport(
  format: "pdf" | "xlsx",
  params: Record<string, unknown>,
  filename: string,
): Promise<void> {
  const { data } = await apiClient.get(`/reports/export.${format}`, { params, responseType: "blob" });
  const url = URL.createObjectURL(data as Blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
