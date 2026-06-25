import os
from typing import Any

from app.domain_models.recognition_result import RecognitionResult, RecognitionAlternative
from app.repositories.interfaces.external.lisa_adapter_protocol import LisaAdapterProtocol
from app.services.recognition_errors import (
    RecognitionUnavailable,
    LowConfidence,
    InvalidRecognitionResponse,
)


class RecognitionService:
    def __init__(
        self,
        lisa_adapter: LisaAdapterProtocol,
        minimum_confidence: float | None = None,
    ):
        self.lisa_adapter = lisa_adapter
        threshold_raw = minimum_confidence if minimum_confidence is not None else os.environ.get(
            "RECOGNITION_MIN_CONFIDENCE",
            "0.90",
        )
        self.minimum_confidence = float(threshold_raw)

    def recognize_image(self, image_data: bytes) -> RecognitionResult:
        if not image_data:
            raise InvalidRecognitionResponse("No image payload provided")

        try:
            payload = self.lisa_adapter.recognize_image(image_data)
        except (RecognitionUnavailable, InvalidRecognitionResponse):
            raise
        except Exception as exc:
            raise RecognitionUnavailable("Recognition provider failed unexpectedly") from exc

        return self._to_recognition_result(payload)

    def _to_recognition_result(self, payload: dict[str, Any]) -> RecognitionResult:
        if not isinstance(payload, dict):
            raise InvalidRecognitionResponse("Recognition payload must be an object")

        label = payload.get("label")
        confidence = payload.get("confidence")
        if not isinstance(label, str) or not label.strip():
            raise InvalidRecognitionResponse("Recognition payload is missing label")
        if not isinstance(confidence, (int, float)):
            raise InvalidRecognitionResponse("Recognition payload is missing numeric confidence")

        confidence_value = float(confidence)
        if confidence_value < self.minimum_confidence:
            raise LowConfidence(label.strip(), confidence_value, self.minimum_confidence)

        raw_alternatives = payload.get("alternatives", [])
        if not isinstance(raw_alternatives, list):
            raise InvalidRecognitionResponse("Recognition alternatives must be a list")

        alternatives: list[RecognitionAlternative] = []
        for alternative in raw_alternatives:
            parsed = self._parse_alternative(alternative)
            if parsed is not None:
                alternatives.append(parsed)

        category_hint = payload.get("category_hint")
        if category_hint is not None and not isinstance(category_hint, str):
            raise InvalidRecognitionResponse("category_hint must be a string or null")

        provider_raw = payload.get("provider_raw")
        if provider_raw is not None and not isinstance(provider_raw, dict):
            raise InvalidRecognitionResponse("provider_raw must be a JSON object when provided")

        return RecognitionResult(
            label=label.strip(),
            confidence=confidence_value,
            alternatives=alternatives,
            category_hint=category_hint.strip() if isinstance(category_hint, str) and category_hint.strip() else None,
            provider_raw=provider_raw,
        )

    @staticmethod
    def _parse_alternative(candidate: Any) -> RecognitionAlternative | None:
        if isinstance(candidate, str):
            label = candidate.strip()
            return RecognitionAlternative(label=label) if label else None

        if not isinstance(candidate, dict):
            return None

        label = candidate.get("label")
        if not isinstance(label, str) or not label.strip():
            return None

        confidence = candidate.get("confidence")
        if confidence is None:
            return RecognitionAlternative(label=label.strip())
        if not isinstance(confidence, (int, float)):
            raise InvalidRecognitionResponse("Alternative confidence must be numeric")

        return RecognitionAlternative(label=label.strip(), confidence=float(confidence))
