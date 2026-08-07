import { useEffect, useState } from "react";
import { Navigate, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { Controller, useForm, useWatch } from "react-hook-form";
import dayjs from "dayjs";
import ClientSelect from "../components/ClientSelect";
import SiteSelect from "../components/SiteSelect";
import TravauxMultiSelect from "../components/TravauxMultiSelect";
import ColleagueTechnicianSelect from "../components/ColleagueTechnicianSelect";
import AttachmentUploader from "../components/AttachmentUploader";
import ConfirmationDialog from "../components/ConfirmationDialog";
import { useAuth } from "../context/AuthContext";
import { listContracts } from "../services/contractService";
import { listProjects } from "../services/projectService";
import {
  createIntervention,
  deleteAttachment,
  getIntervention,
  submitIntervention,
  updateIntervention,
  uploadAttachment,
  type InterventionInput,
} from "../services/interventionService";
import type { InterventionType, LocationType } from "../types/enums";

interface FormValues {
  client_id: number;
  site_id: number;
  contact_person: string;
  intervention_type: InterventionType;
  contract_id: number | "";
  project_id: number | "";
  warranty_reference_bi: string;
  location_type: LocationType;
  intervention_date: string;
  start_time: string;
  end_time: string;
  no_lunch_break: boolean;
  lunch_break_minutes: number | "";
  number_of_technicians: number;
  travail_ids: number[];
  colleague_technician_ids: number[];
  technical_report: string;
}

const LUNCH_PRESETS = [0, 30, 60, 90, 120];

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 2, textTransform: "uppercase", letterSpacing: 0.5 }}>
          {title}
        </Typography>
        {children}
      </CardContent>
    </Card>
  );
}

function extractDetail(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string };
    if (first?.msg) return first.msg.replace(/^Value error,\s*/, "");
  }
  return fallback;
}

export default function InterventionFormPage() {
  const { id } = useParams();
  const interventionId = id ? Number(id) : null;
  const isEdit = interventionId !== null;
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // Optional pre-fill for a fresh intervention started from a dashboard
  // planning/urgent assignment — never present on the edit route, so this
  // has no effect on the isEdit path at all. Read once on mount, matching
  // the same query-param deep-link pattern PlanningPage.tsx already uses.
  const [searchParams] = useSearchParams();
  const prefillClientId = !isEdit ? Number(searchParams.get("client_id")) || 0 : 0;
  const prefillSiteId = !isEdit ? Number(searchParams.get("site_id")) || 0 : 0;
  const prefillDate = !isEdit ? searchParams.get("intervention_date") : null;

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [submitConfirmOpen, setSubmitConfirmOpen] = useState(false);

  const { data: existing, isLoading, isError, error } = useQuery({
    queryKey: ["intervention", interventionId],
    queryFn: () => getIntervention(interventionId!),
    enabled: isEdit,
    retry: false,
  });

  const { register, handleSubmit, control, reset, setValue, formState: { errors } } = useForm<FormValues>({
    defaultValues: {
      client_id: prefillClientId,
      site_id: prefillSiteId,
      contact_person: "",
      intervention_type: "standard",
      contract_id: "",
      project_id: "",
      warranty_reference_bi: "",
      location_type: "sur_site",
      intervention_date: prefillDate || dayjs().format("YYYY-MM-DD"),
      start_time: "08:00",
      end_time: "17:00",
      no_lunch_break: false,
      lunch_break_minutes: 60,
      number_of_technicians: 1,
      travail_ids: [],
      colleague_technician_ids: [],
      technical_report: "",
    },
  });

  const clientId = useWatch({ control, name: "client_id" });
  const interventionType = useWatch({ control, name: "intervention_type" });
  const noLunchBreak = useWatch({ control, name: "no_lunch_break" });
  const startTime = useWatch({ control, name: "start_time" });
  const endTime = useWatch({ control, name: "end_time" });
  const lunchMinutes = useWatch({ control, name: "lunch_break_minutes" });

  useEffect(() => {
    if (!existing) return;
    reset({
      client_id: existing.client_id,
      site_id: existing.site_id,
      contact_person: existing.contact_person ?? "",
      intervention_type: existing.intervention_type,
      contract_id: existing.contract_id ?? "",
      project_id: existing.project_id ?? "",
      warranty_reference_bi: "",
      location_type: existing.location_type,
      intervention_date: existing.intervention_date,
      start_time: existing.start_time.slice(0, 5),
      end_time: existing.end_time.slice(0, 5),
      no_lunch_break: existing.lunch_break_minutes === 0,
      lunch_break_minutes: existing.lunch_break_minutes,
      number_of_technicians: existing.number_of_technicians,
      travail_ids: existing.tasks.map((t) => t.travail_id),
      colleague_technician_ids: existing.colleague_technicians.map((c) => c.user_id),
      technical_report: existing.technical_report ?? "",
    });
  }, [existing, reset]);

  const { data: contractsPage, isError: contractsError } = useQuery({
    queryKey: ["contracts", "for-client", clientId],
    queryFn: () => listContracts({ client_id: clientId, status: "active", page_size: 100 }),
    enabled: !!clientId && interventionType === "contract",
  });

  const { data: projectsPage, isError: projectsError } = useQuery({
    queryKey: ["projects", "for-client", clientId],
    queryFn: () => listProjects({ client_id: clientId, status: "active", page_size: 100 }),
    enabled: !!clientId && interventionType === "project",
  });

  // Ch.27 — displayed read-only preview; the backend remains the source of truth.
  const effectiveLunch = noLunchBreak ? 0 : Number(lunchMinutes) || 0;
  const grossMinutes =
    startTime && endTime ? dayjs(`2000-01-01T${endTime}`).diff(dayjs(`2000-01-01T${startTime}`), "minute") : 0;
  const netMinutes = grossMinutes - effectiveLunch;
  const formatDuration = (minutes: number) =>
    minutes >= 0 ? `${Math.floor(minutes / 60)}h${String(minutes % 60).padStart(2, "0")}` : "—";

  const readOnly = isEdit && existing != null && !["draft", "rejected"].includes(existing.status);

  const toInput = (values: FormValues): InterventionInput => ({
    client_id: values.client_id,
    site_id: values.site_id,
    contact_person: values.contact_person || null,
    intervention_type: values.intervention_type,
    contract_id: values.intervention_type === "contract" ? Number(values.contract_id) || null : null,
    project_id: values.intervention_type === "project" ? Number(values.project_id) || null : null,
    warranty_reference_bi: values.intervention_type === "warranty" ? values.warranty_reference_bi || null : null,
    location_type: values.location_type,
    intervention_date: values.intervention_date,
    start_time: values.start_time.length === 5 ? `${values.start_time}:00` : values.start_time,
    end_time: values.end_time.length === 5 ? `${values.end_time}:00` : values.end_time,
    lunch_break_minutes: values.no_lunch_break ? 0 : Number(values.lunch_break_minutes) || 0,
    number_of_technicians: Number(values.number_of_technicians) || 1,
    travail_ids: values.travail_ids,
    colleague_technician_ids: values.colleague_technician_ids,
    technical_report: values.technical_report || null,
  });

  const saveMutation = useMutation({
    mutationFn: (values: FormValues) =>
      isEdit ? updateIntervention(interventionId!, toInput(values)) : createIntervention(toInput(values), false),
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: ["interventions"] });
      queryClient.invalidateQueries({ queryKey: ["intervention", saved.id] });
      setErrorMessage(null);
      if (!isEdit) {
        navigate(`/interventions/${saved.id}/edit`, { replace: true });
      }
    },
    onError: (err) => setErrorMessage(extractDetail(err, "Failed to save the intervention.")),
  });

  const submitMutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const saved = isEdit
        ? await updateIntervention(interventionId!, toInput(values))
        : await createIntervention(toInput(values), false);
      return submitIntervention(saved.id);
    },
    onSuccess: (saved) => {
      queryClient.invalidateQueries({ queryKey: ["interventions"] });
      setSubmitConfirmOpen(false);
      navigate(`/interventions/${saved.id}`);
    },
    onError: (err) => {
      setSubmitConfirmOpen(false);
      setErrorMessage(extractDetail(err, "Failed to submit the intervention."));
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadAttachment(interventionId!, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["intervention", interventionId] }),
  });

  const deleteAttachmentMutation = useMutation({
    mutationFn: (attachmentId: number) => deleteAttachment(attachmentId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["intervention", interventionId] }),
  });

  if (isEdit && isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isEdit && isError) {
    const status = (error as { response?: { status?: number } })?.response?.status;
    if (status === 403) {
      return <Navigate to="/403" replace />;
    }
    return (
      <Alert severity="error">
        {status === 404 ? "Intervention not found." : "Failed to load this intervention. Please try again."}
      </Alert>
    );
  }

  return (
    <Box sx={{ maxWidth: 900 }}>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          {isEdit ? `Intervention ${existing?.bi_number ?? ""}` : "New Intervention"}
        </Typography>
      </Stack>

      {readOnly && (
        <Alert severity="info" sx={{ mb: 2 }}>
          This intervention is locked ({existing?.status.replaceAll("_", " ")}) and can no longer be edited.
        </Alert>
      )}
      {errorMessage && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {errorMessage}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit((v) => saveMutation.mutate(v))} noValidate>
        <Stack spacing={2}>
          <SectionCard title="A — General Information">
            <Stack spacing={2}>
              <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap", gap: 2 }}>
                <TextField
                  label="Technician"
                  value={user ? `${user.first_name} ${user.last_name}` : ""}
                  slotProps={{ input: { readOnly: true } }}
                  sx={{ flex: 1, minWidth: 200 }}
                />
                <TextField
                  label="BI Number"
                  value={existing?.bi_number ?? "Generated on save"}
                  slotProps={{ input: { readOnly: true } }}
                  sx={{ flex: 1, minWidth: 200 }}
                  helperText="Automatic, read-only"
                />
              </Stack>
              <TextField
                label="Intervention Date"
                type="date"
                disabled={readOnly}
                slotProps={{ inputLabel: { shrink: true } }}
                sx={{ maxWidth: 300 }}
                error={!!errors.intervention_date}
                {...register("intervention_date", { required: true })}
              />
              {existing?.submission_date && (
                <Typography variant="caption" color="text.secondary">
                  Submitted {dayjs(existing.submission_date).format("MMM D, YYYY HH:mm")}
                </Typography>
              )}
            </Stack>
          </SectionCard>

          <SectionCard title="B — Client Information">
            <Stack spacing={2}>
              <Controller
                name="client_id"
                control={control}
                rules={{ required: true, validate: (v) => v > 0 }}
                render={({ field }) => (
                  <ClientSelect
                    {...field}
                    disabled={readOnly}
                    error={!!errors.client_id}
                    helperText={errors.client_id ? "Client is required" : undefined}
                    onChange={(e) => {
                      field.onChange(e);
                      setValue("site_id", 0);
                      setValue("contract_id", "");
                      setValue("project_id", "");
                    }}
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
                    clientId={clientId || null}
                    disabled={readOnly}
                    error={!!errors.site_id}
                    helperText={errors.site_id ? "Site is required" : "Filtered by the selected client"}
                  />
                )}
              />
              <TextField label="Contact Person (optional)" fullWidth disabled={readOnly} {...register("contact_person")} />
            </Stack>
          </SectionCard>

          <SectionCard title="C — Intervention Type">
            <Stack spacing={2}>
              <Controller
                name="intervention_type"
                control={control}
                render={({ field }) => (
                  <TextField select label="Intervention Type" fullWidth disabled={readOnly} {...field}>
                    <MenuItem value="standard">Standard</MenuItem>
                    <MenuItem value="contract">Contract</MenuItem>
                    <MenuItem value="project">Project</MenuItem>
                    <MenuItem value="warranty">Warranty</MenuItem>
                  </TextField>
                )}
              />
              {interventionType === "contract" && (
                <Controller
                  name="contract_id"
                  control={control}
                  rules={{ validate: (v) => (interventionType === "contract" ? !!v : true) }}
                  render={({ field }) => (
                    <TextField
                      select
                      label="Contract"
                      fullWidth
                      disabled={readOnly || !clientId}
                      error={!!errors.contract_id || contractsError}
                      helperText={
                        !clientId
                          ? "Select a client first"
                          : contractsError
                            ? "Failed to load contracts. Please try again."
                            : undefined
                      }
                      {...field}
                    >
                      {(contractsPage?.items ?? []).map((c) => (
                        <MenuItem key={c.id} value={c.id}>
                          {c.contract_name}
                        </MenuItem>
                      ))}
                    </TextField>
                  )}
                />
              )}
              {interventionType === "project" && (
                <Controller
                  name="project_id"
                  control={control}
                  rules={{ validate: (v) => (interventionType === "project" ? !!v : true) }}
                  render={({ field }) => (
                    <TextField
                      select
                      label="Project"
                      fullWidth
                      disabled={readOnly || !clientId}
                      error={!!errors.project_id || projectsError}
                      helperText={
                        !clientId
                          ? "Select a client first"
                          : projectsError
                            ? "Failed to load projects. Please try again."
                            : undefined
                      }
                      {...field}
                    >
                      {(projectsPage?.items ?? []).map((p) => (
                        <MenuItem key={p.id} value={p.id}>
                          {p.project_name}
                        </MenuItem>
                      ))}
                    </TextField>
                  )}
                />
              )}
              {interventionType === "warranty" && (
                <TextField
                  label="Previous BI Number"
                  fullWidth
                  disabled={readOnly}
                  placeholder="BI000015"
                  helperText="The referenced BI must already exist."
                  error={!!errors.warranty_reference_bi}
                  {...register("warranty_reference_bi", {
                    validate: (v) => (interventionType === "warranty" ? !!v : true),
                  })}
                />
              )}
            </Stack>
          </SectionCard>

          <SectionCard title="D — Location">
            <Controller
              name="location_type"
              control={control}
              render={({ field }) => (
                <TextField select label="Location" fullWidth disabled={readOnly} {...field}>
                  <MenuItem value="sur_site">Sur Site (client premises)</MenuItem>
                  <MenuItem value="atelier">Atelier (company workshop)</MenuItem>
                </TextField>
              )}
            />
          </SectionCard>

          <SectionCard title="E — Time Information">
            <Stack spacing={2}>
              <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap", gap: 2 }}>
                <TextField
                  label="Start Time"
                  type="time"
                  disabled={readOnly}
                  slotProps={{ inputLabel: { shrink: true } }}
                  sx={{ flex: 1, minWidth: 160 }}
                  error={!!errors.start_time}
                  {...register("start_time", { required: true })}
                />
                <TextField
                  label="End Time"
                  type="time"
                  disabled={readOnly}
                  slotProps={{ inputLabel: { shrink: true } }}
                  sx={{ flex: 1, minWidth: 160 }}
                  error={!!errors.end_time}
                  {...register("end_time", { required: true })}
                />
              </Stack>
              <Stack direction="row" spacing={2} sx={{ alignItems: "center", flexWrap: "wrap", gap: 2 }}>
                <Controller
                  name="no_lunch_break"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      select
                      label="Lunch Break"
                      disabled={readOnly}
                      sx={{ minWidth: 180 }}
                      value={field.value ? "none" : "custom"}
                      onChange={(e) => field.onChange(e.target.value === "none")}
                    >
                      <MenuItem value="none">No Lunch Break</MenuItem>
                      <MenuItem value="custom">Lunch Break…</MenuItem>
                    </TextField>
                  )}
                />
                {!noLunchBreak && (
                  <Controller
                    name="lunch_break_minutes"
                    control={control}
                    render={({ field }) => (
                      <TextField select label="Duration" disabled={readOnly} sx={{ minWidth: 180 }} {...field}>
                        {LUNCH_PRESETS.map((m) => (
                          <MenuItem key={m} value={m}>
                            {m === 0 ? "0 min" : m < 60 ? `${m} min` : `${m / 60} hour${m > 60 ? "s" : ""}`}
                          </MenuItem>
                        ))}
                      </TextField>
                    )}
                  />
                )}
              </Stack>
              <Divider />
              <Stack direction="row" spacing={4} sx={{ flexWrap: "wrap" }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Gross Duration
                  </Typography>
                  <Typography variant="body1">{formatDuration(grossMinutes)}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Lunch Break
                  </Typography>
                  <Typography variant="body1">{formatDuration(effectiveLunch)}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Net Duration (calculated)
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {existing ? formatDuration(existing.net_duration_minutes) : formatDuration(netMinutes)}
                  </Typography>
                </Box>
              </Stack>
              <Typography variant="caption" color="text.secondary">
                Net duration is calculated automatically and cannot be edited.
              </Typography>
            </Stack>
          </SectionCard>

          <SectionCard title="F — Number of Technicians">
            <Stack spacing={2}>
              <TextField
                label="Number of Technicians"
                type="number"
                disabled={readOnly}
                sx={{ maxWidth: 240 }}
                slotProps={{ htmlInput: { min: 1 } }}
                {...register("number_of_technicians", { valueAsNumber: true, min: 1 })}
              />
              <Controller
                name="colleague_technician_ids"
                control={control}
                render={({ field }) => (
                  <ColleagueTechnicianSelect
                    value={field.value}
                    onChange={field.onChange}
                    excludeUserId={user?.id}
                    disabled={readOnly}
                    helperText="Optional — add other technicians who assisted with this intervention."
                  />
                )}
              />
            </Stack>
          </SectionCard>

          <SectionCard title="G — Travaux Effectués">
            <Controller
              name="travail_ids"
              control={control}
              render={({ field }) => (
                <TravauxMultiSelect
                  value={field.value}
                  onChange={field.onChange}
                  disabled={readOnly}
                  helperText="Selected from the catalog only — free typing is not allowed."
                />
              )}
            />
          </SectionCard>

          <SectionCard title="H — Comments / Technical Report">
            <TextField
              label="Technical Report"
              fullWidth
              multiline
              minRows={4}
              disabled={readOnly}
              placeholder="Problem, solution, notes, recommendations…"
              {...register("technical_report")}
            />
          </SectionCard>

          <SectionCard title="I — Attachments (mandatory before submission)">
            {isEdit ? (
              <AttachmentUploader
                attachments={existing?.attachments ?? []}
                readOnly={readOnly}
                onUpload={async (file) => {
                  await uploadMutation.mutateAsync(file);
                }}
                onDelete={async (attachmentId) => {
                  await deleteAttachmentMutation.mutateAsync(attachmentId);
                }}
              />
            ) : (
              <Alert severity="info">
                Save this intervention as a draft first, then attach the photographed signed paper BI.
              </Alert>
            )}
          </SectionCard>

          {!readOnly && (
            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", pb: 4 }}>
              <Button onClick={() => navigate("/interventions")}>Cancel</Button>
              <Button type="submit" variant="outlined" disabled={saveMutation.isPending}>
                Save Draft
              </Button>
              <Button
                variant="contained"
                disabled={submitMutation.isPending || !isEdit}
                onClick={handleSubmit(() => setSubmitConfirmOpen(true))}
              >
                Submit
              </Button>
            </Stack>
          )}
        </Stack>
      </Box>

      <ConfirmationDialog
        open={submitConfirmOpen}
        title="Submit Intervention"
        message="Once submitted, this intervention is locked and can no longer be edited until a supervisor makes a decision. Continue?"
        confirmLabel="Submit"
        loading={submitMutation.isPending}
        onConfirm={handleSubmit((v) => submitMutation.mutate(v))}
        onCancel={() => setSubmitConfirmOpen(false)}
      />
    </Box>
  );
}
