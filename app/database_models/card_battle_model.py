from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class CardBattleGameModel(db.Model):
    __tablename__ = 'card_battle_game'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    player1_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    player2_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    game_state: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime, nullable=True, default=None)

    player1: Mapped["UserModel"] = relationship(
        "UserModel",
        primaryjoin="CardBattleGameModel.player1_id == UserModel.id",
        foreign_keys=[player1_id],
        back_populates="cardBattleGamesP1"
    )
    player2: Mapped["UserModel"] = relationship(
        "UserModel",
        primaryjoin="CardBattleGameModel.player2_id == UserModel.id",
        foreign_keys=[player2_id],
        back_populates="cardBattleGamesP2"
    )


