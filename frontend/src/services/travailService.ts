import { fetchPage, fetchOne, postOne, putOne, patchOne, deleteOne } from "../api/queryHelpers";
import type { Travail } from "../types/referenceData";
import type { DeletionCheck } from "../types/deletion";

export interface TravailListParams {
  page?: number;
  page_size?: number;
  search?: string;
  active_only?: boolean;
  category?: string;
}

export interface TravailInput {
  travail_code: string;
  travail_name: string;
  category?: string | null;
}

export const listTravaux = (params: TravailListParams = {}) => fetchPage<Travail>("/travaux", params);
export const listTravauxCategories = () => fetchOne<string[]>("/travaux/categories");
export const getTravail = (id: number) => fetchOne<Travail>(`/travaux/${id}`);
export const createTravail = (input: TravailInput) => postOne<Travail>("/travaux", input);
export const updateTravail = (id: number, input: TravailInput) => putOne<Travail>(`/travaux/${id}`, input);
export const deactivateTravail = (id: number) => patchOne<Travail>(`/travaux/${id}/deactivate`);
export const activateTravail = (id: number) => patchOne<Travail>(`/travaux/${id}/activate`);

// --- Task 5: permanent deletion (Administrator only) ---
export const checkTravailDeletable = (id: number) =>
  fetchOne<DeletionCheck>(`/travaux/${id}/deletion-check`);
export const deleteTravailPermanently = (id: number) => deleteOne(`/travaux/${id}`);
