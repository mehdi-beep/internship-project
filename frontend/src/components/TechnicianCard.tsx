import { Card, CardContent, Stack, Typography } from "@mui/material";
import dayjs from "dayjs";
import type { TechnicianPerformanceSummary } from "../types/technicianPerformance";

interface TechnicianCardProps {
  technician: TechnicianPerformanceSummary;
  onClick: () => void;
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <Stack direction="row" sx={{ justifyContent: "space-between" }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 600 }}>
        {value}
      </Typography>
    </Stack>
  );
}

export default function TechnicianCard({ technician, onClick }: TechnicianCardProps) {
  const isApprover = technician.role === "chef_technicien" || technician.role === "admin_supervisor";

  return (
    <Card variant="outlined" sx={{ cursor: "pointer", height: "100%" }} onClick={onClick}>
      <CardContent>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1.5 }}>
          {technician.full_name}
        </Typography>
        <Stack spacing={0.75}>
          {isApprover ? (
            <>
              <Stat label="Approvals Processed" value={technician.approvals_processed ?? 0} />
              <Stat label="Approvals Rejected" value={technician.approvals_rejected ?? 0} />
              <Stat
                label="Avg Turnaround"
                value={
                  technician.avg_turnaround_minutes !== null
                    ? `${Math.round(technician.avg_turnaround_minutes)} min`
                    : "N/A"
                }
              />
            </>
          ) : (
            <>
              <Stat label="Points" value={technician.total_points} />
              <Stat label="Total Interventions" value={technician.total_interventions} />
              <Stat label="Approved" value={technician.completed_interventions} />
              <Stat label="Current Workload" value={technician.pending_interventions} />
              <Stat
                label="Next Planned"
                value={
                  technician.next_planned_date
                    ? `${dayjs(technician.next_planned_date).format("MMM D")} — ${technician.next_planned_client_name}`
                    : "None scheduled"
                }
              />
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
