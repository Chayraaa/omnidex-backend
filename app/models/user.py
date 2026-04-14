from app.extensions import db
from app.services.password_service import PasswordService


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def set_password(self, password: str):
        self.password = PasswordService.hash_password(password)

    def check_password(self, password: str):
        return PasswordService.verify_password(password, self.password)
