import axios, { AxiosError, AxiosInstance } from "axios";

import { tokenStorage } from "@/lib/token-storage";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const token = tokenStorage.get();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ message?: string }>) => {
    if (error.response?.status === 401) {
      tokenStorage.clear();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    const message = error.response?.data?.message ?? error.message ?? "Unexpected error";
    return Promise.reject(new Error(message));
  }
);
