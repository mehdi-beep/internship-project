import { Chip } from "@mui/material";
import { statusColors } from "../styles/theme";
import type { InterventionStatus } from "../types/enums";

const STATUS_LABELS: Record<InterventionStatus, string> = {
  draft: "Draft",
  planned: "Planned",
  in_progress: "In Progress",
  submitted: "Submitted",
  pending_technical_approval: "Pending Technical Approval",
  technical_approved: "Technical Approved",
  pending_administrative_approval: "Pending Administrative Approval",
  fully_approved: "Fully Approved",
  rejected: "Rejected",
};

export default function StatusBadge({ status }: { status: InterventionStatus }) {
  return (
    <Chip
      size="small"
      label={STATUS_LABELS[status]}
      sx={{ bgcolor: statusColors[status], color: "#fff", fontWeight: 500 }}
    />
  );
}
