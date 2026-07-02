import uuid
import random
import string

from app.domain_models.user import User
from app.repositories.interfaces.storage.user_repo_protocol import UserRepoProtocol
from app.repositories.interfaces.storage.friends_repo_protocol import FriendsRepoProtocol
from app.services.password_service import PasswordService


# The user service is completely decoupled from the database. It just interacts with repo.
# repo is the protocol defined. It will accept any Object that provides the methods requested
# by the protocol. See SqlUserRepo for an example.
# Services are use-case-specific. So they handle a single use-case. In this case, user management.
# For cards, you would have a service that manages cards but also registers them to the user e.g.
class UserService:
    def __init__(self, repo: UserRepoProtocol, friend_repo: FriendsRepoProtocol, achievement_service=None):
        self.repo = repo 
        self.friend_repo = friend_repo
        self.achievement_service = achievement_service

    def get_user(self, user_id: int) -> User | None:
        return self.repo.get_user(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        return self.repo.get_user_by_email(email)

    def create_user(self, name: str, email: str, password: str) -> bool:
        if self.repo.get_user_by_email(email):
            return False
        hashed_password = PasswordService.hash_password(password)
        friend_code = self.generate_friend_code()
        success = self.repo.create_user(name=name, password=hashed_password, email=email, friend_code=friend_code)
        if not success:
            return False
        user = self.repo.get_user_by_email(email)
        self.achievement_service.ensure_user_achievements(user)
        return True

    def update_user(self, user: User) -> bool:
        return self.repo.update_user(user)
    
    def get_user_by_friend_code(self, friend_code: str) -> User | None:
        return self.repo.get_user_by_friend_code(friend_code)
    
    def generate_friend_code(self) -> str:
        while True:
            
            code = uuid.uuid4().hex[:8].upper()

            if not self.friend_repo.get_user_by_friend_code(code):
                return code
