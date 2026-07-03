from app.domain_models.user_achievements import UserAchievement
from app.database_models.user_achievement_model import UserAchievementModel
from app.extensions import db
from app.domain_models.achievement import Achievement
from app.domain_models.user import User


class SqlUserAchievementRepo:
    def get_current_progress(self, user: User) -> list[UserAchievement]:
        db_obj = db.session.query(UserAchievementModel).filter_by(user_id = user.id).all()

        return [
            UserAchievement(
                user_id = user.id,
                achievement_id = obj.achievement_id,
                isDone=obj.isDone,
                currentProgress=obj.currentProgress
            )
            for obj in db_obj
        ]

    def update_progress(self, user_id: int, achievement: Achievement, progress: int, isDone: bool) -> None:
        obj = (
            db.session.query(UserAchievementModel).filter_by(user_id=user_id,achievement_id=achievement.id,).first()
        )

        obj.currentProgress = progress
        obj.isDone = isDone

        db.session.commit()

    def create_user_achievement(self, user_id: int, achievement_id: int, currentProgress: int = 0, isDone: bool = False) -> None:
        obj = UserAchievementModel(
            user_id = user_id,
            achievement_id = achievement_id,
            currentProgress = currentProgress,
            isDone = isDone
        )
        db.session.add(obj)
        db.session.commit()
