import { getPlanning } from "../services/planningService";
import type { Notification } from "../types/notification";
import type { UserRole } from "../types/enums";

const PLANNING_TITLES = new Set([
  "New Planning Assignment",
  "Urgent Intervention Assigned",
  "Planning Modified",
  "Planning Cancelled",
  // Task 4 — sent to the previously-assigned technician on reassignment.
  "Assignment Removed",
]);

const INTERVENTION_TITLES = new Set([
  "Intervention Submitted",
  "Administrative Approval Needed",
  "Intervention Rejected",
  "Intervention Approved",
  // Seed/demo-data-only title variants (see backend/app/database/seed.py
  // seed_notifications) — the real notification_service.py never produces
  // these exact strings, but synthetic demo notifications use them.
  "New Intervention Assigned",
  "Urgent Intervention",
  "Technical Approval Needed",
]);

/**
 * Resolves where clicking a notification should navigate, or null if it has
 * no target. Async because a technician-facing planning notification needs
 * to look up the referenced Planning entry first: Planning.intervention_id
 * is never set anywhere in this application (confirmed — no code path ever
 * creates the eventual real intervention record from a planning entry), so
 * there's no existing intervention to link a technician to. Instead, this
 * resolves the assignment's client/site/date and builds a pre-filled
 * "/interventions/new" link — the same query-param pre-fill mechanism the
 * Technician Dashboard's Planned/Urgent card uses (see
 * TechnicianDashboardContent.tsx) — so clicking the notification takes the
 * technician straight into starting that specific assignment's intervention,
 * not a generic, unrelated list.
 */
export async function resolveNotificationPath(notification: Notification, role: UserRole): Promise<string | null> {
  if (PLANNING_TITLES.has(notification.title)) {
    // "Assignment Removed" tells a technician the work is no longer theirs —
    // deep-linking them into starting that intervention would be actively
    // wrong, and GET /planning/{id} would 403 for them now anyway. Their own
    // list is the only sensible destination.
    if (notification.title === "Assignment Removed") {
      return role === "technician" ? "/interventions" : "/planning";
    }
    if (role === "chef_technicien" || role === "admin_supervisor") {
      return notification.related_planning_id != null
        ? `/planning?highlight=${notification.related_planning_id}`
        : "/planning";
    }
    // Technician: resolve the specific assignment, not the generic list.
    if (notification.related_planning_id == null) return "/interventions";
    try {
      const planning = await getPlanning(notification.related_planning_id);
      const params = new URLSearchParams({
        client_id: String(planning.client_id),
        site_id: String(planning.site_id),
        intervention_date: planning.planned_date,
      });
      return `/interventions/new?${params.toString()}`;
    } catch {
      // Planning entry no longer resolvable (e.g. permission edge case) —
      // fall back to the list rather than leave the click dead.
      return "/interventions";
    }
  }
  if (INTERVENTION_TITLES.has(notification.title)) {
    return notification.related_intervention_id != null
      ? `/interventions/${notification.related_intervention_id}`
      : null;
  }
  return null;
}
