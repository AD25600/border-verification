"""
TEAM MEMBER 2 (PaddleOCR — text extraction): implement your model here.

1. Load PaddleOCR in __init__ (use `model_path` if you have custom weights;
   PaddleOCR's default pretrained models don't require a local path).
2. Implement `extract_text()` to run OCR and return an OCRResult.
3. Point OCR_ADAPTER_CLASS in .env at this class:
     OCR_ADAPTER_CLASS=app.ml.adapters.ocr_adapter.PaddleOCRAdapter
     OCR_MODEL_PATH=   (leave blank to use PaddleOCR's default pretrained models)

`regions`, if provided, are the bounding boxes YOLO already found — use them to
crop the image before running OCR for better accuracy, rather than OCR-ing the
whole document from scratch.
"""

from __future__ import annotations

from typing import Optional

from app.core.logging import get_logger
from app.ml.interfaces import BaseOCREngine
from app.schemas.verification import BoundingBox, OCRResult

logger = get_logger(__name__)


class PaddleOCRAdapter(BaseOCREngine):
    def __init__(self, model_path: str = "") -> None:
        self.model_path = model_path
        # TODO(team-member-2): initialize PaddleOCR here, e.g.:
        #     from paddleocr import PaddleOCR
        #     self._engine = PaddleOCR(use_angle_cls=True, lang="en")
        logger.info("PaddleOCRAdapter initialized (not yet implemented)")

    def extract_text(self, image: bytes, regions: Optional[list[BoundingBox]] = None) -> OCRResult:
        # TODO(team-member-2): run PaddleOCR on `image` (optionally cropped to
        # `regions`) and map results onto OCRResult.fields, e.g.:
        #     result = self._engine.ocr(image, cls=True)
        #     fields = [OCRField(field_name=..., value=..., confidence=...) ...]
        #     return OCRResult(fields=fields, raw_text=..., average_confidence=...)
        raise NotImplementedError(
            "PaddleOCRAdapter.extract_text() is a scaffold stub — implement real "
            "OCR inference before this adapter is used in production."
        )
