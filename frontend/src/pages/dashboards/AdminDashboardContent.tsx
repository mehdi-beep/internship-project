import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import { Grid, Stack } from "@mui/material";
import StatTile from "../../components/StatTile";
import SwitchableChartCard from "../../components/SwitchableChartCard";
import QueryStateGate from "../../components/QueryStateGate";
import PeriodModeSelector, { type PeriodMode } from "../../components/PeriodModeSelector";
import { getAdminDashboard, getAdminDashboardCharts } from "../../services/dashboardService";
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
  const [mode, setMode] = useState<PeriodMode>("monthly");
  const [anchor, setAnchor] = useState(() => dayjs().startOf("month").format("YYYY-MM-DD"));

  const { data: charts } = useQuery({
    queryKey: ["dashboard", "admin", "charts", mode, anchor],
    queryFn: () => getAdminDashboardCharts(mode, anchor),
  });

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

      <PeriodModeSelector mode={mode} anchor={anchor} onModeChange={setMode} onAnchorChange={setAnchor} />

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <SwitchableChartCard title="Interventions" data={charts?.interventions_chart ?? []} colorIndex={0} />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <SwitchableChartCard
            title="Points Distribution"
            data={charts?.points_distribution_chart ?? []}
            colorIndex={3}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <SwitchableChartCard title="Client Activity" data={charts?.client_activity_chart ?? []} colorIndex={2} />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <SwitchableChartCard title="City Activity" data={charts?.city_activity_chart ?? []} colorIndex={6} />
        </Grid>
      </Grid>
    </Stack>
  );
}
