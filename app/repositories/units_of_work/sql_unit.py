from app.repositories.interfaces.user_repo_protocol import UserRepoProtocol
from app.repositories.storage_repos.sql_user_repo import SqlUserRepo


# This is a unit of work. It groups repositories that depend on another.
# If you have multiple units of work that have the same use case but with different repositories as implementation,
# they need to have the same variable names.
class SqlUnitOfWork:
    def __init__(self):
        self.user_repo: UserRepoProtocol = SqlUserRepo()