import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Alert, Box, Card, CardContent, Chip, CircularProgress, Stack, Typography } from "@mui/material";
import dayjs from "dayjs";
import PlanningCalendar from "../components/PlanningCalendar";
import { listPlanning } from "../services/planningService";
import { listClients } from "../services/clientService";
import { useAuth } from "../context/AuthContext";
import type { Planning } from "../types/planning";

export default function CalendarPage() {
  const { user } = useAuth();
  const [monthRange] = useState(() => ({
    date_from: dayjs().startOf("month").subtract(1, "month").format("YYYY-MM-DD"),
    date_to: dayjs().endOf("month").add(1, "month").format("YYYY-MM-DD"),
  }));
  const [selected, setSelected] = useState<Planning | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["planning", "my-calendar", monthRange],
    queryFn: () => listPlanning({ ...monthRange, page_size: 200 }),
  });

  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });
  const clientNameById = new Map((clientsData?.items ?? []).map((c) => [c.id, c.client_name]));

  const entries = (data?.items ?? []).filter((p) => p.status !== "cancelled");
  const eventLabel = (planning: Planning) => clientNameById.get(planning.client_id) ?? "Client";

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
        My Calendar
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Read-only view of your planned interventions, {user?.first_name}.
      </Typography>

      {isLoading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress />
        </Box>
      )}

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load your calendar. Please check your connection and try again.
        </Alert>
      )}

      {!isLoading && !isError && entries.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: "center" }}>
          No planning available.
        </Typography>
      )}

      {!isLoading && !isError && entries.length > 0 && (
        <PlanningCalendar entries={entries} eventLabel={eventLabel} onEventClick={setSelected} />
      )}

      {selected && (
        <Card sx={{ mt: 3, maxWidth: 480 }}>
          <CardContent>
            <Stack spacing={1}>
              <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  {clientNameById.get(selected.client_id) ?? "Client"}
                </Typography>
                {selected.priority === "urgent" && <Chip size="small" color="error" label="Urgent" />}
              </Stack>
              <Typography variant="body2">
                {dayjs(selected.planned_date).format("MMMM D, YYYY")} at {selected.planned_start_time.slice(0, 5)}
              </Typography>
              {selected.estimated_duration_minutes && (
                <Typography variant="body2" color="text.secondary">
                  Estimated duration: {selected.estimated_duration_minutes} minutes
                </Typography>
              )}
              {selected.notes && (
                <Typography variant="body2" color="text.secondary">
                  {selected.notes}
                </Typography>
              )}
            </Stack>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
