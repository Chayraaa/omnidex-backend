from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BattleType(Enum):
    FIGHTER = "fighter"
    EQUIPMENT = "equipment"


@dataclass
class Card:
    id: int
    name: str
    image_key: str
    user_id: int
    category_id: int | None
    card_summary: str | None = None
    category: str | None = None
    confidence: float | None = None
    description: str | None = None
    source_title: str | None = None
    source_url: str | None = None
    alternatives_json: str | None = None
    created_at: datetime | None = None
    battle_type: BattleType = BattleType.FIGHTER
    attack: int = 0
    health: int = 0
    cost: int = 0

