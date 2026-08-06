import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import ListIcon from "@mui/icons-material/ViewList";
import CalendarIcon from "@mui/icons-material/CalendarMonth";

export type ViewMode = "list" | "calendar";

interface ViewModeToggleProps {
  value: ViewMode;
  onChange: (value: ViewMode) => void;
}

export default function ViewModeToggle({ value, onChange }: ViewModeToggleProps) {
  return (
    <ToggleButtonGroup
      size="small"
      exclusive
      value={value}
      onChange={(_, next: ViewMode | null) => next && onChange(next)}
    >
      <ToggleButton value="list" aria-label="List view">
        <ListIcon sx={{ mr: 0.5, fontSize: 18 }} /> List
      </ToggleButton>
      <ToggleButton value="calendar" aria-label="Calendar view">
        <CalendarIcon sx={{ mr: 0.5, fontSize: 18 }} /> Calendar
      </ToggleButton>
    </ToggleButtonGroup>
  );
}
