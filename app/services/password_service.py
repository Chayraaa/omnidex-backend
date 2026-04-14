import hashlib

from passlib.context import CryptContext

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordService:

    @staticmethod
    def hash_password(password: str) -> str:
        digest = hashlib.sha256(password.encode()).hexdigest()
        return password_context.hash(digest)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        digest = hashlib.sha256(password.encode()).hexdigest()
        return password_context.verify(digest, hashed_password)