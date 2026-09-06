import { IconButton, Stack, TextField, ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import dayjs from "dayjs";

export type PeriodMode = "daily" | "weekly" | "monthly" | "yearly";

interface PeriodModeSelectorProps {
  mode: PeriodMode;
  /** ISO date (YYYY-MM-DD) anchor — for weekly mode this is always snapped to that week's Monday. */
  anchor: string;
  onModeChange: (mode: PeriodMode) => void;
  onAnchorChange: (anchor: string) => void;
}

// "week" (not "isoWeek") for stepping — a week is always 7 days regardless
// of locale, so plain `.add`/`.subtract` already steps correctly. "isoWeek"
// is only needed for `startOf`, which differs by locale (Sunday vs Monday).
function stepUnit(mode: PeriodMode): "day" | "week" | "month" | "year" {
  if (mode === "daily") return "day";
  if (mode === "weekly") return "week";
  if (mode === "yearly") return "year";
  return "month";
}

function snapToStart(value: string, mode: PeriodMode): string {
  if (mode === "weekly") return dayjs(value).startOf("isoWeek").format("YYYY-MM-DD");
  if (mode === "monthly") return dayjs(value).startOf("month").format("YYYY-MM-DD");
  if (mode === "yearly") return dayjs(value).startOf("year").format("YYYY-MM-DD");
  return dayjs(value).startOf("day").format("YYYY-MM-DD");
}

export default function PeriodModeSelector({ mode, anchor, onModeChange, onAnchorChange }: PeriodModeSelectorProps) {
  const current = dayjs(anchor);

  const step = (delta: number) => {
    onAnchorChange(current.add(delta, stepUnit(mode)).format("YYYY-MM-DD"));
  };

  const reset = () => {
    onAnchorChange(snapToStart(dayjs().format("YYYY-MM-DD"), mode));
  };

  const handleModeChange = (nextMode: PeriodMode) => {
    onModeChange(nextMode);
    onAnchorChange(snapToStart(anchor, nextMode));
  };

  return (
    <Stack direction="row" spacing={1.5} sx={{ alignItems: "center", flexWrap: "wrap" }}>
      <ToggleButtonGroup
        size="small"
        exclusive
        value={mode}
        onChange={(_, next: PeriodMode | null) => next && handleModeChange(next)}
      >
        <ToggleButton value="daily">Day</ToggleButton>
        <ToggleButton value="weekly">Week</ToggleButton>
        <ToggleButton value="monthly">Month</ToggleButton>
        <ToggleButton value="yearly">Year</ToggleButton>
      </ToggleButtonGroup>

      <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
        <IconButton size="small" onClick={() => step(-1)} aria-label={`Previous ${mode}`}>
          <ChevronLeftIcon fontSize="small" />
        </IconButton>

        {mode === "yearly" ? (
          // No native <input type="year"> exists — a constrained number input
          // is the standard substitute, matching this file's one-branch-per-
          // granularity pattern (monthly already has its own "month" branch).
          <TextField
            size="small"
            type="number"
            value={current.format("YYYY")}
            onChange={(e) => {
              const year = Number(e.target.value);
              if (e.target.value && Number.isInteger(year) && year > 0) {
                onAnchorChange(current.year(year).startOf("year").format("YYYY-MM-DD"));
              }
            }}
            slotProps={{ htmlInput: { min: 1, style: { padding: "4px 8px", fontSize: "0.8rem" } } }}
            sx={{ width: 150 }}
          />
        ) : mode === "monthly" ? (
          <TextField
            size="small"
            type="month"
            value={current.format("YYYY-MM")}
            onChange={(e) => e.target.value && onAnchorChange(`${e.target.value}-01`)}
            slotProps={{ htmlInput: { style: { padding: "4px 8px", fontSize: "0.8rem" } } }}
            sx={{ width: 150 }}
          />
        ) : (
          <TextField
            size="small"
            type="date"
            value={current.format("YYYY-MM-DD")}
            onChange={(e) => {
              if (!e.target.value) return;
              // Weekly mode always commits the Monday of whichever week the
              // user clicked in the native day-grid — the visible day picked
              // and the anchor actually used can differ, so the resolved
              // range is echoed as text below.
              const picked = dayjs(e.target.value);
              onAnchorChange(mode === "weekly" ? picked.startOf("isoWeek").format("YYYY-MM-DD") : e.target.value);
            }}
            slotProps={{ htmlInput: { style: { padding: "4px 8px", fontSize: "0.8rem" } } }}
            sx={{ width: 150 }}
          />
        )}

        <IconButton size="small" onClick={() => step(1)} aria-label={`Next ${mode}`}>
          <ChevronRightIcon fontSize="small" />
        </IconButton>
        <IconButton size="small" onClick={reset} aria-label="Reset to current period" title="Reset to today">
          <RestartAltIcon fontSize="small" />
        </IconButton>
      </Stack>

      {mode === "weekly" && (
        <Typography variant="caption" color="text.secondary">
          {current.format("MMM D")} – {current.add(6, "day").format("MMM D, YYYY")}
        </Typography>
      )}
    </Stack>
  );
}
