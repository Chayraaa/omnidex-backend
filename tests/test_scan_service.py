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
from app.services.summary_errors import SummaryUnavailable, InvalidSummaryResponse


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


class _FakeSummaryService:
    def __init__(self, summary: str | None = None, error: Exception | None = None):
        self.summary = summary
        self.error = error
        self.called_with = None

    def summarize_object_info(self, label: str, wiki_text: str) -> str:
        self.called_with = (label, wiki_text)
        if self.error is not None:
            raise self.error
        return self.summary


class _FakeImageStorage:
    def __init__(self):
        self.saved = []

    def save_image(self, key: str, image_data):
        self.saved.append(key)
        return key


class _FakeCardRepo:
    def __init__(self):
        self.created = []
        self.existing_names = set()
        self.next_id = 1

    def create_card(
        self,
        *,
        user_id: int,
        name: str,
        image_key: str,
        card_summary: str | None,
        category: str | None = None,
        confidence: float | None = None,
        description: str | None = None,
        source_title: str | None = None,
        source_url: str | None = None,
        alternatives_json: str | None = None,
    ) -> tuple[int, str | None]:
        card_id = self.next_id
        self.next_id += 1
        self.created.append(
            {
                "id": card_id,
                "user_id": user_id,
                "name": name,
                "image_key": image_key,
                "card_summary": card_summary,
                "category": category,
                "confidence": confidence,
                "description": description,
                "source_title": source_title,
                "source_url": source_url,
                "alternatives_json": alternatives_json,
            }
        )
        self.existing_names.add(name)
        return card_id, "2026-01-01T00:00:00"

    def card_name_exists(self, *, user_id: int, name: str) -> bool:
        return name in self.existing_names


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
        summary_service = _FakeSummaryService(summary="A small domesticated carnivorous mammal.")
        service = ScanService(
            recognition_service,
            wiki_service,
            summary_service,
            _FakeImageStorage(),
            _FakeCardRepo(),
            base_url="http://127.0.0.1:5000",
        )

        result = service.create_scan(42, b"image-bytes")
        payload = result.to_dict()

        self.assertEqual(recognition_service.called_with, b"image-bytes")
        self.assertEqual(wiki_service.called_with, "cat")
        self.assertEqual(payload["label"], "cat")
        self.assertEqual(payload["confidence"], 0.97)
        self.assertEqual(payload["category_hint"], "ANIMAL")
        self.assertEqual(payload["description"], "The cat is a domestic species of small carnivorous mammal.")
        self.assertEqual(payload["card_summary"], "A small domesticated carnivorous mammal.")
        self.assertTrue(payload["summary_generated_by_ai"])
        self.assertTrue(payload["knowledge_enriched"])
        self.assertNotIn("provider_raw", payload)

    def test_low_confidence_is_exposed_as_scan_recognition_failed(self):
        recognition_service = _FakeRecognitionService(
            error=LowConfidence("cat", 0.45, 0.90)
        )
        service = ScanService(
            recognition_service,
            _FakeWikiService(summary="unused"),
            _FakeSummaryService(summary="ok"),
            _FakeImageStorage(),
            _FakeCardRepo(),
            base_url="http://127.0.0.1:5000",
        )

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
            _FakeSummaryService(error=SummaryUnavailable("down")),
            _FakeImageStorage(),
            _FakeCardRepo(),
            base_url="http://127.0.0.1:5000",
        )

        result = service.create_scan(42, b"image-bytes")
        payload = result.to_dict()

        self.assertEqual(payload["description"], "No additional information available.")
        self.assertEqual(payload["card_summary"], "No additional information available.")
        self.assertFalse(payload["summary_generated_by_ai"])
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
        service = ScanService(
            _FakeRecognitionService(result=recognition),
            _FakeWikiService(summary="ok"),
            _FakeSummaryService(summary="ok"),
            _FakeImageStorage(),
            _FakeCardRepo(),
            base_url="http://127.0.0.1:5000",
        )

        with self.assertRaises(ScanInputInvalid):
            service.create_scan(42, b"")

    def test_recognition_unavailable_becomes_scan_recognition_failed(self):
        service = ScanService(
            _FakeRecognitionService(error=RecognitionUnavailable("down")),
            _FakeWikiService(summary="unused"),
            _FakeSummaryService(summary="unused"),
            _FakeImageStorage(),
            _FakeCardRepo(),
            base_url="http://127.0.0.1:5000",
        )

        with self.assertRaises(ScanRecognitionFailed) as ctx:
            service.create_scan(42, b"image-bytes")

        self.assertEqual(ctx.exception.reason, "recognition_unavailable")

    def test_summary_failure_falls_back_to_wiki_text(self):
        recognition = RecognitionResult(
            label="cat",
            confidence=0.97,
            alternatives=[],
            category_hint=None,
            provider_raw={"provider": "lisa"},
        )
        wiki_text = (
            "Cats are small, typically furry carnivorous mammals. "
            "They are often called house cats when kept as indoor pets. "
            "They are valued by humans for companionship."
        )
        service = ScanService(
            _FakeRecognitionService(result=recognition),
            _FakeWikiService(summary=wiki_text),
            _FakeSummaryService(error=SummaryUnavailable("provider down")),
            _FakeImageStorage(),
            _FakeCardRepo(),
            base_url="http://127.0.0.1:5000",
        )

        payload = service.create_scan(42, b"image-bytes").to_dict()
        self.assertEqual(
            payload["card_summary"],
            "Cats are small, typically furry carnivorous mammals. They are often called house cats when kept as indoor pets.",
        )
        self.assertFalse(payload["summary_generated_by_ai"])

    def test_invalid_summary_response_falls_back(self):
        recognition = RecognitionResult(
            label="cat",
            confidence=0.97,
            alternatives=[],
            category_hint=None,
            provider_raw={"provider": "lisa"},
        )
        service = ScanService(
            _FakeRecognitionService(result=recognition),
            _FakeWikiService(summary="Cats are popular pets. They are agile and curious."),
            _FakeSummaryService(error=InvalidSummaryResponse("malformed")),
            _FakeImageStorage(),
            _FakeCardRepo(),
            base_url="http://127.0.0.1:5000",
        )

        payload = service.create_scan(42, b"image-bytes").to_dict()
        self.assertEqual(payload["card_summary"], "Cats are popular pets. They are agile and curious.")
        self.assertFalse(payload["summary_generated_by_ai"])

    def test_summary_is_trimmed_to_two_sentences(self):
        recognition = RecognitionResult(
            label="cat",
            confidence=0.97,
            alternatives=[],
            category_hint=None,
            provider_raw={"provider": "lisa"},
        )
        summary = "One sentence. Two sentence. Third sentence."
        service = ScanService(
            _FakeRecognitionService(result=recognition),
            _FakeWikiService(summary="Detailed description."),
            _FakeSummaryService(summary=summary),
            _FakeImageStorage(),
            _FakeCardRepo(),
            base_url="http://127.0.0.1:5000",
        )

        payload = service.create_scan(42, b"image-bytes").to_dict()
        self.assertEqual(payload["card_summary"], "One sentence. Two sentence.")
        self.assertTrue(payload["summary_generated_by_ai"])


if __name__ == "__main__":
    unittest.main()
