import { ThemeProvider, CssBaseline } from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { theme } from "./styles/theme";
import { AuthProvider } from "./context/AuthContext";
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

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
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
                  <ProtectedRoute allowedRoles={["admin_supervisor"]}>
                    <AppLayout>
                      <UsersPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/clients"
                element={
                  <ProtectedRoute allowedRoles={["admin_supervisor"]}>
                    <AppLayout>
                      <ClientsPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/sites"
                element={
                  <ProtectedRoute allowedRoles={["admin_supervisor"]}>
                    <AppLayout>
                      <SitesPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/contracts"
                element={
                  <ProtectedRoute allowedRoles={["admin_supervisor"]}>
                    <AppLayout>
                      <ContractsPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/projects"
                element={
                  <ProtectedRoute allowedRoles={["admin_supervisor"]}>
                    <AppLayout>
                      <ProjectsPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/admin/travaux"
                element={
                  <ProtectedRoute allowedRoles={["admin_supervisor"]}>
                    <AppLayout>
                      <TravauxPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/planning"
                element={
                  <ProtectedRoute allowedRoles={["chef_technicien", "admin_supervisor"]}>
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
                  <ProtectedRoute allowedRoles={["admin_supervisor"]}>
                    <AppLayout>
                      <AdministrativeApprovalsPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/reports"
                element={
                  <ProtectedRoute allowedRoles={["chef_technicien", "admin_supervisor"]}>
                    <AppLayout>
                      <ReportsPage />
                    </AppLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/technicians/:id"
                element={
                  <ProtectedRoute allowedRoles={["chef_technicien", "admin_supervisor"]}>
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
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
