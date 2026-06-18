from datetime import datetime
from dataclasses import dataclass

@dataclass
class RefreshToken:
    id: int
    user_id: int
    refresh_token: str
    expires_in: datetime
    created_at: datetime
    revoked: bool
