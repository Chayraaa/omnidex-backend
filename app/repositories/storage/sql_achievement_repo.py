from app.domain_models.achievement import Achievement
from app.database_models.achievement_model import AchievementModel
from app.extensions import db


class SqlAchievementRepo:
    def get_all_achievements(self) -> Achievement | None:
        pass

    def get_achievement(self, achievement_id: int) -> Achievement | None:
        db_obj = db.session.get(AchievementModel, achievement_id)
        if not db_obj:
            return None
        return Achievement(db_obj.id, db_obj.name, db_obj.description)

    def get_achievement_by_name(self, name: str) -> Achievement | None:
        db_obj = db.session.query(AchievementModel).filter_by(name=name).first()
        if not db_obj:
            return None
        return Achievement(db_obj.id, db_obj.name, db_obj.description)

    def create_achievement(self, name: str, description: str | None) -> bool:
        db_obj = AchievementModel(name=name, description=description)
        db.session.add(db_obj)
        db.session.commit()
        return True

    def update_achievement(self, achievement: Achievement) -> bool:
        db_obj = db.session.get(AchievementModel, achievement.id)
        db_obj.name = achievement.name
        db_obj.description = achievement.description
        db.session.commit()
        return True