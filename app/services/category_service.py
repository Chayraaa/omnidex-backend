import os
from typing import Any

from app.domain_models.category_assignment_result import CategoryAssignmentResult
from app.repositories.interfaces.external.category_assignment_adapter_protocol import (
    CategoryAssignmentAdapterProtocol,
)
from app.services.category_errors import (
    CategoryAssignmentError,
    InvalidCategoryAssignmentResponse,
)


class CategoryService:
    ALLOWED_CATEGORIES = (
        "pflanzen",
        "insekten",
        "tiere",
        "nahrung",
        "unbekannt",
        "technik",
        "mechanik",
        "gestein",
        "gegenstände",
    )
    UNKNOWN_CATEGORY = "unbekannt"
    HINT_MAPPING = {
        "plant": "Pflanze",
        "plants": "Pflanze",
        "nature": "Pflanze",
        "pflanze": "Pflanze",
        "insect": "Insekten",
        "bug": "Insekten",
        "käfer": "Insekten",
        "insects": "Insekten",
        "insekten": "Insekten",
        "animal": "Tiere",
        "animals": "Tiere",
        "tier": "Tiere",
        "tiere": "Tiere",
        "food": "Nahrung",
        "meal": "Nahrung",
        "nahrung": "Nahrung",
        "technology": "Technik",
        "tech": "Technik",
        "technik": "Technik",
        "mechanic": "Mechanik",
        "vehicle": "Mechanik",
        "fahrzeug": "Mechanik",
        "mechanical": "Mechanik",
        "machine": "Mechanik",
        "mechanik": "Mechanik",
        "rock": "Gestein",
        "gem": "Gestein",
        "stone": "Gestein",
        "ore": "Gestein",
        "mineral": "Gestein",
        "gestein": "Gestein",
        "object": "Gegenstände",
        "objects": "Gegenstände",
        "item": "Gegenstände",
        "gegenstand": "Gegenstände",
        "gegenstände": "Gegenstände",
        "unknown": "Unbekannt",
        "unbekannt": "Unbekannt",
    }

    def __init__(
        self,
        assignment_adapter: CategoryAssignmentAdapterProtocol | None = None,
        minimum_confidence: float | None = None,
    ):
        self.assignment_adapter = assignment_adapter
        threshold_raw = minimum_confidence
        if threshold_raw is None:
            threshold_raw = os.environ.get("CATEGORY_ASSIGNMENT_MIN_CONFIDENCE", "0.60")
        self.minimum_confidence = float(threshold_raw)

    def assign_category(
        self,
        *,
        label: str,
        category_hint: str | None = None,
        wiki_text: str | None = None,
    ) -> CategoryAssignmentResult:
        cleaned_label = label.strip() if isinstance(label, str) else ""
        cleaned_hint = category_hint.strip() if isinstance(category_hint, str) and category_hint.strip() else None
        cleaned_wiki_text = wiki_text.strip() if isinstance(wiki_text, str) else ""
        if not cleaned_label:
            return self._unknown(generated_by_ai=False)

        if self.assignment_adapter is not None:
            try:
                prompt = self._build_prompt(cleaned_label, cleaned_hint, cleaned_wiki_text)
                result = self._parse_provider_payload(self.assignment_adapter.assign_category(prompt))
                return result
            except CategoryAssignmentError:
                pass
            except Exception:
                pass

        fallback_category = self._fallback_category(cleaned_hint, cleaned_label, cleaned_wiki_text)
        return CategoryAssignmentResult(
            category=fallback_category,
            confidence=1.0 if fallback_category != self.UNKNOWN_CATEGORY else 0.0,
            scores={fallback_category: 1.0} if fallback_category != self.UNKNOWN_CATEGORY else {},
            generated_by_ai=False,
        )

    def _build_prompt(self, label: str, category_hint: str | None, wiki_text: str) -> str:
        categories = ", ".join(self.ALLOWED_CATEGORIES)
        hint = category_hint or "None"
        info = wiki_text if wiki_text else "No additional description available."
        return (
            "Assign the scanned object to exactly one of the allowed Omnidex categories. "
            "Return JSON only. Include a score between 0 and 1 for every allowed category. "
            "Do not invent categories. If the object is unclear, use Unbekannt.\n\n"
            f"Allowed categories: {categories}\n"
            f"Recognized label: {label}\n"
            f"Recognition category hint: {hint}\n"
            f"Object information:\n{info}\n\n"
            "Required JSON shape:\n"
            '{"selected_category": "Tiere", "confidence": 0.91, '
            '"scores": {"Pflanze": 0.0, "Insekten": 0.0, "Tiere": 0.91, "Nahrung": 0.0, '
            '"Unbekannt": 0.0, "Technik": 0.0, "Mechanik": 0.0, "Gestein": 0.0, "Gegenstände": 0.09}}'
        )

    def _parse_provider_payload(self, payload: dict[str, Any]) -> CategoryAssignmentResult:
        if not isinstance(payload, dict):
            raise InvalidCategoryAssignmentResponse("Category assignment payload must be an object")

        selected = payload.get("selected_category", payload.get("category"))
        if not isinstance(selected, str):
            raise InvalidCategoryAssignmentResponse("Category assignment is missing selected_category")
        selected = selected.strip()
        if selected not in self.ALLOWED_CATEGORIES:
            raise InvalidCategoryAssignmentResponse(f"Unsupported category '{selected}'")

        scores = self._parse_scores(payload.get("scores"))
        confidence = payload.get("confidence", payload.get("score"))
        if isinstance(confidence, str):
            try:
                confidence = float(confidence)
            except ValueError:
                confidence = None
        if not isinstance(confidence, (int, float)):
            confidence = scores.get(selected)
        if not isinstance(confidence, (int, float)):
            raise InvalidCategoryAssignmentResponse("Category assignment is missing numeric confidence")

        confidence_value = self._clamp_score(float(confidence))
        if not scores:
            scores = {selected: confidence_value}

        if confidence_value < self.minimum_confidence:
            return CategoryAssignmentResult(
                category=self.UNKNOWN_CATEGORY,
                confidence=confidence_value,
                scores=scores,
                generated_by_ai=True,
            )

        return CategoryAssignmentResult(
            category=selected,
            confidence=confidence_value,
            scores=scores,
            generated_by_ai=True,
        )

    def _parse_scores(self, raw_scores: Any) -> dict[str, float]:
        if not isinstance(raw_scores, dict):
            return {}
        scores = {}
        for category in self.ALLOWED_CATEGORIES:
            raw_score = raw_scores.get(category)
            if isinstance(raw_score, str):
                try:
                    raw_score = float(raw_score)
                except ValueError:
                    continue
            if isinstance(raw_score, (int, float)):
                scores[category] = self._clamp_score(float(raw_score))
        return scores

    @staticmethod
    def _clamp_score(value: float) -> float:
        return max(0.0, min(1.0, value))

    def _fallback_category(self, category_hint: str | None, label: str, wiki_text: str) -> str:
        for text in (category_hint, label, wiki_text):
            category = self._category_from_text(text)
            if category is not None:
                return category
        return self.UNKNOWN_CATEGORY

    def _category_from_text(self, text: str | None) -> str | None:
        if not isinstance(text, str) or not text.strip():
            return None
        normalized = text.casefold()
        for token, category in self.HINT_MAPPING.items():
            if token in normalized:
                return category
        return None

    def _unknown(self, generated_by_ai: bool) -> CategoryAssignmentResult:
        return CategoryAssignmentResult(
            category=self.UNKNOWN_CATEGORY,
            confidence=0.0,
            scores={},
            generated_by_ai=generated_by_ai,
        )
