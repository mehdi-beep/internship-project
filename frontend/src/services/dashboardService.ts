import { fetchOne } from "../api/queryHelpers";
import type { PeriodMode } from "../components/PeriodModeSelector";
import type {
  AdminDashboard,
  AdminDashboardCharts,
  ChefDashboard,
  ChefDashboardCharts,
  TechnicianDashboard,
  TechnicianDashboardCharts,
} from "../types/dashboard";

export const getTechnicianDashboard = () => fetchOne<TechnicianDashboard>("/dashboard/technician");
export const getSupervisorDashboard = () => fetchOne<ChefDashboard>("/dashboard/supervisor");
export const getAdminDashboard = () => fetchOne<AdminDashboard>("/dashboard/admin");

export const getTechnicianDashboardCharts = (mode: PeriodMode, anchor: string) =>
  fetchOne<TechnicianDashboardCharts>(`/dashboard/technician/charts?mode=${mode}&anchor=${anchor}`);

export const getSupervisorDashboardCharts = (mode: PeriodMode, anchor: string) =>
  fetchOne<ChefDashboardCharts>(`/dashboard/supervisor/charts?mode=${mode}&anchor=${anchor}`);

export const getAdminDashboardCharts = (mode: PeriodMode, anchor: string) =>
  fetchOne<AdminDashboardCharts>(`/dashboard/admin/charts?mode=${mode}&anchor=${anchor}`);
