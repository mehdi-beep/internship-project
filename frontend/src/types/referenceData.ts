import type { UserRole } from "./enums";

export interface Client {
  id: number;
  client_name: string;
  phone: string | null;
  email: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ClientSite {
  id: number;
  client_id: number;
  site_name: string;
  city: string;
  address: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export type ContractStatus = "active" | "archived";

export interface Contract {
  id: number;
  client_id: number;
  contract_name: string;
  start_date: string;
  end_date: string | null;
  status: ContractStatus;
  created_at: string;
  updated_at: string;
}

export type ProjectStatus = "active" | "archived";

export interface Project {
  id: number;
  client_id: number;
  project_name: string;
  start_date: string;
  end_date: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface Travail {
  id: number;
  travail_code: string;
  travail_name: string;
  category: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TechnicianOption {
  id: number;
  first_name: string;
  last_name: string;
}

export interface AppUser {
  id: number;
  first_name: string;
  last_name: string;
  username: string;
  email: string;
  phone: string | null;
  role: UserRole;
  active: boolean;
  created_at: string;
  updated_at: string;
}
