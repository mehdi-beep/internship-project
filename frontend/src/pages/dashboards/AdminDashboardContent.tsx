import { useQuery } from "@tanstack/react-query";
import { Grid, Stack } from "@mui/material";
import StatTile from "../../components/StatTile";
import ChartCard from "../../components/ChartCard";
import SimpleBarChart from "../../components/SimpleBarChart";
import QueryStateGate from "../../components/QueryStateGate";
import { getAdminDashboard } from "../../services/dashboardService";
import { CHART_STATUS } from "../../styles/chartColors";
import type { AdminDashboard } from "../../types/dashboard";

export default function AdminDashboardContent() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dashboard", "admin"],
    queryFn: getAdminDashboard,
  });

  return (
    <QueryStateGate isLoading={isLoading} isError={isError} error={error} onRetry={refetch}>
      {data && <AdminDashboardBody data={data} />}
    </QueryStateGate>
  );
}

function AdminDashboardBody({ data }: { data: AdminDashboard }) {
  return (
    <Stack spacing={3}>
      <Grid container spacing={2}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Pending Admin Approvals" value={data.pending_administrative_approvals} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Approved This Month" value={data.approved_this_month} accent={CHART_STATUS.good} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Rejected This Month" value={data.rejected_this_month} accent={CHART_STATUS.critical} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Avg Approval Time" value={`${(data.average_approval_time_minutes / 60).toFixed(1)}h`} />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Approval Rate" value={`${data.approval_rate}%`} accent={CHART_STATUS.good} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Rejection Rate" value={`${data.rejection_rate}%`} accent={CHART_STATUS.critical} />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <ChartCard title="Monthly Interventions">
            <SimpleBarChart data={data.monthly_interventions_chart} colorIndex={0} />
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <ChartCard title="Points Distribution">
            <SimpleBarChart data={data.points_distribution_chart} colorIndex={3} />
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <ChartCard title="Client Activity">
            <SimpleBarChart data={data.client_activity_chart} colorIndex={2} />
          </ChartCard>
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <ChartCard title="City Activity">
            <SimpleBarChart data={data.city_activity_chart} colorIndex={6} />
          </ChartCard>
        </Grid>
      </Grid>
    </Stack>
  );
}
