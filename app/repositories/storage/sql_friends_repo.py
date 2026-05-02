from app.domain_models.friends import Friends
from app.database_models.friends_model import FriendsModel
from app.extensions import db
from app.domain_models.user import User


class SqlFriendsRepo:
    def get_friends(self, user: User, friend: User) -> Friends | None:
        db_obj = db.session.get(FriendsModel, (user, friend))
        if not db_obj:
            return None
        return Friends(
            user_id=db_obj.user,
            friend_id=db_obj.friend,
            status=db_obj.status
        )

    def create_friend_request(self, user: User, friend: User) -> bool:
        db_obj = FriendsModel(
            user_id=user,
            friend_id=friend,
            status="pending"
        )
        db.session.add(db_obj)
        db.session.commit()
        return True

    def update_friendship(self, friendship: Friends) -> bool:
        db_obj = db.session.get(FriendsModel, (friendship.user_id, friendship.friend_id))
        db_obj.status = friendship.status
        db.session.commit()
        return True