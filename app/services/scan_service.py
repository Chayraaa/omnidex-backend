from urllib.parse import quote

from app.domain_models.scan_result_dto import ScanResultDto, ScanAlternativeDto
from app.services.recognition_errors import (
    RecognitionUnavailable,
    LowConfidence,
    InvalidRecognitionResponse,
)
from app.services.scan_errors import (
    ScanInputInvalid,
    ScanRecognitionFailed,
)


class ScanService:
    def __init__(self, recognition_service, wiki_service):
        self.recognition_service = recognition_service
        self.wiki_service = wiki_service

    def create_scan(self, user_id: int, image_input: bytes) -> ScanResultDto:
        if user_id <= 0:
            raise ScanInputInvalid("user_id must be a positive integer")
        if not image_input:
            raise ScanInputInvalid("image input is required")

        recognition_result = self._recognize_image(image_input)
        description, knowledge_enriched = self._get_knowledge(recognition_result.label)

        # TODO: Persist scan results once scan/collection repository contracts are implemented.
        # TODO: Trigger achievement checks once AchievementService exists.
        return ScanResultDto(
            label=recognition_result.label,
            confidence=recognition_result.confidence,
            category_hint=recognition_result.category_hint,
            alternatives=[
                ScanAlternativeDto(label=alternative.label, confidence=alternative.confidence)
                for alternative in recognition_result.alternatives
            ],
            description=description,
            source_title=recognition_result.label if knowledge_enriched else None,
            source_url=self._build_wikipedia_url(recognition_result.label) if knowledge_enriched else None,
            knowledge_enriched=knowledge_enriched,
        )

    def _recognize_image(self, image_input: bytes):
        try:
            return self.recognition_service.recognize_image(image_input)
        except LowConfidence as exc:
            raise ScanRecognitionFailed(
                "Recognition confidence below accepted threshold.",
                reason="low_confidence",
                label=exc.label,
                confidence=exc.confidence,
                minimum_confidence=exc.minimum_confidence,
            ) from exc
        except RecognitionUnavailable as exc:
            raise ScanRecognitionFailed(
                "Recognition service unavailable.",
                reason="recognition_unavailable",
            ) from exc
        except InvalidRecognitionResponse as exc:
            raise ScanRecognitionFailed(
                "Recognition provider returned invalid data.",
                reason="recognition_invalid_response",
            ) from exc
        except Exception as exc:
            raise ScanRecognitionFailed(
                "Unexpected error in recognition flow.",
                reason="recognition_unexpected_error",
            ) from exc

    def _get_knowledge(self, label: str) -> tuple[str, bool]:
        fallback = "No additional information available."
        try:
            summary = self.wiki_service.get_summary(label)
        except Exception:
            return fallback, False

        if not isinstance(summary, str) or not summary.strip():
            return fallback, False
        if summary.strip().lower() == "no article found":
            return fallback, False
        return summary.strip(), True

    @staticmethod
    def _build_wikipedia_url(label: str) -> str:
        return f"https://en.wikipedia.org/wiki/{quote(label.replace(' ', '_'))}"
