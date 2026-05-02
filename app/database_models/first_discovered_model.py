from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class FirstDiscoveredModel(db.Model):
    __tablename__ = "first_discovered"

    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id"),
        primary_key=True
    )

    card: Mapped["CardModel"] = relationship("CardModel")