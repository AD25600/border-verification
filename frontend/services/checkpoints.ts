import { apiClient } from "@/services/api";
import { Checkpoint } from "@/types";

export const checkpointsService = {
  async list(): Promise<Checkpoint[]> {
    const { data } = await apiClient.get<Checkpoint[]>("/checkpoints");
    return data;
  },

  async create(payload: Omit<Checkpoint, "id">): Promise<Checkpoint> {
    const { data } = await apiClient.post<Checkpoint>("/checkpoints", payload);
    return data;
  },
};
