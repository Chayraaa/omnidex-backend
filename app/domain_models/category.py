from dataclasses import dataclass


@dataclass
class Category:
    id: int
    name: str
    description: str | None = None