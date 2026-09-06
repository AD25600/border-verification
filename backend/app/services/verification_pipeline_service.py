"""
Orchestrates the full document verification pipeline:

    UPLOAD
      -> YOLO document/region detection
      -> PaddleOCR text extraction
      -> MRZ parsing + validation
      -> Tampering detection
      -> Feature engineering
      -> XGBoost verification/risk prediction
      -> Final verification result

This is the ONLY place that calls the five ML adapters, and it calls them purely
through the interfaces in app/ml/interfaces.py — never a concrete implementation
class directly. That is what lets each ML component be developed, tested, and
swapped independently of this file and of the API layer.

Design principle: one stage failing must never crash the whole request. Each stage
runs through `_run_stage`, which catches exceptions and records a clear
success/failed/not_configured outcome, so the caller always gets back whatever
partial evidence *did* complete, plus a clear reason for anything that didn't —
this mirrors the architecture's "AI failure must never silently resolve to
verified" rule.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable, TypeVar

from app.core.logging import get_logger
from app.ml.interfaces import (
    BaseMRZParser,
    BaseOCREngine,
    BaseRiskClassifier,
    BaseTamperingDetector,
    BaseYoloDetector,
)
from app.schemas.verification import (
    MRZResult,
    OCRResult,
    PipelineStageResult,
    PipelineStageStatus,
    RiskResult,
    TamperingResult,
    VerificationResponse,
    YoloDetectionResult,
)

logger = get_logger(__name__)

T = TypeVar("T")


class VerificationPipelineService:
    def __init__(
        self,
        yolo_detector: BaseYoloDetector,
        ocr_engine: BaseOCREngine,
        mrz_parser: BaseMRZParser,
        tampering_detector: BaseTamperingDetector,
        risk_classifier: BaseRiskClassifier,
    ) -> None:
        self.yolo_detector = yolo_detector
        self.ocr_engine = ocr_engine
        self.mrz_parser = mrz_parser
        self.tampering_detector = tampering_detector
        self.risk_classifier = risk_classifier

    def run(self, image: bytes, session_id: str | None = None) -> VerificationResponse:
        session_id = session_id or str(uuid.uuid4())
        logger.info("Starting verification pipeline for session_id=%s", session_id)

        detection_stage = self._run_stage("detection", lambda: self.yolo_detector.detect(image))
        detection_result: YoloDetectionResult | None = detection_stage.data
        regions = detection_result.regions if detection_result else []

        ocr_stage = self._run_stage("ocr", lambda: self.ocr_engine.extract_text(image, regions=regions))
        ocr_result: OCRResult | None = ocr_stage.data

        mrz_stage = self._run_mrz_stage(image, regions)
        mrz_result: MRZResult | None = mrz_stage.data

        tampering_stage = self._run_stage("tampering", lambda: self.tampering_detector.predict(image))
        tampering_result: TamperingResult | None = tampering_stage.data

        features = self._build_feature_vector(
            detection_result=detection_result,
            ocr_result=ocr_result,
            mrz_result=mrz_result,
            tampering_result=tampering_result,
        )
        risk_stage = self._run_stage("risk", lambda: self.risk_classifier.predict(features))
        risk_result: RiskResult | None = risk_stage.data

        overall_status = self._aggregate_status(
            [detection_stage, ocr_stage, mrz_stage, tampering_stage, risk_stage]
        )

        response = VerificationResponse(
            session_id=session_id,
            overall_status=overall_status,
            detection=detection_stage,
            ocr=ocr_stage,
            mrz=mrz_stage,
            tampering=tampering_stage,
            risk=risk_stage,
            document_type=detection_result.document_type if detection_result else None,
            ocr_fields=ocr_result.fields if ocr_result else [],
            mrz_validated=mrz_result.all_checksums_valid if mrz_result else None,
            risk_score=risk_result.risk_score if risk_result else None,
            risk_level=risk_result.risk_level if risk_result else None,
        )

        logger.info(
            "Verification pipeline finished for session_id=%s overall_status=%s",
            session_id,
            overall_status.value,
        )
        return response

    # ── internal helpers ────────────────────────────────────────────────────

    def _run_mrz_stage(self, image: bytes, regions: list) -> PipelineStageResult:
        """
        MRZ parsing needs text, not an image — so this stage first runs OCR again,
        scoped to just the mrz_zone region YOLO found (if any), then hands that text
        to the MRZ parser. Skipped (not failed) if no mrz_zone region was detected.
        """
        mrz_regions = [r for r in regions if r.label == "mrz_zone"]
        if not mrz_regions:
            return PipelineStageResult(
                stage="mrz",
                status=PipelineStageStatus.SKIPPED,
                error="No 'mrz_zone' region was detected — skipping MRZ parsing.",
            )

        def _extract_and_parse() -> MRZResult:
            mrz_ocr = self.ocr_engine.extract_text(image, regions=mrz_regions)
            mrz_text = mrz_ocr.raw_text or "\n".join(f.value for f in mrz_ocr.fields)
            return self.mrz_parser.parse(mrz_text)

        return self._run_stage("mrz", _extract_and_parse)

    def _build_feature_vector(
        self,
        detection_result: YoloDetectionResult | None,
        ocr_result: OCRResult | None,
        mrz_result: MRZResult | None,
        tampering_result: TamperingResult | None,
    ) -> dict[str, Any]:
        """
        Assembles the flat feature dict handed to the risk classifier. Every key
        here is documented for team member 5 in app/ml/adapters/xgboost_adapter.py —
        keep the two in sync if you add or rename a feature.
        """
        return {
            "document_type_confidence": (
                detection_result.document_type_confidence if detection_result else None
            ),
            "ocr_average_confidence": ocr_result.average_confidence if ocr_result else None,
            "ocr_field_count": len(ocr_result.fields) if ocr_result else 0,
            "mrz_all_checksums_valid": mrz_result.all_checksums_valid if mrz_result else None,
            "mrz_checksum_failure_count": (
                sum(1 for c in mrz_result.checksum_results if not c.checksum_valid) if mrz_result else None
            ),
            "tampering_anomaly_score": tampering_result.anomaly_score if tampering_result else None,
            "tampering_indicator_count": len(tampering_result.indicators) if tampering_result else 0,
        }

    def _run_stage(self, stage_name: str, fn: Callable[[], T]) -> PipelineStageResult:
        start = time.perf_counter()
        try:
            data = fn()
            duration_ms = (time.perf_counter() - start) * 1000
            return PipelineStageResult(
                stage=stage_name, status=PipelineStageStatus.SUCCESS, data=data, duration_ms=duration_ms
            )
        except NotImplementedError as exc:
            logger.warning("Pipeline stage '%s' not configured: %s", stage_name, exc)
            return PipelineStageResult(
                stage=stage_name,
                status=PipelineStageStatus.NOT_CONFIGURED,
                error=str(exc),
                duration_ms=(time.perf_counter() - start) * 1000,
            )
        except Exception as exc:  # noqa: BLE001 — intentionally broad: isolate stage failures
            logger.exception("Pipeline stage '%s' failed", stage_name)
            return PipelineStageResult(
                stage=stage_name,
                status=PipelineStageStatus.FAILED,
                error=str(exc),
                duration_ms=(time.perf_counter() - start) * 1000,
            )

    @staticmethod
    def _aggregate_status(stages: list[PipelineStageResult]) -> PipelineStageStatus:
        statuses = {s.status for s in stages}
        if PipelineStageStatus.FAILED in statuses:
            return PipelineStageStatus.FAILED
        if PipelineStageStatus.NOT_CONFIGURED in statuses:
            return PipelineStageStatus.NOT_CONFIGURED
        if PipelineStageStatus.SKIPPED in statuses:
            return PipelineStageStatus.SKIPPED
        return PipelineStageStatus.SUCCESS
