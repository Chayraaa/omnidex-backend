from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecognitionAlternative:
    label: str
    confidence: float | None = None


@dataclass
class RecognitionResult:
    label: str
    confidence: float
    alternatives: list[RecognitionAlternative] = field(default_factory=list)
    category_hint: str | None = None
    provider_raw: dict[str, Any] | None = None
