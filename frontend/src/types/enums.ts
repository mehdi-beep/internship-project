export type UserRole = "technician" | "chef_technicien" | "admin_supervisor" | "display";

export type InterventionStatus =
  | "draft"
  | "planned"
  | "in_progress"
  | "submitted"
  | "pending_technical_approval"
  | "technical_approved"
  | "pending_administrative_approval"
  | "fully_approved"
  | "rejected";

export type InterventionType = "standard" | "contract" | "project" | "warranty";

export type LocationType = "sur_site" | "atelier";

export type Priority = "normal" | "high" | "urgent";
