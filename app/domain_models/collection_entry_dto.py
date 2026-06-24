from dataclasses import dataclass, field


@dataclass
class CollectionEntrySummaryDto:
    id: int
    label: str
    category: str | None
    card_summary: str | None
    image_url: str | None
    created_at: str | None
    confidence: float | None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "category": self.category,
            "card_summary": self.card_summary,
            "image_url": self.image_url,
            "created_at": self.created_at,
            "confidence": self.confidence,
        }


@dataclass
class CollectionEntryDetailDto:
    id: int
    label: str
    category: str | None
    confidence: float | None
    card_summary: str | None
    description: str | None
    source_title: str | None
    source_url: str | None
    alternatives: list[dict] = field(default_factory=list)
    image_url: str | None = None
    created_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "category": self.category,
            "confidence": self.confidence,
            "card_summary": self.card_summary,
            "description": self.description,
            "source_title": self.source_title,
            "source_url": self.source_url,
            "alternatives": self.alternatives,
            "image_url": self.image_url,
            "created_at": self.created_at,
        }
