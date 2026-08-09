import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import PriorityHighIcon from "@mui/icons-material/PriorityHigh";
import { Controller, useForm } from "react-hook-form";
import dayjs from "dayjs";
import PlanningCalendar from "../components/PlanningCalendar";
import Modal from "../components/Modal";
import ConfirmationDialog from "../components/ConfirmationDialog";
import ClientSelect from "../components/ClientSelect";
import SiteSelect from "../components/SiteSelect";
import { listClients } from "../services/clientService";
import { listUsers } from "../services/userService";
import {
  cancelPlanning,
  createPlanning,
  listPlanning,
  markPlanningUrgent,
  updatePlanning,
  type PlanningCreateInput,
  type PlanningUpdateInput,
} from "../services/planningService";
import type { Planning } from "../types/planning";

interface FormValues {
  technician_id: number;
  client_id: number;
  site_id: number;
  planned_date: string;
  planned_start_time: string;
  estimated_duration_minutes: number | "";
  priority: "normal" | "high" | "urgent";
  notes: string;
}

export default function PlanningPage() {
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const highlightId = searchParams.get("highlight");
  const [monthRange] = useState(() => ({
    date_from: dayjs().startOf("month").subtract(1, "month").format("YYYY-MM-DD"),
    date_to: dayjs().endOf("month").add(1, "month").format("YYYY-MM-DD"),
  }));
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Planning | null>(null);
  const [cancelTarget, setCancelTarget] = useState<Planning | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [cancelErrorMessage, setCancelErrorMessage] = useState<string | null>(null);

  const { data: planningPage, isLoading, isError } = useQuery({
    queryKey: ["planning", "calendar", monthRange],
    queryFn: () => listPlanning({ ...monthRange, page_size: 200 }),
  });

  const { data: techniciansPage } = useQuery({
    queryKey: ["users", "technicians-select"],
    queryFn: () => listUsers({ role: "technician", page_size: 100 }),
  });
  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });
  const clientNameById = new Map((clientsData?.items ?? []).map((c) => [c.id, c.client_name]));
  const technicianNameById = new Map(
    (techniciansPage?.items ?? []).map((t) => [t.id, `${t.first_name} ${t.last_name}`]),
  );

  const { register, handleSubmit, reset, watch, control, formState: { errors } } = useForm<FormValues>({
    defaultValues: {
      technician_id: 0,
      client_id: 0,
      site_id: 0,
      planned_date: dayjs().format("YYYY-MM-DD"),
      planned_start_time: "09:00",
      estimated_duration_minutes: 60,
      priority: "normal",
      notes: "",
    },
  });
  const selectedClientId = watch("client_id");

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["planning"] });

  const createMutation = useMutation({
    mutationFn: (input: PlanningCreateInput) => createPlanning(input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErrorMessage(detail ?? "Failed to save planning entry.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: (input: PlanningUpdateInput) => updatePlanning(editing!.id, input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErrorMessage(detail ?? "Failed to save planning entry.");
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (planning: Planning) => cancelPlanning(planning.id),
    onSuccess: () => {
      invalidate();
      setCancelTarget(null);
      setCancelErrorMessage(null);
    },
    onError: () => setCancelErrorMessage("Failed to cancel the planning entry. Please try again."),
  });

  const urgentMutation = useMutation({
    mutationFn: (planning: Planning) => markPlanningUrgent(planning.id),
    onSuccess: invalidate,
    onError: () => setErrorMessage("Failed to mark the planning entry as urgent. Please try again."),
  });

  const openCreate = (priority: FormValues["priority"] = "normal") => {
    setEditing(null);
    reset({
      technician_id: 0,
      client_id: 0,
      site_id: 0,
      planned_date: dayjs().format("YYYY-MM-DD"),
      planned_start_time: "09:00",
      estimated_duration_minutes: 60,
      priority,
      notes: "",
    });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const openEdit = (planning: Planning) => {
    setEditing(planning);
    reset({
      technician_id: planning.technician_id,
      client_id: planning.client_id,
      site_id: planning.site_id,
      planned_date: planning.planned_date,
      planned_start_time: planning.planned_start_time.slice(0, 5),
      estimated_duration_minutes: planning.estimated_duration_minutes ?? "",
      priority: planning.priority,
      notes: planning.notes ?? "",
    });
    setErrorMessage(null);
    setModalOpen(true);
  };

  useEffect(() => {
    if (!highlightId || !planningPage?.items.length) return;
    const match = planningPage.items.find((p) => p.id === Number(highlightId));
    if (match) openEdit(match);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highlightId, planningPage]);

  const onSubmit = (values: FormValues) => {
    const startTime = values.planned_start_time.length === 5 ? `${values.planned_start_time}:00` : values.planned_start_time;
    if (editing) {
      updateMutation.mutate({
        technician_id: values.technician_id,
        planned_date: values.planned_date,
        planned_start_time: startTime,
        estimated_duration_minutes: values.estimated_duration_minutes === "" ? null : values.estimated_duration_minutes,
        priority: values.priority,
        notes: values.notes || null,
      });
    } else {
      createMutation.mutate({
        technician_id: values.technician_id,
        client_id: values.client_id,
        site_id: values.site_id,
        planned_date: values.planned_date,
        planned_start_time: startTime,
        estimated_duration_minutes: values.estimated_duration_minutes === "" ? null : values.estimated_duration_minutes,
        priority: values.priority,
        notes: values.notes || null,
      });
    }
  };

  const eventLabel = (planning: Planning) =>
    `${technicianNameById.get(planning.technician_id) ?? "Technician"} — ${clientNameById.get(planning.client_id) ?? "Client"}`;

  const activeEntries = (planningPage?.items ?? []).filter((p) => p.status !== "cancelled");
  const urgentCount = activeEntries.filter((p) => p.priority === "urgent").length;

  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            Planning
          </Typography>
          {urgentCount > 0 && (
            <Chip
              size="small"
              color="error"
              label={`${urgentCount} urgent`}
              icon={<PriorityHighIcon sx={{ fontSize: 16 }} />}
            />
          )}
        </Stack>
        <Stack direction="row" spacing={1}>
          <Button
            variant="outlined"
            color="error"
            startIcon={<PriorityHighIcon />}
            onClick={() => openCreate("urgent")}
          >
            New Urgent Intervention
          </Button>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => openCreate()}>
            New Planning
          </Button>
        </Stack>
      </Stack>

      {isLoading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress />
        </Box>
      )}

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load the planning calendar. Please check your connection and try again.
        </Alert>
      )}

      {!isLoading && !isError && activeEntries.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ py: 4, textAlign: "center" }}>
          No planning available.
        </Typography>
      )}

      {!isLoading && !isError && activeEntries.length > 0 && (
        <PlanningCalendar entries={activeEntries} eventLabel={eventLabel} onEventClick={openEdit} />
      )}

      <Modal open={modalOpen} title={editing ? "Edit Planning" : "New Planning"} onClose={() => setModalOpen(false)}>
        <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate sx={{ pt: 1 }}>
          <Stack spacing={2}>
            {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
            <Controller
              name="client_id"
              control={control}
              rules={{ required: true, validate: (v) => v > 0 }}
              render={({ field }) => (
                <ClientSelect
                  {...field}
                  disabled={!!editing}
                  error={!!errors.client_id}
                  helperText={editing ? "Client cannot be changed." : errors.client_id ? "Client is required" : undefined}
                />
              )}
            />
            <Controller
              name="site_id"
              control={control}
              rules={{ required: true, validate: (v) => v > 0 }}
              render={({ field }) => (
                <SiteSelect
                  {...field}
                  clientId={selectedClientId || null}
                  disabled={!!editing}
                  error={!!errors.site_id}
                  helperText={editing ? "Site cannot be changed." : errors.site_id ? "Site is required" : undefined}
                />
              )}
            />
            <Controller
              name="technician_id"
              control={control}
              rules={{ required: true, validate: (v) => v > 0 }}
              render={({ field }) => (
                <TextField select label="Technician" fullWidth error={!!errors.technician_id} {...field}>
                  {(techniciansPage?.items ?? []).map((t) => (
                    <MenuItem key={t.id} value={t.id}>
                      {t.first_name} {t.last_name}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
            <Stack direction="row" spacing={2}>
              <TextField
                label="Date"
                type="date"
                fullWidth
                slotProps={{ inputLabel: { shrink: true } }}
                error={!!errors.planned_date}
                {...register("planned_date", { required: true })}
              />
              <TextField
                label="Start Time"
                type="time"
                fullWidth
                slotProps={{ inputLabel: { shrink: true } }}
                error={!!errors.planned_start_time}
                {...register("planned_start_time", { required: true })}
              />
            </Stack>
            <Stack direction="row" spacing={2}>
              <TextField
                label="Estimated Duration (minutes)"
                type="number"
                fullWidth
                {...register("estimated_duration_minutes", { valueAsNumber: true })}
              />
              <Controller
                name="priority"
                control={control}
                rules={{ required: true }}
                render={({ field }) => (
                  <TextField select label="Priority" fullWidth {...field}>
                    <MenuItem value="normal">Normal</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="urgent">Urgent</MenuItem>
                  </TextField>
                )}
              />
            </Stack>
            <TextField label="Notes" fullWidth multiline minRows={2} {...register("notes")} />
            <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
              {editing && (
                <Stack direction="row" spacing={1}>
                  <Button color="error" onClick={() => { setModalOpen(false); setCancelErrorMessage(null); setCancelTarget(editing); }}>
                    Cancel Planning
                  </Button>
                  {editing.priority !== "urgent" && (
                    <Button color="warning" disabled={urgentMutation.isPending} onClick={() => urgentMutation.mutate(editing)}>
                      Mark Urgent
                    </Button>
                  )}
                </Stack>
              )}
              <Stack direction="row" spacing={1} sx={{ ml: "auto" }}>
                <Button onClick={() => setModalOpen(false)}>Close</Button>
                <Button type="submit" variant="contained" disabled={createMutation.isPending || updateMutation.isPending}>
                  Save
                </Button>
              </Stack>
            </Stack>
          </Stack>
        </Box>
      </Modal>

      <ConfirmationDialog
        open={!!cancelTarget}
        title="Cancel Planning"
        message="Cancel this planned intervention? The technician will be notified and the history will remain stored."
        confirmLabel="Cancel Planning"
        confirmColor="error"
        loading={cancelMutation.isPending}
        errorMessage={cancelErrorMessage}
        onConfirm={() => cancelTarget && cancelMutation.mutate(cancelTarget)}
        onCancel={() => { setCancelTarget(null); setCancelErrorMessage(null); }}
      />
    </Box>
  );
}
