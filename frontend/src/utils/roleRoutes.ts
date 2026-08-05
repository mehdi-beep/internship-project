import type { UserRole } from "../types/enums";

export function dashboardPathForRole(role: UserRole): string {
  switch (role) {
    case "technician":
      return "/dashboard";
    case "chef_technicien":
      return "/dashboard";
    case "admin_supervisor":
      return "/dashboard";
    default:
      return "/dashboard";
  }
}
