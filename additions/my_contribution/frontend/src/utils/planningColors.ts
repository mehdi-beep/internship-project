import type { Priority } from "../types/enums";
import type { Planning } from "../types/planning";

// Ch.143 calendar color rules: Blue=Planned, Green=Completed, Red=Urgent,
// Gray=Draft (n/a to planning), Orange=Pending Approval (n/a to planning),
// Purple=Administrative Approval (n/a to planning).
// Urgent (a priority, not a status) overrides the status color per the
// priority-overlay decision — an urgent-and-planned entry renders red.
const PLANNING_STATUS_COLORS: Record<Planning["status"], string> = {
  planned: "#1976d2",
  in_progress: "#4fc3f7",
  completed: "#2e7d32",
  cancelled: "#9e9e9e",
};

const URGENT_COLOR = "#c62828";

export function planningEventColor(status: Planning["status"], priority: Priority): string {
  if (priority === "urgent" && status !== "cancelled") {
    return URGENT_COLOR;
  }
  return PLANNING_STATUS_COLORS[status];
}
