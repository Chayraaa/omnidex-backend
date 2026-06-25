from dataclasses import dataclass


@dataclass
class Achievement:
    id: int
    name: str
    required: int
    achievementReward: int
    icon: str