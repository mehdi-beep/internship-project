import type { Priority } from "../types/enums";
import type { Planning } from "../types/planning";

// Ch.143 calendar color rules: Blue=Planned, Green=Completed, Red=Urgent,
// Gray=Draft (n/a to planning), Orange=Pending Approval (n/a to planning),
// Purple=Administrative Approval (n/a to planning).
// Urgent and High (priorities, not statuses) overlay the status color per
// the priority-overlay decision, only while the entry is still active
// (planned/in_progress) — a completed or cancelled entry keeps its own
// status color regardless of priority, so "green = done" stays true for
// every priority level, not just Normal.
const PLANNING_STATUS_COLORS: Record<Planning["status"], string> = {
  planned: "#1976d2",
  in_progress: "#4fc3f7",
  completed: "#2e7d32",
  cancelled: "#9e9e9e",
};

const URGENT_COLOR = "#c62828";
const HIGH_PRIORITY_COLOR = "#ef6c00";

const ACTIVE_STATUSES: ReadonlySet<Planning["status"]> = new Set(["planned", "in_progress"]);

export function planningEventColor(status: Planning["status"], priority: Priority): string {
  if (priority === "urgent" && status !== "cancelled") {
    return URGENT_COLOR;
  }
  if (priority === "high" && ACTIVE_STATUSES.has(status)) {
    return HIGH_PRIORITY_COLOR;
  }
  return PLANNING_STATUS_COLORS[status];
}
