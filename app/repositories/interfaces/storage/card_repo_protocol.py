from typing import Protocol


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
    ) -> tuple[int, str | None]: ...

    def card_name_exists(self, *, user_id: int, name: str) -> bool: ...
