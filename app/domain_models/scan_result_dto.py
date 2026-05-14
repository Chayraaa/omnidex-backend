from dataclasses import dataclass, field


@dataclass
class ScanAlternativeDto:
    label: str
    confidence: float | None = None

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": self.confidence,
        }


@dataclass
class ScanResultDto:
    label: str
    confidence: float
    alternatives: list[ScanAlternativeDto] = field(default_factory=list)
    category_hint: str | None = None
    description: str = "No additional information available."
    card_summary: str = "No short description is currently available."
    source_title: str | None = None
    source_url: str | None = None
    knowledge_enriched: bool = False
    summary_generated_by_ai: bool = False
    id: int | None = None
    image_reference: str | None = None
    created_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "confidence": self.confidence,
            "category_hint": self.category_hint,
            "alternatives": [alternative.to_dict() for alternative in self.alternatives],
            "description": self.description,
            "card_summary": self.card_summary,
            "source_title": self.source_title,
            "source_url": self.source_url,
            "image_reference": self.image_reference,
            "knowledge_enriched": self.knowledge_enriched,
            "summary_generated_by_ai": self.summary_generated_by_ai,
            "created_at": self.created_at,
        }
