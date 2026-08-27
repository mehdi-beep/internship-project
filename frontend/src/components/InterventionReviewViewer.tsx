import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  AppBar,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  Divider,
  Grid,
  IconButton,
  Stack,
  TextField,
  Toolbar,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import OpenInNewIcon from "@mui/icons-material/OpenInNewOutlined";
import ZoomInIcon from "@mui/icons-material/ZoomIn";
import ZoomOutIcon from "@mui/icons-material/ZoomOut";
import CenterFocusStrongIcon from "@mui/icons-material/CenterFocusStrong";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import PictureAsPdfIcon from "@mui/icons-material/PictureAsPdfOutlined";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import dayjs from "dayjs";
import StatusBadge from "./StatusBadge";
import { getIntervention } from "../services/interventionService";
import { listClients } from "../services/clientService";
import { listSites } from "../services/siteService";
import { listTravaux } from "../services/travailService";
import { listTechnicianOptions } from "../services/userService";
import { listContracts } from "../services/contractService";
import { listProjects } from "../services/projectService";
import { useAuthenticatedPreview } from "../hooks/useAuthenticatedPreview";
import type { ApprovalDecision } from "../services/approvalService";
import type { Attachment } from "../types/intervention";

interface InterventionReviewViewerProps {
  interventionId: number | null;
  onClose: () => void;
  onDecide?: (decision: ApprovalDecision, comment: string) => void;
  deciding?: boolean;
  errorMessage?: string | null;
  level?: "technical" | "administrative";
  /** No Approve/Reject actions — used when a technician views their own intervention. */
  readOnly?: boolean;
  /** Which attachment to open on first render, when launched from a specific thumbnail. */
  initialAttachmentIndex?: number;
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

function AttachmentImage({ attachment }: { attachment: Attachment }) {
  const previewUrl = useAuthenticatedPreview(attachment.id);
  const isPdf = attachment.content_type === "application/pdf";

  if (isPdf) {
    return (
      <Stack sx={{ height: "100%", alignItems: "center", justifyContent: "center" }} spacing={2}>
        <PictureAsPdfIcon sx={{ fontSize: 96, color: "grey.500" }} />
        <Typography color="grey.300">{attachment.file_name}</Typography>
        <Button
          variant="outlined"
          onClick={() => previewUrl && window.open(previewUrl, "_blank", "noopener,noreferrer")}
          disabled={!previewUrl}
        >
          Open PDF in new tab
        </Button>
      </Stack>
    );
  }

  if (!previewUrl) {
    return (
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
        <CircularProgress sx={{ color: "grey.400" }} />
      </Box>
    );
  }

  return (
    <TransformWrapper key={attachment.id} centerOnInit>
      {({ zoomIn, zoomOut, resetTransform }) => (
        <>
          <Stack
            direction="row"
            spacing={1}
            sx={{ position: "absolute", top: 8, right: 8, zIndex: 2, bgcolor: "rgba(0,0,0,0.5)", borderRadius: 1 }}
          >
            <IconButton size="small" onClick={() => zoomIn()} aria-label="Zoom in" sx={{ color: "#fff" }}>
              <ZoomInIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => zoomOut()} aria-label="Zoom out" sx={{ color: "#fff" }}>
              <ZoomOutIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => resetTransform()} aria-label="Fit to screen" sx={{ color: "#fff" }}>
              <CenterFocusStrongIcon fontSize="small" />
            </IconButton>
          </Stack>
          <TransformComponent wrapperStyle={{ width: "100%", height: "100%" }} contentStyle={{ width: "100%", height: "100%" }}>
            <Box
              component="img"
              src={previewUrl}
              alt={attachment.file_name}
              sx={{ width: "100%", height: "100%", objectFit: "contain" }}
            />
          </TransformComponent>
        </>
      )}
    </TransformWrapper>
  );
}

export default function InterventionReviewViewer({
  interventionId,
  onClose,
  onDecide,
  deciding = false,
  errorMessage = null,
  level = "administrative",
  readOnly = false,
  initialAttachmentIndex = 0,
}: InterventionReviewViewerProps) {
  const navigate = useNavigate();
  const [comment, setComment] = useState("");
  const [rejecting, setRejecting] = useState(false);
  const [activeIndex, setActiveIndex] = useState(initialAttachmentIndex);

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
  const { data: technicianOptions } = useQuery({
    queryKey: ["users", "technician-options"],
    queryFn: listTechnicianOptions,
  });
  const { data: contractsData } = useQuery({
    queryKey: ["contracts", "lookup-all"],
    queryFn: () => listContracts({ page_size: 100 }),
  });
  const { data: projectsData } = useQuery({
    queryKey: ["projects", "lookup-all"],
    queryFn: () => listProjects({ page_size: 100 }),
  });

  useEffect(() => {
    setActiveIndex(initialAttachmentIndex);
  }, [interventionId, initialAttachmentIndex]);

  const attachments = intervention?.attachments ?? [];
  const activeAttachment = attachments[activeIndex];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (attachments.length <= 1) return;
      if (e.key === "ArrowLeft") setActiveIndex((i) => (i - 1 + attachments.length) % attachments.length);
      if (e.key === "ArrowRight") setActiveIndex((i) => (i + 1) % attachments.length);
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [attachments.length]);

  const handleClose = () => {
    setComment("");
    setRejecting(false);
    onClose();
  };

  const handleApprove = () => onDecide?.("approved", comment);
  const handleReject = () => onDecide?.("rejected", comment);

  const clientName = clientsData?.items.find((c) => c.id === intervention?.client_id)?.client_name;
  const site = sitesData?.items.find((s) => s.id === intervention?.site_id);
  const travailById = new Map((travauxData?.items ?? []).map((t) => [t.id, t]));
  const technicianNameById = new Map((technicianOptions ?? []).map((t) => [t.id, `${t.first_name} ${t.last_name}`]));
  // The lead technician lookup is sourced from an active-only technician
  // list, so it already can't resolve a deactivated account's name — and now
  // it also can't resolve a permanently deleted one, since technician_id
  // itself is null in that case. deleted_user_label (frozen at deletion
  // time) is the only remaining source of their name once that happens.
  const leadTechnicianName =
    intervention?.technician_id != null
      ? technicianNameById.get(intervention.technician_id)
      : (intervention?.deleted_user_label ?? undefined);
  const contractName = contractsData?.items.find((c) => c.id === intervention?.contract_id)?.contract_name;
  const projectName = projectsData?.items.find((p) => p.id === intervention?.project_id)?.project_name;
  const formatDuration = (minutes: number) => `${Math.floor(minutes / 60)}h${String(minutes % 60).padStart(2, "0")}`;

  return (
    <Dialog open={interventionId !== null} onClose={handleClose} fullScreen>
      <AppBar position="static" color="inherit" sx={{ boxShadow: "none", borderBottom: "1px solid", borderColor: "divider" }}>
        <Toolbar sx={{ gap: 2 }}>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
              {intervention ? intervention.bi_number : "Review Intervention"}
            </Typography>
            {!readOnly && (
              <Typography variant="caption" color="text.secondary">
                {level === "administrative" ? "Administrative Review" : "Technical Review"}
              </Typography>
            )}
          </Box>
          {intervention && <StatusBadge status={intervention.status} />}
          {intervention && (
            <IconButton onClick={() => navigate(`/interventions/${intervention.id}`)} aria-label="Open full details">
              <OpenInNewIcon />
            </IconButton>
          )}
          <IconButton onClick={handleClose} aria-label="Close">
            <CloseIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      {isLoading || !intervention ? (
        <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container sx={{ flex: 1, minHeight: 0 }}>
          {/* Left panel — complete digital intervention information */}
          <Grid size={{ xs: 12, md: 5 }} sx={{ display: "flex", flexDirection: "column", minHeight: 0 }}>
            <Box sx={{ p: 3, overflow: "auto", flex: 1 }}>
              <Stack spacing={1.5}>
                <Stack direction="row" spacing={3} sx={{ flexWrap: "wrap", rowGap: 1 }}>
                  <Field label="BI Number" value={intervention.bi_number} />
                  <Field label="Status" value={<StatusBadge status={intervention.status} />} />
                </Stack>
                <Stack direction="row" spacing={3}>
                  <Field label="Technician" value={leadTechnicianName} />
                  <Field label="Submitted" value={intervention.submission_date ? dayjs(intervention.submission_date).format("MMM D, YYYY HH:mm") : "—"} />
                </Stack>
                <Stack direction="row" spacing={3}>
                  <Field label="Client" value={clientName} />
                  <Field label="Site" value={site ? `${site.site_name} (${site.city})` : undefined} />
                </Stack>
                <Stack direction="row" spacing={3}>
                  <Field label="Type" value={intervention.intervention_type} />
                  <Field label="Location" value={intervention.location_type === "sur_site" ? "Sur Site" : "Atelier"} />
                  <Field label="Contact Person" value={intervention.contact_person} />
                </Stack>
                {intervention.contract_id && <Field label="Contract" value={contractName ?? `#${intervention.contract_id}`} />}
                {intervention.project_id && <Field label="Project" value={projectName ?? `#${intervention.project_id}`} />}
                {intervention.warranty_reference_id && (
                  <Field
                    label="Warranty Reference"
                    value={intervention.warranty_reference_bi_number ?? `#${intervention.warranty_reference_id}`}
                  />
                )}

                <Divider />
                <Stack direction="row" spacing={3}>
                  <Field label="Date" value={dayjs(intervention.intervention_date).format("MMM D, YYYY")} />
                  <Field label="Start" value={intervention.start_time.slice(0, 5)} />
                  <Field label="End" value={intervention.end_time.slice(0, 5)} />
                </Stack>
                <Stack direction="row" spacing={3}>
                  <Field label="Gross Duration" value={formatDuration(intervention.net_duration_minutes + intervention.lunch_break_minutes)} />
                  <Field label="Lunch Break" value={formatDuration(intervention.lunch_break_minutes)} />
                  <Field label="Net Duration" value={formatDuration(intervention.net_duration_minutes)} />
                  <Field label="Points Earned" value={intervention.points_earned} />
                </Stack>

                <Divider />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Team
                  </Typography>
                  <Stack direction="row" spacing={3} sx={{ mt: 0.5, mb: intervention.colleague_technicians.length ? 1 : 0 }}>
                    <Field label="Lead Technician" value={leadTechnicianName} />
                    <Field label="Number of Technicians" value={intervention.number_of_technicians} />
                  </Stack>
                  {intervention.colleague_technicians.length > 0 && (
                    <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", gap: 0.5 }}>
                      {intervention.colleague_technicians.map((colleague) => (
                        <Chip
                          key={colleague.id}
                          size="small"
                          label={technicianNameById.get(colleague.user_id) ?? `#${colleague.user_id}`}
                        />
                      ))}
                    </Stack>
                  )}
                </Box>

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
                        return (
                          <Chip
                            key={task.id}
                            size="small"
                            label={travail ? `${travail.travail_code} — ${travail.travail_name}` : `#${task.travail_id}`}
                          />
                        );
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

                <Divider />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Attachments
                  </Typography>
                  <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                    {attachments.length === 0 ? (
                      <Typography variant="body2" color="text.secondary">
                        No attachments.
                      </Typography>
                    ) : (
                      attachments.map((attachment) => (
                        <Typography key={attachment.id} variant="body2" color={attachment.id === activeAttachment?.id ? "text.primary" : "text.secondary"}>
                          {attachment.file_name} — {dayjs(attachment.upload_date).format("MMM D, YYYY HH:mm")}
                        </Typography>
                      ))
                    )}
                  </Stack>
                </Box>

                <Divider />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Approval History
                  </Typography>
                  {intervention.approval_history.length === 0 ? (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                      No approval decisions recorded yet.
                    </Typography>
                  ) : (
                    <Stack spacing={1} sx={{ mt: 0.5 }}>
                      {intervention.approval_history.map((entry) => (
                        <Box key={entry.id}>
                          <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
                            <Chip
                              size="small"
                              label={entry.decision}
                              color={entry.decision === "approved" ? "success" : "error"}
                            />
                            <Typography variant="body2">
                              {entry.approval_level} —{" "}
                              {entry.approver_name ?? (entry.approved_by != null ? `User #${entry.approved_by}` : "Unknown user")}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {dayjs(entry.approval_date).format("MMM D, YYYY HH:mm")}
                            </Typography>
                          </Stack>
                          {entry.comment && (
                            <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                              {entry.comment}
                            </Typography>
                          )}
                        </Box>
                      ))}
                    </Stack>
                  )}
                </Box>
              </Stack>
            </Box>

            {!readOnly && (
              <Box sx={{ p: 2, borderTop: "1px solid", borderColor: "divider" }}>
                {errorMessage && (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    {errorMessage}
                  </Alert>
                )}
                {rejecting ? (
                  <Stack spacing={1.5}>
                    <TextField
                      label="Rejection Reason"
                      fullWidth
                      multiline
                      minRows={2}
                      required
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      autoFocus
                    />
                    <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end" }}>
                      <Button onClick={() => setRejecting(false)} disabled={deciding}>
                        Back
                      </Button>
                      <Button color="error" variant="contained" disabled={!comment.trim() || deciding} onClick={handleReject}>
                        Confirm Rejection
                      </Button>
                    </Stack>
                  </Stack>
                ) : (
                  <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end" }}>
                    <Button color="error" variant="outlined" disabled={deciding} onClick={() => setRejecting(true)}>
                      Reject
                    </Button>
                    <Button color="success" variant="contained" disabled={deciding} onClick={handleApprove}>
                      Approve
                    </Button>
                  </Stack>
                )}
              </Box>
            )}
          </Grid>

          {/* Right panel — zoomable/pannable image, synchronized with the left panel's data */}
          <Grid
            size={{ xs: 12, md: 7 }}
            sx={{ display: "flex", flexDirection: "column", minHeight: 0, bgcolor: "#1c1c1c" }}
          >
            <Box sx={{ position: "relative", flex: 1, minHeight: 0, overflow: "hidden" }}>
              {attachments.length === 0 ? (
                <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%" }}>
                  <Typography color="grey.400">No attachments.</Typography>
                </Box>
              ) : (
                <>
                  {activeAttachment && <AttachmentImage attachment={activeAttachment} />}
                  {attachments.length > 1 && (
                    <>
                      <IconButton
                        onClick={() => setActiveIndex((i) => (i - 1 + attachments.length) % attachments.length)}
                        aria-label="Previous attachment"
                        sx={{ position: "absolute", left: 8, top: "50%", transform: "translateY(-50%)", bgcolor: "rgba(0,0,0,0.5)", color: "#fff" }}
                      >
                        <ChevronLeftIcon />
                      </IconButton>
                      <IconButton
                        onClick={() => setActiveIndex((i) => (i + 1) % attachments.length)}
                        aria-label="Next attachment"
                        sx={{ position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)", bgcolor: "rgba(0,0,0,0.5)", color: "#fff" }}
                      >
                        <ChevronRightIcon />
                      </IconButton>
                    </>
                  )}
                </>
              )}
            </Box>

            {attachments.length > 1 && (
              <Stack direction="row" spacing={1} sx={{ p: 1.5, overflowX: "auto", bgcolor: "#111" }}>
                {attachments.map((attachment, index) => (
                  <ThumbnailTile
                    key={attachment.id}
                    attachment={attachment}
                    active={index === activeIndex}
                    onClick={() => setActiveIndex(index)}
                  />
                ))}
              </Stack>
            )}
          </Grid>
        </Grid>
      )}
    </Dialog>
  );
}

function ThumbnailTile({ attachment, active, onClick }: { attachment: Attachment; active: boolean; onClick: () => void }) {
  const previewUrl = useAuthenticatedPreview(attachment.id);
  const isPdf = attachment.content_type === "application/pdf";

  return (
    <Box
      onClick={onClick}
      sx={{
        width: 64,
        height: 64,
        flexShrink: 0,
        borderRadius: 1,
        overflow: "hidden",
        cursor: "pointer",
        border: "2px solid",
        borderColor: active ? "primary.main" : "transparent",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "#222",
      }}
    >
      {isPdf ? (
        <PictureAsPdfIcon sx={{ color: "grey.400" }} />
      ) : previewUrl ? (
        <Box component="img" src={previewUrl} alt={attachment.file_name} sx={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : (
        <CircularProgress size={16} sx={{ color: "grey.500" }} />
      )}
    </Box>
  );
}
