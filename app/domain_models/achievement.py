from dataclasses import dataclass


@dataclass
class Achievement:
    id: int
    name: str
    description: str | None = None