import { useState } from "react";
import { Stack, ToggleButton, ToggleButtonGroup, Typography } from "@mui/material";
import { useAuth } from "../context/AuthContext";
import TechnicianDashboardContent from "./dashboards/TechnicianDashboardContent";
import ChefDashboardContent from "./dashboards/ChefDashboardContent";
import AdminDashboardContent from "./dashboards/AdminDashboardContent";
import CeoDashboardContent from "./dashboards/CeoDashboardContent";
import TechnicianPerformanceDashboardContent from "./dashboards/TechnicianPerformanceDashboardContent";

type DashboardMode = "global" | "technician-performance";

export default function DashboardPage() {
  const { user } = useAuth();
  const [mode, setMode] = useState<DashboardMode>("global");
  const canToggle = user?.role === "chef_technicien" || user?.role === "admin_supervisor" || user?.role === "ceo";

  return (
    <>
      <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 600 }}>
          Welcome, {user?.first_name}
        </Typography>
        {canToggle && (
          <ToggleButtonGroup
            size="small"
            exclusive
            value={mode}
            onChange={(_, next: DashboardMode | null) => next && setMode(next)}
          >
            <ToggleButton value="global">Global Dashboard</ToggleButton>
            <ToggleButton value="technician-performance">Employees Performance</ToggleButton>
          </ToggleButtonGroup>
        )}
      </Stack>
      {user?.role === "technician" && <TechnicianDashboardContent />}
      {user?.role === "chef_technicien" && (mode === "global" ? <ChefDashboardContent /> : <TechnicianPerformanceDashboardContent />)}
      {user?.role === "admin_supervisor" && (mode === "global" ? <AdminDashboardContent /> : <TechnicianPerformanceDashboardContent />)}
      {user?.role === "ceo" && (mode === "global" ? <CeoDashboardContent /> : <TechnicianPerformanceDashboardContent />)}
    </>
  );
}
