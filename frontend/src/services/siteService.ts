import { fetchPage, fetchOne, postOne, putOne, patchOne } from "../api/queryHelpers";
import type { ClientSite } from "../types/referenceData";

export interface SiteListParams {
  page?: number;
  page_size?: number;
  client_id?: number;
  city?: string;
  search?: string;
  active_only?: boolean;
}

export interface SiteInput {
  client_id: number;
  site_name: string;
  city: string;
  address?: string | null;
}

export const listSites = (params: SiteListParams = {}) => fetchPage<ClientSite>("/sites", params);
export const getSite = (id: number) => fetchOne<ClientSite>(`/sites/${id}`);
export const createSite = (input: SiteInput) => postOne<ClientSite>("/sites", input);
export const updateSite = (id: number, input: Omit<SiteInput, "client_id">) => putOne<ClientSite>(`/sites/${id}`, input);
export const deactivateSite = (id: number) => patchOne<ClientSite>(`/sites/${id}/deactivate`);
export const activateSite = (id: number) => patchOne<ClientSite>(`/sites/${id}/activate`);
