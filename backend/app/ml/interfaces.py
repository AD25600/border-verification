"""
Abstract interfaces for the five independently-developed ML components.

Each of the five teammates implements ONE of the classes below as a concrete
subclass, then points the corresponding `*_ADAPTER_CLASS` setting in `.env` at it
(dotted import path). The pipeline orchestrator (`app.services.verification_pipeline
.VerificationPipelineService`) only ever calls the methods defined here — it never
imports a teammate's concrete class directly. This is the whole point of the
interface: the orchestration/API layer is written once, today, and does not change
no matter what YOLO/OCR/tampering/XGBoost implementation eventually lands.

Contract rules that apply to every adapter:
  - Accept raw bytes for image input (already-read file content), not file paths or
    file handles — the orchestrator owns file I/O via DocumentService.
  - Return one of the Pydantic models in app/schemas/verification.py. Never return a
    raw dict, tensor, or framework-specific object.
  - Raise on failure (any exception) rather than returning a low-confidence guess.
    The orchestrator catches exceptions per-stage and reports them cleanly — it is
    always better for your adapter to raise than to fabricate a plausible-looking
    result.
  - Do all model loading in `__init__` (or lazily on first call, cached), not on
    every call — the orchestrator instantiates each adapter once at startup via the
    registry, not per-request.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.verification import (
    BoundingBox,
    MRZResult,
    OCRResult,
    RiskResult,
    TamperingResult,
    YoloDetectionResult,
)


class BaseYoloDetector(ABC):
    """
    Component 1 — YOLO document/field detection.

    Input:  raw image bytes (jpg/png) of the uploaded document.
    Output: YoloDetectionResult — document type + bounding boxes for the regions
            later stages need (document boundary, photo, MRZ zone, individual
            text fields if available).
    """

    @abstractmethod
    def detect(self, image: bytes) -> YoloDetectionResult:
        raise NotImplementedError


class BaseOCREngine(ABC):
    """
    Component 2 — PaddleOCR text extraction.

    Input:  raw image bytes, plus optionally the regions YOLO already found (so OCR
            can run on tight crops instead of the whole image for better accuracy).
    Output: OCRResult — structured field/value pairs with per-field confidence.
    """

    @abstractmethod
    def extract_text(self, image: bytes, regions: Optional[list[BoundingBox]] = None) -> OCRResult:
        raise NotImplementedError


class BaseMRZParser(ABC):
    """
    Component 3 — MRZ extraction and validation.

    Input:  the raw MRZ text as a string (typically OCR's output on the MRZ region,
            already isolated by YOLO — the orchestrator is responsible for handing
            you that substring, not a whole-document image).
    Output: MRZResult — parsed fields plus per-field ICAO 9303 checksum validity.
    """

    @abstractmethod
    def parse(self, mrz_text: str) -> MRZResult:
        raise NotImplementedError


class BaseTamperingDetector(ABC):
    """
    Component 4 — document manipulation / tampering detection.

    Input:  raw image bytes of the full document (tampering analysis typically
            needs the whole image, not just cropped regions, to catch compression
            and metadata-level anomalies).
    Output: TamperingResult — an overall anomaly score plus a list of named,
            independently-explainable indicators (never a single opaque verdict).
    """

    @abstractmethod
    def predict(self, image: bytes) -> TamperingResult:
        raise NotImplementedError


class BaseRiskClassifier(ABC):
    """
    Component 5 — XGBoost final verification / risk classification.

    Input:  a flat feature dict assembled by the orchestrator from every earlier
            stage's output (see VerificationPipelineService._build_feature_vector
            for exactly which keys are provided and their types).
    Output: RiskResult — numeric score, a discrete risk level, and an itemized,
            weighted breakdown of contributing factors. Never a bare "suspicious"
            verdict with no explanation.
    """

    @abstractmethod
    def predict(self, features: dict) -> RiskResult:
        raise NotImplementedError
