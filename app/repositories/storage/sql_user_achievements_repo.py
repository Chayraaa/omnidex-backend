from app.domain_models.user_achievements import UserAchievements
from app.database_models.user_achievement_model import UserAchievementModel
from app.extensions import db
from app.domain_models.user import User
from app.domain_models.achievement import Achievement


class SqlUserAchievementRepo:
    def get(self, user: User, achievement: Achievement) -> UserAchievements | None:
        db_obj = db.session.get(UserAchievementModel, (user, achievement))
        if not db_obj:
            return None
        return UserAchievements(
            user=db_obj.user_id,
            achievement=db_obj.achievement_id
        )

    def add(self, user: User, achievement: Achievement) -> bool:
        db_obj = UserAchievementModel(
            user_id=user,
            achievement_id=achievement
        )
        db.session.add(db_obj)
        db.session.commit()
        return True