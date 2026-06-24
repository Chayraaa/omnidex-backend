from typing import Protocol


class LisaSummaryAdapterProtocol(Protocol):
    def summarize_text(self, prompt: str) -> str: ...
