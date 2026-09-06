import io

from app.api.v1.verification import get_pipeline_service
from app.main import app
from app.schemas.verification import PipelineStageStatus
from app.services.verification_pipeline_service import VerificationPipelineService

from tests.ml.mock_adapters import (
    MockMRZParser,
    MockOCREngine,
    MockRiskClassifier,
    MockTamperingDetector,
    MockYoloDetector,
)


def _register_and_login_officer(client, email="verification.officer@demo.example"):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Verification Officer",
            "password": "TestPass@123",
            "role_name": "OFFICER",
        },
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "TestPass@123"})
    return login.json()["access_token"]


def _override_pipeline_with_mocks():
    def _mock_pipeline_service() -> VerificationPipelineService:
        return VerificationPipelineService(
            yolo_detector=MockYoloDetector(),
            ocr_engine=MockOCREngine(),
            mrz_parser=MockMRZParser(),
            tampering_detector=MockTamperingDetector(),
            risk_classifier=MockRiskClassifier(),
        )

    app.dependency_overrides[get_pipeline_service] = _mock_pipeline_service


def test_analyze_requires_authentication(client):
    files = {"file": ("passport.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")}
    response = client.post("/api/v1/verification/analyze", files=files)
    assert response.status_code == 401


def test_analyze_returns_structured_result_with_mocked_pipeline(client):
    token = _register_and_login_officer(client)
    _override_pipeline_with_mocks()
    try:
        files = {"file": ("passport.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")}
        response = client.post(
            "/api/v1/verification/analyze",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["overall_status"] == PipelineStageStatus.SUCCESS.value
        assert body["document_type"] == "passport"
        assert body["mrz_validated"] is True
        assert body["risk_score"] == 15.0
        assert body["risk_level"] == "low"
        assert len(body["ocr_fields"]) == 2
        assert body["detection"]["status"] == "success"
    finally:
        app.dependency_overrides.pop(get_pipeline_service, None)


def test_analyze_rejects_unsupported_file_type(client):
    token = _register_and_login_officer(client, email="verification.officer2@demo.example")
    _override_pipeline_with_mocks()
    try:
        files = {"file": ("passport.txt", io.BytesIO(b"not an image"), "text/plain")}
        response = client.post(
            "/api/v1/verification/analyze",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
        assert response.json()["code"] == "validation_error"
    finally:
        app.dependency_overrides.pop(get_pipeline_service, None)


def test_analyze_with_no_adapters_configured_reports_not_configured_never_fakes_success(client):
    """
    With no *_ADAPTER_CLASS env vars set (the default, out-of-the-box state before
    any teammate has wired in their model), hitting the real endpoint must report
    every stage as not_configured — it must NEVER return overall_status=success.
    """
    token = _register_and_login_officer(client, email="verification.officer4@demo.example")
    files = {"file": ("passport.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")}
    response = client.post(
        "/api/v1/verification/analyze",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["overall_status"] != PipelineStageStatus.SUCCESS.value
    assert body["detection"]["status"] == "not_configured"
    assert body["risk_score"] is None


def test_analyze_rejects_empty_file(client):
    token = _register_and_login_officer(client, email="verification.officer5@demo.example")
    _override_pipeline_with_mocks()
    try:
        files = {"file": ("passport.jpg", io.BytesIO(b""), "image/jpeg")}
        response = client.post(
            "/api/v1/verification/analyze",
            files=files,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_pipeline_service, None)
