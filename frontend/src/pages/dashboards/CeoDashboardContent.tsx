import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import dayjs from "dayjs";
import { Grid, Stack } from "@mui/material";
import StatTile from "../../components/StatTile";
import SwitchableChartCard from "../../components/SwitchableChartCard";
import QueryStateGate from "../../components/QueryStateGate";
import PeriodModeSelector, { type PeriodMode } from "../../components/PeriodModeSelector";
import { getCeoDashboard, getCeoDashboardCharts } from "../../services/dashboardService";
import { CHART_STATUS } from "../../styles/chartColors";
import type { CeoDashboard } from "../../types/dashboard";

export default function CeoDashboardContent() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dashboard", "ceo"],
    queryFn: getCeoDashboard,
  });

  return (
    <QueryStateGate isLoading={isLoading} isError={isError} error={error} onRetry={refetch}>
      {data && <CeoDashboardBody data={data} />}
    </QueryStateGate>
  );
}

function CeoDashboardBody({ data }: { data: CeoDashboard }) {
  const [mode, setMode] = useState<PeriodMode>("monthly");
  const [anchor, setAnchor] = useState(() => dayjs().startOf("month").format("YYYY-MM-DD"));

  const { data: charts } = useQuery({
    queryKey: ["dashboard", "ceo", "charts", mode, anchor],
    queryFn: () => getCeoDashboardCharts(mode, anchor),
  });

  return (
    <Stack spacing={3}>
      {/* Company-wide funnel — all-time, not "this month" like Admin's operational view. */}
      <Grid container spacing={2}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Total Interventions" value={data.total_interventions} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Completed" value={data.completed_interventions} accent={CHART_STATUS.good} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Pending Approval" value={data.pending_interventions} accent={CHART_STATUS.warning} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Rejected" value={data.rejected_interventions} accent={CHART_STATUS.critical} />
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Approval Rate" value={`${data.approval_rate}%`} accent={CHART_STATUS.good} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Rejection Rate" value={`${data.rejection_rate}%`} accent={CHART_STATUS.critical} />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile
            label="Avg Intervention Duration"
            value={`${(data.average_intervention_duration_minutes / 60).toFixed(1)}h`}
          />
        </Grid>
        <Grid size={{ xs: 6, sm: 3 }}>
          <StatTile label="Urgent in Planning" value={data.urgent_planning_count} accent={CHART_STATUS.serious} />
        </Grid>
      </Grid>

      {/* Organization scale — headcount/roster-style metrics a CEO tracks that
          Admin's day-to-day approval-queue dashboard has no reason to show. */}
      <Grid container spacing={2}>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Clients" value={`${data.active_clients} / ${data.total_clients}`} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Technicians" value={`${data.active_technicians} / ${data.total_technicians}`} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Active Contracts" value={data.active_contracts} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile
            label="Contracts Expiring (60d)"
            value={data.contracts_expiring_soon}
            accent={data.contracts_expiring_soon > 0 ? CHART_STATUS.warning : undefined}
          />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Active Projects" value={data.active_projects} />
        </Grid>
        <Grid size={{ xs: 6, sm: 4, md: 2 }}>
          <StatTile label="Upcoming Planned Work" value={data.upcoming_planned_interventions} />
        </Grid>
      </Grid>

      {/* All 7 charts below are mode-aware (Day/Week/Month/Year), scoped to
          exactly the selected period via /ceo/charts — unlike the scalar KPI
          tiles above, which stay wired to the all-time /ceo endpoint. */}
      <PeriodModeSelector mode={mode} anchor={anchor} onModeChange={setMode} onAnchorChange={setAnchor} />

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <SwitchableChartCard
            title="Intervention Volume"
            data={charts?.interventions_chart ?? []}
            colorIndex={0}
            defaultType="line"
          />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <SwitchableChartCard
            title="Completion Trend"
            data={charts?.completion_chart ?? []}
            colorIndex={2}
            defaultType="line"
          />
        </Grid>
      </Grid>

      {/* Cross-cutting roll-ups — whole-team workload, contract/project-level
          activity, and priority mix, none of which Admin's dashboard shows. */}
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}>
          <SwitchableChartCard
            title="Technician Workload (All)"
            data={charts?.technician_workload_chart ?? []}
            colorIndex={4}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <SwitchableChartCard title="Top Clients" data={charts?.top_clients_chart ?? []} colorIndex={2} />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <SwitchableChartCard title="Contract Activity" data={charts?.contract_activity_chart ?? []} colorIndex={6} />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <SwitchableChartCard title="Project Activity" data={charts?.project_activity_chart ?? []} colorIndex={5} />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <SwitchableChartCard
            title="Planning Priority Mix"
            data={charts?.priority_distribution_chart ?? []}
            colorIndex={3}
          />
        </Grid>
      </Grid>
    </Stack>
  );
}
