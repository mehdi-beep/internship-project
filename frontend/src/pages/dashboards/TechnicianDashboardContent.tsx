import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import {
  Box,
  Button,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import StatTile from "../../components/StatTile";
import ChartCard from "../../components/ChartCard";
import SimpleBarChart from "../../components/SimpleBarChart";
import SimpleLineChart from "../../components/SimpleLineChart";
import QueryStateGate from "../../components/QueryStateGate";
import PeriodModeSelector, { type PeriodMode } from "../../components/PeriodModeSelector";
import { getTechnicianDashboard, getTechnicianDashboardCharts } from "../../services/dashboardService";
import { priorityColors } from "../../styles/theme";
import type { ActionableInterventionSummary, PlanningSummary, TechnicianDashboard } from "../../types/dashboard";

export default function TechnicianDashboardContent() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dashboard", "technician"],
    queryFn: getTechnicianDashboard,
  });

  return (
    <QueryStateGate isLoading={isLoading} isError={isError} error={error} onRetry={refetch}>
      {data && <TechnicianDashboardBody data={data} />}
    </QueryStateGate>
  );
}

function TechnicianDashboardBody({ data }: { data: TechnicianDashboard }) {
  const navigate = useNavigate();
  const [mode, setMode] = useState<PeriodMode>("monthly");
  const [anchor, setAnchor] = useState(() => dayjs().startOf("month").format("YYYY-MM-DD"));

  const { data: charts } = useQuery({
    queryKey: ["dashboard", "technician", "charts", mode, anchor],
    queryFn: () => getTechnicianDashboardCharts(mode, anchor),
  });

  // Clicking a planned/urgent assignment opens a pre-filled New Intervention
  // form — Planning entries never link to a real Intervention row in this
  // app (confirmed: nothing ever sets Planning.intervention_id), so there is
  // no existing intervention to open yet. Carrying over what the Chef/Admin
  // already specified means the technician never has to re-select it.
  const openAssignment = (p: PlanningSummary) => {
    const params = new URLSearchParams({
      client_id: String(p.client_id),
      site_id: String(p.site_id),
      intervention_date: p.planned_date,
    });
    navigate(`/interventions/new?${params.toString()}`);
  };

  const openForEdit = (i: ActionableInterventionSummary) => navigate(`/interventions/${i.id}/edit`);

  return (
    <Stack spacing={3}>
      <Grid container spacing={2}>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Planned Today" value={data.planned_today} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Completed Today" value={data.completed_today} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Pending Approval" value={data.pending_approval} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Rejected" value={data.rejected} accent={data.rejected > 0 ? "#d03b3b" : undefined} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Monthly Points" value={data.monthly_points} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Avg Daily Duration" value={`${(data.average_daily_duration_minutes / 60).toFixed(1)}h`} />
        </Grid>
      </Grid>

      <Stack direction="row" spacing={1}>
        <Button variant="contained" onClick={() => navigate("/interventions/new")}>
          New Intervention
        </Button>
        <Button variant="outlined" onClick={() => navigate("/interventions")}>
          My Interventions
        </Button>
      </Stack>

      <PeriodModeSelector mode={mode} anchor={anchor} onModeChange={setMode} onAnchorChange={setAnchor} />

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <ChartCard title="Completed Interventions">
            <SimpleBarChart data={charts?.completed_chart ?? []} colorIndex={0} />
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <ChartCard title="Points Earned">
            <SimpleLineChart data={charts?.points_chart ?? []} colorIndex={3} />
          </ChartCard>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 4 }}>
          <ChartCard title="Today's Planning / Assigned Interventions" height={320}>
            {data.today_planning.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No assignments right now.
              </Typography>
            ) : (
              <List dense sx={{ overflow: "auto", maxHeight: 320 }}>
                {data.today_planning.map((p) => (
                  <ListItem key={p.id} divider disablePadding>
                    <ListItemButton onClick={() => openAssignment(p)} sx={{ alignItems: "flex-start" }}>
                      <ListItemText
                        primary={
                          <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                              {p.client_name}
                            </Typography>
                            {p.priority === "urgent" && (
                              <Chip size="small" label="Urgent" sx={{ bgcolor: priorityColors.urgent, color: "#fff" }} />
                            )}
                          </Stack>
                        }
                        secondary={
                          <>
                            {p.site_name}
                            <br />
                            {dayjs(p.planned_date).format("MMM D, YYYY")} — {p.planned_start_time.slice(0, 5)}
                            {"  ·  "}
                            <Typography component="span" variant="caption" sx={{ textTransform: "capitalize" }}>
                              {p.status.replace("_", " ")}
                            </Typography>
                          </>
                        }
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            )}
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <ChartCard title="Draft &amp; Pending Actions" height={320}>
            <Stack spacing={1.5} sx={{ height: "100%", overflow: "auto" }}>
              <Box>
                <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>
                  DRAFT ({data.draft_interventions.length})
                </Typography>
                {data.draft_interventions.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 1 }}>
                    No drafts.
                  </Typography>
                ) : (
                  <List dense disablePadding>
                    {data.draft_interventions.map((i) => (
                      <ListItem key={i.id} divider disablePadding>
                        <ListItemButton onClick={() => openForEdit(i)}>
                          <ListItemText primary={i.bi_number} secondary={i.client_name} />
                        </ListItemButton>
                      </ListItem>
                    ))}
                  </List>
                )}
              </Box>

              <Box>
                <Typography
                  variant="caption"
                  sx={{ fontWeight: 700 }}
                  color={data.rejected_interventions.length > 0 ? "error" : "text.secondary"}
                >
                  REJECTED — ACTION REQUIRED ({data.rejected_interventions.length})
                </Typography>
                {data.rejected_interventions.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ py: 1 }}>
                    No rejected interventions.
                  </Typography>
                ) : (
                  <List dense disablePadding>
                    {data.rejected_interventions.map((i) => (
                      <ListItem key={i.id} divider disablePadding>
                        <ListItemButton
                          onClick={() => openForEdit(i)}
                          sx={{ borderLeft: "3px solid", borderColor: "error.main" }}
                        >
                          <ListItemText
                            primary={
                              <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                  {i.bi_number}
                                </Typography>
                                <Chip size="small" color="error" label="Needs correction" />
                              </Stack>
                            }
                            secondary={
                              <>
                                {i.client_name}
                                <br />
                                {i.rejection_reason ?? "No reason provided."}
                              </>
                            }
                          />
                        </ListItemButton>
                      </ListItem>
                    ))}
                  </List>
                )}
              </Box>
            </Stack>
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <ChartCard title="Recently Completed" height={320}>
            {data.recently_completed.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No completed interventions yet.
              </Typography>
            ) : (
              <List dense sx={{ overflow: "auto", maxHeight: 320 }}>
                {data.recently_completed.map((i) => (
                  <ListItem key={i.id} divider disablePadding>
                    <ListItemButton onClick={() => navigate(`/interventions/${i.id}`)}>
                      <ListItemText primary={i.bi_number} secondary={i.client_name} />
                    </ListItemButton>
                  </ListItem>
                ))}
              </List>
            )}
          </ChartCard>
        </Grid>
      </Grid>
    </Stack>
  );
}
