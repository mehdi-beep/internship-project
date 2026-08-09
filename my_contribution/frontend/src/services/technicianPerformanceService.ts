import { fetchOne } from "../api/queryHelpers";
import type { TechnicianPerformanceDetail, TechnicianPerformanceSummary } from "../types/technicianPerformance";

export const listTechnicianPerformance = () =>
  fetchOne<TechnicianPerformanceSummary[]>("/technician-performance");

export const getTechnicianPerformance = (technicianId: number) =>
  fetchOne<TechnicianPerformanceDetail>(`/technician-performance/${technicianId}`);

export const getMyTechnicianPerformance = () =>
  fetchOne<TechnicianPerformanceDetail>("/technician-performance/me");
