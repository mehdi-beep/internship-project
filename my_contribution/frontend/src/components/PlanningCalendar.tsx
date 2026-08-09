import { useMemo } from "react";
import dayjs from "dayjs";
import GenericCalendar, { type GenericCalendarEvent } from "./GenericCalendar";
import { planningEventColor } from "../utils/planningColors";
import type { Planning } from "../types/planning";

interface PlanningCalendarProps {
  entries: Planning[];
  onEventClick?: (planning: Planning) => void;
  eventLabel: (planning: Planning) => string;
}

export default function PlanningCalendar({ entries, onEventClick, eventLabel }: PlanningCalendarProps) {
  const events: GenericCalendarEvent[] = useMemo(
    () =>
      entries.map((entry) => ({
        id: entry.id,
        date: dayjs(`${entry.planned_date}T${entry.planned_start_time}`).toISOString(),
        durationMinutes: entry.estimated_duration_minutes ?? 60,
        title: eventLabel(entry),
        color: planningEventColor(entry.status, entry.priority),
      })),
    [entries, eventLabel],
  );

  const handleEventClick = (event: GenericCalendarEvent) => {
    const planning = entries.find((e) => e.id === event.id);
    if (planning && onEventClick) {
      onEventClick(planning);
    }
  };

  return <GenericCalendar events={events} onEventClick={onEventClick ? handleEventClick : undefined} />;
}
