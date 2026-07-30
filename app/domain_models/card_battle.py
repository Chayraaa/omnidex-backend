from dataclasses import dataclass, field
from datetime import datetime

from app.services.games.card_battle.card_battle import GameState


@dataclass
class CardBattleGame:
    id: int
    name: str
    player1_id: int | None
    player2_id: int | None
    game_state: GameState
    created_at: datetime | None = field(default=None)

