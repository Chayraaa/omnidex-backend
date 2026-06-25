from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class AchievementModel(db.Model):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    required: Mapped[int] = mapped_column(nullable=False, default=20)
    achievementReward: Mapped[int] = mapped_column(nullable=False, default=100)
    icon: Mapped[str] = mapped_column(nullable=True)

    user_achievements: Mapped[list["UserAchievementModel"]] = relationship(
        "UserAchievementModel",
        back_populates="achievement"
    )