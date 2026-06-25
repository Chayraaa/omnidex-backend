from dataclasses import dataclass, field


@dataclass(frozen=True)
class CategoryAssignmentResult:
    category: str
    confidence: float
    scores: dict[str, float] = field(default_factory=dict)
    generated_by_ai: bool = False

