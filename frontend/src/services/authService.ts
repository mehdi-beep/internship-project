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

// Task 8 — self-service password reset with email verification.
export async function checkPasswordResetAvailable(): Promise<boolean> {
  const { data } = await apiClient.get<ApiResponse<{ available: boolean }>>("/auth/password-reset/availability");
  return data.data?.available ?? false;
}

export async function requestPasswordReset(): Promise<void> {
  await apiClient.post("/auth/password-reset/request");
}

export async function confirmPasswordReset(code: string, newPassword: string): Promise<void> {
  await apiClient.post("/auth/password-reset/confirm", { code, new_password: newPassword });
}
