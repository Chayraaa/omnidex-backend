from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    hashed_password: str
    oauth: str = "local"
    profile_picture_key: str = ""
    email: str = ""
    friend_code: str = ""
