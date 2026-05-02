from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db


class FriendsModel(db.Model):
    __tablename__ = "friends"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, primary_key=True)
    friend_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, primary_key=True)
    status: Mapped[str] = mapped_column(default="pending")

    user: Mapped["UserModel"] = relationship(
        "UserModel",
        foreign_keys=[user_id],
        back_populates="sent_friendships",
    )

    friend: Mapped["UserModel"] = relationship(
        "UserModel",
        foreign_keys=[friend_id],
        back_populates="received_friendships",
    )