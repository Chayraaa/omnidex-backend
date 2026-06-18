import re

from app.repositories.interfaces.external.lisa_summary_adapter_protocol import LisaSummaryAdapterProtocol
from app.services.summary_errors import InvalidSummaryResponse


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
            f"Summarize the following information about '{cleaned_label}' for a mobile object card. "
            "Return maximum two short sentences. Keep it factual, simple, and user-friendly. "
            "Do not add unsupported facts.\n\n"
            f"Information:\n{cleaned_text}"
        )
        summary = self.summary_adapter.summarize_text(prompt)
        if not isinstance(summary, str) or not summary.strip():
            raise InvalidSummaryResponse("Summary provider returned an empty summary")
        return self.trim_summary(summary.strip())

    @staticmethod
    def trim_summary(text: str, max_sentences: int = 2) -> str:
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
        if not sentences:
            return text.strip()
        return " ".join(sentences[:max_sentences]).strip()
