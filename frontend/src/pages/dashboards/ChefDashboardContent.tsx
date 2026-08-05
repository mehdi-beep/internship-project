import { useQuery } from "@tanstack/react-query";
import {
  Chip,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import StatTile from "../../components/StatTile";
import ChartCard from "../../components/ChartCard";
import SimpleBarChart from "../../components/SimpleBarChart";
import QueryStateGate from "../../components/QueryStateGate";
import { getSupervisorDashboard } from "../../services/dashboardService";
import { priorityColors } from "../../styles/theme";
import type { ChefDashboard } from "../../types/dashboard";

export default function ChefDashboardContent() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dashboard", "supervisor"],
    queryFn: getSupervisorDashboard,
  });

  return (
    <QueryStateGate isLoading={isLoading} isError={isError} error={error} onRetry={refetch}>
      {data && <ChefDashboardBody data={data} />}
    </QueryStateGate>
  );
}

function ChefDashboardBody({ data }: { data: ChefDashboard }) {
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
          <StatTile label="Pending Technical" value={data.pending_technical_approvals} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Urgent" value={data.urgent_interventions} accent={data.urgent_interventions > 0 ? "#d03b3b" : undefined} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Active Technicians" value={data.active_technicians} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Avg Completion" value={`${(data.average_completion_time_minutes / 60).toFixed(1)}h`} />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <ChartCard title="Interventions by Technician">
            <SimpleBarChart data={data.interventions_by_technician_chart} colorIndex={0} />
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <ChartCard title="Interventions by Client">
            <SimpleBarChart data={data.interventions_by_client_chart} colorIndex={2} />
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <ChartCard title="Daily Activity (This Week)">
            <SimpleBarChart data={data.daily_activity_chart} colorIndex={1} />
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <ChartCard title="Weekly Activity (Last 4 Weeks)">
            <SimpleBarChart data={data.weekly_activity_chart} colorIndex={3} />
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
                    <ListItemText primary={`${p.planned_start_time.slice(0, 5)} — ${p.client_name}`} secondary={p.site_name} />
                    {p.priority === "urgent" && <Chip size="small" label="Urgent" sx={{ bgcolor: priorityColors.urgent, color: "#fff" }} />}
                  </ListItem>
                ))}
              </List>
            )}
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <ChartCard title="Technician Workload (This Week)" height={260}>
            <SimpleBarChart data={data.technician_workload} colorIndex={4} emptyLabel="No planning assigned this week." />
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <ChartCard title="Urgent Queue" height={260}>
            {data.urgent_queue.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No urgent interventions.
              </Typography>
            ) : (
              <List dense sx={{ overflow: "auto", maxHeight: 260 }}>
                {data.urgent_queue.map((p) => (
                  <ListItem key={p.id} divider>
                    <ListItemText primary={`${p.planned_start_time.slice(0, 5)} — ${p.client_name}`} secondary={p.site_name} />
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
