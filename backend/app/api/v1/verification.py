from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_current_user
from app.core.logging import get_logger
from app.ml.registry import (
    get_mrz_parser,
    get_ocr_engine,
    get_risk_classifier,
    get_tampering_detector,
    get_yolo_detector,
)
from app.models.user import User
from app.schemas.verification import VerificationResponse
from app.services.document_service import DocumentService
from app.services.verification_pipeline_service import VerificationPipelineService

router = APIRouter(prefix="/verification", tags=["verification"])
logger = get_logger(__name__)


def get_pipeline_service() -> VerificationPipelineService:
    """
    Constructs the orchestrator with adapters resolved from the registry. Each
    adapter is either a teammate's real implementation (if configured) or the
    unimplemented scaffold stub — either way, the orchestrator and this endpoint
    are written identically and don't need to know which.
    """
    return VerificationPipelineService(
        yolo_detector=get_yolo_detector(),
        ocr_engine=get_ocr_engine(),
        mrz_parser=get_mrz_parser(),
        tampering_detector=get_tampering_detector(),
        risk_classifier=get_risk_classifier(),
    )


@router.post("/analyze", response_model=VerificationResponse)
async def analyze_document(
    file: UploadFile = File(..., description="Document image (jpg/jpeg/png) or PDF page."),
    current_user: User = Depends(get_current_user),
    pipeline: VerificationPipelineService = Depends(get_pipeline_service),
) -> VerificationResponse:
    """
    Runs the full verification pipeline on an uploaded document image and returns
    a structured, stage-by-stage result. Any individual stage that is not yet
    configured or that fails is reported clearly in that stage's result — it never
    silently resolves to a "verified" outcome. The officer reviewing the response
    always makes the final call; this endpoint only ever produces evidence.
    """
    document_service = DocumentService()
    contents = await document_service.read_and_validate(file)

    session_id = str(uuid.uuid4())
    logger.info(
        "Verification requested by user_id=%s filename=%s session_id=%s",
        current_user.id,
        file.filename,
        session_id,
    )

    return pipeline.run(image=contents, session_id=session_id)
