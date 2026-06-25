from app.domain_models.notification import Notification
from app.repositories.storage.sql_notification_repo import SqlNotificationRepo


class NotificationService:
    def __init__(self, repo: SqlNotificationRepo):
        self.repo = repo

    def send(self, user_id: int, type: str, message: str):
        notification = Notification(
            id=None,
            user_id=user_id,
            type=type,
            message=message,
            is_read=False
        )
        return self.repo.create(notification)
    
    def get_for_user(self, user_id: int):
        return self.repo.get_for_user(user_id)