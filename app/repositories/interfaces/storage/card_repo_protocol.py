from typing import Protocol


class CardRepoProtocol(Protocol):
    def create_card(self, *, user_id: int, name: str, image_key: str, card_summary: str | None) -> int: ...

    def card_name_exists(self, *, user_id: int, name: str) -> bool: ...
