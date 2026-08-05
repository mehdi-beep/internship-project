import { fetchPage, postOne } from "../api/queryHelpers";
import type { Intervention, InterventionDetail } from "../types/intervention";

export type ApprovalDecision = "approved" | "rejected";

export interface ApprovalDecisionInput {
  decision: ApprovalDecision;
  comment?: string | null;
}

export const listTechnicalPending = (params: { page?: number; page_size?: number } = {}) =>
  fetchPage<Intervention>("/approvals/technical-pending", params);

export const listAdministrativePending = (params: { page?: number; page_size?: number } = {}) =>
  fetchPage<Intervention>("/approvals/administrative-pending", params);

export const decideTechnicalApproval = (interventionId: number, input: ApprovalDecisionInput) =>
  postOne<InterventionDetail>(`/interventions/${interventionId}/technical-approval`, input);

export const decideAdministrativeApproval = (interventionId: number, input: ApprovalDecisionInput) =>
  postOne<InterventionDetail>(`/interventions/${interventionId}/administrative-approval`, input);
