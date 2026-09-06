"""
TEAM MEMBER 1 (YOLO — document/field detection): implement your model here.

1. Load your trained YOLO weights in __init__ (use `model_path`, sourced from the
   YOLO_MODEL_PATH setting — do not hard-code a path).
2. Implement `detect()` to run inference and return a YoloDetectionResult (see
   app/schemas/verification.py for the exact fields).
3. Point YOLO_ADAPTER_CLASS in .env at this class's dotted path:
     YOLO_ADAPTER_CLASS=app.ml.adapters.yolo_adapter.YoloDetectorAdapter
     YOLO_MODEL_PATH=/path/to/your/weights.pt

Do not remove the `NotImplementedError` until real inference is wired in — the
orchestrator relies on it to surface an honest "not configured yet" error instead
of a fabricated result.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.ml.interfaces import BaseYoloDetector
from app.schemas.verification import YoloDetectionResult

logger = get_logger(__name__)


class YoloDetectorAdapter(BaseYoloDetector):
    def __init__(self, model_path: str) -> None:
        self.model_path = model_path
        # TODO(team-member-1): load your YOLO model weights here, e.g.:
        #     from ultralytics import YOLO
        #     self._model = YOLO(model_path)
        logger.info("YoloDetectorAdapter initialized with model_path=%s (not yet implemented)", model_path)

    def detect(self, image: bytes) -> YoloDetectionResult:
        # TODO(team-member-1): run inference on `image` (raw bytes) and map your
        # model's output onto YoloDetectionResult, e.g.:
        #     results = self._model.predict(...)
        #     regions = [BoundingBox(x_min=..., y_min=..., x_max=..., y_max=...,
        #                             label=..., confidence=...) for box in results]
        #     return YoloDetectionResult(document_type=..., regions=regions)
        raise NotImplementedError(
            "YoloDetectorAdapter.detect() is a scaffold stub — implement real YOLO "
            "inference before this adapter is used in production."
        )
