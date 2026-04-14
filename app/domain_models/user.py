from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    hashed_password: str
