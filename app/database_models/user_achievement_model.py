from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class UserAchievementModel(db.Model):
    __tablename__ = "user_achievements"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"), primary_key=True)
    isDone: Mapped[bool] = mapped_column(nullable=False, default=False)
    currentProgress: Mapped[int] = mapped_column(nullable=False, default=0)


    user: Mapped["UserModel"] = relationship("UserModel",back_populates="user_achievements")
    achievement: Mapped["AchievementModel"] = relationship("AchievementModel",back_populates="user_achievements")
