import { Typography } from "@mui/material";
import { useAuth } from "../context/AuthContext";
import TechnicianDashboardContent from "./dashboards/TechnicianDashboardContent";
import ChefDashboardContent from "./dashboards/ChefDashboardContent";
import AdminDashboardContent from "./dashboards/AdminDashboardContent";

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <>
      <Typography variant="h5" sx={{ fontWeight: 600 }} gutterBottom>
        Welcome, {user?.first_name}
      </Typography>
      {user?.role === "technician" && <TechnicianDashboardContent />}
      {user?.role === "chef_technicien" && <ChefDashboardContent />}
      {user?.role === "admin_supervisor" && <AdminDashboardContent />}
    </>
  );
}
