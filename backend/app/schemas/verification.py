"""
Data contracts for the document verification pipeline.

Every ML adapter (YOLO, OCR, MRZ, tampering, risk/XGBoost) returns its result as one
of the Pydantic models below, and only these models. This is the single source of
truth for "what shape of data does my stage need to return" — read this file first
if you are implementing one of the five ML components.

These are also used directly as the final API response shape, so a teammate's
adapter output flows through to the frontend unchanged.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Shared primitives
# ─────────────────────────────────────────────────────────────────────────────


class BoundingBox(BaseModel):
    """Pixel coordinates of a detected region, top-left origin."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float
    label: str = Field(description="e.g. 'photo', 'mrz_zone', 'passport_number_field'")
    confidence: float = Field(ge=0.0, le=1.0)


class PipelineStageStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    NOT_CONFIGURED = "not_configured"
    SKIPPED = "skipped"


# ─────────────────────────────────────────────────────────────────────────────
# 1. YOLO — document / field detection
# ─────────────────────────────────────────────────────────────────────────────


class YoloDetectionResult(BaseModel):
    """
    Return type of BaseYoloDetector.detect().

    `regions` should include, at minimum, any regions the later stages depend on:
    a 'document' region (the cropped document boundary), a 'photo' region (the
    face photo on the document), and an 'mrz_zone' region if applicable to the
    document type. Additional field-level regions (e.g. 'passport_number_field')
    are optional but help OCR run on a tighter crop for better accuracy.
    """

    document_type: Optional[str] = Field(default=None, description="e.g. 'passport', 'visa', 'national_id'")
    document_type_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    regions: list[BoundingBox] = Field(default_factory=list)
    raw_model_output: Optional[dict[str, Any]] = Field(
        default=None, description="Optional passthrough of raw model metadata for debugging/audit."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. PaddleOCR — text extraction
# ─────────────────────────────────────────────────────────────────────────────


class OCRField(BaseModel):
    field_name: str = Field(description="e.g. 'full_name', 'date_of_birth', 'document_number'")
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_region: Optional[BoundingBox] = None


class OCRResult(BaseModel):
    """Return type of BaseOCREngine.extract_text()."""

    fields: list[OCRField] = Field(default_factory=list)
    raw_text: Optional[str] = Field(default=None, description="Full unstructured OCR text, if useful for audit.")
    average_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


# ─────────────────────────────────────────────────────────────────────────────
# 3. MRZ Parser — passport MRZ extraction and validation
# ─────────────────────────────────────────────────────────────────────────────


class MRZFieldCheck(BaseModel):
    field_name: str = Field(description="e.g. 'document_number', 'date_of_birth', 'expiry_date', 'composite'")
    checksum_valid: bool


class MRZResult(BaseModel):
    """Return type of BaseMRZParser.parse()."""

    raw_mrz_lines: list[str] = Field(default_factory=list)
    document_number: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[str] = Field(default=None, description="ISO 8601 (YYYY-MM-DD)")
    expiry_date: Optional[str] = Field(default=None, description="ISO 8601 (YYYY-MM-DD)")
    sex: Optional[str] = None
    surname: Optional[str] = None
    given_names: Optional[str] = None
    checksum_results: list[MRZFieldCheck] = Field(default_factory=list)
    all_checksums_valid: Optional[bool] = None


# ─────────────────────────────────────────────────────────────────────────────
# 4. Tampering Detection — document manipulation detection
# ─────────────────────────────────────────────────────────────────────────────


class TamperingIndicator(BaseModel):
    indicator: str = Field(description="e.g. 'font_inconsistency', 'compression_anomaly', 'copy_paste_region'")
    score: float = Field(ge=0.0, le=1.0)
    region: Optional[BoundingBox] = None


class TamperingResult(BaseModel):
    """Return type of BaseTamperingDetector.predict()."""

    anomaly_score: float = Field(ge=0.0, le=1.0, description="0 = no signs of tampering, 1 = highly likely tampered")
    indicators: list[TamperingIndicator] = Field(default_factory=list)
    flagged_regions: list[BoundingBox] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# 5. XGBoost — final verification / risk classification
# ─────────────────────────────────────────────────────────────────────────────


class RiskFactor(BaseModel):
    """One line of the explainable risk breakdown — never just a bare score."""

    factor_name: str = Field(description="e.g. 'mrz_checksum_mismatch', 'face_similarity_low'")
    contribution: float = Field(description="Points/weight this factor contributed to the total score")
    description: str


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskResult(BaseModel):
    """Return type of BaseRiskClassifier.predict()."""

    model_config = {"protected_namespaces": ()}

    risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel
    factors: list[RiskFactor] = Field(default_factory=list)
    model_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline stage wrapper + final aggregated response
# ─────────────────────────────────────────────────────────────────────────────


class PipelineStageResult(BaseModel):
    """
    Wraps every stage's outcome uniformly, so a failure in one stage never crashes
    the whole request — it just gets recorded in-line with a status and error
    message, alongside whatever stages *did* succeed.
    """

    stage: str
    status: PipelineStageStatus
    data: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None


class VerificationResponse(BaseModel):
    """Final structured API response for POST /api/v1/verification/analyze."""

    session_id: str
    overall_status: PipelineStageStatus = Field(
        description="SUCCESS only if every configured stage completed; FAILED if any configured stage errored."
    )

    detection: PipelineStageResult
    ocr: PipelineStageResult
    mrz: PipelineStageResult
    tampering: PipelineStageResult
    risk: PipelineStageResult

    # Convenience top-level fields, flattened from the stage results above when
    # available, so simple frontend consumers don't need to dig into each stage's
    # `data` payload to get the headline numbers.
    document_type: Optional[str] = None
    ocr_fields: list[OCRField] = Field(default_factory=list)
    mrz_validated: Optional[bool] = Field(default=None, description="Mirrors MRZResult.all_checksums_valid")
    risk_score: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
