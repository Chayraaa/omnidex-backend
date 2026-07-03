from typing import Protocol
from app.domain_models.user_achievements import UserAchievement
from app.domain_models.achievement import Achievement
from app.domain_models.user import User


class UserAchievementRepoProtocol(Protocol):

    def get_current_progress(self, user: User) -> list[UserAchievement]: ...

    def update_progress(self, user_id: int, achievement: Achievement, progress: int, isDone: bool) -> None: ...

    def create_user_achievement(self, user_id: int, achievement_id: int, currentProgress: int = 0, isDone: bool = False) -> None: ...