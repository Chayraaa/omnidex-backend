from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

class WBRModel(db.Model):
    __tablename__ = "what_beats_rock"
    id: Mapped[int] = mapped_column(primary_key=True)
    defender_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id"), default=None, nullable=True)
    streak: Mapped[int] = mapped_column(default=0)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    history: Mapped[str | None] = mapped_column(default=None, nullable=True)

    user = relationship("UserModel", back_populates="wbr")
    defender = relationship("CardModel", back_populates="wbr")