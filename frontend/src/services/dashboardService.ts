import { fetchOne } from "../api/queryHelpers";
import type { AdminDashboard, ChefDashboard, TechnicianDashboard } from "../types/dashboard";

export const getTechnicianDashboard = () => fetchOne<TechnicianDashboard>("/dashboard/technician");
export const getSupervisorDashboard = () => fetchOne<ChefDashboard>("/dashboard/supervisor");
export const getAdminDashboard = () => fetchOne<AdminDashboard>("/dashboard/admin");
