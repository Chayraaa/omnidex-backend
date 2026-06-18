import datetime
import hashlib
import hmac
import os
import secrets

import jwt
from passlib.context import CryptContext

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
jwt_secret_key = os.environ.get("JWT_SECRET")
if not jwt_secret_key:
    raise ValueError("JWT_SECRET environment variable is not set")


class PasswordService:

    @staticmethod
    def hash_password(password: str) -> str:
        return password_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return password_context.verify(password, hashed_password)

    @staticmethod
    def hash_refresh_token(token: str) -> str:
        return hmac.new(
            jwt_secret_key.encode(),
            token.encode(),
            hashlib.sha256
        ).hexdigest()

    # Generate a JWT token for the user
    @staticmethod
    def generate_access_token(user_id: int):
        payload = {
            "id": user_id,
            "type": "access",
            "exp": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).timestamp(),
        }

        return jwt.encode(payload, jwt_secret_key, algorithm="HS256")

    @staticmethod
    def generate_refresh_token():
        return secrets.token_urlsafe(64)

    # Checks the provided token and returns the user id if valid
    @staticmethod
    def verify_token(token: str):
        try:
            payload = jwt.decode(token, jwt_secret_key, algorithms=["HS256"])
            if payload.get("type") != "access":
                return None
            return payload.get("id")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
