"""
Mock ML adapters used ONLY in tests, to validate the orchestrator/interface
contracts without depending on any teammate's real model being ready yet.

These are intentionally kept out of app/ml/adapters/ — production code must never
import test mocks, and the stub scaffolds in app/ml/adapters/ already serve as the
non-fake "not configured" fallback for real usage.
"""

from __future__ import annotations

from typing import Optional

from app.ml.interfaces import (
    BaseMRZParser,
    BaseOCREngine,
    BaseRiskClassifier,
    BaseTamperingDetector,
    BaseYoloDetector,
)
from app.schemas.verification import (
    BoundingBox,
    MRZFieldCheck,
    MRZResult,
    OCRField,
    OCRResult,
    RiskFactor,
    RiskLevel,
    RiskResult,
    TamperingIndicator,
    TamperingResult,
    YoloDetectionResult,
)


class MockYoloDetector(BaseYoloDetector):
    def detect(self, image: bytes) -> YoloDetectionResult:
        return YoloDetectionResult(
            document_type="passport",
            document_type_confidence=0.97,
            regions=[
                BoundingBox(x_min=0, y_min=0, x_max=100, y_max=100, label="document", confidence=0.99),
                BoundingBox(x_min=10, y_min=10, x_max=40, y_max=50, label="photo", confidence=0.95),
                BoundingBox(x_min=0, y_min=80, x_max=100, y_max=100, label="mrz_zone", confidence=0.93),
            ],
        )


class MockOCREngine(BaseOCREngine):
    def extract_text(self, image: bytes, regions: Optional[list[BoundingBox]] = None) -> OCRResult:
        is_mrz_only = bool(regions) and all(r.label == "mrz_zone" for r in regions)
        if is_mrz_only:
            return OCRResult(
                fields=[],
                raw_text="P<UTOTRAVELER<<JANE<<<<<<<<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10",
                average_confidence=0.9,
            )
        return OCRResult(
            fields=[
                OCRField(field_name="full_name", value="JANE TRAVELER", confidence=0.96),
                OCRField(field_name="document_number", value="L898902C3", confidence=0.94),
            ],
            raw_text="JANE TRAVELER L898902C3",
            average_confidence=0.95,
        )


class MockMRZParser(BaseMRZParser):
    def parse(self, mrz_text: str) -> MRZResult:
        return MRZResult(
            raw_mrz_lines=mrz_text.splitlines(),
            document_number="L898902C3",
            nationality="UTO",
            date_of_birth="1974-08-12",
            expiry_date="2012-04-15",
            sex="F",
            surname="TRAVELER",
            given_names="JANE",
            checksum_results=[
                MRZFieldCheck(field_name="document_number", checksum_valid=True),
                MRZFieldCheck(field_name="composite", checksum_valid=True),
            ],
            all_checksums_valid=True,
        )


class MockTamperingDetector(BaseTamperingDetector):
    def predict(self, image: bytes) -> TamperingResult:
        return TamperingResult(
            anomaly_score=0.12,
            indicators=[TamperingIndicator(indicator="compression_anomaly", score=0.12)],
            flagged_regions=[],
        )


class MockRiskClassifier(BaseRiskClassifier):
    def predict(self, features: dict) -> RiskResult:
        return RiskResult(
            risk_score=15.0,
            risk_level=RiskLevel.LOW,
            factors=[
                RiskFactor(
                    factor_name="tampering_anomaly_score",
                    contribution=15.0,
                    description="Low tampering anomaly score.",
                )
            ],
            model_confidence=0.92,
        )


class FailingYoloDetector(BaseYoloDetector):
    """Simulates a configured-but-broken model, to test stage-level failure isolation."""

    def detect(self, image: bytes) -> YoloDetectionResult:
        raise RuntimeError("Simulated inference crash")


class UnconfiguredMRZParser(BaseMRZParser):
    """Simulates the scaffold-stub behavior for a not-yet-implemented adapter."""

    def parse(self, mrz_text: str) -> MRZResult:
        raise NotImplementedError("MRZParserAdapter.parse() is a scaffold stub")


class ConfigurableMockYoloDetector(BaseYoloDetector):
    """
    Shaped like a real adapter (accepts model_path in __init__, per the interface
    contract) — used to test that the registry correctly instantiates a configured
    dotted-path class rather than falling back to the scaffold stub.
    """

    def __init__(self, model_path: str = "") -> None:
        self.model_path = model_path

    def detect(self, image: bytes) -> YoloDetectionResult:
        return MockYoloDetector().detect(image)
