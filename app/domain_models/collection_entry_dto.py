from dataclasses import dataclass, field

from app.domain_models.card import BattleType


@dataclass
class CollectionEntrySummaryDto:
    id: int
    label: str
    category: str | None
    card_summary: str | None
    image_url: str | None
    created_at: str | None
    confidence: float | None
    battle_type: BattleType = BattleType.FIGHTER
    attack: int = 0
    health: int = 0
    cost: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "category": self.category,
            "card_summary": self.card_summary,
            "image_url": self.image_url,
            "created_at": self.created_at,
            "confidence": self.confidence,
            "battle_type": self.battle_type.value,
            "attack": self.attack,
            "health": self.health,
            "cost": self.cost,
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
    battle_type: BattleType = BattleType.FIGHTER
    attack: int = 0
    health: int = 0
    cost: int = 0

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
            "battle_type": self.battle_type.value,
            "attack": self.attack,
            "health": self.health,
            "cost": self.cost,
        }
