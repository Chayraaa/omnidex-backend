from urllib.parse import quote
from io import BytesIO
from uuid import uuid4
import json

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
from app.services.summary_errors import SummaryError
from app.services.summary_service import SummaryService
from app.services.scan_errors import ScanCreationFailed
from app.services.category_service import CategoryService
from app.services.label_translation_service import LabelTranslationService


class ScanService:
    FALLBACK_CARD_SUMMARY = "No short description is currently available."

    def __init__(
        self,
        recognition_service,
        wiki_service,
        summary_service,
        image_storage,
        card_repo,
        base_url: str,
        category_service=None,
        label_translation_service=None,
        achievement_service=None,
    ):
        self.recognition_service = recognition_service
        self.wiki_service = wiki_service
        self.summary_service = summary_service
        self.image_storage = image_storage
        self.card_repo = card_repo
        self.base_url = base_url.rstrip("/")
        self.category_service = category_service or CategoryService()
        self.label_translation_service = label_translation_service or LabelTranslationService()
        self.achievement_service = achievement_service

    def create_scan(self, user_id: int, image_input: bytes) -> ScanResultDto:
        if user_id <= 0:
            raise ScanInputInvalid("user_id must be a positive integer")
        if not image_input:
            raise ScanInputInvalid("image input is required")

        recognition_result = self._recognize_image(image_input)
        description, knowledge_enriched = self._get_knowledge(recognition_result.label)
        category_assignment = self.category_service.assign_category(
            label=recognition_result.label,
            category_hint=recognition_result.category_hint,
            wiki_text=description,
        )
        card_summary, summary_generated_by_ai = self._get_card_summary(recognition_result.label, description)
        display_label = recognition_result.label

        card_id, image_reference, created_at = self._persist_card(
            user_id=user_id,
            card_label=display_label,
            card_summary=card_summary,
            image_bytes=image_input,
            confidence=recognition_result.confidence,
            description=description,
            source_title=recognition_result.label if knowledge_enriched else None,
            source_url=self._build_wikipedia_url(recognition_result.label) if knowledge_enriched else None,
            category=category_assignment.category,
            alternatives=[
                {"label": alternative.label, "confidence": alternative.confidence}
                for alternative in recognition_result.alternatives
            ],
        )

        if self.achievement_service is not None:
            self.achievement_service.process_card_created(user_id)

        return ScanResultDto(
            label=display_label,
            confidence=recognition_result.confidence,
            category_hint=recognition_result.category_hint,
            category=category_assignment.category,
            alternatives=[
                ScanAlternativeDto(label=alternative.label, confidence=alternative.confidence)
                for alternative in recognition_result.alternatives
            ],
            description=description,
            card_summary=card_summary,
            source_title=recognition_result.label if knowledge_enriched else None,
            source_url=self._build_wikipedia_url(recognition_result.label) if knowledge_enriched else None,
            knowledge_enriched=knowledge_enriched,
            summary_generated_by_ai=summary_generated_by_ai,
            id=card_id,
            image_reference=image_reference,
            created_at=created_at,
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

    def _get_card_summary(self, label: str, description: str) -> tuple[str, bool]:
        try:
            summary = self.summary_service.summarize_object_info(label, description)
        except SummaryError:
            return self._fallback_card_summary(description), False
        except Exception:
            return self._fallback_card_summary(description), False

        if not isinstance(summary, str) or not summary.strip():
            return self._fallback_card_summary(description), False
        return SummaryService.trim_summary(summary.strip()), True

    def _get_display_label(self, recognition_label: str) -> str:
        try:
            translated = self.label_translation_service.translate_label_to_german(recognition_label)
        except Exception:
            translated = None
        if isinstance(translated, str) and translated.strip():
            return translated.strip()
        if isinstance(recognition_label, str) and recognition_label.strip():
            return recognition_label.strip()
        return "unknown"

    def _fallback_card_summary(self, description: str) -> str:
        if not isinstance(description, str) or not description.strip():
            return self.FALLBACK_CARD_SUMMARY
        candidate = SummaryService.trim_summary(description.strip())
        if not candidate:
            return self.FALLBACK_CARD_SUMMARY
        return candidate

    def _persist_card(
        self,
        *,
        user_id: int,
        card_label: str,
        card_summary: str,
        image_bytes: bytes,
        confidence: float,
        description: str,
        source_title: str | None,
        source_url: str | None,
        category: str,
        alternatives: list[dict],
    ) -> tuple[int, str, str | None]:
        key: str | None = None
        try:
            extension = self._detect_extension(image_bytes)
            key = f"cards/{user_id}/{uuid4()}.{extension}"
            self.image_storage.save_image(key, BytesIO(image_bytes))
            image_reference = self._build_image_reference(key)

            name = self._unique_card_name(
                user_id,
                card_label.strip() if isinstance(card_label, str) else "unknown",
            )
            card_id, created_at = self.card_repo.create_card(
                user_id=user_id,
                name=name,
                image_key=key,
                card_summary=card_summary,
                category=category,
                confidence=confidence,
                description=description,
                source_title=source_title,
                source_url=source_url,
                alternatives_json=json.dumps(alternatives),
            )
            return card_id, image_reference, created_at
        except Exception as exc:
            if key is not None:
                try:
                    self.image_storage.delete_image(key)
                except Exception:
                    pass
            raise ScanCreationFailed("Failed to persist scan result") from exc

    def _unique_card_name(self, user_id: int, base_name: str) -> str:
        candidate = base_name if base_name else "unknown"
        if not self.card_repo.card_name_exists(user_id=user_id, name=candidate):
            return candidate

        # Avoid violating unique constraint for cards per user.
        for index in range(2, 1000):
            alt = f"{candidate} ({index})"
            if not self.card_repo.card_name_exists(user_id=user_id, name=alt):
                return alt
        return f"{candidate} ({uuid4()})"

    @staticmethod
    def _detect_extension(image_bytes: bytes) -> str:
        if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"
        if image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP":
            return "webp"
        if image_bytes.startswith(b"\xff\xd8\xff"):
            return "jpeg"
        return "jpeg"

    @staticmethod
    def _build_wikipedia_url(label: str) -> str:
        return f"https://de.wikipedia.org/wiki/{quote(label.replace(' ', '_'))}"

    def _build_image_reference(self, key: str) -> str:
        return f"{self.base_url}/api/image/{key}"
