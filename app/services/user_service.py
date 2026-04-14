from app.domain_models.user import User
from app.repositories.interfaces.user_repo_protocol import UserRepoProtocol
from app.services.password_service import PasswordService

# The user service is completely decoupled from the database. It just interacts with repo
# repo is the protocol defined. It will accept any Object that provides the methods requested
# by the protocol. See SqlUserRepo for an example.
class UserService:
    def __init__(self, repo: UserRepoProtocol):
        self.repo = repo

    def get_user(self, user_id: int) -> User | None:
        return self.repo.get_user(user_id)

    def get_user_by_name(self, name: str) -> User | None:
        return self.repo.get_user_by_name(name)

    def create_user(self, name: str, password: str) -> bool:
        if self.repo.get_user_by_name(name):
            return False
        hashed_password = PasswordService.hash_password(password)
        return self.repo.create_user(name, hashed_password)
