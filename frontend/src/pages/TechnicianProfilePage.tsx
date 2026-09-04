import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Box, Button, Chip, Grid, List, ListItem, ListItemText, Stack, Typography } from "@mui/material";
import dayjs from "dayjs";
import ChartCard from "../components/ChartCard";
import SimpleBarChart from "../components/SimpleBarChart";
import ProfileHeader from "../components/ProfileHeader";
import ProfileStatGrid from "../components/ProfileStatGrid";
import StatusBadge from "../components/StatusBadge";
import QueryStateGate from "../components/QueryStateGate";
import { getTechnicianPerformance } from "../services/technicianPerformanceService";
import { listInterventions } from "../services/interventionService";
import { listPlanning } from "../services/planningService";
import { listChefOptions } from "../services/userService";

export default function TechnicianProfilePage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const technicianId = Number(id);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["technician-performance", technicianId],
    queryFn: () => getTechnicianPerformance(technicianId),
    enabled: Number.isFinite(technicianId),
  });

  const { data: recentInterventions } = useQuery({
    queryKey: ["interventions", "by-technician", technicianId],
    queryFn: () => listInterventions({ technician_id: technicianId, page_size: 5 }),
    enabled: Number.isFinite(technicianId) && data?.role === "technician",
  });

  const { data: planningSummary } = useQuery({
    queryKey: ["planning", "by-technician", technicianId],
    queryFn: () => listPlanning({ technician_id: technicianId, page_size: 5 }),
    enabled: Number.isFinite(technicianId) && data?.role === "technician",
  });

  const { data: chefOptions } = useQuery({
    queryKey: ["users", "chef-options"],
    queryFn: listChefOptions,
    enabled: data?.role === "technician",
  });

  const isApprover = data?.role === "chef_technicien" || data?.role === "admin_supervisor";

  return (
    <Box>
      <Button onClick={() => navigate(-1)} sx={{ mb: 2 }}>
        ← Back
      </Button>

      <QueryStateGate isLoading={isLoading} isError={isError} error={error} onRetry={refetch}>
        {data && (
          <Stack spacing={3}>
            <ProfileHeader
              firstName={data.first_name}
              lastName={data.last_name}
              role={data.role}
              email={data.email}
              phone={data.phone}
              active={isApprover ? undefined : data.active}
              supervisingRole={
                !isApprover && (
                  <>
                    Supervised by Chef des Techniciens
                    {chefOptions && chefOptions.length > 0
                      ? ` (${chefOptions.map((c) => `${c.first_name} ${c.last_name}`).join(", ")})`
                      : ""}
                  </>
                )
              }
            />

            {isApprover ? (
              <ProfileStatGrid
                stats={[
                  { label: "Approvals Processed", value: data.approvals_processed ?? 0 },
                  { label: "Approvals Rejected", value: data.approvals_rejected ?? 0 },
                  {
                    label: "Avg Turnaround",
                    value: data.avg_turnaround_minutes !== null ? `${Math.round(data.avg_turnaround_minutes)} min` : "N/A",
                  },
                ]}
              />
            ) : (
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
            )}

            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <ChartCard title={isApprover ? "Monthly Approval Activity" : "Monthly Activity"}>
                  <SimpleBarChart data={data.monthly_activity_chart} colorIndex={0} />
                </ChartCard>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <ChartCard title={isApprover ? "Weekly Approval Activity" : "Weekly Activity"}>
                  <SimpleBarChart data={data.weekly_activity_chart} colorIndex={1} />
                </ChartCard>
              </Grid>
            </Grid>

            {!isApprover && (
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
                            <ListItemText
                              primary={i.bi_number}
                              secondary={dayjs(i.intervention_date).format("MMM D, YYYY")}
                            />
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
            )}
          </Stack>
        )}
      </QueryStateGate>
    </Box>
  );
}
