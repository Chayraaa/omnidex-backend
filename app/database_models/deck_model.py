from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class DeckModel(db.Model):
    __tablename__ = 'decks'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    deck: Mapped[str] = mapped_column(nullable=False)
    is_main: Mapped[bool] = mapped_column(nullable=False, default=False)

    user: Mapped["UserModel"] = relationship(back_populates="decks")