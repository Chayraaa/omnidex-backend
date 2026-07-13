from typing import Protocol


class WBRAdapterProtocol(Protocol):
    def evaluate_match(self, attacker: str, defender: str) -> tuple[bool, str]: ...
