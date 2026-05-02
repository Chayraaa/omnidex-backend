from typing import Protocol
from app.domain_models.first_discovered import FirstDiscovered


class FirstDiscoveredRepoProtocol(Protocol):

    def get(self, card_id: int) -> FirstDiscovered | None: ...

    def get_by_name(self, name: str) -> FirstDiscovered | None: ...

    def create(self, card_id: int) -> bool: ...