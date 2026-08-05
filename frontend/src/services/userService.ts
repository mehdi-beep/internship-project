import { fetchPage, fetchOne, postOne, putOne, patchOne } from "../api/queryHelpers";
import type { UserRole } from "../types/enums";
import type { AppUser } from "../types/referenceData";

export interface UserListParams {
  page?: number;
  page_size?: number;
  role?: UserRole;
  active_only?: boolean;
  search?: string;
}

export interface UserCreateInput {
  first_name: string;
  last_name: string;
  username: string;
  email: string;
  phone?: string | null;
  role: UserRole;
  password: string;
}

export interface UserUpdateInput {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  role: UserRole;
}

export const listUsers = (params: UserListParams = {}) => fetchPage<AppUser>("/users", params);
export const getUser = (id: number) => fetchOne<AppUser>(`/users/${id}`);
export const createUser = (input: UserCreateInput) => postOne<AppUser>("/users", input);
export const updateUser = (id: number, input: UserUpdateInput) => putOne<AppUser>(`/users/${id}`, input);
export const activateUser = (id: number) => patchOne<AppUser>(`/users/${id}/activate`);
export const deactivateUser = (id: number) => patchOne<AppUser>(`/users/${id}/deactivate`);
export const resetPassword = (id: number, newPassword: string) =>
  patchOne<AppUser>(`/users/${id}/reset-password`, { new_password: newPassword });
