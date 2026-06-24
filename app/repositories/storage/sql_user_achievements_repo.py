from app.domain_models.user_achievements import UserAchievement
from app.database_models.user_achievement_model import UserAchievementModel
from app.extensions import db
from app.domain_models.user import User
from app.domain_models.achievement import Achievement


class SqlUserAchievementRepo:
    def get_current_progress(self, user: User, achievement: Achievement) -> UserAchievement | None:
        db_obj = db.session.get(UserAchievementModel, (user, achievement))
        if not db_obj:
            return None
        return UserAchievement(
            user=db_obj.user_id,
            achievement=db_obj.achievement_id
        )
