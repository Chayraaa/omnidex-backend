from app.domain_models.user import User
from app.repositories.interfaces.storage.friends_repo_protocol import FriendsRepoProtocol
from app.repositories.interfaces.storage.user_repo_protocol import UserRepoProtocol
from enum import Enum


class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class FriendsService:
    def __init__(self, friends_repo: FriendsRepoProtocol, user_repo: UserRepoProtocol, notification_service=None):
        self.friends_repo = friends_repo
        self.user_repo = user_repo
        self.notification_service = notification_service

    # SEND FRIEND REQUEST
    def create_friend_request(self, sender: User, friend_code: str) -> bool:
        receiver = self.friends_repo.get_user_by_friend_code(friend_code)

        if not receiver or sender.id == receiver.id:
            return False

        existing = self.friends_repo.get_friend_request(sender.id, receiver.id)

        if existing:
            return False

        self.friends_repo.create_friend_request(
            user=sender,
            friend=receiver,
            status=FriendshipStatus.PENDING.value
        )

        if self.notification_service:
            self.notification_service.send(
                user_id=receiver.id,
                type="friend_request",
                message=f"{sender.name} sent you a friend request"
            )

        return True
    
    # ACCEPT REQUEST
    def accept_friend_request(self, receiver: User, sender_id: int):
        friendship = self.friends_repo.get_friend_request(sender_id, receiver.id)

        if not friendship:
            return False

        if friendship.status != FriendshipStatus.PENDING.value:
            return False

        friendship.status = FriendshipStatus.ACCEPTED.value

        self.friends_repo.update_friend_request(friendship)
        return True


    # DECLINE REQUEST
    def decline_friend_request(self, receiver: User, sender_id: int):
        friendship = self.friends_repo.get_friend_request(sender_id, receiver.id)

        if not friendship:
            return False

        if friendship.status != FriendshipStatus.PENDING.value:
            return False

        friendship.status = FriendshipStatus.REJECTED.value

        self.friends_repo.delete_friendship(sender_id, receiver.id)
        return True

    # REMOVE FRIEND
    def remove_friend(self, user: User, friend_id: int):
        return self.friends_repo.delete_friendship(user.id, friend_id)

    # GET FRIENDS LIST
    def get_friends(self, user: User):
        friendships = self.friends_repo.get_friendships(user.id)

        return [
            f for f in friendships
        ]

