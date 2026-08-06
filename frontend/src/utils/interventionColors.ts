import { statusColors } from "../styles/theme";
import type { InterventionStatus } from "../types/enums";

export function interventionEventColor(status: InterventionStatus): string {
  return statusColors[status];
}
