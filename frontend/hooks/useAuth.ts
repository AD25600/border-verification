"use client";

import { useQuery } from "@tanstack/react-query";

import { authService } from "@/services/auth";
import { tokenStorage } from "@/lib/token-storage";

export function useAuth() {
  const hasToken = typeof window !== "undefined" && !!tokenStorage.get();

  const query = useQuery({
    queryKey: ["current-user"],
    queryFn: authService.getCurrentUser,
    enabled: hasToken,
    retry: false,
  });

  function logout() {
    tokenStorage.clear();
    document.cookie = "bvp_access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
    window.location.href = "/login";
  }

  return {
    user: query.data ?? null,
    isLoading: hasToken && query.isLoading,
    isAuthenticated: !!query.data,
    logout,
  };
}
