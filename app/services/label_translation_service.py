import json
import re

from app.repositories.interfaces.external.label_translation_adapter_protocol import LabelTranslationAdapterProtocol
from app.services.label_translation_errors import LabelTranslationError


class LabelTranslationService:
    FALLBACK_LABEL = "unknown"
    MAX_LABEL_LENGTH = 80

    def __init__(self, translation_adapter: LabelTranslationAdapterProtocol | None = None):
        self.translation_adapter = translation_adapter

    def translate_label_to_german(self, label: str) -> str:
        original_label = label.strip() if isinstance(label, str) else ""
        if not original_label:
            return self.FALLBACK_LABEL
        if self.translation_adapter is None:
            return original_label

        prompt = self._build_prompt(original_label)
        try:
            translated = self.translation_adapter.translate_label(prompt)
        except LabelTranslationError:
            return original_label
        except Exception:
            return original_label

        cleaned = self._clean_translation(translated)
        return cleaned or original_label

    @staticmethod
    def _build_prompt(label: str) -> str:
        return (
            "Übersetze das folgende Objekt-Label ins Deutsche für eine mobile Objektkarte. "
            "Gib ausschließlich den deutschen Objekt-Namen zurück. Verwende das gängige Substantiv im Singular. "
            "Keine Erklärungen, keine Artikel, keine Satzzeichen, kein JSON oder zusätzliche Informationen. "
            "Wenn es sich um einen Markennamen, Modellnamen oder Eigennamen handelt, lasse ihn unverändert.\n\n"
            f"Label:\n{label}"
        )

    @classmethod
    def _clean_translation(cls, text: str) -> str | None:
        if not isinstance(text, str):
            return None

        cleaned = text.strip()
        if not cleaned:
            return None
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").strip()
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()

        parsed = cls._parse_json_label(cleaned)
        if parsed:
            cleaned = parsed

        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if lines:
            cleaned = lines[0]

        cleaned = re.sub(r"^[-*•\d.)\s]+", "", cleaned).strip()
        cleaned = cleaned.strip("\"'“”„` ")
        cleaned = re.sub(r"^(der|die|das|ein|eine|einen|einem)\s+", "", cleaned).strip()
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        cleaned = cleaned.rstrip(".,;:! ").strip()

        if not cleaned or len(cleaned) > cls.MAX_LABEL_LENGTH:
            return None
        return cleaned

    @staticmethod
    def _parse_json_label(text: str) -> str | None:
        if not text.startswith("{"):
            return None
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        for key in ("german_label", "label_de", "translation", "label"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None
