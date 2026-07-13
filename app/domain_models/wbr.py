from dataclasses import dataclass

from app.domain_models.card import Card
from app.domain_models.user import User


@dataclass
class WBR:
    id: int
    user: User
    defender: Card | None
    streak: int
    highscore: int = 0
    history: str | None = None