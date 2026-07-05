import re

from app.repositories.interfaces.external.lisa_summary_adapter_protocol import LisaSummaryAdapterProtocol
from app.services.summary_errors import InvalidSummaryResponse

KI_KNOWLEDGE_TAG = "(KI-Wissen)"
_KI_TAG_PATTERN = re.compile(r"\(\s*ki[-\s]?wissen\s*\)", re.IGNORECASE)
_ABBREVIATIONS = {
    "z.b", "u.a", "u.ä", "d.h", "bzw", "usw", "etc", "ca", "nr", "dr", "prof", "st", "sog", "jh",
}


def _looks_incomplete(buffer: str) -> bool:
    """True if `buffer` ends in something that looks like an abbreviation
    or a number (e.g. '19.' in '19. Jahrhundert'), not a real sentence end."""
    if not buffer.endswith("."):
        return False

    words = buffer.rstrip(".!?").split()
    if not words:
        return False

    last_word = words[-1]
    if last_word.isdigit():
        return True

    if last_word.lower().rstrip(".") in _ABBREVIATIONS:
        return True

    return False

class SummaryService:
    def __init__(self, summary_adapter: LisaSummaryAdapterProtocol):
        self.summary_adapter = summary_adapter

    def summarize_object_info(self, label: str, wiki_text: str) -> str:
        cleaned_label = label.strip() if isinstance(label, str) else ""
        cleaned_text = wiki_text.strip() if isinstance(wiki_text, str) else ""
        if not cleaned_label:
            raise InvalidSummaryResponse("Object label is required for summarization")
        if not cleaned_text:
            raise InvalidSummaryResponse("Wiki text is required for summarization")

        prompt = (
            f"Erstelle eine kurze Beschreibung von '{cleaned_label}' für eine mobile Objektkarte, "
            "auf Deutsch, maximal zwei kurze Sätze. Bleibe sachlich.\n\n"
            f"Prüfe zuerst, ob der folgende Text thematisch zu '{cleaned_label}' passt.\n"
            "- Falls ja: Fasse ausschließlich Fakten aus dem Text auf die geforderte länge zusammen. Füge keine neuen Informationen hinzu.\n"
            f"- Falls nein: Ignoriere den Text, beschreibe '{cleaned_label}' stattdessen anhand deines eigenen "
            f"Allgemeinwissens sachlich und objektiv im Stil von Wikipedia. Füge am Ende der Antwort genau '{KI_KNOWLEDGE_TAG}' in Klammern an.\n\n"
            "Gib nur die fertige Beschreibung zurück, ohne weitere Erklärungen oder Kommentare.\n\n"
            f"Informationen:\n{cleaned_text}"
        )

        summary = self.summary_adapter.summarize_text(prompt)
        if not isinstance(summary, str) or not summary.strip():
            raise InvalidSummaryResponse("Summary provider returned an empty summary")

        return self._finalize_summary(summary.strip())

    def _finalize_summary(self, summary: str) -> str:
        """Normalize the optional (KI-Wissen) marker and make sure trimming
        can't accidentally cut it off or leave a mangled/duplicated tag."""
        is_ki_generated = bool(_KI_TAG_PATTERN.search(summary))

        body = _KI_TAG_PATTERN.sub("", summary).strip()
        body = self.trim_summary(body)

        if is_ki_generated:
            body = f"{body} {KI_KNOWLEDGE_TAG}"

        return body

    @staticmethod
    def trim_summary(text: str, max_sentences: int = 2) -> str:
        text = text.strip()
        if not text:
            return text

        raw_parts = [part for part in re.split(r"(?<=[.!?])\s+", text) if part]

        sentences: list[str] = []
        buffer = ""
        for part in raw_parts:
            buffer = f"{buffer} {part}".strip() if buffer else part

            if _looks_incomplete(buffer):
                continue

            sentences.append(buffer.strip())
            buffer = ""

        if buffer.strip():
            sentences.append(buffer.strip())

        if not sentences:
            return text

        return " ".join(sentences[:max_sentences]).strip()
