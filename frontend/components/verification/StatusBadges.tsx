import clsx from "clsx";

import { PipelineStageStatusValue, RiskLevelValue } from "@/types";

const STAGE_STYLES: Record<PipelineStageStatusValue, string> = {
  success: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  not_configured: "bg-amber-100 text-amber-700",
  skipped: "bg-slate-100 text-slate-500",
};

const STAGE_LABELS: Record<PipelineStageStatusValue, string> = {
  success: "Success",
  failed: "Failed",
  not_configured: "Not configured",
  skipped: "Skipped",
};

export function StageStatusBadge({ status }: { status: PipelineStageStatusValue }) {
  return (
    <span className={clsx("rounded-full px-2 py-0.5 text-xs font-medium", STAGE_STYLES[status])}>
      {STAGE_LABELS[status]}
    </span>
  );
}

const RISK_STYLES: Record<RiskLevelValue, string> = {
  low: "bg-risk-low/10 text-risk-low",
  medium: "bg-risk-medium/10 text-risk-medium",
  high: "bg-risk-high/10 text-risk-high",
  critical: "bg-risk-critical/10 text-risk-critical",
};

export function RiskLevelBadge({ level }: { level: RiskLevelValue }) {
  return (
    <span className={clsx("rounded-full px-3 py-1 text-sm font-semibold uppercase tracking-wide", RISK_STYLES[level])}>
      {level}
    </span>
  );
}
