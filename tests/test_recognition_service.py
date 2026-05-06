import os
import pathlib
import sys
import types
import unittest

os.environ.setdefault("JWT_SECRET", "test-secret")

# Prevent app/__init__.py side effects during unit tests.
if "app" not in sys.modules:
    app_package = types.ModuleType("app")
    app_package.__path__ = [str(pathlib.Path(__file__).resolve().parents[1] / "app")]
    sys.modules["app"] = app_package

from app.services.recognition_service import RecognitionService
from app.services.recognition_errors import (
    RecognitionUnavailable,
    LowConfidence,
    InvalidRecognitionResponse,
)


class _FakeAdapter:
    def __init__(self, payload=None, error: Exception | None = None):
        self.payload = payload
        self.error = error

    def recognize_image(self, image_data: bytes):
        if self.error is not None:
            raise self.error
        return self.payload


class RecognitionServiceTests(unittest.TestCase):
    def test_success_mapping_returns_recognition_result(self):
        adapter = _FakeAdapter(payload={
            "label": "cat",
            "confidence": 0.91,
            "alternatives": [{"label": "lynx", "confidence": 0.52}],
            "category_hint": "ANIMAL",
            "provider_raw": {"provider": "lisa"},
        })
        service = RecognitionService(adapter, minimum_confidence=0.90)

        result = service.recognize_image(b"image-bytes")

        self.assertEqual(result.label, "cat")
        self.assertEqual(result.confidence, 0.91)
        self.assertEqual(len(result.alternatives), 1)
        self.assertEqual(result.alternatives[0].label, "lynx")
        self.assertEqual(result.category_hint, "ANIMAL")

    def test_provider_failure_becomes_recognition_unavailable(self):
        adapter = _FakeAdapter(error=RuntimeError("timeout"))
        service = RecognitionService(adapter, minimum_confidence=0.90)

        with self.assertRaises(RecognitionUnavailable):
            service.recognize_image(b"image-bytes")

    def test_low_confidence_raises(self):
        adapter = _FakeAdapter(payload={
            "label": "cat",
            "confidence": 0.42,
            "alternatives": [],
            "category_hint": None,
        })
        service = RecognitionService(adapter, minimum_confidence=0.90)

        with self.assertRaises(LowConfidence):
            service.recognize_image(b"image-bytes")

    def test_confidence_equal_to_threshold_is_accepted(self):
        adapter = _FakeAdapter(payload={
            "label": "cat",
            "confidence": 0.90,
            "alternatives": [],
            "category_hint": "ANIMAL",
        })
        service = RecognitionService(adapter, minimum_confidence=0.90)

        result = service.recognize_image(b"image-bytes")
        self.assertEqual(result.label, "cat")
        self.assertEqual(result.confidence, 0.90)

    def test_malformed_provider_response_raises_invalid_response(self):
        adapter = _FakeAdapter(payload={
            "confidence": 0.88,
            "alternatives": [],
        })
        service = RecognitionService(adapter, minimum_confidence=0.90)

        with self.assertRaises(InvalidRecognitionResponse):
            service.recognize_image(b"image-bytes")


if __name__ == "__main__":
    unittest.main()
