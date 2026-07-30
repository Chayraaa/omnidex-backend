from typing import Protocol
from app.domain_models.card import Card

class CardRepoProtocol(Protocol):
    def create_card(
        self,
        *,
        user_id: int,
        name: str,
        image_key: str,
        card_summary: str | None,
        category: str | None = None,
        confidence: float | None = None,
        description: str | None = None,
        source_title: str | None = None,
        source_url: str | None = None,
        alternatives_json: str | None = None,
        battle_type: str | None = None,
        attack: int | None = None,
        health: int | None = None,
        cost: int | None = None,
    ) -> tuple[int, str | None]: ...

    def card_name_exists(self, *, user_id: int, name: str) -> bool: ...

    def count_cards(self, user_id: int) -> int:...

    def count_cards_by_category(self, user_id: int, category: str) -> int:...

    def get_card_by_id(self, card_id: int) -> Card | None: ...

    def get_cards_by_ids(self, card_ids: list[int]) -> list[Card]: ...
    
    def get_all_by_user(self, user_id: int) -> list[Card]: ...

    def get_cards_by_friends(self, user_ids: list[int]) -> list[Card]: ...
