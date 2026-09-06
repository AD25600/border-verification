import { apiClient } from "@/services/api";
import { VerificationResponse } from "@/types";

export const verificationService = {
  async analyze(file: File): Promise<VerificationResponse> {
    const formData = new FormData();
    formData.append("file", file);

    // Let the browser set Content-Type (including the multipart boundary) itself —
    // apiClient's default "application/json" header must be explicitly cleared,
    // not overridden with a boundary-less "multipart/form-data" string.
    const { data } = await apiClient.post<VerificationResponse>("/verification/analyze", formData, {
      headers: { "Content-Type": undefined },
    });
    return data;
  },
};
