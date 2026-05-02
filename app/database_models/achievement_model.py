from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class AchievementModel(db.Model):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(nullable=True)

    user_achievements: Mapped[list["UserAchievementModel"]] = relationship(
        "UserAchievementModel",
        back_populates="achievement"
    )