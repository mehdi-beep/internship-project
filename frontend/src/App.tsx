import { ThemeProvider, CssBaseline } from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { theme } from "./styles/theme";
import { AuthProvider } from "./context/AuthContext";
import { NotificationPollingProvider } from "./context/NotificationPollingContext";
import NotificationToastQueue from "./components/NotificationToastQueue";
import ProtectedRoute from "./routes/ProtectedRoute";
import AppLayout from "./layouts/AppLayout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import ForbiddenPage from "./pages/ForbiddenPage";
import UsersPage from "./pages/admin/UsersPage";
import ClientsPage from "./pages/admin/ClientsPage";
import SitesPage from "./pages/admin/SitesPage";
import ContractsPage from "./pages/admin/ContractsPage";
import ProjectsPage from "./pages/admin/ProjectsPage";
import TravauxPage from "./pages/admin/TravauxPage";
import PointRulesPage from "./pages/admin/PointRulesPage";
import PlanningPage from "./pages/PlanningPage";
import NotificationsPage from "./pages/NotificationsPage";
import MyInterventionsPage from "./pages/MyInterventionsPage";
import InterventionFormPage from "./pages/InterventionFormPage";
import InterventionDetailsPage from "./pages/InterventionDetailsPage";
import TechnicalApprovalsPage from "./pages/TechnicalApprovalsPage";
import AdministrativeApprovalsPage from "./pages/AdministrativeApprovalsPage";
import ReportsPage from "./pages/ReportsPage";
import TechnicianProfilePage from "./pages/TechnicianProfilePage";
import ProfilePage from "./pages/ProfilePage";
import DisplayCalendarPage from "./pages/DisplayCalendarPage";
import { useAuth } from "./context/AuthContext";
import { dashboardPathForRole } from "./utils/roleRoutes";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Replaces a hardcoded "/dashboard" fallback for "/" and any unmatched path:
// the display role has no dashboard at all (DashboardPage.tsx renders
// nothing for it), so blindly redirecting there would land it on a blank
// page. Role-aware via the same dashboardPathForRole() LoginPage.tsx already
// uses post-login, so all three redirect sites stay in agreement.
function RootRedirect() {
  const { isAuthenticated, isLoading, user } = useAuth();
  if (isLoading) return null;
  if (!isAuthenticated || !user) return <Navigate to="/login" replace />;
  return <Navigate to={dashboardPathForRole(user.role)} replace />;
}

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <NotificationPollingProvider>
              <NotificationToastQueue />
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/403" element={<ForbiddenPage />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <DashboardPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/users"
                  element={
                    <ProtectedRoute allowedRoles={["admin_supervisor", "ceo"]}>
                      <AppLayout>
                        <UsersPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/clients"
                  element={
                    <ProtectedRoute allowedRoles={["admin_supervisor", "ceo"]}>
                      <AppLayout>
                        <ClientsPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/sites"
                  element={
                    <ProtectedRoute allowedRoles={["admin_supervisor", "ceo"]}>
                      <AppLayout>
                        <SitesPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/contracts"
                  element={
                    <ProtectedRoute allowedRoles={["admin_supervisor", "ceo"]}>
                      <AppLayout>
                        <ContractsPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/projects"
                  element={
                    <ProtectedRoute allowedRoles={["admin_supervisor", "ceo"]}>
                      <AppLayout>
                        <ProjectsPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/travaux"
                  element={
                    <ProtectedRoute allowedRoles={["admin_supervisor", "ceo"]}>
                      <AppLayout>
                        <TravauxPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/point-rules"
                  element={
                    <ProtectedRoute allowedRoles={["admin_supervisor", "ceo"]}>
                      <AppLayout>
                        <PointRulesPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/planning"
                  element={
                    <ProtectedRoute allowedRoles={["chef_technicien", "admin_supervisor", "ceo"]}>
                      <AppLayout>
                        <PlanningPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/notifications"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <NotificationsPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/interventions"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <MyInterventionsPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/interventions/new"
                  element={
                    <ProtectedRoute allowedRoles={["technician"]}>
                      <AppLayout>
                        <InterventionFormPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/interventions/:id/edit"
                  element={
                    <ProtectedRoute allowedRoles={["technician"]}>
                      <AppLayout>
                        <InterventionFormPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/interventions/:id"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <InterventionDetailsPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/approvals/technical"
                  element={
                    <ProtectedRoute allowedRoles={["chef_technicien"]}>
                      <AppLayout>
                        <TechnicalApprovalsPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/approvals/administrative"
                  element={
                    <ProtectedRoute allowedRoles={["admin_supervisor", "ceo"]}>
                      <AppLayout>
                        <AdministrativeApprovalsPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/reports"
                  element={
                    <ProtectedRoute allowedRoles={["chef_technicien", "admin_supervisor", "ceo"]}>
                      <AppLayout>
                        <ReportsPage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/technicians/:id"
                  element={
                    <ProtectedRoute allowedRoles={["chef_technicien", "admin_supervisor", "ceo"]}>
                      <AppLayout>
                        <TechnicianProfilePage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/profile"
                  element={
                    <ProtectedRoute>
                      <AppLayout>
                        <ProfilePage />
                      </AppLayout>
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/display-calendar"
                  element={
                    <ProtectedRoute allowedRoles={["display"]}>
                      <DisplayCalendarPage />
                    </ProtectedRoute>
                  }
                />
                <Route path="/" element={<RootRedirect />} />
                <Route path="*" element={<RootRedirect />} />
              </Routes>
            </NotificationPollingProvider>
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
