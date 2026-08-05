import { apiClient } from "./client";
import type { ApiResponse } from "../types/auth";
import type { Page } from "../types/pagination";

export async function fetchPage<T>(url: string, params: object): Promise<Page<T>> {
  const { data } = await apiClient.get<ApiResponse<Page<T>>>(url, { params });
  if (!data.data) {
    throw new Error(data.message ?? "Request failed.");
  }
  return data.data;
}

export async function fetchOne<T>(url: string): Promise<T> {
  const { data } = await apiClient.get<ApiResponse<T>>(url);
  if (!data.data) {
    throw new Error(data.message ?? "Request failed.");
  }
  return data.data;
}

export async function postOne<T>(url: string, body?: unknown): Promise<T> {
  const { data } = await apiClient.post<ApiResponse<T>>(url, body);
  if (!data.data) {
    throw new Error(data.message ?? "Request failed.");
  }
  return data.data;
}

export async function putOne<T>(url: string, body: unknown): Promise<T> {
  const { data } = await apiClient.put<ApiResponse<T>>(url, body);
  if (!data.data) {
    throw new Error(data.message ?? "Request failed.");
  }
  return data.data;
}

export async function patchOne<T>(url: string, body?: unknown): Promise<T> {
  const { data } = await apiClient.patch<ApiResponse<T>>(url, body);
  if (!data.data) {
    throw new Error(data.message ?? "Request failed.");
  }
  return data.data;
}
