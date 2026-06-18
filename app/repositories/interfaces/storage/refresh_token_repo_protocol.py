from typing import Protocol

from app.domain_models.refresh_token import RefreshToken


class RefreshTokenRepositoryProtocol(Protocol):

    def create(self, hashed_token: str, user_id: int): ...

    def get_by_token_hash(self, hashed_token: str) -> RefreshToken: ...

    def revoke(self, refresh_token: RefreshToken): ...
