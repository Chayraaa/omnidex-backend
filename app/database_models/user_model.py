from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


# Defines a user in the database. Will automatically create tables and interactions in flask.
# Basically an easy way to avoid SQL lul.
# Take this as a template if more needs to be created. See sqlalchemy docs for capabilities.
class UserModel(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    oauth_method: Mapped[str] = mapped_column(nullable=False, default="local")
    profile_picture_key: Mapped[str] = mapped_column(nullable=False, default="")
    friend_code: Mapped[str] = mapped_column(nullable=False, unique=True)

    cards: Mapped[list["CardModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    user_achievements: Mapped[list["UserAchievementModel"]] = relationship(
        "UserAchievementModel",
        back_populates="user"
    )

    refresh_tokens = relationship(
        "RefreshTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    sent_friendships: Mapped[list["FriendsModel"]] = relationship(
        "FriendsModel",
        foreign_keys="FriendsModel.user_id",
        back_populates="user",
    )

    received_friendships: Mapped[list["FriendsModel"]] = relationship(
        "FriendsModel",
        foreign_keys="FriendsModel.friend_id",
        back_populates="friend",
    )

