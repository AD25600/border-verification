"use client";

import { useQuery } from "@tanstack/react-query";

import { Card } from "@/components/ui/Card";
import { usersService } from "@/services/users";

export default function UsersPage() {
  const { data: users, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: usersService.list,
  });

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900">Users</h1>
      <p className="mt-1 text-sm text-slate-500">Officers and staff registered in the system.</p>

      <Card className="mt-6 overflow-hidden">
        {isLoading && <p className="p-4 text-sm text-slate-500">Loading users...</p>}
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Checkpoint</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {users?.map((u) => (
              <tr key={u.id}>
                <td className="px-4 py-3">{u.full_name}</td>
                <td className="px-4 py-3">{u.email}</td>
                <td className="px-4 py-3">{u.role_name}</td>
                <td className="px-4 py-3">{u.checkpoint?.name ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
