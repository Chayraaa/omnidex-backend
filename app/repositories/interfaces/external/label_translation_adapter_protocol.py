from typing import Protocol


class LabelTranslationAdapterProtocol(Protocol):
    def translate_label(self, prompt: str) -> str: ...
