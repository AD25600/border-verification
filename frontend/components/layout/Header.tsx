"use client";

import { LogOut } from "lucide-react";

import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6">
      <div>
        <p className="text-sm font-medium text-slate-900">
          {user?.checkpoint ? user.checkpoint.name : "No checkpoint assigned"}
        </p>
        <p className="text-xs text-slate-500">{user?.checkpoint?.code ?? "—"}</p>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <p className="text-sm font-medium text-slate-900">{user?.full_name}</p>
          <p className="text-xs text-slate-500">{user?.role_name}</p>
        </div>
        <Button variant="secondary" onClick={logout} className="gap-2">
          <LogOut className="h-4 w-4" />
          Logout
        </Button>
      </div>
    </header>
  );
}
