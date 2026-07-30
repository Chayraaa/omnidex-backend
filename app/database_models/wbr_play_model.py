from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class WBRPlayModel(db.Model):
    __tablename__ = 'wbr_play'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    streak: Mapped[int] = mapped_column(nullable=False)
    highscore: Mapped[int] = mapped_column(nullable=False)
    won: Mapped[bool] = mapped_column(nullable=False)
    played_at: Mapped[object] = mapped_column(DateTime, nullable=False)

    user: Mapped["UserModel"] = relationship("UserModel", foreign_keys=[user_id])
