import pathlib
import sys
import types
import unittest

# Prevent app/__init__.py side effects during unit tests.
if "app" not in sys.modules:
    app_package = types.ModuleType("app")
    app_package.__path__ = [str(pathlib.Path(__file__).resolve().parents[1] / "app")]
    sys.modules["app"] = app_package

from app.services.category_errors import InvalidCategoryAssignmentResponse
from app.services.category_service import CategoryService


class _FakeCategoryAdapter:
    def __init__(self, payload=None, error: Exception | None = None):
        self.payload = payload
        self.error = error
        self.prompt = None

    def assign_category(self, prompt: str):
        self.prompt = prompt
        if self.error is not None:
            raise self.error
        return self.payload


class CategoryServiceTests(unittest.TestCase):
    def test_ai_assignment_returns_selected_category_above_threshold(self):
        adapter = _FakeCategoryAdapter(
            {
                "selected_category": "Tiere",
                "confidence": 0.91,
                "scores": {
                    "Pflanze": 0.01,
                    "Insekten": 0.02,
                    "Tiere": 0.91,
                    "Nahrung": 0.0,
                    "Unbekannt": 0.0,
                    "Technik": 0.0,
                    "Mechanik": 0.0,
                    "Gestein": 0.0,
                    "Gegenstände": 0.06,
                },
            }
        )
        service = CategoryService(adapter, minimum_confidence=0.60)

        result = service.assign_category(label="cat", category_hint="animal", wiki_text="A domestic cat.")

        self.assertEqual(result.category, "Tiere")
        self.assertEqual(result.confidence, 0.91)
        self.assertTrue(result.generated_by_ai)
        self.assertIn("Allowed categories", adapter.prompt)

    def test_ai_assignment_below_threshold_returns_unknown(self):
        service = CategoryService(
            _FakeCategoryAdapter(
                {
                    "selected_category": "Tiere",
                    "confidence": 0.42,
                    "scores": {"Tiere": 0.42, "Gegenstände": 0.30},
                }
            ),
            minimum_confidence=0.60,
        )

        result = service.assign_category(label="cat", category_hint="animal", wiki_text="A domestic cat.")

        self.assertEqual(result.category, "Unbekannt")
        self.assertEqual(result.confidence, 0.42)
        self.assertTrue(result.generated_by_ai)

    def test_invalid_ai_response_falls_back_to_hint_mapping(self):
        service = CategoryService(
            _FakeCategoryAdapter(error=InvalidCategoryAssignmentResponse("bad payload")),
            minimum_confidence=0.60,
        )

        result = service.assign_category(label="cat", category_hint="animal", wiki_text="")

        self.assertEqual(result.category, "Tiere")
        self.assertFalse(result.generated_by_ai)

    def test_without_adapter_uses_unknown_when_no_hint_matches(self):
        service = CategoryService(None, minimum_confidence=0.60)

        result = service.assign_category(label="ambiguous thing", category_hint=None, wiki_text="")

        self.assertEqual(result.category, "Unbekannt")
        self.assertEqual(result.confidence, 0.0)
        self.assertFalse(result.generated_by_ai)

    def test_unsupported_provider_category_falls_back_to_unknown(self):
        service = CategoryService(
            _FakeCategoryAdapter({"selected_category": "Furniture", "confidence": 0.9}),
            minimum_confidence=0.60,
        )

        result = service.assign_category(label="chair", category_hint=None, wiki_text="")

        self.assertEqual(result.category, "Unbekannt")
        self.assertFalse(result.generated_by_ai)


if __name__ == "__main__":
    unittest.main()

