import type { InterventionStatus, InterventionType, LocationType } from "./enums";

export interface InterventionTask {
  id: number;
  travail_id: number;
}

export interface InterventionTechnician {
  id: number;
  user_id: number;
}

export interface Attachment {
  id: number;
  file_name: string;
  file_path: string;
  content_type: string | null;
  upload_date: string;
  // Task 5: nullable — permanently deleting the uploader detaches (never
  // deletes) the attachment; deleted_user_label carries their name forward.
  uploaded_by: number | null;
  deleted_user_label?: string | null;
}

export interface ApprovalHistoryEntry {
  id: number;
  approval_level: string;
  // Task 5: nullable for the same reason as Attachment.uploaded_by above.
  // approver_name already covers the display fallback server-side.
  approved_by: number | null;
  approver_name?: string | null;
  decision: string;
  comment: string | null;
  approval_date: string;
}

export interface AuditLogEntry {
  id: number;
  // Task 5: nullable for the same reason as the fields above.
  user_id: number | null;
  deleted_user_label?: string | null;
  action: string;
  comment: string | null;
  created_at: string;
}

export interface Intervention {
  id: number;
  bi_number: string;
  // Task 5: nullable — permanently deleting the lead technician detaches
  // (never deletes) the intervention; deleted_user_label carries their name
  // forward once technician_id is cleared.
  technician_id: number | null;
  deleted_user_label?: string | null;
  // Task 5: nullable — permanently deleting the referenced Client or
  // ClientSite detaches (never deletes) the intervention.
  client_id: number | null;
  site_id: number | null;
  contract_id: number | null;
  project_id: number | null;
  warranty_reference_id: number | null;
  warranty_reference_bi_number?: string | null;
  intervention_type: InterventionType;
  location_type: LocationType;
  intervention_date: string;
  start_time: string;
  end_time: string;
  lunch_break_minutes: number;
  net_duration_minutes: number;
  number_of_technicians: number;
  technical_report: string | null;
  contact_person: string | null;
  status: InterventionStatus;
  submission_date: string | null;
  technical_approval_date: string | null;
  administrative_approval_date: string | null;
  points_earned: number;
  created_at: string;
  updated_at: string;
}

export interface InterventionDetail extends Intervention {
  tasks: InterventionTask[];
  attachments: Attachment[];
  approval_history: ApprovalHistoryEntry[];
  audit_log: AuditLogEntry[];
  colleague_technicians: InterventionTechnician[];
}
