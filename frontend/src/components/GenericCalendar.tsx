import { useMemo } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import type { DatesSetArg, EventClickArg, EventInput, MoreLinkArg } from "@fullcalendar/core";
import { Box } from "@mui/material";
import dayjs from "dayjs";

export interface GenericCalendarEvent {
  id: string | number;
  /** ISO date (YYYY-MM-DD) or full ISO datetime. */
  date: string;
  /** Optional time (HH:mm or HH:mm:ss) appended to `date` when `date` has no time component. */
  time?: string;
  durationMinutes?: number;
  title: string;
  color: string;
  onClick?: (event: GenericCalendarEvent) => void;
}

interface GenericCalendarProps {
  events: GenericCalendarEvent[];
  onEventClick?: (event: GenericCalendarEvent) => void;
  /** Fires whenever the visible date range changes (initial render, prev/next, today, view switch). */
  onVisibleRangeChange?: (range: { start: string; end: string }) => void;
  /** FullCalendar's own height mode. Defaults to "auto" — the calendar grows
   * to fit its content and the page scrolls — which is right for every
   * calendar rendered inside AppLayout's scrolling content area.
   *
   * Pass an explicit **pixel number** for a fixed-height container that must
   * never overflow (the hallway DisplayCalendarPage). Note: "100%" does NOT
   * work reliably here — FullCalendar resolves height in JS at render time,
   * and inside a flex child it measures 0 and collapses the grid to just its
   * header row. A concrete number is what actually works, so the caller is
   * responsible for measuring its own container. */
  height?: "auto" | number;
  /** Overrides FullCalendar's own "+N more" behavior (popover/day-view/etc.)
   * with a caller-supplied handler, given the day and the ids of every event
   * on it (visible + hidden). FullCalendar's built-in popover anchors itself
   * next to the link that was clicked, so on a day near the bottom of the
   * grid it can render partially or fully below the viewport — there is no
   * built-in way to force it to center. Passing this prop suppresses the
   * native popover entirely so the caller can render its own
   * always-centered UI (e.g. a Dialog) instead. */
  onMoreLinkClick?: (date: string, eventIds: (string | number)[]) => void;
}

export default function GenericCalendar({
  events,
  onEventClick,
  onVisibleRangeChange,
  height = "auto",
  onMoreLinkClick,
}: GenericCalendarProps) {
  const fcEvents: EventInput[] = useMemo(
    () =>
      events.map((event) => {
        const start = event.time ? dayjs(`${event.date}T${event.time}`) : dayjs(event.date);
        const duration = event.durationMinutes ?? 60;
        return {
          id: String(event.id),
          title: event.title,
          start: start.toISOString(),
          end: start.add(duration, "minute").toISOString(),
          backgroundColor: event.color,
          borderColor: event.color,
        };
      }),
    [events],
  );

  const handleEventClick = (arg: EventClickArg) => {
    const match = events.find((e) => String(e.id) === arg.event.id);
    if (!match) return;
    if (match.onClick) {
      match.onClick(match);
    } else if (onEventClick) {
      onEventClick(match);
    }
  };

  const handleDatesSet = (arg: DatesSetArg) => {
    onVisibleRangeChange?.({
      start: dayjs(arg.start).format("YYYY-MM-DD"),
      end: dayjs(arg.end).format("YYYY-MM-DD"),
    });
  };

  // FullCalendar's own MoreLinkContainer (internal-common.js) resolves the
  // native popover with:
  //   if (!moreLinkClick || moreLinkClick === 'popover') { open native popover }
  //   else if (typeof moreLinkClick === 'string') { calendarApi.zoomTo(date, moreLinkClick) }
  // Two things this means, both confirmed by testing against the actual
  // running library (not just its .d.ts, which is misleading here):
  //  1. Returning `undefined`/void — the documented "do nothing" value per
  //     the MoreLinkHandler type (`MoreLinkSimpleAction | void`) — is treated
  //     as "no handler was given" and opens the native popover ANYWAY: it
  //     rendered a live `.fc-popover` element on top of this app's own
  //     Dialog when this returned void.
  //  2. There is no value the published type permits that reaches neither
  //     branch: any string other than 'popover' still hits the `zoomTo`
  //     branch (which would navigate to a nonsense view), and `boolean` is
  //     rejected by the type even though the runtime's `!moreLinkClick` /
  //     `typeof ... === 'string'` checks would treat `true` correctly (both
  //     conditions false, neither branch runs). The type declaration is
  //     simply incomplete for this case — the cast below reflects verified
  //     runtime behavior, not a guess.
  const handleMoreLinkClick = (arg: MoreLinkArg) => {
    if (!onMoreLinkClick) return "popover" as const;
    onMoreLinkClick(
      dayjs(arg.date).format("YYYY-MM-DD"),
      arg.allSegs.map((seg) => seg.event.id),
    );
    return true as unknown as "popover";
  };

  return (
    <Box
      sx={{
        "& .fc": { fontFamily: "inherit" },
        "& .fc-event": { cursor: "pointer", fontSize: "0.75rem" },
      }}
    >
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        headerToolbar={{ left: "prev,next today", center: "title", right: "dayGridMonth,timeGridWeek,timeGridDay" }}
        height={height}
        // Only constrain rows in fixed-height mode. Without this, a dense week
        // still grows its row past the container even though the overall
        // height is honored, pushing the final week off-screen; `true` caps
        // each cell to the space available and collapses the rest into a
        // "+N more" link. In "auto" mode (every other calendar in the app,
        // rendered inside a scrolling page) this stays off so every event
        // remains visible, exactly as before.
        dayMaxEventRows={height === "auto" ? undefined : true}
        // See onMoreLinkClick's own doc comment above for why this is a
        // handler function rather than the simpler "popover" string when the
        // caller wants centered control over what opens.
        moreLinkClick={handleMoreLinkClick}
        events={fcEvents}
        eventClick={handleEventClick}
        datesSet={handleDatesSet}
      />
    </Box>
  );
}
