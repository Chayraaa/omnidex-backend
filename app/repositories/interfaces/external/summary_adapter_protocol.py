from typing import Protocol


class SummaryAdapterProtocol(Protocol):
    def summarize_text(self, prompt: str) -> str: ...
