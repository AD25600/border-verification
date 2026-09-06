"""
TEAM MEMBER 4 (Tampering Detection — document manipulation detection): implement here.

1. Load your trained tampering-classifier weights in __init__ (use `model_path`,
   sourced from TAMPERING_MODEL_PATH).
2. Implement `predict()` to run inference and return a TamperingResult — an overall
   anomaly score plus a list of named, independently-explainable indicators. Do
   NOT collapse this into a single boolean; the officer-facing UI shows each
   indicator individually per the architecture's explainability requirement.
3. Point TAMPERING_ADAPTER_CLASS in .env at this class:
     TAMPERING_ADAPTER_CLASS=app.ml.adapters.tampering_adapter.TamperingDetectorAdapter
     TAMPERING_MODEL_PATH=/path/to/your/weights
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.ml.interfaces import BaseTamperingDetector
from app.schemas.verification import TamperingResult

logger = get_logger(__name__)


class TamperingDetectorAdapter(BaseTamperingDetector):
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        # TODO(team-member-4): load your tampering-detection model here.
        logger.info("TamperingDetectorAdapter initialized with model_path=%s (not yet implemented)", model_path)

    def predict(self, image: bytes) -> TamperingResult:
        # TODO(team-member-4): run inference on `image` and map results onto
        # TamperingResult, e.g.:
        #     score, indicator_map = self._model.analyze(image)
        #     indicators = [TamperingIndicator(indicator=name, score=s)
        #                   for name, s in indicator_map.items()]
        #     return TamperingResult(anomaly_score=score, indicators=indicators)
        raise NotImplementedError(
            "TamperingDetectorAdapter.predict() is a scaffold stub — implement real "
            "tampering-detection inference before this adapter is used in production."
        )
