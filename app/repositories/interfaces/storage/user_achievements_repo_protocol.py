from typing import Protocol
from app.domain_models.user_achievements import UserAchievement
from app.domain_models.user import User
from app.domain_models.achievement import Achievement


class UserAchievementRepoProtocol(Protocol):

    def get_current_progress(self, user: User, achievement: Achievement) -> UserAchievement | None: ...

    def update_progress(self, user: User, achievement: Achievement) -> None: ...