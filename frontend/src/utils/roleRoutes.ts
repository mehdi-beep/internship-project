import type { UserRole } from "../types/enums";

export function dashboardPathForRole(role: UserRole): string {
  switch (role) {
    case "technician":
      return "/dashboard";
    case "chef_technicien":
      return "/dashboard";
    case "admin_supervisor":
      return "/dashboard";
    // Task 7 — the CEO lands on the same dashboard an Administrator does.
    case "ceo":
      return "/dashboard";
    // Task 3 — the display role has no dashboard at all (DashboardPage.tsx
    // renders nothing for it); its one and only destination is the
    // dedicated full-screen calendar.
    case "display":
      return "/display-calendar";
    default:
      return "/dashboard";
  }
}
