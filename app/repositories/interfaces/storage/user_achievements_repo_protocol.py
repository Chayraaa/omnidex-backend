from typing import Protocol
from app.domain_models.user_achievements import UserAchievement
from app.domain_models.user import User
from app.domain_models.achievement import Achievement


class UserAchievementRepoProtocol(Protocol):

    def add(self, user: User, achievement: Achievement) -> bool: ...

    def get(self, user: User, achievement: Achievement) -> UserAchievement | None: ...