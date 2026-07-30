from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class CardBattleResultModel(db.Model):
    __tablename__ = 'card_battle_result'

    id: Mapped[int] = mapped_column(primary_key=True)
    player1_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    player2_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    player1_won: Mapped[bool] = mapped_column(nullable=False)
    game_id: Mapped[int | None] = mapped_column(nullable=True)
    played_at: Mapped[object] = mapped_column(DateTime, nullable=False)

    player1: Mapped["UserModel"] = relationship(
        "UserModel",
        primaryjoin="CardBattleResultModel.player1_id == UserModel.id",
        foreign_keys=[player1_id],
    )
    player2: Mapped["UserModel"] = relationship(
        "UserModel",
        primaryjoin="CardBattleResultModel.player2_id == UserModel.id",
        foreign_keys=[player2_id],
    )
