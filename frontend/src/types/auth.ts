import type { UserRole } from "./enums";

export interface UserProfile {
  id: number;
  first_name: string;
  last_name: string;
  username: string;
  email: string;
  role: UserRole;
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}
