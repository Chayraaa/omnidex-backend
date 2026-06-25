from dataclasses import dataclass
from datetime import datetime


@dataclass
class Notification:
    id: int | None
    user_id: int
    type: str
    message: str
    is_read: bool
    created_at: datetime | None = None