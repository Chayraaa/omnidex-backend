from dataclasses import dataclass


@dataclass
class Deck:
    id: int
    user_id: int
    name: str
    deck: str
    is_main: bool = False
