"use client";

import { useMutation } from "@tanstack/react-query";
import { AlertTriangle, FileUp, ShieldCheck } from "lucide-react";
import { useRef, useState } from "react";

import { RiskLevelBadge, StageStatusBadge } from "@/components/verification/StatusBadges";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { verificationService } from "@/services/verification";
import { VerificationResponse } from "@/types";

export default function VerificationPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const mutation = useMutation({
    mutationFn: (file: File) => verificationService.analyze(file),
  });

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
    mutation.reset();
  }

  function handleAnalyze() {
    if (selectedFile) {
      mutation.mutate(selectedFile);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Verification Workflow</h1>
        <p className="mt-1 text-sm text-slate-500">
          Upload a document image to run detection, OCR, MRZ validation, tampering
          analysis, and risk scoring. Every result below is evidence for your
          review — the system never makes the final decision.
        </p>
      </div>

      <Card className="p-6">
        <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <FileUp className="h-5 w-5 text-slate-400" />
            <div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/jpg,image/png,application/pdf"
                onChange={handleFileChange}
                className="text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200"
              />
              <p className="mt-1 text-xs text-slate-400">JPG, PNG, or PDF — max 15 MB</p>
            </div>
          </div>
          <Button onClick={handleAnalyze} disabled={!selectedFile} isLoading={mutation.isPending}>
            Analyze Document
          </Button>
        </div>

        {mutation.isError && (
          <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {mutation.error instanceof Error ? mutation.error.message : "Analysis failed"}
          </p>
        )}
      </Card>

      {mutation.data && <VerificationEvidence response={mutation.data} />}
    </div>
  );
}

function VerificationEvidence({ response }: { response: VerificationResponse }) {
  const anyNotConfigured = [response.detection, response.ocr, response.mrz, response.tampering, response.risk].some(
    (stage) => stage.status === "not_configured"
  );

  return (
    <div className="space-y-4">
      {anyNotConfigured && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
          <p className="text-sm text-amber-800">
            One or more pipeline stages are not yet configured with a real model.
            This is expected during development — see stage statuses below. No
            result here should be treated as a final verification.
          </p>
        </div>
      )}

      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-slate-700" />
            <h2 className="text-base font-semibold text-slate-900">
              {response.document_type ?? "Document"} — Session {response.session_id.slice(0, 8)}
            </h2>
          </div>
          <StageStatusBadge status={response.overall_status} />
        </div>

        {response.risk_score !== null && response.risk_level && (
          <div className="mt-4 flex items-center gap-4 rounded-md bg-slate-50 p-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Risk Score</p>
              <p className="text-2xl font-semibold text-slate-900">{response.risk_score.toFixed(0)}/100</p>
            </div>
            <RiskLevelBadge level={response.risk_level} />
          </div>
        )}
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <StageCard title="Detection (YOLO)" status={response.detection.status} error={response.detection.error}>
          {response.detection.data && (
            <dl className="space-y-1 text-sm">
              <Row label="Document type" value={response.detection.data.document_type ?? "—"} />
              <Row
                label="Type confidence"
                value={
                  response.detection.data.document_type_confidence != null
                    ? `${(response.detection.data.document_type_confidence * 100).toFixed(0)}%`
                    : "—"
                }
              />
              <Row label="Regions found" value={String(response.detection.data.regions.length)} />
            </dl>
          )}
        </StageCard>

        <StageCard title="OCR (PaddleOCR)" status={response.ocr.status} error={response.ocr.error}>
          {response.ocr_fields.length > 0 && (
            <table className="w-full text-sm">
              <tbody className="divide-y divide-slate-100">
                {response.ocr_fields.map((field) => (
                  <tr key={field.field_name}>
                    <td className="py-1 pr-3 font-medium text-slate-600">{field.field_name}</td>
                    <td className="py-1 text-slate-900">{field.value}</td>
                    <td className="py-1 pl-3 text-right text-xs text-slate-400">
                      {(field.confidence * 100).toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </StageCard>

        <StageCard title="MRZ Validation" status={response.mrz.status} error={response.mrz.error}>
          {response.mrz.data && (
            <dl className="space-y-1 text-sm">
              <Row label="Document number" value={response.mrz.data.document_number ?? "—"} />
              <Row label="Nationality" value={response.mrz.data.nationality ?? "—"} />
              <Row label="Date of birth" value={response.mrz.data.date_of_birth ?? "—"} />
              <Row label="Expiry date" value={response.mrz.data.expiry_date ?? "—"} />
              <Row
                label="Checksums valid"
                value={
                  response.mrz.data.all_checksums_valid === null
                    ? "—"
                    : response.mrz.data.all_checksums_valid
                      ? "Yes"
                      : "No — mismatch found"
                }
              />
            </dl>
          )}
        </StageCard>

        <StageCard title="Tampering Detection" status={response.tampering.status} error={response.tampering.error}>
          {response.tampering.data && (
            <div className="space-y-2 text-sm">
              <Row label="Anomaly score" value={response.tampering.data.anomaly_score.toFixed(2)} />
              {response.tampering.data.indicators.length > 0 && (
                <ul className="list-inside list-disc text-slate-600">
                  {response.tampering.data.indicators.map((ind) => (
                    <li key={ind.indicator}>
                      {ind.indicator.replaceAll("_", " ")} — {(ind.score * 100).toFixed(0)}%
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </StageCard>
      </div>

      {response.risk.data && response.risk.data.factors.length > 0 && (
        <Card className="p-6">
          <h3 className="text-sm font-semibold text-slate-900">Risk Factors</h3>
          <ul className="mt-3 space-y-2">
            {response.risk.data.factors.map((factor) => (
              <li key={factor.factor_name} className="flex items-center justify-between text-sm">
                <span className="text-slate-600">{factor.description}</span>
                <span className="font-medium text-slate-900">+{factor.contribution}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}

function StageCard({
  title,
  status,
  error,
  children,
}: {
  title: string;
  status: VerificationResponse["detection"]["status"];
  error: string | null;
  children?: React.ReactNode;
}) {
  return (
    <Card className="p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
        <StageStatusBadge status={status} />
      </div>
      {status === "success" && children}
      {status !== "success" && (
        <p className="text-xs text-slate-500">
          {error ?? "This stage did not produce a result."}
        </p>
      )}
    </Card>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium text-slate-900">{value}</dd>
    </div>
  );
}
