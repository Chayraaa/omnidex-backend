from dataclasses import dataclass


@dataclass
class UserAchievement:
    user_id: int
    achievement_id: int
    isDone: bool
    currentProgress: int
