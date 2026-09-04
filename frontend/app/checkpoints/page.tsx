"use client";

import { useQuery } from "@tanstack/react-query";

import { Card } from "@/components/ui/Card";
import { checkpointsService } from "@/services/checkpoints";

export default function CheckpointsPage() {
  const { data: checkpoints, isLoading } = useQuery({
    queryKey: ["checkpoints"],
    queryFn: checkpointsService.list,
  });

  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900">Checkpoints</h1>
      <p className="mt-1 text-sm text-slate-500">Checkpoints registered in the system.</p>

      <div className="mt-6 space-y-3">
        {isLoading && <p className="text-sm text-slate-500">Loading checkpoints...</p>}
        {checkpoints?.map((checkpoint) => (
          <Card key={checkpoint.id} className="flex items-center justify-between p-4">
            <div>
              <p className="text-sm font-medium text-slate-900">{checkpoint.name}</p>
              <p className="text-xs text-slate-500">{checkpoint.code}</p>
            </div>
            <span
              className={
                checkpoint.is_active
                  ? "rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-700"
                  : "rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-500"
              }
            >
              {checkpoint.is_active ? "Active" : "Inactive"}
            </span>
          </Card>
        ))}
        {checkpoints?.length === 0 && (
          <p className="text-sm text-slate-500">No checkpoints found. Run the backend seed script.</p>
        )}
      </div>
    </div>
  );
}
