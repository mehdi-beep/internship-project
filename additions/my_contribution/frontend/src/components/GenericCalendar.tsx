import { useMemo } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import type { DatesSetArg, EventClickArg, EventInput } from "@fullcalendar/core";
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
}

export default function GenericCalendar({ events, onEventClick, onVisibleRangeChange }: GenericCalendarProps) {
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
        height="auto"
        events={fcEvents}
        eventClick={handleEventClick}
        datesSet={handleDatesSet}
      />
    </Box>
  );
}
