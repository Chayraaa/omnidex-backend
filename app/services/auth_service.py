import datetime

from app.repositories.interfaces.storage.refresh_token_repo_protocol import RefreshTokenRepositoryProtocol
from app.repositories.interfaces.storage.user_repo_protocol import UserRepoProtocol
from app.services.password_service import PasswordService


class AuthService:
    def __init__(self, user_repo: UserRepoProtocol, refresh_token_repo: RefreshTokenRepositoryProtocol):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    def authenticate_local(self, email: str, password: str) -> tuple[str, str] | None:

        user = self.user_repo.get_user_by_email(email)

        if not user or user.oauth != "local":
            return None

        if not PasswordService.verify_password(
                password,
                user.hashed_password
        ):
            return None

        access_token = PasswordService.generate_access_token(user.id)

        refresh_token = PasswordService.generate_refresh_token()

        refresh_token_hash = PasswordService.hash_refresh_token(refresh_token)

        self.refresh_token_repo.create(
            user_id=user.id,
            hashed_token=refresh_token_hash,
        )

        return access_token, refresh_token

    def refresh_session(self, refresh_token: str) -> tuple[str, str] | None:

        refresh_token_hash = PasswordService.hash_refresh_token(refresh_token)

        session = self.refresh_token_repo.get_by_token_hash(refresh_token_hash)

        if not session:
            return None
        if session.revoked:
            return None

        if session.expires_in < datetime.datetime.now(datetime.timezone.utc):
            return None

        access_token = PasswordService.generate_access_token(session.user_id)

        new_refresh_token = PasswordService.generate_refresh_token()

        new_refresh_token_hash = PasswordService.hash_refresh_token(new_refresh_token)

        # rotation
        self.refresh_token_repo.revoke(session)

        self.refresh_token_repo.create(
            user_id=session.user_id,
            hashed_token=new_refresh_token_hash,
        )

        return access_token, new_refresh_token
