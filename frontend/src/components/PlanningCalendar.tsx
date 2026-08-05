import { useMemo } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import type { EventClickArg, EventInput } from "@fullcalendar/core";
import { Box } from "@mui/material";
import dayjs from "dayjs";
import { planningEventColor } from "../utils/planningColors";
import type { Planning } from "../types/planning";

interface PlanningCalendarProps {
  entries: Planning[];
  onEventClick?: (planning: Planning) => void;
  eventLabel: (planning: Planning) => string;
}

export default function PlanningCalendar({ entries, onEventClick, eventLabel }: PlanningCalendarProps) {
  const events: EventInput[] = useMemo(
    () =>
      entries.map((entry) => {
        const start = dayjs(`${entry.planned_date}T${entry.planned_start_time}`);
        const durationMinutes = entry.estimated_duration_minutes ?? 60;
        return {
          id: String(entry.id),
          title: eventLabel(entry),
          start: start.toISOString(),
          end: start.add(durationMinutes, "minute").toISOString(),
          backgroundColor: planningEventColor(entry.status, entry.priority),
          borderColor: planningEventColor(entry.status, entry.priority),
          extendedProps: { planningId: entry.id },
        };
      }),
    [entries, eventLabel],
  );

  const handleEventClick = (arg: EventClickArg) => {
    const planning = entries.find((e) => e.id === Number(arg.event.id));
    if (planning && onEventClick) {
      onEventClick(planning);
    }
  };

  return (
    <Box
      sx={{
        "& .fc": { fontFamily: "inherit" },
        "& .fc-event": { cursor: onEventClick ? "pointer" : "default", fontSize: "0.75rem" },
      }}
    >
      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        headerToolbar={{ left: "prev,next today", center: "title", right: "dayGridMonth,timeGridWeek,timeGridDay" }}
        height="auto"
        events={events}
        eventClick={onEventClick ? handleEventClick : undefined}
      />
    </Box>
  );
}
