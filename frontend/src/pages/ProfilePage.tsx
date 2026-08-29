import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Alert,
  Box,
  Button,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import dayjs from "dayjs";
import { useNavigate } from "react-router-dom";
import ChartCard from "../components/ChartCard";
import SimpleBarChart from "../components/SimpleBarChart";
import Modal from "../components/Modal";
import ProfileHeader from "../components/ProfileHeader";
import ProfileStatGrid from "../components/ProfileStatGrid";
import StatusBadge from "../components/StatusBadge";
import QueryStateGate from "../components/QueryStateGate";
import { useAuth } from "../context/AuthContext";
import { getMyTechnicianPerformance } from "../services/technicianPerformanceService";
import { listInterventions } from "../services/interventionService";
import { listPlanning } from "../services/planningService";
import { listChefOptions } from "../services/userService";
import { listMyRecentDecisions } from "../services/approvalService";
import { checkPasswordResetAvailable, confirmPasswordReset, requestPasswordReset } from "../services/authService";

function extractErrorDetail(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
  return detail ?? fallback;
}

/** Task 8 — the two-step self-service reset flow, shared by every role's
 * profile body via ProfileHeader's onResetPasswordClick. Centralized here
 * (rather than duplicated per profile body) since the flow itself has
 * nothing role-specific about it — it always acts on the caller's own
 * account, identically, regardless of who they are. */
function usePasswordResetDialog() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<"request" | "confirm">("request");
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const { data: available, isLoading: availabilityLoading } = useQuery({
    queryKey: ["auth", "password-reset-available"],
    queryFn: checkPasswordResetAvailable,
    enabled: open,
  });

  const requestMutation = useMutation({
    mutationFn: requestPasswordReset,
    onSuccess: () => {
      setStep("confirm");
      setErrorMessage(null);
    },
    onError: (err: unknown) => setErrorMessage(extractErrorDetail(err, "Could not send the reset code.")),
  });

  const confirmMutation = useMutation({
    mutationFn: () => confirmPasswordReset(code, newPassword),
    onSuccess: () => {
      setSuccessMessage("Your password has been reset.");
      setErrorMessage(null);
    },
    onError: (err: unknown) => setErrorMessage(extractErrorDetail(err, "Could not reset your password.")),
  });

  const reset = () => {
    setStep("request");
    setCode("");
    setNewPassword("");
    setErrorMessage(null);
    setSuccessMessage(null);
  };

  const openDialog = () => {
    reset();
    setOpen(true);
  };

  const close = () => setOpen(false);

  const dialog = (
    <Modal open={open} title="Reset Password" onClose={close}>
      <Stack spacing={2}>
        {errorMessage && <Alert severity="error">{errorMessage}</Alert>}
        {successMessage ? (
          <>
            <Alert severity="success">{successMessage}</Alert>
            <Stack direction="row" sx={{ justifyContent: "flex-end" }}>
              <Button variant="contained" onClick={close}>
                Done
              </Button>
            </Stack>
          </>
        ) : availabilityLoading ? (
          <Typography variant="body2" color="text.secondary">
            Checking availability…
          </Typography>
        ) : !available ? (
          <Alert severity="warning">
            Password reset by email isn't set up yet. Ask an Administrator to reset your password instead.
          </Alert>
        ) : step === "request" ? (
          <>
            <Typography variant="body2">
              We'll email a 6-digit code to your address on file. Enter it on the next screen along with your new
              password.
            </Typography>
            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end" }}>
              <Button onClick={close}>Cancel</Button>
              <Button variant="contained" onClick={() => requestMutation.mutate()} disabled={requestMutation.isPending}>
                Send Code
              </Button>
            </Stack>
          </>
        ) : (
          <>
            <Typography variant="body2" color="text.secondary">
              Enter the code we emailed you, and choose your new password.
            </Typography>
            <TextField
              label="6-digit code"
              fullWidth
              autoFocus
              value={code}
              onChange={(e) => setCode(e.target.value)}
              slotProps={{ htmlInput: { maxLength: 6, inputMode: "numeric" } }}
            />
            <TextField
              label="New Password"
              type="password"
              fullWidth
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              helperText="Minimum 8 characters."
            />
            <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between" }}>
              <Button onClick={() => requestMutation.mutate()} disabled={requestMutation.isPending}>
                Resend Code
              </Button>
              <Stack direction="row" spacing={1}>
                <Button onClick={close}>Cancel</Button>
                <Button
                  variant="contained"
                  onClick={() => confirmMutation.mutate()}
                  disabled={code.length !== 6 || newPassword.length < 8 || confirmMutation.isPending}
                >
                  Reset Password
                </Button>
              </Stack>
            </Stack>
          </>
        )}
      </Stack>
    </Modal>
  );

  return { dialog, openDialog };
}

export default function ProfilePage() {
  const { user } = useAuth();
  const { dialog, openDialog } = usePasswordResetDialog();

  if (!user) return null;

  return (
    <Box>
      <Typography variant="h5" sx={{ fontWeight: 600, mb: 2 }}>
        My Profile
      </Typography>
      {user.role === "technician" ? (
        <TechnicianProfileBody userId={user.id} onResetPasswordClick={openDialog} />
      ) : (
        <SupervisorProfileBody role={user.role} onResetPasswordClick={openDialog} />
      )}
      {dialog}
    </Box>
  );
}

function TechnicianProfileBody({ userId, onResetPasswordClick }: { userId: number; onResetPasswordClick: () => void }) {
  const navigate = useNavigate();

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["technician-performance", "me"],
    queryFn: getMyTechnicianPerformance,
  });

  const { data: recentInterventions } = useQuery({
    queryKey: ["interventions", "by-technician", userId],
    queryFn: () => listInterventions({ technician_id: userId, page_size: 5 }),
  });

  const { data: planningSummary } = useQuery({
    queryKey: ["planning", "by-technician", userId],
    queryFn: () => listPlanning({ technician_id: userId, page_size: 5 }),
  });

  const { data: chefOptions } = useQuery({
    queryKey: ["users", "chef-options"],
    queryFn: listChefOptions,
  });

  return (
    <QueryStateGate isLoading={isLoading} isError={isError} error={error} onRetry={refetch}>
      {data && (
        <Stack spacing={3}>
          <ProfileHeader
            firstName={data.first_name}
            lastName={data.last_name}
            role="technician"
            email={data.email}
            phone={data.phone}
            active={data.active}
            onResetPasswordClick={onResetPasswordClick}
            supervisingRole={
              <>
                Supervised by Chef des Techniciens
                {chefOptions && chefOptions.length > 0
                  ? ` (${chefOptions.map((c) => `${c.first_name} ${c.last_name}`).join(", ")})`
                  : ""}
              </>
            }
          />

          <ProfileStatGrid
            stats={[
              { label: "Total", value: data.total_interventions },
              { label: "Completed", value: data.completed_interventions },
              { label: "Pending", value: data.pending_interventions },
              { label: "Rejected", value: data.rejected_interventions },
              { label: "Warranty", value: data.warranty_interventions },
              { label: "Points", value: data.total_points },
              { label: "Avg Duration", value: `${data.average_duration_minutes} min` },
              { label: "Completed / Planned", value: `${data.completed_vs_planned_ratio}%` },
              { label: "Colleague Participations", value: data.colleague_participation_count },
            ]}
          />

          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <ChartCard title="Monthly Activity">
                <SimpleBarChart data={data.monthly_activity_chart} colorIndex={0} />
              </ChartCard>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <ChartCard title="Weekly Activity">
                <SimpleBarChart data={data.weekly_activity_chart} colorIndex={1} />
              </ChartCard>
            </Grid>
          </Grid>

          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <ChartCard title="Recent Interventions" height={260}>
                {(recentInterventions?.items.length ?? 0) === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No interventions yet.
                  </Typography>
                ) : (
                  <List dense sx={{ overflow: "auto", maxHeight: 260 }}>
                    {recentInterventions!.items.map((i) => (
                      <ListItem
                        key={i.id}
                        divider
                        sx={{ cursor: "pointer" }}
                        onClick={() => navigate(`/interventions/${i.id}`)}
                      >
                        <ListItemText primary={i.bi_number} secondary={dayjs(i.intervention_date).format("MMM D, YYYY")} />
                        <StatusBadge status={i.status} />
                      </ListItem>
                    ))}
                  </List>
                )}
              </ChartCard>
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <ChartCard title="Planning Summary" height={260}>
                {(planningSummary?.items.length ?? 0) === 0 ? (
                  <Typography variant="body2" color="text.secondary">
                    No planning available.
                  </Typography>
                ) : (
                  <List dense sx={{ overflow: "auto", maxHeight: 260 }}>
                    {planningSummary!.items.map((p) => (
                      <ListItem key={p.id} divider>
                        <ListItemText
                          primary={dayjs(p.planned_date).format("MMM D, YYYY")}
                          secondary={p.planned_start_time.slice(0, 5)}
                        />
                        {p.priority === "urgent" && <Chip size="small" color="error" label="Urgent" />}
                      </ListItem>
                    ))}
                  </List>
                )}
              </ChartCard>
            </Grid>
          </Grid>
        </Stack>
      )}
    </QueryStateGate>
  );
}

function SupervisorProfileBody({ role, onResetPasswordClick }: { role: string; onResetPasswordClick: () => void }) {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isChef = role === "chef_technicien";

  const { data: myPlanning, isLoading: planningLoading, isError: planningError } = useQuery({
    queryKey: ["planning", "created-by-me"],
    queryFn: () => listPlanning({ page_size: 10 }),
    enabled: isChef,
  });

  const { data: myDecisions, isLoading: decisionsLoading, isError: decisionsError } = useQuery({
    queryKey: ["approvals", "my-recent-decisions"],
    queryFn: listMyRecentDecisions,
    enabled: !isChef,
  });

  if (!user) return null;

  return (
    <Stack spacing={3}>
      <ProfileHeader
        firstName={user.first_name}
        lastName={user.last_name}
        role={role}
        email={user.email}
        onResetPasswordClick={onResetPasswordClick}
      />

      {isChef ? (
        <ChartCard title="Recent Planning Created" height={300}>
          {planningLoading ? (
            <Typography variant="body2" color="text.secondary">
              Loading…
            </Typography>
          ) : planningError ? (
            <Typography variant="body2" color="error">
              Failed to load recent activity.
            </Typography>
          ) : (myPlanning?.items.length ?? 0) === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No planning entries created yet.
            </Typography>
          ) : (
            <List dense sx={{ overflow: "auto", maxHeight: 260 }}>
              {myPlanning!.items.map((p) => (
                <ListItem key={p.id} divider sx={{ cursor: "pointer" }} onClick={() => navigate("/planning")}>
                  <ListItemText
                    primary={dayjs(p.planned_date).format("MMM D, YYYY")}
                    secondary={p.planned_start_time.slice(0, 5)}
                  />
                  {p.priority === "urgent" && <Chip size="small" color="error" label="Urgent" />}
                </ListItem>
              ))}
            </List>
          )}
        </ChartCard>
      ) : (
        <ChartCard title="Recent Approval Decisions" height={300}>
          {decisionsLoading ? (
            <Typography variant="body2" color="text.secondary">
              Loading…
            </Typography>
          ) : decisionsError ? (
            <Typography variant="body2" color="error">
              Failed to load recent activity.
            </Typography>
          ) : (myDecisions?.length ?? 0) === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No approval decisions made yet.
            </Typography>
          ) : (
            <List dense sx={{ overflow: "auto", maxHeight: 260 }}>
              {myDecisions!.map((d) => (
                <ListItem
                  key={`${d.intervention_id}-${d.approval_level}-${d.approval_date}`}
                  divider
                  sx={{ cursor: "pointer" }}
                  onClick={() => navigate(`/interventions/${d.intervention_id}`)}
                >
                  <ListItemText
                    primary={`${d.bi_number} — ${d.approval_level}`}
                    secondary={dayjs(d.approval_date).format("MMM D, YYYY HH:mm")}
                  />
                  <Chip size="small" color={d.decision === "approved" ? "success" : "error"} label={d.decision} />
                </ListItem>
              ))}
            </List>
          )}
        </ChartCard>
      )}
    </Stack>
  );
}
