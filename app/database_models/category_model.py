from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm import relationship
from app.extensions import db


class CategoryModel(db.Model):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True, default="???")
    description: Mapped[str | None] = mapped_column(nullable=True, default="")

    cards: Mapped[list["CardModel"]] = relationship(
        back_populates="category_ref"
    )
