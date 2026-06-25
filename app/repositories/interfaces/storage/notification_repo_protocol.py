from typing import Protocol
from app.domain_models.notification import Notification


class NotificationRepoProtocol(Protocol):
    def create(self, notification: Notification) -> Notification: ...