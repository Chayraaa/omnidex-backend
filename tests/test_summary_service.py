import pathlib
import sys
import types
import unittest

# Prevent app/__init__.py side effects during unit tests.
if "app" not in sys.modules:
    app_package = types.ModuleType("app")
    app_package.__path__ = [str(pathlib.Path(__file__).resolve().parents[1] / "app")]
    sys.modules["app"] = app_package

from app.services.summary_errors import InvalidSummaryResponse
from app.services.summary_service import SummaryService


class _FakeSummaryAdapter:
    def __init__(self, response: str | None = None):
        self.response = response
        self.last_prompt = None

    def summarize_text(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


class SummaryServiceTests(unittest.TestCase):
    def test_success_summary_and_prompt(self):
        adapter = _FakeSummaryAdapter(response="Sentence one. Sentence two. Sentence three.")
        service = SummaryService(adapter)

        result = service.summarize_object_info("cat", "Cats are mammals.")

        self.assertEqual(result, "Sentence one. Sentence two.")
        self.assertIn("über 'cat'", adapter.last_prompt)
        self.assertIn("auf Deutsch", adapter.last_prompt)
        self.assertIn("maximal zwei kurze Sätze", adapter.last_prompt)

    def test_empty_summary_raises_invalid_summary_response(self):
        adapter = _FakeSummaryAdapter(response="   ")
        service = SummaryService(adapter)

        with self.assertRaises(InvalidSummaryResponse):
            service.summarize_object_info("cat", "Cats are mammals.")

    def test_missing_label_raises_invalid_summary_response(self):
        adapter = _FakeSummaryAdapter(response="summary")
        service = SummaryService(adapter)

        with self.assertRaises(InvalidSummaryResponse):
            service.summarize_object_info("", "Cats are mammals.")


if __name__ == "__main__":
    unittest.main()
