import { Chip } from "@mui/material";
import PriorityHighIcon from "@mui/icons-material/PriorityHigh";
import { priorityColors } from "../styles/theme";
import type { Priority } from "../types/enums";

const PRIORITY_LABELS: Record<Priority, string> = {
  normal: "Normal",
  high: "High",
  urgent: "Urgent",
};

export default function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <Chip
      size="small"
      variant={priority === "normal" ? "filled" : "outlined"}
      icon={priority === "urgent" ? <PriorityHighIcon fontSize="small" /> : undefined}
      label={PRIORITY_LABELS[priority]}
      sx={{
        borderColor: priorityColors[priority],
        color: priority === "normal" ? "#fff" : priorityColors[priority],
        bgcolor: priority === "normal" ? priorityColors[priority] : "transparent",
        fontWeight: 500,
      }}
    />
  );
}
