import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import {
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
import type { TechnicianDashboard } from "../../types/dashboard";

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
          <ChartCard title="Today's Planning" height={260}>
            {data.today_planning.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No planning for today.
              </Typography>
            ) : (
              <List dense sx={{ overflow: "auto", maxHeight: 260 }}>
                {data.today_planning.map((p) => (
                  <ListItem key={p.id} divider>
                    <ListItemText
                      primary={`${p.planned_start_time.slice(0, 5)} — ${p.client_name}`}
                      secondary={p.site_name}
                    />
                    {p.priority === "urgent" && <Chip size="small" label="Urgent" sx={{ bgcolor: priorityColors.urgent, color: "#fff" }} />}
                  </ListItem>
                ))}
              </List>
            )}
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <ChartCard title="Draft / Pending Actions" height={260}>
            <Stack spacing={2}>
              <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                <Typography variant="body2">Draft</Typography>
                <Typography variant="body2" sx={{ fontWeight: 700 }}>
                  {data.draft_count}
                </Typography>
              </Stack>
              <Stack direction="row" sx={{ justifyContent: "space-between" }}>
                <Typography variant="body2">Rejected</Typography>
                <Typography
                  variant="body2"
                  sx={{ fontWeight: 700 }}
                  color={data.rejected > 0 ? "error" : undefined}
                >
                  {data.rejected}
                </Typography>
              </Stack>
            </Stack>
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <ChartCard title="Recently Completed" height={260}>
            {data.recently_completed.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No completed interventions yet.
              </Typography>
            ) : (
              <List dense sx={{ overflow: "auto", maxHeight: 260 }}>
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
