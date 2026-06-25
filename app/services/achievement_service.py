from app.domain_models.achievement import Achievement
from app.domain_models.user import User
from app.domain_models.user_achievements import UserAchievement
from app.repositories.interfaces.storage.achievement_repo_protocol import AchievementRepoProtocol
from app.repositories.interfaces.storage.user_achievements_repo_protocol import UserAchievementRepoProtocol


class AchievementService:
    def __init__(self, user_achievement_repo: UserAchievementRepoProtocol, achievement_repo: AchievementRepoProtocol):
        self.user_achievement_repo = user_achievement_repo
        self.achievement_repo = achievement_repo

    def get_all_achievements(self) -> Achievement | None:
        return self.achievement_repo.get_all_achievements()

    def get_current_progress(self, user: User, achievement: Achievement) -> UserAchievement | None:
        return self.user_achievement_repo.get_current_progress(user, achievement)

    def update_progress(self, user: User, achievement: Achievement) -> None:
        return self.user_achievement_repo.update_progress(user, achievement)