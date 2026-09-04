"use client";

import { Card } from "@/components/ui/Card";

const METRICS = [
  { label: "Active Checkpoint", value: "—", note: "Populated once sessions begin" },
  { label: "Verification Sessions", value: "0", note: "Phase 3+ module" },
  { label: "Documents Processed", value: "0", note: "Phase 3+ module" },
  { label: "Alerts", value: "0", note: "Phase 5+ risk engine" },
];

export default function DashboardPage() {
  return (
    <div>
      <h1 className="text-xl font-semibold text-slate-900">Dashboard</h1>
      <p className="mt-1 text-sm text-slate-500">
        Foundation metrics shown below are placeholders. Verification data will populate this view
        once later modules are integrated.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {METRICS.map((metric) => (
          <Card key={metric.label} className="p-5">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{metric.label}</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">{metric.value}</p>
            <p className="mt-1 text-xs text-slate-400">{metric.note}</p>
          </Card>
        ))}
      </div>
    </div>
  );
}
