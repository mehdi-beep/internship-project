import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { List, ListItem, ListItemText, Typography } from "@mui/material";
import DragIndicatorIcon from "@mui/icons-material/DragIndicator";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
  arrayMove,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { reorderUrgentQueue } from "../services/planningService";
import type { PlanningSummary } from "../types/dashboard";

interface UrgentQueueListProps {
  entries: PlanningSummary[];
}

function SortableRow({ entry }: { entry: PlanningSummary }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: entry.id });

  return (
    <ListItem
      ref={setNodeRef}
      divider
      sx={{
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
        cursor: "grab",
        bgcolor: isDragging ? "action.hover" : undefined,
      }}
      {...attributes}
      {...listeners}
      secondaryAction={<DragIndicatorIcon fontSize="small" color="disabled" />}
    >
      <ListItemText
        primary={`${entry.planned_start_time.slice(0, 5)} — ${entry.client_name}`}
        secondary={entry.site_name}
      />
    </ListItem>
  );
}

export default function UrgentQueueList({ entries }: UrgentQueueListProps) {
  const queryClient = useQueryClient();
  const [order, setOrder] = useState(entries.map((e) => e.id));

  useEffect(() => {
    setOrder(entries.map((e) => e.id));
  }, [entries]);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  const reorderMutation = useMutation({
    mutationFn: (orderedIds: number[]) => reorderUrgentQueue(orderedIds),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboard", "supervisor"] }),
  });

  const entryById = new Map(entries.map((e) => [e.id, e]));
  const orderedEntries = order.map((id) => entryById.get(id)).filter((e): e is PlanningSummary => !!e);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = order.indexOf(Number(active.id));
    const newIndex = order.indexOf(Number(over.id));
    const next = arrayMove(order, oldIndex, newIndex);
    setOrder(next);
    reorderMutation.mutate(next);
  };

  if (entries.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No urgent interventions.
      </Typography>
    );
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={order} strategy={verticalListSortingStrategy}>
        <List dense sx={{ overflow: "auto", maxHeight: 260 }}>
          {orderedEntries.map((entry) => (
            <SortableRow key={entry.id} entry={entry} />
          ))}
        </List>
      </SortableContext>
    </DndContext>
  );
}
