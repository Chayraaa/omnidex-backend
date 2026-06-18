from app.database_models.refresh_token_model import RefreshTokenModel
from app.domain_models.refresh_token import RefreshToken
from app.extensions import db


class SqlRefreshTokenRepo:

    def create(self, hashed_token: str, user_id: int):
        new_token = RefreshTokenModel(token_hash=hashed_token, user_id=user_id)
        db.session.add(new_token)
        db.session.commit()

    def get_by_token_hash(self, hashed_token: str) -> RefreshToken:
        results: RefreshTokenModel = db.session.query(RefreshTokenModel).filter(
            RefreshTokenModel.token_hash == hashed_token).first()
        return RefreshToken(
            id=results.id,
            user_id=results.user_id,
            refresh_token=results.token_hash,
            expires_in=results.expires_at,
            created_at=results.created_at,
            revoked=results.revoked,
        )

    def revoke(self, refresh_token: RefreshToken):
        result = db.session.get(RefreshTokenModel, refresh_token.id)
        if not result:
            return
        result.revoked = True
        db.session.commit()
