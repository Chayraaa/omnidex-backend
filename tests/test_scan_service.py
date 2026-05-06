import pathlib
import sys
import types
import unittest

# Prevent app/__init__.py side effects during unit tests.
if "app" not in sys.modules:
    app_package = types.ModuleType("app")
    app_package.__path__ = [str(pathlib.Path(__file__).resolve().parents[1] / "app")]
    sys.modules["app"] = app_package

from app.domain_models.recognition_result import RecognitionResult, RecognitionAlternative
from app.services.recognition_errors import LowConfidence, RecognitionUnavailable
from app.services.scan_errors import ScanInputInvalid, ScanRecognitionFailed
from app.services.scan_service import ScanService


class _FakeRecognitionService:
    def __init__(self, result=None, error: Exception | None = None):
        self.result = result
        self.error = error
        self.called_with = None

    def recognize_image(self, image_data: bytes):
        self.called_with = image_data
        if self.error is not None:
            raise self.error
        return self.result


class _FakeWikiService:
    def __init__(self, summary: str | None = None, error: Exception | None = None):
        self.summary = summary
        self.error = error
        self.called_with = None

    def get_summary(self, article_title: str) -> str:
        self.called_with = article_title
        if self.error is not None:
            raise self.error
        return self.summary


class ScanServiceTests(unittest.TestCase):
    def test_successful_scan_orchestration(self):
        recognition = RecognitionResult(
            label="cat",
            confidence=0.97,
            alternatives=[RecognitionAlternative(label="lynx", confidence=0.33)],
            category_hint="ANIMAL",
            provider_raw={"provider": "lisa"},
        )
        recognition_service = _FakeRecognitionService(result=recognition)
        wiki_service = _FakeWikiService(summary="The cat is a domestic species of small carnivorous mammal.")
        service = ScanService(recognition_service, wiki_service)

        result = service.create_scan(42, b"image-bytes")
        payload = result.to_dict()

        self.assertEqual(recognition_service.called_with, b"image-bytes")
        self.assertEqual(wiki_service.called_with, "cat")
        self.assertEqual(payload["label"], "cat")
        self.assertEqual(payload["confidence"], 0.97)
        self.assertEqual(payload["category_hint"], "ANIMAL")
        self.assertEqual(payload["description"], "The cat is a domestic species of small carnivorous mammal.")
        self.assertTrue(payload["knowledge_enriched"])
        self.assertNotIn("provider_raw", payload)

    def test_low_confidence_is_exposed_as_scan_recognition_failed(self):
        recognition_service = _FakeRecognitionService(
            error=LowConfidence("cat", 0.45, 0.90)
        )
        service = ScanService(recognition_service, _FakeWikiService(summary="unused"))

        with self.assertRaises(ScanRecognitionFailed) as ctx:
            service.create_scan(42, b"image-bytes")

        self.assertEqual(ctx.exception.reason, "low_confidence")
        self.assertEqual(ctx.exception.label, "cat")
        self.assertEqual(ctx.exception.confidence, 0.45)
        self.assertEqual(ctx.exception.minimum_confidence, 0.90)

    def test_knowledge_failure_degrades_gracefully(self):
        recognition = RecognitionResult(
            label="cat",
            confidence=0.97,
            alternatives=[],
            category_hint=None,
            provider_raw={"provider": "lisa"},
        )
        service = ScanService(
            _FakeRecognitionService(result=recognition),
            _FakeWikiService(error=RuntimeError("network error")),
        )

        result = service.create_scan(42, b"image-bytes")
        payload = result.to_dict()

        self.assertEqual(payload["description"], "No additional information available.")
        self.assertFalse(payload["knowledge_enriched"])
        self.assertIsNone(payload["source_url"])

    def test_invalid_image_input_raises_scan_input_invalid(self):
        recognition = RecognitionResult(
            label="cat",
            confidence=0.97,
            alternatives=[],
            category_hint=None,
            provider_raw={"provider": "lisa"},
        )
        service = ScanService(_FakeRecognitionService(result=recognition), _FakeWikiService(summary="ok"))

        with self.assertRaises(ScanInputInvalid):
            service.create_scan(42, b"")

    def test_recognition_unavailable_becomes_scan_recognition_failed(self):
        service = ScanService(
            _FakeRecognitionService(error=RecognitionUnavailable("down")),
            _FakeWikiService(summary="unused"),
        )

        with self.assertRaises(ScanRecognitionFailed) as ctx:
            service.create_scan(42, b"image-bytes")

        self.assertEqual(ctx.exception.reason, "recognition_unavailable")


if __name__ == "__main__":
    unittest.main()
