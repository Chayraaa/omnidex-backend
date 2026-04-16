from app.domain_models.user import User
from app.database_models.user_model import UserModel
from app.extensions import db


# This is how the user_repo_protocol is implemented, note that it doesn't mention the protocol anywhere
# The protocol just defines the methods in a class the service should accept.
# Any class that provides these methods can be used as a user_repo_protocol
class SqlUserRepo:
    def get_user(self, user_id: int) -> User | None:
        db_user = db.session.get(UserModel, user_id)
        if not db_user:
            return None
        return User(id=db_user.id, name=db_user.name, hashed_password=db_user.password)

    def get_user_by_name(self, name: str) -> User | None:
        db_user = db.session.query(UserModel).filter_by(name=name).first()
        if not db_user:
            return None
        return User(id=db_user.id, name=db_user.name, hashed_password=db_user.password)

    def create_user(self, name: str, password: str) -> bool:
        db_user = UserModel(name=name, password=password)
        db.session.add(db_user)
        db.session.commit()
        return True
