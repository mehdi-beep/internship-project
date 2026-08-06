import { useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  Stack,
  Typography,
} from "@mui/material";
import EditIcon from "@mui/icons-material/EditOutlined";
import dayjs from "dayjs";
import AttachmentUploader from "../components/AttachmentUploader";
import InterventionReviewViewer from "../components/InterventionReviewViewer";
import StatusBadge from "../components/StatusBadge";
import { getIntervention } from "../services/interventionService";
import { listClients } from "../services/clientService";
import { listSites } from "../services/siteService";
import { listTravaux } from "../services/travailService";
import { listTechnicianOptions } from "../services/userService";
import { useAuth } from "../context/AuthContext";

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <Box sx={{ minWidth: 180 }}>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2">{value ?? "—"}</Typography>
    </Box>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
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

const formatDuration = (minutes: number) => `${Math.floor(minutes / 60)}h${String(minutes % 60).padStart(2, "0")}`;

export default function InterventionDetailsPage() {
  const { id } = useParams();
  const interventionId = Number(id);
  const navigate = useNavigate();
  const { user } = useAuth();
  const [reviewingAttachmentIndex, setReviewingAttachmentIndex] = useState<number | null>(null);

  const { data: intervention, isLoading, isError, error } = useQuery({
    queryKey: ["intervention", interventionId],
    queryFn: () => getIntervention(interventionId),
    retry: false,
  });

  const { data: clientsData } = useQuery({
    queryKey: ["clients", "lookup-all"],
    queryFn: () => listClients({ page_size: 100, active_only: true }),
  });
  const { data: sitesData } = useQuery({
    queryKey: ["sites", "lookup-all"],
    queryFn: () => listSites({ page_size: 100, active_only: true }),
  });
  const { data: travauxData } = useQuery({
    queryKey: ["travaux", "catalog-all"],
    queryFn: () => listTravaux({ page_size: 100, active_only: true }),
  });
  const { data: technicianOptions } = useQuery({
    queryKey: ["users", "technician-options"],
    queryFn: listTechnicianOptions,
  });

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError) {
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

  if (!intervention) {
    return null;
  }

  const clientName = clientsData?.items.find((c) => c.id === intervention.client_id)?.client_name;
  const site = sitesData?.items.find((s) => s.id === intervention.site_id);
  const travailById = new Map((travauxData?.items ?? []).map((t) => [t.id, t]));
  const technicianNameById = new Map(
    (technicianOptions ?? []).map((t) => [t.id, `${t.first_name} ${t.last_name}`]),
  );

  // Ch.15/17 — only the owning technician may edit, and only while Draft or Rejected.
  const isOwner = user?.id === intervention.technician_id;
  const isEditable = isOwner && ["draft", "rejected"].includes(intervention.status);

  return (
    <Box sx={{ maxWidth: 900 }}>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2, flexWrap: "wrap", gap: 2 }}>
        <Stack direction="row" spacing={2} sx={{ alignItems: "center" }}>
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            {intervention.bi_number}
          </Typography>
          <StatusBadge status={intervention.status} />
        </Stack>
        {isEditable && (
          <Button variant="contained" startIcon={<EditIcon />} onClick={() => navigate(`/interventions/${intervention.id}/edit`)}>
            Edit
          </Button>
        )}
      </Stack>

      <Stack spacing={2}>
        <Section title="General Information">
          <Stack direction="row" spacing={4} sx={{ flexWrap: "wrap", gap: 2 }}>
            <Field label="BI Number" value={intervention.bi_number} />
            <Field label="Intervention Date" value={dayjs(intervention.intervention_date).format("MMM D, YYYY")} />
            <Field
              label="Submission Date"
              value={intervention.submission_date ? dayjs(intervention.submission_date).format("MMM D, YYYY HH:mm") : "—"}
            />
            <Field
              label="Technical Approval"
              value={
                intervention.technical_approval_date
                  ? dayjs(intervention.technical_approval_date).format("MMM D, YYYY HH:mm")
                  : "—"
              }
            />
            <Field
              label="Administrative Approval"
              value={
                intervention.administrative_approval_date
                  ? dayjs(intervention.administrative_approval_date).format("MMM D, YYYY HH:mm")
                  : "—"
              }
            />
          </Stack>
        </Section>

        <Section title="Client Information">
          <Stack direction="row" spacing={4} sx={{ flexWrap: "wrap", gap: 2 }}>
            <Field label="Client" value={clientName ?? `#${intervention.client_id}`} />
            <Field label="Site" value={site ? `${site.site_name} (${site.city})` : `#${intervention.site_id}`} />
            <Field label="Contact Person" value={intervention.contact_person} />
          </Stack>
        </Section>

        <Section title="Intervention Information">
          <Stack direction="row" spacing={4} sx={{ flexWrap: "wrap", gap: 2 }}>
            <Field label="Type" value={intervention.intervention_type} />
            <Field label="Location" value={intervention.location_type === "sur_site" ? "Sur Site" : "Atelier"} />
            <Field label="Number of Technicians" value={intervention.number_of_technicians} />
            {intervention.warranty_reference_id && (
              <Field label="Warranty Reference" value={`Intervention #${intervention.warranty_reference_id}`} />
            )}
          </Stack>
        </Section>

        <Section title="Colleague Technicians">
          {intervention.colleague_technicians.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No colleague technicians added.
            </Typography>
          ) : (
            <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", gap: 1 }}>
              {intervention.colleague_technicians.map((colleague) => (
                <Chip
                  key={colleague.id}
                  label={technicianNameById.get(colleague.user_id) ?? `#${colleague.user_id}`}
                />
              ))}
            </Stack>
          )}
        </Section>

        <Section title="Time & Duration">
          <Stack direction="row" spacing={4} sx={{ flexWrap: "wrap", gap: 2 }}>
            <Field label="Start Time" value={intervention.start_time.slice(0, 5)} />
            <Field label="End Time" value={intervention.end_time.slice(0, 5)} />
            <Field label="Lunch Break" value={formatDuration(intervention.lunch_break_minutes)} />
            <Field label="Net Duration" value={formatDuration(intervention.net_duration_minutes)} />
            <Field label="Points Earned" value={intervention.points_earned} />
          </Stack>
        </Section>

        <Section title="Travaux Effectués">
          {intervention.tasks.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No travaux selected.
            </Typography>
          ) : (
            <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", gap: 1 }}>
              {intervention.tasks.map((task) => {
                const travail = travailById.get(task.travail_id);
                return (
                  <Chip
                    key={task.id}
                    label={travail ? `${travail.travail_code} — ${travail.travail_name}` : `#${task.travail_id}`}
                  />
                );
              })}
            </Stack>
          )}
        </Section>

        <Section title="Technical Report">
          <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
            {intervention.technical_report || "—"}
          </Typography>
        </Section>

        <Section title="Attachments">
          <AttachmentUploader
            attachments={intervention.attachments}
            readOnly
            onUpload={async () => {}}
            onDelete={async () => {}}
            onImageClick={(index) => setReviewingAttachmentIndex(index)}
          />
        </Section>

        <Section title="Approval History">
          {intervention.approval_history.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No approval decisions recorded yet.
            </Typography>
          ) : (
            <Stack spacing={1}>
              {intervention.approval_history.map((entry) => (
                <Box key={entry.id}>
                  <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
                    <Chip
                      size="small"
                      label={entry.decision}
                      color={entry.decision === "approved" ? "success" : "error"}
                    />
                    <Typography variant="body2">{entry.approval_level} approval</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {dayjs(entry.approval_date).format("MMM D, YYYY HH:mm")}
                    </Typography>
                  </Stack>
                  {entry.comment && (
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                      {entry.comment}
                    </Typography>
                  )}
                  <Divider sx={{ mt: 1 }} />
                </Box>
              ))}
            </Stack>
          )}
        </Section>

        <Section title="Timeline (Audit Trail)">
          <Stack spacing={1}>
            {intervention.audit_log.map((entry) => (
              <Stack key={entry.id} direction="row" spacing={2} sx={{ alignItems: "baseline" }}>
                <Typography variant="caption" color="text.secondary" sx={{ minWidth: 140 }}>
                  {dayjs(entry.created_at).format("MMM D, YYYY HH:mm")}
                </Typography>
                <Typography variant="body2">{entry.action.replaceAll("_", " ")}</Typography>
                {entry.comment && (
                  <Typography variant="caption" color="text.secondary">
                    {entry.comment}
                  </Typography>
                )}
              </Stack>
            ))}
          </Stack>
        </Section>
      </Stack>

      <InterventionReviewViewer
        interventionId={reviewingAttachmentIndex !== null ? intervention.id : null}
        readOnly
        initialAttachmentIndex={reviewingAttachmentIndex ?? 0}
        onClose={() => setReviewingAttachmentIndex(null)}
      />
    </Box>
  );
}
