from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.services.password_service import PasswordService

# Defines a user in the database. Will automatically create tables and interactions in flask.
# Basically an easy way to avoid SQL lul.
# Take this as a template if more needs to be created. See sqlalchemy docs for capabilities.
class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)

    def set_password(self, password: str):
        self.password = PasswordService.hash_password(password)

    def check_password(self, password: str):
        return PasswordService.verify_password(password, self.password)
