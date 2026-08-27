import type { Notification } from "../types/notification";
import type { UserRole } from "../types/enums";

const PLANNING_TITLES = new Set([
  "New Planning Assignment",
  "Urgent Intervention Assigned",
  "Planning Modified",
  "Planning Cancelled",
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
 * no target. Planning-titled notifications are always technician-targeted in
 * practice, but routing still depends on the viewer's role: chefs have
 * /planning (which supports ?highlight=), while technicians have no page
 * that renders an individual Planning row, so they land on their
 * interventions list instead of a dead link.
 */
export function resolveNotificationPath(notification: Notification, role: UserRole): string | null {
  if (PLANNING_TITLES.has(notification.title)) {
    if (role === "chef_technicien") {
      return notification.related_planning_id != null
        ? `/planning?highlight=${notification.related_planning_id}`
        : "/planning";
    }
    return "/interventions";
  }
  if (INTERVENTION_TITLES.has(notification.title)) {
    return notification.related_intervention_id != null
      ? `/interventions/${notification.related_intervention_id}`
      : null;
  }
  return null;
}
