"""
Adapter registry: resolves each pipeline stage's concrete implementation from
configuration, so the orchestrator and API layer never hard-code which class to use.

Each `get_*` function is cached (module-level singleton per adapter) since model
loading is expensive and adapters are expected to be stateless/thread-safe after
construction — this matches the "load in __init__, not per-call" contract in
app/ml/interfaces.py.

If a `*_ADAPTER_CLASS` setting is left blank, the corresponding scaffold stub
(app/ml/adapters/*) is used instead. Calling a stub's method raises
NotImplementedError, which the orchestrator translates into a clear
MLComponentNotConfiguredError — never a fabricated result.
"""

from __future__ import annotations

import importlib
from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger
from app.ml.adapters.mrz_adapter import MRZParserAdapter
from app.ml.adapters.ocr_adapter import PaddleOCRAdapter
from app.ml.adapters.tampering_adapter import TamperingDetectorAdapter
from app.ml.adapters.xgboost_adapter import XGBoostRiskAdapter
from app.ml.adapters.yolo_adapter import YoloDetectorAdapter
from app.ml.interfaces import (
    BaseMRZParser,
    BaseOCREngine,
    BaseRiskClassifier,
    BaseTamperingDetector,
    BaseYoloDetector,
)

logger = get_logger(__name__)


def _resolve_class(dotted_path: str):
    module_path, _, class_name = dotted_path.rpartition(".")
    if not module_path:
        raise ValueError(f"'{dotted_path}' is not a valid dotted class path.")
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


@lru_cache
def get_yolo_detector() -> BaseYoloDetector:
    if settings.YOLO_ADAPTER_CLASS:
        cls = _resolve_class(settings.YOLO_ADAPTER_CLASS)
        logger.info("Using configured YOLO adapter: %s", settings.YOLO_ADAPTER_CLASS)
        return cls(model_path=settings.YOLO_MODEL_PATH)
    logger.warning("YOLO_ADAPTER_CLASS not set — using unimplemented scaffold stub.")
    return YoloDetectorAdapter(model_path=settings.YOLO_MODEL_PATH)


@lru_cache
def get_ocr_engine() -> BaseOCREngine:
    if settings.OCR_ADAPTER_CLASS:
        cls = _resolve_class(settings.OCR_ADAPTER_CLASS)
        logger.info("Using configured OCR adapter: %s", settings.OCR_ADAPTER_CLASS)
        return cls(model_path=settings.OCR_MODEL_PATH)
    logger.warning("OCR_ADAPTER_CLASS not set — using unimplemented scaffold stub.")
    return PaddleOCRAdapter(model_path=settings.OCR_MODEL_PATH)


@lru_cache
def get_mrz_parser() -> BaseMRZParser:
    if settings.MRZ_ADAPTER_CLASS:
        cls = _resolve_class(settings.MRZ_ADAPTER_CLASS)
        logger.info("Using configured MRZ adapter: %s", settings.MRZ_ADAPTER_CLASS)
        return cls()
    logger.warning("MRZ_ADAPTER_CLASS not set — using unimplemented scaffold stub.")
    return MRZParserAdapter()


@lru_cache
def get_tampering_detector() -> BaseTamperingDetector:
    if settings.TAMPERING_ADAPTER_CLASS:
        cls = _resolve_class(settings.TAMPERING_ADAPTER_CLASS)
        logger.info("Using configured tampering adapter: %s", settings.TAMPERING_ADAPTER_CLASS)
        return cls(model_path=settings.TAMPERING_MODEL_PATH)
    logger.warning("TAMPERING_ADAPTER_CLASS not set — using unimplemented scaffold stub.")
    return TamperingDetectorAdapter(model_path=settings.TAMPERING_MODEL_PATH)


@lru_cache
def get_risk_classifier() -> BaseRiskClassifier:
    if settings.RISK_ADAPTER_CLASS:
        cls = _resolve_class(settings.RISK_ADAPTER_CLASS)
        logger.info("Using configured risk adapter: %s", settings.RISK_ADAPTER_CLASS)
        return cls(model_path=settings.RISK_MODEL_PATH)
    logger.warning("RISK_ADAPTER_CLASS not set — using unimplemented scaffold stub.")
    return XGBoostRiskAdapter(model_path=settings.RISK_MODEL_PATH)


def reset_registry_cache() -> None:
    """Test-only helper: clears cached adapter singletons between tests."""
    get_yolo_detector.cache_clear()
    get_ocr_engine.cache_clear()
    get_mrz_parser.cache_clear()
    get_tampering_detector.cache_clear()
    get_risk_classifier.cache_clear()
