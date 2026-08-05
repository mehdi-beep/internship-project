import { fetchPage, fetchOne, postOne, putOne, patchOne } from "../api/queryHelpers";
import type { Page } from "../types/pagination";
import type { Client, ClientSite } from "../types/referenceData";

export interface ClientListParams {
  page?: number;
  page_size?: number;
  search?: string;
  active_only?: boolean;
}

export interface ClientInput {
  client_name: string;
  phone?: string | null;
  email?: string | null;
}

export const listClients = (params: ClientListParams = {}) => fetchPage<Client>("/clients", params);
export const getClient = (id: number) => fetchOne<Client>(`/clients/${id}`);
export const createClient = (input: ClientInput) => postOne<Client>("/clients", input);
export const updateClient = (id: number, input: ClientInput) => putOne<Client>(`/clients/${id}`, input);
export const deactivateClient = (id: number) => patchOne<Client>(`/clients/${id}/deactivate`);
export const activateClient = (id: number) => patchOne<Client>(`/clients/${id}/activate`);
export const listSitesForClient = (clientId: number, params: { page_size?: number } = {}) =>
  fetchPage<ClientSite>(`/clients/${clientId}/sites`, params);

export type { Page };
