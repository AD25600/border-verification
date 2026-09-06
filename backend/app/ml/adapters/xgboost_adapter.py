"""
TEAM MEMBER 5 (XGBoost — final verification/risk classification): implement here.

1. Train and export your XGBoost model (e.g. `booster.save_model("risk_model.json")`).
2. Load it in __init__ (use `model_path`, sourced from RISK_MODEL_PATH).
3. Implement `predict()`: accept the flat feature dict the orchestrator assembles
   (see VerificationPipelineService._build_feature_vector for exactly which keys
   you'll receive and their types — it includes MRZ checksum results, OCR field
   confidences, and the tampering anomaly score), run inference, and return a
   RiskResult with an itemized, weighted `factors` breakdown. The architecture
   explicitly requires an explainable score — never return just a bare number.
4. Point RISK_ADAPTER_CLASS in .env at this class:
     RISK_ADAPTER_CLASS=app.ml.adapters.xgboost_adapter.XGBoostRiskAdapter
     RISK_MODEL_PATH=/path/to/your/risk_model.json
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.ml.interfaces import BaseRiskClassifier
from app.schemas.verification import RiskResult

logger = get_logger(__name__)


class XGBoostRiskAdapter(BaseRiskClassifier):
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        # TODO(team-member-5): load your trained XGBoost model here, e.g.:
        #     import xgboost as xgb
        #     self._booster = xgb.Booster()
        #     self._booster.load_model(model_path)
        logger.info("XGBoostRiskAdapter initialized with model_path=%s (not yet implemented)", model_path)

    def predict(self, features: dict) -> RiskResult:
        # TODO(team-member-5): run inference on `features` and map the result onto
        # RiskResult, including an itemized `factors` breakdown, e.g.:
        #     dmatrix = xgb.DMatrix([list(features.values())])
        #     score = float(self._booster.predict(dmatrix)[0])
        #     factors = [RiskFactor(factor_name=..., contribution=..., description=...)]
        #     return RiskResult(risk_score=score, risk_level=..., factors=factors)
        raise NotImplementedError(
            "XGBoostRiskAdapter.predict() is a scaffold stub — implement real "
            "inference before this adapter is used in production."
        )
