from urllib.parse import quote
from io import BytesIO
from uuid import uuid4

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


class ScanService:
    FALLBACK_CARD_SUMMARY = "No short description is currently available."

    def __init__(self, recognition_service, wiki_service, summary_service, image_storage, card_repo, base_url: str):
        self.recognition_service = recognition_service
        self.wiki_service = wiki_service
        self.summary_service = summary_service
        self.image_storage = image_storage
        self.card_repo = card_repo
        self.base_url = base_url.rstrip("/")

    def create_scan(self, user_id: int, image_input: bytes) -> ScanResultDto:
        if user_id <= 0:
            raise ScanInputInvalid("user_id must be a positive integer")
        if not image_input:
            raise ScanInputInvalid("image input is required")

        recognition_result = self._recognize_image(image_input)
        description, knowledge_enriched = self._get_knowledge(recognition_result.label)
        card_summary, summary_generated_by_ai = self._get_card_summary(recognition_result.label, description)

        card_id, image_reference = self._persist_card(user_id, recognition_result.label, card_summary, image_input)

        return ScanResultDto(
            label=recognition_result.label,
            confidence=recognition_result.confidence,
            category_hint=recognition_result.category_hint,
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

    def _fallback_card_summary(self, description: str) -> str:
        if not isinstance(description, str) or not description.strip():
            return self.FALLBACK_CARD_SUMMARY
        candidate = SummaryService.trim_summary(description.strip())
        if not candidate:
            return self.FALLBACK_CARD_SUMMARY
        return candidate

    def _persist_card(self, user_id: int, label: str, card_summary: str, image_bytes: bytes) -> tuple[int, str]:
        try:
            extension = self._detect_extension(image_bytes)
            key = f"cards/{user_id}/{uuid4()}.{extension}"
            self.image_storage.save_image(key, BytesIO(image_bytes))
            image_reference = f"{self.base_url}/api/image/{key}"

            name = self._unique_card_name(user_id, label.strip() if isinstance(label, str) else "unknown")
            card_id = self.card_repo.create_card(
                user_id=user_id,
                name=name,
                image_key=image_reference,
                card_summary=card_summary,
            )
            return card_id, image_reference
        except Exception as exc:
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
        return f"https://en.wikipedia.org/wiki/{quote(label.replace(' ', '_'))}"
