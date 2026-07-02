import uuid

from app.repositories.interfaces.storage.image_repo_protocol import ImageRepoProtocol
from app.repositories.interfaces.storage.refresh_token_repo_protocol import RefreshTokenRepositoryProtocol
from app.repositories.interfaces.storage.user_repo_protocol import UserRepoProtocol
from app.services.password_service import PasswordService


class GoogleOauthService:
    def __init__(
            self,
            user_repo: UserRepoProtocol,
            refresh_token_repo: RefreshTokenRepositoryProtocol,
    ):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo

    def authenticate_user(self, token: dict) -> tuple[str, str] | None:

        name: str = token.get("name", "")
        email: str = token.get("email", "")
        picture_url = token.get("picture", "")

        user = self.user_repo.get_user_by_email(email)

        if not user:
            self.user_repo.create_user(
                name=name,
                email=email,
                password="",
                oauth="google",
                friend_code=str(uuid.uuid4())[:8]
            )

            user = self.user_repo.get_user_by_email(email)

        if not user or user.oauth != "google":
            return None

        user.profile_picture_key = picture_url

        self.user_repo.update_user(user)

        access_token = (
            PasswordService.generate_access_token(user.id)
        )

        refresh_token = (
            PasswordService.generate_refresh_token()
        )

        refresh_token_hash = PasswordService.hash_refresh_token(refresh_token)

        self.refresh_token_repo.create(
            user_id=user.id,
            hashed_token=refresh_token_hash,
        )

        return access_token, refresh_token, user.id
