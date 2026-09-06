"""
XGBoost final verification / risk classification adapter.

Wraps the trained XGBoost booster (models/risk_model.json) behind the
BaseRiskClassifier interface. Feature keys/types here match EXACTLY what
VerificationPipelineService._build_feature_vector produces:

    document_type_confidence     float | None   [0,1]
    ocr_average_confidence       float | None   [0,1]
    ocr_field_count               int
    mrz_all_checksums_valid      bool  | None
    mrz_checksum_failure_count    int  | None
    tampering_anomaly_score      float | None   [0,1]  (0=clean, 1=tampered)
    tampering_indicator_count     int

Any of the nullable fields being None means that upstream stage was SKIPPED,
FAILED, or NOT_CONFIGURED. Per the architecture's "AI failure must never
silently resolve to verified" rule, missing values are imputed fail-closed
(toward higher risk), never toward a value that would make the document
look safer than an incomplete pipeline run actually justifies. See
models/imputation_stats.json for the current median values used for the
non-security-critical continuous fields.

risk_score is reported on a 0-100 scale per RiskResult's contract (the
underlying model outputs a 0-1 probability; this adapter multiplies by 100).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import xgboost as xgb

from app.core.logging import get_logger
from app.ml.interfaces import BaseRiskClassifier
from app.schemas.verification import RiskFactor, RiskLevel, RiskResult

logger = get_logger(__name__)

FEATURE_ORDER = [
    "document_type_confidence",
    "ocr_average_confidence",
    "ocr_field_count",
    "mrz_all_checksums_valid",
    "mrz_checksum_failure_count",
    "tampering_anomaly_score",
    "tampering_indicator_count",
]

# Missing-value policy — fail-closed for anything security relevant.
_FAIL_CLOSED_ZERO = {"mrz_all_checksums_valid"}                              # missing -> "not all valid"
_FAIL_CLOSED_HIGH = {"tampering_anomaly_score"}                              # missing -> max risk (1.0)
_FAIL_CLOSED_FAILURE_COUNT_DEFAULT = 3                                       # missing -> assume several checksum failures
_MEDIAN_IMPUTE = {"document_type_confidence", "ocr_average_confidence", "ocr_field_count", "tampering_indicator_count"}


class XGBoostRiskAdapter(BaseRiskClassifier):
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        self._booster = xgb.XGBClassifier()
        self._booster.load_model(model_path)

        imputer_path = Path(model_path).parent / "imputation_stats.json"
        if not imputer_path.exists():
            raise FileNotFoundError(
                f"Imputation stats file not found at {imputer_path}. "
                "This file is produced by training alongside the model and must ship with it."
            )
        self._medians: dict[str, float] = json.loads(imputer_path.read_text())

        logger.info("XGBoostRiskAdapter loaded model from %s", model_path)

    def predict(self, features: dict) -> RiskResult:
        row = self._impute(features)
        X = [[row[c] for c in FEATURE_ORDER]]

        proba_verified = float(self._booster.predict_proba(X)[0, 1])
        risk_score_0_100 = round((1.0 - proba_verified) * 100, 2)
        risk_level = self._risk_level(risk_score_0_100)

        factors = self._explain(features, row, risk_score_0_100)

        return RiskResult(
            risk_score=risk_score_0_100,
            risk_level=risk_level,
            factors=factors,
            model_confidence=round(max(proba_verified, 1 - proba_verified), 4),
        )

    # ── internal helpers ────────────────────────────────────────────────────

    def _impute(self, features: dict) -> dict[str, Any]:
        row: dict[str, Any] = {}

        mrz_valid = features.get("mrz_all_checksums_valid")
        row["mrz_all_checksums_valid"] = 1 if mrz_valid is True else 0  # None or False -> 0 (fail-closed)

        failure_count = features.get("mrz_checksum_failure_count")
        row["mrz_checksum_failure_count"] = (
            _FAIL_CLOSED_FAILURE_COUNT_DEFAULT if failure_count is None else failure_count
        )

        tampering = features.get("tampering_anomaly_score")
        row["tampering_anomaly_score"] = 1.0 if tampering is None else tampering

        for col in _MEDIAN_IMPUTE:
            val = features.get(col)
            row[col] = self._medians.get(col, 0.0) if val is None else val

        return row

    @staticmethod
    def _risk_level(score_0_100: float) -> RiskLevel:
        if score_0_100 < 15:
            return RiskLevel.LOW
        if score_0_100 < 40:
            return RiskLevel.MEDIUM
        if score_0_100 < 70:
            return RiskLevel.HIGH
        return RiskLevel.CRITICAL

    def _explain(self, raw_features: dict, imputed_row: dict, risk_score: float) -> list[RiskFactor]:
        """Itemized, human-readable breakdown — required by the architecture
        (never return a bare score). Uses simple, transparent rules aligned
        with what actually drives risk, rather than trying to decompose the
        boosted trees' internal math per-prediction."""
        factors: list[RiskFactor] = []

        if raw_features.get("mrz_all_checksums_valid") is None:
            factors.append(RiskFactor(
                factor_name="mrz_stage_unavailable",
                contribution=15.0,
                description="MRZ validation did not run (no MRZ zone detected or stage failed); treated as unverified.",
            ))
        elif not raw_features.get("mrz_all_checksums_valid"):
            fail_count = imputed_row["mrz_checksum_failure_count"]
            factors.append(RiskFactor(
                factor_name="mrz_checksum_mismatch",
                contribution=min(40.0, 10.0 * fail_count),
                description=f"{fail_count} MRZ checksum field(s) failed validation.",
            ))

        tampering = raw_features.get("tampering_anomaly_score")
        if tampering is None:
            factors.append(RiskFactor(
                factor_name="tampering_stage_unavailable",
                contribution=10.0,
                description="Tampering detection did not run; treated as elevated risk.",
            ))
        elif tampering > 0.3:
            factors.append(RiskFactor(
                factor_name="tampering_anomaly_detected",
                contribution=round(tampering * 40, 2),
                description=f"Tampering model anomaly score {tampering:.2f} (0=clean, 1=tampered).",
            ))

        ocr_conf = raw_features.get("ocr_average_confidence")
        if ocr_conf is not None and ocr_conf < 0.75:
            factors.append(RiskFactor(
                factor_name="low_ocr_confidence",
                contribution=round((0.75 - ocr_conf) * 30, 2),
                description=f"Average OCR confidence {ocr_conf:.2f} is below the reliable-read threshold.",
            ))

        doc_conf = raw_features.get("document_type_confidence")
        if doc_conf is not None and doc_conf < 0.7:
            factors.append(RiskFactor(
                factor_name="low_document_detection_confidence",
                contribution=round((0.7 - doc_conf) * 20, 2),
                description=f"Document type detection confidence {doc_conf:.2f} is low.",
            ))

        if not factors:
            factors.append(RiskFactor(
                factor_name="no_significant_risk_indicators",
                contribution=0.0,
                description="All available checks passed within normal thresholds.",
            ))

        return factors
