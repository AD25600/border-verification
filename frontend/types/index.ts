export type RoleName = "ADMIN" | "SUPERVISOR" | "OFFICER";

export interface Checkpoint {
  id: string;
  name: string;
  code: string;
  location: string | null;
  is_active: boolean;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  role_name: RoleName;
  checkpoint: Checkpoint | null;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface ServiceResult<T> {
  status: "success" | "error";
  confidence?: number | null;
  result?: T | null;
  errors: string[];
}

// ── Verification pipeline types ────────────────────────────────────────────
// These mirror backend/app/schemas/verification.py field-for-field. Keep in
// sync if the backend schema changes — it is the API's response_model, so
// /docs always shows the authoritative current shape.

export type PipelineStageStatusValue = "success" | "failed" | "not_configured" | "skipped";

export interface BoundingBox {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
  label: string;
  confidence: number;
}

export interface OCRField {
  field_name: string;
  value: string;
  confidence: number;
  source_region: BoundingBox | null;
}

export interface MRZFieldCheck {
  field_name: string;
  checksum_valid: boolean;
}

export interface MRZResult {
  raw_mrz_lines: string[];
  document_number: string | null;
  nationality: string | null;
  date_of_birth: string | null;
  expiry_date: string | null;
  sex: string | null;
  surname: string | null;
  given_names: string | null;
  checksum_results: MRZFieldCheck[];
  all_checksums_valid: boolean | null;
}

export interface TamperingIndicator {
  indicator: string;
  score: number;
  region: BoundingBox | null;
}

export interface TamperingResult {
  anomaly_score: number;
  indicators: TamperingIndicator[];
  flagged_regions: BoundingBox[];
}

export type RiskLevelValue = "low" | "medium" | "high" | "critical";

export interface RiskFactor {
  factor_name: string;
  contribution: number;
  description: string;
}

export interface RiskResult {
  risk_score: number;
  risk_level: RiskLevelValue;
  factors: RiskFactor[];
  model_confidence: number | null;
}

export interface YoloDetectionResult {
  document_type: string | null;
  document_type_confidence: number | null;
  regions: BoundingBox[];
}

export interface PipelineStageResult<T = unknown> {
  stage: string;
  status: PipelineStageStatusValue;
  data: T | null;
  error: string | null;
  duration_ms: number | null;
}

export interface VerificationResponse {
  session_id: string;
  overall_status: PipelineStageStatusValue;
  detection: PipelineStageResult<YoloDetectionResult>;
  ocr: PipelineStageResult<{ fields: OCRField[]; raw_text: string | null; average_confidence: number | null }>;
  mrz: PipelineStageResult<MRZResult>;
  tampering: PipelineStageResult<TamperingResult>;
  risk: PipelineStageResult<RiskResult>;
  document_type: string | null;
  ocr_fields: OCRField[];
  mrz_validated: boolean | null;
  risk_score: number | null;
  risk_level: RiskLevelValue | null;
}
