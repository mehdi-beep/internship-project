import { apiClient } from "../api/client";
import type { ApiResponse, TokenResponse, UserProfile } from "../types/auth";

export async function login(username: string, password: string): Promise<TokenResponse> {
  const { data } = await apiClient.post<ApiResponse<TokenResponse>>("/auth/login", {
    username,
    password,
  });
  if (!data.data) {
    throw new Error(data.message ?? "Login failed.");
  }
  return data.data;
}

export async function fetchCurrentUser(): Promise<UserProfile> {
  const { data } = await apiClient.get<ApiResponse<UserProfile>>("/auth/me");
  if (!data.data) {
    throw new Error("Unable to load current user.");
  }
  return data.data;
}
