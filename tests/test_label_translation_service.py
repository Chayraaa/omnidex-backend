import pathlib
import sys
import types
import unittest

# Prevent app/__init__.py side effects during unit tests.
if "app" not in sys.modules:
    app_package = types.ModuleType("app")
    app_package.__path__ = [str(pathlib.Path(__file__).resolve().parents[1] / "app")]
    sys.modules["app"] = app_package

from app.services.label_translation_errors import LabelTranslationUnavailable
from app.services.label_translation_service import LabelTranslationService


class _FakeLabelTranslationAdapter:
    def __init__(self, response: str | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.last_prompt = None

    def translate_label(self, prompt: str) -> str:
        self.last_prompt = prompt
        if self.error is not None:
            raise self.error
        return self.response


class LabelTranslationServiceTests(unittest.TestCase):
    def test_successful_translation_returns_clean_german_label(self):
        adapter = _FakeLabelTranslationAdapter(response="die Katze.")
        service = LabelTranslationService(adapter)

        result = service.translate_label_to_german("cat")

        self.assertEqual(result, "Katze")
        self.assertIn("Translate the following object label into German", adapter.last_prompt)
        self.assertIn("Label:\ncat", adapter.last_prompt)

    def test_json_like_response_is_supported(self):
        adapter = _FakeLabelTranslationAdapter(response='{"label": "Komodowaran"}')
        service = LabelTranslationService(adapter)

        self.assertEqual(service.translate_label_to_german("Komodo dragon"), "Komodowaran")

    def test_provider_failure_falls_back_to_original_label(self):
        adapter = _FakeLabelTranslationAdapter(error=LabelTranslationUnavailable("down"))
        service = LabelTranslationService(adapter)

        self.assertEqual(service.translate_label_to_german("cat"), "cat")

    def test_missing_adapter_falls_back_to_original_label(self):
        service = LabelTranslationService()

        self.assertEqual(service.translate_label_to_german("cat"), "cat")

    def test_missing_label_returns_unknown(self):
        service = LabelTranslationService(_FakeLabelTranslationAdapter(response="Katze"))

        self.assertEqual(service.translate_label_to_german("  "), "unknown")


if __name__ == "__main__":
    unittest.main()
