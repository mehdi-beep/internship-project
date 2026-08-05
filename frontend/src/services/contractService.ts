import { fetchPage, fetchOne, postOne, putOne, patchOne } from "../api/queryHelpers";
import type { Contract, ContractStatus } from "../types/referenceData";

export interface ContractListParams {
  page?: number;
  page_size?: number;
  client_id?: number;
  status?: ContractStatus;
  search?: string;
}

export interface ContractInput {
  client_id: number;
  contract_name: string;
  start_date: string;
  end_date?: string | null;
}

export const listContracts = (params: ContractListParams = {}) => fetchPage<Contract>("/contracts", params);
export const getContract = (id: number) => fetchOne<Contract>(`/contracts/${id}`);
export const createContract = (input: ContractInput) => postOne<Contract>("/contracts", input);
export const updateContract = (id: number, input: Omit<ContractInput, "client_id">) =>
  putOne<Contract>(`/contracts/${id}`, input);
export const archiveContract = (id: number) => patchOne<Contract>(`/contracts/${id}/archive`);
