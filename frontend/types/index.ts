export type RoleName = "ADMIN" | "SUPERVISOR" | "OFFICER";

export interface Checkpoint {
  id: string;
  name: string;
  code: string;
  location: string | null;
  is_active: boolean;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  role_name: RoleName;
  checkpoint: Checkpoint | null;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ServiceResult<T> {
  status: "success" | "error";
  confidence?: number | null;
  result?: T | null;
  errors: string[];
}
