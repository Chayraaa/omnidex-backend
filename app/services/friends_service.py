from app.domain_models.user import User
from app.repositories.interfaces.storage.friends_repo_protocol import FriendsRepoProtocol
from app.repositories.interfaces.storage.user_repo_protocol import UserRepoProtocol
from app.repositories.interfaces.storage.card_repo_protocol import CardRepoProtocol
from enum import Enum


class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class FriendsService:
    def __init__(self, friends_repo: FriendsRepoProtocol, user_repo: UserRepoProtocol, card_repo: CardRepoProtocol, base_url: str):
        self.friends_repo = friends_repo
        self.user_repo = user_repo
        self.card_repo = card_repo
        self.base_url = base_url.rstrip("/")

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

        return True

    # ACCEPT REQUEST
    def accept_friend_request(self, receiver: User, sender_id: int):
        friendship = self.friends_repo.get_friend_request(sender_id, receiver.id)
        print(sender_id)
        print(receiver.id)
        print(friendship)

        if not friendship or friendship.status != FriendshipStatus.PENDING.value:
            return False

        friendship.status = FriendshipStatus.ACCEPTED.value
        self.friends_repo.update_friend_request(friendship)
        return True

    # DECLINE REQUEST
    def decline_friend_request(self, receiver: User, sender_id: int):
        friendship = self.friends_repo.get_friend_request(sender_id, receiver.id)

        if not friendship or friendship.status != FriendshipStatus.PENDING.value:
            return False

        self.friends_repo.delete_friendship(sender_id, receiver.id)
        return True

    # REMOVE FRIEND
    def remove_friend(self, user: User, friend_id: int):
        return self.friends_repo.delete_friendship(user.id, friend_id)

    # GET FRIENDS LIST
    def get_friends(self, user: User):
        friendships = self.friends_repo.get_friendships(user.id)

        result = []

        for f in friendships:
            if f["status"] != FriendshipStatus.ACCEPTED.value:
                continue

            result.append({
                "friend_id": f["friend_id"],
                "name": f["name"],
                "profile_picture_key": f["profile_picture_key"],
                "status": f["status"]
            })

        return result

    # GET INCOMING REQUESTS (FIXED TO MATCH ROUTE)
    def get_incoming_requests(self, user: User):
        friendships = self.friends_repo.get_pending(user.id)

        return [
            {
                "sender_id": f["friend_id"],
                "name": f["name"],
                "profile_picture_key": f["profile_picture_key"],
                "status": f["status"]
            }
            for f in friendships
            if f["status"] == FriendshipStatus.PENDING.value
        ]

    def _build_image_url(self, image_key: str | None) -> str | None:
        if not isinstance(image_key, str) or not image_key.strip():
            return None
        if image_key.startswith("http://") or image_key.startswith("https://"):
            return image_key
        return f"{self.base_url}/v1/images/{image_key.lstrip('/')}"

    def get_friends_feed(self, user: User):
        friend_ids = self.friends_repo.get_friend_ids(user.id)

        if not friend_ids:
            return []

        cards = self.card_repo.get_cards_by_friends(friend_ids)[:50]

        return [
            {
                "id": c.id,
                "firstDiscoveredUserId": c.user_id,
                "name": c.name,
                "pictureUrl": self._build_image_url(c.image_key),
                "description": c.card_summary,
                "category": c.category,
                "entryDate": c.created_at.isoformat() if c.created_at else None,
            }
            for c in cards
        ]
