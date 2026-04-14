from typing import Protocol

from app.domain_models.user import User

# This is basically an interface in python (called Protocol)
class UserRepoProtocol(Protocol):

    def get_user(self, user_id: int) -> User | None: ...

    def get_user_by_name(self, name: str) -> User | None: ...

    def create_user(self, name: str, password: str) -> bool: ...
