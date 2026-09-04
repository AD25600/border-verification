import { apiClient } from "@/services/api";
import { User } from "@/types";

export const usersService = {
  async list(): Promise<User[]> {
    const { data } = await apiClient.get<User[]>("/users");
    return data;
  },

  async getById(id: string): Promise<User> {
    const { data } = await apiClient.get<User>(`/users/${id}`);
    return data;
  },
};
