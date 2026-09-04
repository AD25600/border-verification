import { apiClient } from "@/services/api";
import { LoginPayload, TokenResponse, User } from "@/types";

export const authService = {
  async login(payload: LoginPayload): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>("/auth/login", payload);
    return data;
  },

  async getCurrentUser(): Promise<User> {
    const { data } = await apiClient.get<User>("/auth/me");
    return data;
  },
};
