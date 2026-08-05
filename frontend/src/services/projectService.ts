import { fetchPage, fetchOne, postOne, putOne, patchOne } from "../api/queryHelpers";
import type { Project, ProjectStatus } from "../types/referenceData";

export interface ProjectListParams {
  page?: number;
  page_size?: number;
  client_id?: number;
  status?: ProjectStatus;
  search?: string;
}

export interface ProjectInput {
  client_id: number;
  project_name: string;
  start_date: string;
  end_date?: string | null;
}

export const listProjects = (params: ProjectListParams = {}) => fetchPage<Project>("/projects", params);
export const getProject = (id: number) => fetchOne<Project>(`/projects/${id}`);
export const createProject = (input: ProjectInput) => postOne<Project>("/projects", input);
export const updateProject = (id: number, input: Omit<ProjectInput, "client_id">) =>
  putOne<Project>(`/projects/${id}`, input);
export const archiveProject = (id: number) => patchOne<Project>(`/projects/${id}/archive`);
