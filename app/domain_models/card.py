from dataclasses import dataclass


@dataclass
class Card:
    id: int
    name: str
    image_key: str
    user_id: int
    category_id: int