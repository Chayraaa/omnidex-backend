from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain_models.card import BattleType
from app.extensions import db


class CardModel(db.Model):
    __tablename__ = "cards"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_cards_user_id_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    card_summary: Mapped[str | None] = mapped_column(nullable=True)
    category: Mapped[str | None] = mapped_column(nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_title: Mapped[str | None] = mapped_column(nullable=True)
    source_url: Mapped[str | None] = mapped_column(nullable=True)
    alternatives_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_key: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    battle_type: Mapped[str] = mapped_column(nullable=False, default=BattleType.FIGHTER.value)
    attack: Mapped[int] = mapped_column(nullable=False, default=10)
    health: Mapped[int] = mapped_column(nullable=False, default=10)
    cost: Mapped[int] = mapped_column(nullable=False, default=1)

    user: Mapped["UserModel"] = relationship(
        back_populates="cards"
    )
    category_ref: Mapped["CategoryModel"] = relationship(
        back_populates="cards"
    )

    wbr: Mapped[list["WBRModel"]] = relationship(
        "WBRModel",
        back_populates="defender",
        cascade="all, delete-orphan"
    )

    first_discovered: Mapped[list["FirstDiscoveredModel"]] = relationship(
        "FirstDiscoveredModel",
        back_populates="card",
        cascade="all, delete-orphan",
    )
