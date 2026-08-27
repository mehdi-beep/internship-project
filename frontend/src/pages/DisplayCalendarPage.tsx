import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import WifiTetheringIcon from "@mui/icons-material/WifiTethering";
import LogoutIcon from "@mui/icons-material/LogoutOutlined";
import dayjs from "dayjs";
import GenericCalendar, { type GenericCalendarEvent } from "../components/GenericCalendar";
import Modal from "../components/Modal";
import { listPlanningForDisplay } from "../services/planningService";
import type { PlanningDisplayEntry } from "../types/planning";
import { planningEventColor } from "../utils/planningColors";
import { useAuth } from "../context/AuthContext";

const PRIORITY_LABELS: Record<PlanningDisplayEntry["priority"], string> = {
  normal: "Normal",
  high: "High",
  urgent: "Urgent",
};

const STATUS_LABELS: Record<PlanningDisplayEntry["status"], string> = {
  planned: "Planned",
  in_progress: "In Progress",
  completed: "Completed",
  cancelled: "Cancelled",
};

// Matches the proven useNotificationPolling interval elsewhere in the app —
// the "least invasive suitable mechanism" per Task 3's own instructions,
// reusing TanStack Query's built-in refetchInterval rather than introducing
// WebSocket/SSE infrastructure that doesn't exist anywhere else in this
// codebase. 20s keeps "planning created -> display updates" feeling live on
// a hallway screen without hammering the API from a device that never stops
// polling (this page is meant to run 24/7).
const POLL_INTERVAL_MS = 20_000;

// Unbounded on purpose (user request): every planning entry that has ever
// existed or ever will, with no prev/next navigation needed since there's no
// window to page through (this screen is unattended, so nobody could click
// "next month" anyway). `date_from`/`date_to` left undefined rather than
// computed — the backend's list_planning_for_display only applies a WHERE
// clause when a bound is actually given (planning_service.py:44-48), and
// axios drops undefined query params entirely, so this really does request
// zero date filtering rather than a very large date range standing in for
// one. Worth knowing: every 20s poll now re-fetches the company's entire
// planning history, which only grows over time — if the kiosk ever needs to
// scale to a very large multi-year dataset, this is the first place to
// revisit.
function displayRange() {
  return {
    date_from: undefined,
    date_to: undefined,
  };
}

export default function DisplayCalendarPage() {
  const { logout } = useAuth();
  const [now, setNow] = useState(() => dayjs());

  // FullCalendar needs a concrete pixel height (see GenericCalendar's `height`
  // prop docs — "100%" collapses the grid inside a flex child). This measures
  // whatever vertical space is actually left between the header and footer and
  // feeds it in, re-measuring on window resize so the hallway screen stays
  // correct if the display resolution or browser window ever changes.
  const calendarBoxRef = useRef<HTMLDivElement | null>(null);
  const [calendarHeight, setCalendarHeight] = useState(0);

  useEffect(() => {
    const measure = () => {
      const el = calendarBoxRef.current;
      if (el) setCalendarHeight(el.clientHeight);
    };
    measure();
    const observer = new ResizeObserver(measure);
    if (calendarBoxRef.current) observer.observe(calendarBoxRef.current);
    window.addEventListener("resize", measure);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);

  useEffect(() => {
    const clockTimer = setInterval(() => setNow(dayjs()), 1000);
    return () => clearInterval(clockTimer);
  }, []);

  const { data: entries, isError, dataUpdatedAt } = useQuery({
    queryKey: ["planning", "display"],
    queryFn: () => listPlanningForDisplay(displayRange()),
    refetchInterval: POLL_INTERVAL_MS,
    refetchIntervalInBackground: true,
    // A hallway kiosk has no human present to dismiss a stale-data warning —
    // keep showing the last-known-good calendar through a transient network
    // blip rather than blanking the screen, and let the (still-running)
    // next poll recover silently.
    retry: 3,
  });

  const entriesById = useMemo(() => new Map((entries ?? []).map((e) => [String(e.id), e])), [entries]);

  const events: GenericCalendarEvent[] = (entries ?? []).map((entry) => ({
    id: entry.id,
    date: entry.planned_date,
    time: entry.planned_start_time,
    durationMinutes: entry.estimated_duration_minutes ?? 60,
    // "HH:MM Technician — Client". The time is folded into the title (and
    // FullCalendar's own separate time element is hidden via CSS) because
    // when both render side by side in a narrow month cell they each get
    // truncated; as one string the ellipsis falls at the end, leaving the
    // time and technician name always readable. City was dropped from the
    // cell for the same width reason — it's still shown in the detail popup.
    title: `${entry.planned_start_time.slice(0, 5)} ${entry.technician_name} — ${entry.client_name}`,
    color: planningEventColor(entry.status, entry.priority),
  }));

  // Two read-only popups, both plain MUI Dialogs (via the shared Modal
  // component) rather than FullCalendar's own popover: a Dialog is always
  // centered in the viewport by MUI itself regardless of which day/event was
  // clicked or where it sits in the grid, which is what actually fixes "the
  // popup renders below/off the screen for a day near the bottom" — that
  // could never be fixed by styling FullCalendar's own popover, since it
  // deliberately anchors itself next to the triggering element, not the
  // viewport center. Both dialogs are portal-rendered to the document body
  // (standard Dialog behavior), so the full calendar remains visible,
  // dimmed, behind them.
  const [overflowDay, setOverflowDay] = useState<{ date: string; eventIds: string[] } | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const selectedEntry = selectedEventId ? entriesById.get(selectedEventId) : undefined;
  const overflowEntries = overflowDay
    ? overflowDay.eventIds.map((id) => entriesById.get(id)).filter((e): e is PlanningDisplayEntry => !!e)
    : [];

  return (
    <Box
      sx={{
        // A hard viewport ceiling, not just height:"100%" resolving through
        // the html/body/#root chain in index.css. That chain uses
        // min-height:100vh (so ordinary scrolling pages can still grow
        // taller than one screen) — which means if THIS page's own content
        // ever exceeds one screen (e.g. FullCalendar rendering a 6-row
        // month), height:"100%" alone lets body/#root grow to match rather
        // than clipping, and the whole page scrolls instead of this box's
        // own overflow:hidden ever taking effect. 100dvh is a hard cap that
        // content cannot stretch — "dvh" (dynamic viewport height) also
        // correctly accounts for real browser chrome (tab strip, bookmarks
        // bar) the way plain "vh"/height:"100%" do not, so this box is sized
        // against what's actually visible on screen, not the OS display
        // resolution.
        height: "100dvh",
        width: "100%",
        display: "flex",
        flexDirection: "column",
        bgcolor: "background.default",
        overflow: "hidden",
        boxSizing: "border-box",
        p: 2,
      }}
    >
      {/* Header sizes scale with the viewport (clamp) rather than being fixed
          at h3/h4: on a 768px-tall laptop the old fixed sizes consumed ~80px
          before the calendar even began, contributing to it overflowing the
          bottom of the screen. On a genuinely large hallway screen these
          still render large. */}
      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "center", mb: 1, flexShrink: 0, gap: 2, flexWrap: "wrap" }}
      >
        <Typography sx={{ fontWeight: 700, fontSize: "clamp(1.25rem, 2.2vw, 2.25rem)", lineHeight: 1.2 }}>
          Global Planning Calendar
        </Typography>
        <Stack direction="row" spacing={1.5} sx={{ alignItems: "center", flexWrap: "wrap" }}>
          <Chip
            icon={<WifiTetheringIcon />}
            label="Live"
            color="success"
            variant="outlined"
            size="small"
          />
          <Typography
            sx={{ fontWeight: 600, fontVariantNumeric: "tabular-nums", fontSize: "clamp(1.1rem, 1.8vw, 1.9rem)" }}
          >
            {now.format("HH:mm:ss")}
          </Typography>
          <Typography color="text.secondary" sx={{ fontSize: "clamp(0.8rem, 1vw, 1.1rem)" }}>
            {now.format("dddd, MMMM D, YYYY")}
          </Typography>
        </Stack>
      </Stack>

      {isError && (
        <Alert severity="warning" sx={{ mb: 1, flexShrink: 0 }}>
          Could not refresh planning data — showing the last successfully loaded calendar.
        </Alert>
      )}

      <Box
        ref={calendarBoxRef}
        sx={{
          flex: 1,
          // minHeight: 0 lets this flex child actually shrink below its
          // content size; without it a flex item's default min-height:auto
          // would push the calendar past the bottom of the screen.
          minHeight: 0,
          overflow: "hidden",
          // Font sizes are kept modest on purpose: this box is a fixed height,
          // so anything larger just squeezes the day cells rather than making
          // the calendar bigger. Readability at a distance comes from the
          // screen being large, not from the browser zooming.
          "& .fc-toolbar-title": { fontSize: "1.25rem", fontWeight: 700 },
          "& .fc-col-header-cell-cushion": { fontSize: "0.9rem", fontWeight: 600 },
          "& .fc-daygrid-day-number": { fontSize: "0.9rem" },
          "& .fc-event": { fontSize: "0.8rem !important", padding: "1px 3px" },
          "& .fc-button": { fontSize: "0.85rem" },
          "& .fc-toolbar.fc-header-toolbar": { marginBottom: "0.5rem" },
          // In the narrow month cells the time and the name compete for width
          // and BOTH end up truncated ("1... Cynthia Diaz — Adki..."). The
          // time is the less useful half at a glance and is always shown in
          // full in the day popover, so it's hidden here to give the
          // technician/client name the entire cell width.
          "& .fc-daygrid-event .fc-event-time": { display: "none" },
          "& .fc-daygrid-event .fc-event-title": {
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          },
          // The "+N more" link: make it obviously clickable on a big screen.
          "& .fc-daygrid-more-link": {
            fontSize: "0.78rem",
            fontWeight: 700,
            color: "primary.main",
          },
        }}
      >
        {/* Rendered only once the container has been measured — passing 0 (or
            "100%") makes FullCalendar collapse its grid to just the header
            row, which is exactly the bug this measurement avoids. */}
        {calendarHeight > 0 && (
          <GenericCalendar
            events={events}
            height={calendarHeight}
            onEventClick={(event) => setSelectedEventId(String(event.id))}
            onMoreLinkClick={(date, eventIds) => setOverflowDay({ date, eventIds: eventIds.map(String) })}
          />
        )}
      </Box>

      <Stack
        direction="row"
        sx={{ justifyContent: "space-between", alignItems: "center", mt: 0.5, flexShrink: 0, gap: 2 }}
      >
        <Typography variant="caption" color="text.secondary">
          Last updated {dataUpdatedAt ? dayjs(dataUpdatedAt).format("HH:mm:ss") : "—"} · refreshes automatically every{" "}
          {POLL_INTERVAL_MS / 1000}s
        </Typography>
        {/* No navigation, no admin affordances anywhere on this screen by
            design — the one exception is a way to end an unattended kiosk
            session if the device is ever repurposed. Rendered as a real
            outlined Button (it was previously small underlined caption text,
            which read as a label rather than something clickable). */}
        <Button
          variant="outlined"
          size="small"
          color="inherit"
          startIcon={<LogoutIcon />}
          onClick={logout}
          sx={{ flexShrink: 0, textTransform: "none" }}
        >
          Sign out
        </Button>
      </Stack>

      {/* A busy day's full list — each row opens the same detail dialog below. */}
      <Modal
        open={!!overflowDay}
        title={overflowDay ? dayjs(overflowDay.date).format("dddd, MMMM D, YYYY") : ""}
        onClose={() => setOverflowDay(null)}
      >
        <List dense disablePadding sx={{ maxHeight: "60vh", overflowY: "auto" }}>
          {overflowEntries.map((entry, index) => (
            <Box key={entry.id}>
              {index > 0 && <Divider component="li" />}
              <ListItemButton
                onClick={() => {
                  setSelectedEventId(String(entry.id));
                  setOverflowDay(null);
                }}
                sx={{ borderLeft: 4, borderLeftColor: planningEventColor(entry.status, entry.priority), py: 1 }}
              >
                <ListItemText
                  primary={`${entry.planned_start_time.slice(0, 5)} — ${entry.technician_name}`}
                  secondary={`${entry.client_name} · ${entry.site_name}, ${entry.city}`}
                />
              </ListItemButton>
            </Box>
          ))}
        </List>
      </Modal>

      {/* A single assignment's full detail — the read-only equivalent of what
          the Admin/Chef Planning page shows in its edit form, minus the
          fields that only make sense for someone who can act on it
          (notes, who created it): this screen has no write access at all,
          per Task 3, so there's nothing here to edit or act on. */}
      <Modal
        open={!!selectedEntry}
        title={selectedEntry ? `${selectedEntry.technician_name} — ${selectedEntry.client_name}` : ""}
        onClose={() => setSelectedEventId(null)}
      >
        {selectedEntry && (
          <Stack spacing={1.5}>
            <Stack direction="row" spacing={1}>
              <Chip
                size="small"
                label={STATUS_LABELS[selectedEntry.status]}
                sx={{ bgcolor: planningEventColor(selectedEntry.status, selectedEntry.priority), color: "#fff" }}
              />
              {selectedEntry.priority !== "normal" && (
                <Chip
                  size="small"
                  label={PRIORITY_LABELS[selectedEntry.priority]}
                  color={selectedEntry.priority === "urgent" ? "error" : "warning"}
                  variant="outlined"
                />
              )}
            </Stack>
            <Stack spacing={0.5}>
              <Typography variant="overline" color="text.secondary">Technician</Typography>
              <Typography variant="body1">{selectedEntry.technician_name}</Typography>
            </Stack>
            <Stack spacing={0.5}>
              <Typography variant="overline" color="text.secondary">Client &amp; Site</Typography>
              <Typography variant="body1">{selectedEntry.client_name}</Typography>
              <Typography variant="body2" color="text.secondary">
                {selectedEntry.site_name}, {selectedEntry.city}
              </Typography>
            </Stack>
            <Stack spacing={0.5}>
              <Typography variant="overline" color="text.secondary">Date &amp; Time</Typography>
              <Typography variant="body1">
                {dayjs(selectedEntry.planned_date).format("dddd, MMMM D, YYYY")} at{" "}
                {selectedEntry.planned_start_time.slice(0, 5)}
              </Typography>
              {selectedEntry.estimated_duration_minutes != null && (
                <Typography variant="body2" color="text.secondary">
                  Estimated duration: {selectedEntry.estimated_duration_minutes} min
                </Typography>
              )}
            </Stack>
          </Stack>
        )}
      </Modal>
    </Box>
  );
}
