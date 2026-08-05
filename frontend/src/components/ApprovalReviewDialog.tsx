import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Grid,
  IconButton,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import OpenInNewIcon from "@mui/icons-material/OpenInNewOutlined";
import dayjs from "dayjs";
import AttachmentUploader from "./AttachmentUploader";
import { getIntervention } from "../services/interventionService";
import { listClients } from "../services/clientService";
import { listSites } from "../services/siteService";
import { listTravaux } from "../services/travailService";
import type { ApprovalDecision } from "../services/approvalService";

interface ApprovalReviewDialogProps {
  interventionId: number | null;
  onClose: () => void;
  onDecide: (decision: ApprovalDecision, comment: string) => void;
  deciding: boolean;
  errorMessage: string | null;
  level: "technical" | "administrative";
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <Box>
      <Typography variant="caption" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2">{value ?? "—"}</Typography>
    </Box>
  );
}

export default function ApprovalReviewDialog({
  interventionId,
  onClose,
  onDecide,
  deciding,
  errorMessage,
  level,
}: ApprovalReviewDialogProps) {
  const navigate = useNavigate();
  const [comment, setComment] = useState("");
  const [rejecting, setRejecting] = useState(false);

  const { data: intervention, isLoading } = useQuery({
    queryKey: ["intervention", interventionId],
    queryFn: () => getIntervention(interventionId!),
    enabled: interventionId !== null,
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

  const handleClose = () => {
    setComment("");
    setRejecting(false);
    onClose();
  };

  const handleApprove = () => onDecide("approved", comment);
  const handleReject = () => onDecide("rejected", comment);

  const clientName = clientsData?.items.find((c) => c.id === intervention?.client_id)?.client_name;
  const site = sitesData?.items.find((s) => s.id === intervention?.site_id);
  const travailById = new Map((travauxData?.items ?? []).map((t) => [t.id, t]));
  const formatDuration = (minutes: number) => `${Math.floor(minutes / 60)}h${String(minutes % 60).padStart(2, "0")}`;

  return (
    <Dialog open={interventionId !== null} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        {intervention ? `Review ${intervention.bi_number}` : "Review Intervention"}
        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
          {intervention && (
            <IconButton size="small" onClick={() => navigate(`/interventions/${intervention.id}`)} aria-label="Open full details">
              <OpenInNewIcon fontSize="small" />
            </IconButton>
          )}
          <IconButton size="small" onClick={handleClose} aria-label="Close">
            <CloseIcon fontSize="small" />
          </IconButton>
        </Stack>
      </DialogTitle>
      <DialogContent dividers>
        {isLoading || !intervention ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                Digital Form
              </Typography>
              <Stack spacing={1.5}>
                <Stack direction="row" spacing={3}>
                  <Field label="Client" value={clientName} />
                  <Field label="Site" value={site ? `${site.site_name} (${site.city})` : undefined} />
                </Stack>
                <Stack direction="row" spacing={3}>
                  <Field label="Date" value={dayjs(intervention.intervention_date).format("MMM D, YYYY")} />
                  <Field label="Type" value={intervention.intervention_type} />
                  <Field label="Location" value={intervention.location_type === "sur_site" ? "Sur Site" : "Atelier"} />
                </Stack>
                <Stack direction="row" spacing={3}>
                  <Field label="Start" value={intervention.start_time.slice(0, 5)} />
                  <Field label="End" value={intervention.end_time.slice(0, 5)} />
                  <Field label="Net Duration" value={formatDuration(intervention.net_duration_minutes)} />
                </Stack>
                <Divider />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Travaux Effectués
                  </Typography>
                  <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", gap: 0.5, mt: 0.5 }}>
                    {intervention.tasks.length === 0 ? (
                      <Typography variant="body2" color="text.secondary">
                        —
                      </Typography>
                    ) : (
                      intervention.tasks.map((task) => {
                        const travail = travailById.get(task.travail_id);
                        return <Chip key={task.id} size="small" label={travail?.travail_code ?? `#${task.travail_id}`} />;
                      })
                    )}
                  </Stack>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Technical Report
                  </Typography>
                  <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
                    {intervention.technical_report || "—"}
                  </Typography>
                </Box>
                {level === "administrative" && (
                  <>
                    <Divider />
                    <Typography variant="caption" color="text.secondary">
                      Technical Approval History
                    </Typography>
                    {intervention.approval_history
                      .filter((entry) => entry.approval_level === "technical")
                      .map((entry) => (
                        <Typography key={entry.id} variant="body2">
                          Approved {dayjs(entry.approval_date).format("MMM D, YYYY HH:mm")}
                          {entry.comment ? ` — "${entry.comment}"` : ""}
                        </Typography>
                      ))}
                  </>
                )}
              </Stack>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1 }}>
                Attached Paper BI
              </Typography>
              <AttachmentUploader
                attachments={intervention.attachments}
                readOnly
                onUpload={async () => {}}
                onDelete={async () => {}}
              />
            </Grid>
          </Grid>
        )}

        {errorMessage && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {errorMessage}
          </Alert>
        )}

        {rejecting && (
          <TextField
            label="Rejection Reason"
            fullWidth
            multiline
            minRows={2}
            required
            sx={{ mt: 2 }}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            autoFocus
          />
        )}
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        {rejecting ? (
          <>
            <Button onClick={() => setRejecting(false)} disabled={deciding}>
              Back
            </Button>
            <Button color="error" variant="contained" disabled={!comment.trim() || deciding} onClick={handleReject}>
              Confirm Rejection
            </Button>
          </>
        ) : (
          <>
            <Button onClick={handleClose} disabled={deciding}>
              Close
            </Button>
            <Button color="error" variant="outlined" disabled={deciding || !intervention} onClick={() => setRejecting(true)}>
              Reject
            </Button>
            <Button color="success" variant="contained" disabled={deciding || !intervention} onClick={handleApprove}>
              Approve
            </Button>
          </>
        )}
      </DialogActions>
    </Dialog>
  );
}
