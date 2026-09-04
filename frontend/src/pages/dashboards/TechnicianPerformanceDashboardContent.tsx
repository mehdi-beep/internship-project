import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Grid, Typography } from "@mui/material";
import QueryStateGate from "../../components/QueryStateGate";
import TechnicianCard from "../../components/TechnicianCard";
import { listTechnicianPerformance } from "../../services/technicianPerformanceService";

export default function TechnicianPerformanceDashboardContent() {
  const navigate = useNavigate();
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["technician-performance"],
    queryFn: listTechnicianPerformance,
  });

  return (
    <QueryStateGate isLoading={isLoading} isError={isError} error={error} onRetry={refetch}>
      {(data?.length ?? 0) === 0 ? (
        <Typography variant="body2" color="text.secondary">
          No employees found.
        </Typography>
      ) : (
        <Grid container spacing={2}>
          {data!.map((technician) => (
            <Grid key={technician.technician_id} size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
              <TechnicianCard technician={technician} onClick={() => navigate(`/technicians/${technician.technician_id}`)} />
            </Grid>
          ))}
        </Grid>
      )}
    </QueryStateGate>
  );
}
