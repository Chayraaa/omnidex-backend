from app.domain_models.friends import Friends
from app.database_models.friends_model import FriendsModel
from app.database_models.user_model import UserModel
from app.extensions import db
from app.domain_models.user import User
from app.services.friends_service import FriendshipStatus


class SqlFriendsRepo:

    def get_friend_request(self, sender_id: int, receiver_id: int) -> Friends | None:
        db_obj = db.session.query(FriendsModel).filter(
            (FriendsModel.user_id == sender_id) &
            (FriendsModel.friend_id == receiver_id)
        ).first()

        if not db_obj:
            return None

        return Friends(
            user_id=db_obj.user_id,
            friend_id=db_obj.friend_id,
            status=db_obj.status
        )

    def create_friend_request(self, user: User, friend: User, status: str) -> Friends:
        db_obj = FriendsModel(
            user_id=user.id,
            friend_id=friend.id,
            status=status
        )

        db.session.add(db_obj)
        db.session.commit()

        return Friends(
            user_id=db_obj.user_id,
            friend_id=db_obj.friend_id,
            status=db_obj.status
        )

    def update_friend_request(self, friendship: Friends) -> Friends:
        db_obj = db.session.query(FriendsModel).filter(
            (FriendsModel.user_id == friendship.user_id) &
            (FriendsModel.friend_id == friendship.friend_id)
        ).first()

        if not db_obj:
            raise ValueError("Friendship not found")

        db_obj.status = friendship.status
        db.session.commit()

        return Friends(
            user_id=db_obj.user_id,
            friend_id=db_obj.friend_id,
            status=db_obj.status
        )

    def get_friendships(self, user_id: int) -> list[dict]:
        rows = (
            db.session.query(FriendsModel, UserModel)
            .join(
                UserModel,
                (
                    ((FriendsModel.user_id == user_id) & (UserModel.id == FriendsModel.friend_id))
                    |
                    ((FriendsModel.friend_id == user_id) & (UserModel.id == FriendsModel.user_id))
                )
            )
            .filter(
                (FriendsModel.user_id == user_id) |
                (FriendsModel.friend_id == user_id)
            )
            .all()
        )

        result = []

        for friendship, other_user in rows:
            if friendship.user_id == user_id:
                other_user_id = friendship.friend_id
            else:
                other_user_id = friendship.user_id

            result.append({
                "friend_id": other_user_id,
                "name": other_user.name,
                "profile_picture_key": other_user.profile_picture_key,
                "status": friendship.status,
            })

        return result

    def get_pending(self, user_id: int) -> list[dict]:
        rows = (
            db.session.query(FriendsModel, UserModel)
            .join(
                UserModel,
                (
                        (UserModel.id == FriendsModel.friend_id)
                )
            )
            .filter(
                (FriendsModel.friend_id == user_id) &
                (FriendsModel.status == FriendshipStatus.PENDING.value)
            )
            .all()
        )
        print(rows)
        return [
            {
                "friend_id": friendship.user_id,
                "name": other_user.name,
                "profile_picture_key": other_user.profile_picture_key,
                "status": friendship.status,
            }
            for friendship, other_user in rows
        ]
    

    def delete_friendship(self, user_id: int, friend_id: int) -> bool:
        db_obj = db.session.query(FriendsModel).filter(
            (
                (FriendsModel.user_id == user_id) &
                (FriendsModel.friend_id == friend_id)
            ) |
            (
                (FriendsModel.user_id == friend_id) &
                (FriendsModel.friend_id == user_id)
            )
        ).first()

        if not db_obj:
            return False

        db.session.delete(db_obj)
        db.session.commit()
        return True

    def get_user_by_friend_code(self, friend_code: str) -> User | None:
        db_obj = UserModel.query.filter_by(friend_code=friend_code).first()

        if not db_obj:
            return None

        return User(
            id=db_obj.id,
            name=db_obj.name,
            hashed_password=db_obj.password,
            oauth=db_obj.oauth_method,
            profile_picture_key=db_obj.profile_picture_key,
            email=db_obj.email,
            friend_code=db_obj.friend_code,
        )

    def delete_rejected_friend_requests(self) -> int:
        deleted_count = (
            db.session.query(FriendsModel)
            .filter(FriendsModel.status == FriendshipStatus.REJECTED.value)
            .delete(synchronize_session=False)
        )

        db.session.commit()
        return deleted_count
    
    def get_friend_ids(self, user_id: int) -> list[int]:
        rows = (
            db.session.query(FriendsModel)
            .filter(
                ((FriendsModel.user_id == user_id) | (FriendsModel.friend_id == user_id)),
                FriendsModel.status == "accepted"
            )
            .all()
        )

        friend_ids = []

        for r in rows:
            if r.user_id == user_id:
                friend_ids.append(r.friend_id)
            else:
                friend_ids.append(r.user_id)

        return friend_ids