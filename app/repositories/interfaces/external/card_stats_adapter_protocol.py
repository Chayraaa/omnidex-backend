from typing import Protocol, Any


class CardStatsAdapterProtocol(Protocol):
    def classify_card(self, label: str, description: str) -> dict[str, Any]:
        ...
