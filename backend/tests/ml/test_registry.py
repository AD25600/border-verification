import pytest

from app.ml import registry


@pytest.fixture(autouse=True)
def _clear_registry_cache():
    registry.reset_registry_cache()
    yield
    registry.reset_registry_cache()


def test_unconfigured_adapters_resolve_to_scaffold_stubs():
    """
    With no *_ADAPTER_CLASS settings configured (the default), the registry must
    return the scaffold stub adapters — never None, and never something that
    silently fabricates a result.
    """
    yolo = registry.get_yolo_detector()
    ocr = registry.get_ocr_engine()
    mrz = registry.get_mrz_parser()
    tampering = registry.get_tampering_detector()
    risk = registry.get_risk_classifier()

    assert yolo is not None
    assert ocr is not None
    assert mrz is not None
    assert tampering is not None
    assert risk is not None


def test_unconfigured_yolo_stub_raises_not_implemented_when_called():
    yolo = registry.get_yolo_detector()
    with pytest.raises(NotImplementedError):
        yolo.detect(b"fake-bytes")


def test_registry_resolves_configured_class_by_dotted_path(monkeypatch):
    """
    Simulates a teammate having wired up a real adapter: settings.YOLO_ADAPTER_CLASS
    pointed at a concrete class should make the registry instantiate THAT class,
    not the scaffold stub.
    """
    from app.core.config import settings

    monkeypatch.setattr(settings, "YOLO_ADAPTER_CLASS", "tests.ml.mock_adapters.ConfigurableMockYoloDetector")
    registry.reset_registry_cache()

    yolo = registry.get_yolo_detector()
    result = yolo.detect(b"fake-bytes")
    assert result.document_type == "passport"
