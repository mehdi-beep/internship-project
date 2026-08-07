import type { Notification } from "../types/notification";

export type NotificationCategory = "urgent" | "success" | "error" | "info";

// Every real title notification_service.py produces, plus the seed/demo-data-
// only variants (see backend/app/database/seed.py seed_notifications) —
// mirrors the exact same title inventory notificationRouting.ts routes on,
// since "what color is this" and "where does clicking it go" are two
// different questions about the same underlying classification.
const URGENT_TITLES = new Set(["Urgent Intervention Assigned", "Urgent Intervention"]);

const SUCCESS_TITLES = new Set(["Intervention Approved"]);

const ERROR_TITLES = new Set(["Intervention Rejected", "Planning Cancelled"]);

/** Everything else — new/modified assignments, submissions, approval-needed
 * notices — is informational rather than good/bad/urgent news on its own. */
export function categorizeNotification(notification: Notification): NotificationCategory {
  if (URGENT_TITLES.has(notification.title)) return "urgent";
  if (SUCCESS_TITLES.has(notification.title)) return "success";
  if (ERROR_TITLES.has(notification.title)) return "error";
  return "info";
}
