import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Chip,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/EditOutlined";
import DeleteIcon from "@mui/icons-material/DeleteOutlined";
import BlockIcon from "@mui/icons-material/BlockOutlined";
import CheckCircleIcon from "@mui/icons-material/CheckCircleOutlined";
import { useForm } from "react-hook-form";
import DataTable, { type DataTableColumn } from "../../components/DataTable";
import Modal from "../../components/Modal";
import ConfirmationDialog from "../../components/ConfirmationDialog";
import {
  activatePointRule,
  createPointRule,
  deactivatePointRule,
  deletePointRule,
  getAppSettings,
  listPointRules,
  updateAppSettings,
  updatePointRule,
  type PointRuleInput,
} from "../../services/pointRuleService";
import type { PointRule } from "../../types/pointRule";

// GMT-12 to GMT+14 in whole-hour steps (the backend's full supported range,
// see app_settings_service.MIN/MAX_OFFSET_MINUTES) plus the well-known
// half-hour/45-minute real-world offsets (India, Newfoundland, Nepal,
// Chatham Islands, etc.) — a whole-hour-only dropdown would be an odd
// omission given the range explicitly reaches GMT+14, itself a real offset
// (Kiribati) most numeric pickers leave out entirely.
const HALF_AND_QUARTER_HOUR_OFFSETS_MINUTES = [-570, -180, -30, 330, 345, 525, 570, 630] as const;

function formatOffsetLabel(minutes: number): string {
  const sign = minutes < 0 ? "-" : "+";
  const abs = Math.abs(minutes);
  const hours = Math.floor(abs / 60);
  const mins = abs % 60;
  return mins === 0 ? `GMT${sign}${hours}` : `GMT${sign}${hours}:${String(mins).padStart(2, "0")}`;
}

const UTC_OFFSET_OPTIONS_MINUTES = Array.from(
  new Set([
    ...Array.from({ length: 27 }, (_, i) => (i - 12) * 60), // GMT-12 .. GMT+14
    ...HALF_AND_QUARTER_HOUR_OFFSETS_MINUTES,
  ]),
).sort((a, b) => a - b);

function toInputTime(value: string): string {
  return value.slice(0, 5);
}

function toApiTime(value: string): string {
  return value.length === 5 ? `${value}:00` : value;
}

// A rule's end_time <= start_time is the documented midnight-crossing
// representation (e.g. 22:00-00:00, or 23:00-02:00) — not a data error.
function formatWindow(rule: PointRule): string {
  const start = toInputTime(rule.start_time);
  const end = toInputTime(rule.end_time);
  const crossesMidnight = rule.end_time <= rule.start_time;
  return crossesMidnight ? `${start} → ${end} (+1 day)` : `${start} → ${end}`;
}

export default function PointRulesPage() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<PointRule | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [confirmTarget, setConfirmTarget] = useState<PointRule | null>(null);
  const [confirmErrorMessage, setConfirmErrorMessage] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<PointRule | null>(null);
  const [deleteErrorMessage, setDeleteErrorMessage] = useState<string | null>(null);
  // Client-side pagination only — the Administrator may configure any number
  // of rules (no server-side cap), GET /point-rules always returns the full
  // set, and this just controls how many rows are shown per page here.
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const { data: rules, isLoading, isError } = useQuery({
    queryKey: ["point-rules"],
    queryFn: () => listPointRules(),
  });

  const sortedRules = [...(rules ?? [])].sort((a, b) => a.start_time.localeCompare(b.start_time));
  const pagedRules = sortedRules.slice((page - 1) * pageSize, page * pageSize);

  // Company Timezone (fixed UTC offset) — a separate settings surface from
  // the rules table above, but on the same page/router since both feed
  // calculate_points(). Local `selectedOffset` state, synced from the fetched
  // value via useEffect below rather than read live off `appSettings` in the
  // dropdown's `value` prop directly: this lets the dropdown show the
  // Administrator's in-progress selection immediately without waiting for
  // the PUT round-trip, the same "local state captured on load" shape the
  // rest of this page already uses for its edit modal (see openEdit's reset()
  // below) — a background refetch of this query updating `appSettings`
  // underneath a not-yet-saved selection would otherwise revert it.
  const { data: appSettings, isLoading: settingsLoading, isError: settingsError } = useQuery({
    queryKey: ["app-settings"],
    queryFn: () => getAppSettings(),
  });
  const [selectedOffset, setSelectedOffset] = useState<number | null>(null);
  const [settingsSaved, setSettingsSaved] = useState(false);
  useEffect(() => {
    if (appSettings && selectedOffset === null) {
      setSelectedOffset(appSettings.company_utc_offset_minutes);
    }
  }, [appSettings, selectedOffset]);

  const updateSettingsMutation = useMutation({
    mutationFn: (offsetMinutes: number) => updateAppSettings(offsetMinutes),
    onSuccess: (updated) => {
      queryClient.setQueryData(["app-settings"], updated);
      setSettingsSaved(true);
    },
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<PointRuleInput>();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["point-rules"] });

  const extractErrorDetail = (err: unknown, fallback: string): string => {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    return detail ?? fallback;
  };

  const createMutation = useMutation({
    mutationFn: (input: PointRuleInput) => createPointRule(input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: (err: unknown) => setErrorMessage(extractErrorDetail(err, "Failed to create point rule.")),
  });

  const updateMutation = useMutation({
    mutationFn: (input: PointRuleInput) => updatePointRule(editing!.id, input),
    onSuccess: () => {
      invalidate();
      setModalOpen(false);
    },
    onError: (err: unknown) => setErrorMessage(extractErrorDetail(err, "Failed to update point rule.")),
  });

  const toggleActiveMutation = useMutation({
    mutationFn: (rule: PointRule) => (rule.active ? deactivatePointRule(rule.id) : activatePointRule(rule.id)),
    onSuccess: () => {
      invalidate();
      setConfirmTarget(null);
      setConfirmErrorMessage(null);
    },
    onError: (err: unknown) =>
      setConfirmErrorMessage(extractErrorDetail(err, "Failed to update the rule. Please try again.")),
  });

  const deleteMutation = useMutation({
    mutationFn: (rule: PointRule) => deletePointRule(rule.id),
    onSuccess: () => {
      invalidate();
      setDeleteTarget(null);
      setDeleteErrorMessage(null);
    },
    onError: () => setDeleteErrorMessage("Failed to delete the rule. Please try again."),
  });

  const openCreate = () => {
    setEditing(null);
    reset({ start_time: "17:00", end_time: "19:00", points: 5 });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const openEdit = (rule: PointRule) => {
    setEditing(rule);
    reset({ start_time: toInputTime(rule.start_time), end_time: toInputTime(rule.end_time), points: rule.points });
    setErrorMessage(null);
    setModalOpen(true);
  };

  const onSubmit = (values: PointRuleInput) => {
    const payload: PointRuleInput = {
      start_time: toApiTime(values.start_time),
      end_time: toApiTime(values.end_time),
      points: Number(values.points),
    };
    if (editing) {
      updateMutation.mutate(payload);
    } else {
      createMutation.mutate(payload);
    }
  };

  const columns: DataTableColumn<PointRule>[] = [
    { key: "window", label: "Time Window", render: (r) => formatWindow(r) },
    {
      key: "points",
      label: "Points",
      render: (r) => (
        <Chip
          size="small"
          label={r.points > 0 ? `+${r.points}` : `${r.points}`}
          color={r.points > 0 ? "success" : r.points < 0 ? "error" : "default"}
        />
      ),
    },
    { key: "status", label: "Status", render: (r) => (r.active ? "Active" : "Inactive") },
    {
      key: "actions",
      label: "Actions",
      align: "right",
      render: (r) => (
        <Stack direction="row" spacing={0.5} sx={{ justifyContent: "flex-end" }}>
          <Tooltip title="Edit">
            <IconButton size="small" onClick={() => openEdit(r)}>
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title={r.active ? "Deactivate" : "Activate"}>
            <IconButton size="small" onClick={() => { setConfirmErrorMessage(null); setConfirmTarget(r); }}>
              {r.active ? <BlockIcon fontSize="small" /> : <CheckCircleIcon fontSize="small" />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete">
            <IconButton size="small" onClick={() => { setDeleteErrorMessage(null); setDeleteTarget(r); }}>
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Stack>
      ),
    },
  ];

  return (
    <Box>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            Point Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Configure the time windows and point values technicians earn when submitting an intervention. Editing or
            deleting a rule only affects future submissions — points already awarded on past interventions never
            change.
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          New Rule
        </Button>
      </Stack>

      <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          Company Timezone (for Point Rule time windows)
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          A fixed UTC offset used to convert a submission's timestamp before checking it against the time windows
          above. This is a fixed offset, not automatically DST-adjusted — if the real local clock changes (e.g.
          seasonal shifts), an Administrator must update this value manually.
        </Typography>
        {settingsError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to load the company timezone setting. Please check your connection and try again.
          </Alert>
        )}
        {updateSettingsMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to save the company timezone. Please try again.
          </Alert>
        )}
        <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
          <TextField
            select
            size="small"
            label="Company Timezone"
            disabled={settingsLoading}
            value={selectedOffset ?? ""}
            onChange={(e) => {
              setSelectedOffset(Number(e.target.value));
              setSettingsSaved(false);
            }}
            sx={{ minWidth: 220 }}
          >
            {UTC_OFFSET_OPTIONS_MINUTES.map((minutes) => (
              <MenuItem key={minutes} value={minutes}>
                {formatOffsetLabel(minutes)}
              </MenuItem>
            ))}
          </TextField>
          <Button
            variant="contained"
            disabled={
              selectedOffset === null ||
              selectedOffset === appSettings?.company_utc_offset_minutes ||
              updateSettingsMutation.isPending
            }
            onClick={() => selectedOffset !== null && updateSettingsMutation.mutate(selectedOffset)}
          >
            Save
          </Button>
          {settingsSaved && !updateSettingsMutation.isPending && (
            <Typography variant="body2" color="success.main">
              Saved.
            </Typography>
          )}
        </Stack>
      </Paper>

      {isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load point rules. Please check your connection and try again.
        </Alert>
      )}

      <DataTable
        columns={columns}
        rows={pagedRules}
        rowKey={(r) => r.id}
        loading={isLoading}
        emptyMessage="No point rules configured. Every submission will receive the default penalty until at least one active rule exists."
        page={page}
        pageSize={pageSize}
        total={sortedRules.length}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setPage(1);
        }}
      />

      <Modal open={modalOpen} title={editing ? "Edit Point Rule" : "New Point Rule"} onClose={() => setModalOpen(false)}>
        <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate sx={{ pt: 1 }}>
          <Stack spacing={2}>
            {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
            <Stack direction="row" spacing={2}>
              <TextField
                label="Start Time"
                type="time"
                fullWidth
                slotProps={{ inputLabel: { shrink: true } }}
                error={!!errors.start_time}
                helperText={errors.start_time?.message}
                {...register("start_time", { required: "Start time is required" })}
              />
              <TextField
                label="End Time"
                type="time"
                fullWidth
                slotProps={{ inputLabel: { shrink: true } }}
                error={!!errors.end_time}
                helperText={errors.end_time?.message ?? "An end time at or before start time means the window crosses midnight."}
                {...register("end_time", { required: "End time is required" })}
              />
            </Stack>
            <TextField
              label="Points"
              type="number"
              fullWidth
              error={!!errors.points}
              helperText={errors.points?.message ?? "Positive, zero, or negative values are all allowed."}
              {...register("points", { required: "Points is required", valueAsNumber: true })}
            />
            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end" }}>
              <Button onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button type="submit" variant="contained" disabled={createMutation.isPending || updateMutation.isPending}>
                Save
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Modal>

      <ConfirmationDialog
        open={!!confirmTarget}
        title={confirmTarget?.active ? "Deactivate Point Rule" : "Activate Point Rule"}
        message={
          confirmTarget?.active
            ? `Deactivate this rule (${confirmTarget ? formatWindow(confirmTarget) : ""})? It will no longer apply to new submissions, but past interventions already scored under it are unaffected.`
            : `Reactivate this rule (${confirmTarget ? formatWindow(confirmTarget) : ""})?`
        }
        confirmLabel={confirmTarget?.active ? "Deactivate" : "Activate"}
        confirmColor={confirmTarget?.active ? "error" : "primary"}
        loading={toggleActiveMutation.isPending}
        errorMessage={confirmErrorMessage}
        onConfirm={() => confirmTarget && toggleActiveMutation.mutate(confirmTarget)}
        onCancel={() => { setConfirmTarget(null); setConfirmErrorMessage(null); }}
      />

      <ConfirmationDialog
        open={!!deleteTarget}
        title="Delete Point Rule"
        message={`Permanently delete this rule (${deleteTarget ? formatWindow(deleteTarget) : ""})? This cannot be undone. Past interventions already scored under it are unaffected — only future submissions are impacted.`}
        confirmLabel="Delete"
        confirmColor="error"
        loading={deleteMutation.isPending}
        errorMessage={deleteErrorMessage}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget)}
        onCancel={() => { setDeleteTarget(null); setDeleteErrorMessage(null); }}
      />
    </Box>
  );
}
