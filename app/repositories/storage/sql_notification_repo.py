from app.extensions import db
from app.database_models.notification_model import NotificationModel
from app.domain_models.notification import Notification


class SqlNotificationRepo:

    def create(self, notification: Notification) -> Notification:
        db_obj = NotificationModel(
            user_id=notification.user_id,
            type=notification.type,
            message=notification.message,
            is_read=False
        )

        db.session.add(db_obj)
        db.session.commit()

        return Notification(
            id=db_obj.id,
            user_id=db_obj.user_id,
            type=db_obj.type,
            message=db_obj.message,
            is_read=db_obj.is_read,
            created_at=db_obj.created_at
        )
    def get_for_user(self, user_id: int):
        return NotificationModel.query.filter_by(user_id=user_id)\
            .order_by(NotificationModel.created_at.desc())\
            .all()