from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from app.extensions import db
from datetime import datetime, timezone


class NotificationModel(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey("users.id"), index=True, nullable=False)

    user = relationship("UserModel", back_populates="notifications")

    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(255), nullable=False)

    is_read = db.Column(db.Boolean, default=False)

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )