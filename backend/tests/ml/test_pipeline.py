from app.schemas.verification import PipelineStageStatus
from app.services.verification_pipeline_service import VerificationPipelineService

from .mock_adapters import (
    FailingYoloDetector,
    MockMRZParser,
    MockOCREngine,
    MockRiskClassifier,
    MockTamperingDetector,
    MockYoloDetector,
    UnconfiguredMRZParser,
)


def _build_pipeline(**overrides) -> VerificationPipelineService:
    defaults = dict(
        yolo_detector=MockYoloDetector(),
        ocr_engine=MockOCREngine(),
        mrz_parser=MockMRZParser(),
        tampering_detector=MockTamperingDetector(),
        risk_classifier=MockRiskClassifier(),
    )
    defaults.update(overrides)
    return VerificationPipelineService(**defaults)


def test_full_pipeline_success_with_all_mocks():
    pipeline = _build_pipeline()
    response = pipeline.run(image=b"fake-image-bytes", session_id="test-session-1")

    assert response.overall_status == PipelineStageStatus.SUCCESS
    assert response.detection.status == PipelineStageStatus.SUCCESS
    assert response.ocr.status == PipelineStageStatus.SUCCESS
    assert response.mrz.status == PipelineStageStatus.SUCCESS
    assert response.tampering.status == PipelineStageStatus.SUCCESS
    assert response.risk.status == PipelineStageStatus.SUCCESS

    assert response.document_type == "passport"
    assert response.mrz_validated is True
    assert response.risk_score == 15.0
    assert len(response.ocr_fields) == 2


def test_one_stage_failure_does_not_crash_pipeline():
    pipeline = _build_pipeline(yolo_detector=FailingYoloDetector())
    response = pipeline.run(image=b"fake-image-bytes", session_id="test-session-2")

    # The whole request still returns a structured response...
    assert response.overall_status == PipelineStageStatus.FAILED
    assert response.detection.status == PipelineStageStatus.FAILED
    assert "Simulated inference crash" in response.detection.error

    # ...and later stages still ran and produced evidence, since they don't
    # strictly require detection's regions to have SOME output (OCR/tampering
    # can still run on the raw image without cropped regions).
    assert response.tampering.status == PipelineStageStatus.SUCCESS
    assert response.risk.status == PipelineStageStatus.SUCCESS


def test_unconfigured_stage_is_reported_as_not_configured_not_faked():
    pipeline = _build_pipeline(mrz_parser=UnconfiguredMRZParser())
    response = pipeline.run(image=b"fake-image-bytes", session_id="test-session-3")

    assert response.mrz.status == PipelineStageStatus.NOT_CONFIGURED
    assert response.mrz.data is None
    assert response.mrz_validated is None
    # Overall status reflects that something in the pipeline isn't ready yet —
    # it must NOT be reported as SUCCESS just because other stages completed.
    assert response.overall_status == PipelineStageStatus.NOT_CONFIGURED


def test_mrz_stage_skipped_when_no_mrz_zone_detected():
    class NoMrzZoneYolo(MockYoloDetector):
        def detect(self, image: bytes):
            result = super().detect(image)
            result.regions = [r for r in result.regions if r.label != "mrz_zone"]
            return result

    pipeline = _build_pipeline(yolo_detector=NoMrzZoneYolo())
    response = pipeline.run(image=b"fake-image-bytes", session_id="test-session-4")

    assert response.mrz.status == PipelineStageStatus.SKIPPED
    assert response.overall_status == PipelineStageStatus.SKIPPED


def test_feature_vector_includes_expected_keys():
    pipeline = _build_pipeline()
    response = pipeline.run(image=b"fake-image-bytes", session_id="test-session-5")

    # Indirect check: risk stage succeeded, which means _build_feature_vector ran
    # without raising and the mock classifier received a usable dict.
    assert response.risk.status == PipelineStageStatus.SUCCESS
    assert response.risk.data.risk_score == 15.0
