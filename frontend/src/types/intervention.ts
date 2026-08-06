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
  uploaded_by: number;
}

export interface ApprovalHistoryEntry {
  id: number;
  approval_level: string;
  approved_by: number;
  decision: string;
  comment: string | null;
  approval_date: string;
}

export interface AuditLogEntry {
  id: number;
  user_id: number;
  action: string;
  comment: string | null;
  created_at: string;
}

export interface Intervention {
  id: number;
  bi_number: string;
  technician_id: number;
  client_id: number;
  site_id: number;
  contract_id: number | null;
  project_id: number | null;
  warranty_reference_id: number | null;
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
