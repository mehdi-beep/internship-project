import { Box, Button, Typography } from "@mui/material";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { dashboardPathForRole } from "../utils/roleRoutes";

export default function ForbiddenPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  // A hardcoded "/dashboard" here would dead-end the display role (whose
  // dashboard is the full-screen calendar, not DashboardPage.tsx) — routed
  // the same role-aware way as post-login and the root-path redirect.
  const homePath = user ? dashboardPathForRole(user.role) : "/login";

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: 2,
        px: 2,
        textAlign: "center",
      }}
    >
      <LockOutlinedIcon sx={{ fontSize: 48, color: "text.secondary" }} />
      <Typography variant="h5" sx={{ fontWeight: 600 }}>
        Access Denied
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 360 }}>
        Your role does not have permission to view this page.
      </Typography>
      <Button variant="contained" onClick={() => navigate(homePath, { replace: true })}>
        Back to Dashboard
      </Button>
    </Box>
  );
}
