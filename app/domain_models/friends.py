from dataclasses import dataclass


@dataclass
class Friends:
    user_id: int
    friend_id: int
    status: str = "pending"
