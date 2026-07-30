from app.domain_models.user import User
from app.repositories.interfaces.storage.friends_repo_protocol import FriendsRepoProtocol
from app.repositories.interfaces.storage.user_repo_protocol import UserRepoProtocol
from app.repositories.interfaces.storage.card_repo_protocol import CardRepoProtocol
from app.repositories.interfaces.storage.card_battle_repo_interface import CardBattleGameRepoInterface
from app.repositories.interfaces.external.what_beats_rock_protocol import WhatBeatsRockProtocol
from enum import Enum


class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class FriendsService:
    def __init__(self, friends_repo: FriendsRepoProtocol, user_repo: UserRepoProtocol, card_repo: CardRepoProtocol, base_url: str, wbr_service: WhatBeatsRockProtocol = None, card_battle_repo: CardBattleGameRepoInterface = None):
        self.friends_repo = friends_repo
        self.user_repo = user_repo
        self.card_repo = card_repo
        self.base_url = base_url.rstrip("/")
        self.wbr_service = wbr_service
        self.card_battle_repo = card_battle_repo

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

        feed = []

        cards = self.card_repo.get_cards_by_friends(friend_ids)[:50]
        for c in cards:
            feed.append({
                "type": "card_discovered",
                "id": c.id,
                "firstDiscoveredUserId": c.user_id,
                "name": c.name,
                "pictureUrl": self._build_image_url(c.image_key),
                "description": c.card_summary,
                "category": c.category,
                "entryDate": c.created_at.isoformat() if c.created_at else None,
                "battleType": c.battle_type.value,
                "attack": c.attack,
                "health": c.health,
                "cost": c.cost,
            })

        if self.wbr_service:
            wbr_stats = self.wbr_service.get_wbr_stats_for_user_ids(friend_ids)
            for stat in wbr_stats:
                feed.append({
                    "type": "wbr_played",
                    "userId": stat["userId"],
                    "streak": stat["streak"],
                    "highscore": stat["highscore"],
                })

        if self.card_battle_repo:
            games = self.card_battle_repo.get_games_by_player_ids(friend_ids)
            for game in games:
                gs = game.game_state
                if not gs.p1_has_won and not gs.p2_has_won:
                    continue
                for friend_id in friend_ids:
                    if game.player1_id == friend_id:
                        feed.append({
                            "type": "card_battle_result",
                            "gameId": game.id,
                            "userId": friend_id,
                            "opponentId": game.player2_id,
                            "won": gs.p1_has_won,
                        })
                    elif game.player2_id == friend_id:
                        feed.append({
                            "type": "card_battle_result",
                            "gameId": game.id,
                            "userId": friend_id,
                            "opponentId": game.player1_id,
                            "won": gs.p2_has_won,
                        })

        return feed
