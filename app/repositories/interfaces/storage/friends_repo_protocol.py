from typing import Protocol
from app.domain_models.friends import Friends
from app.domain_models.user import User


class FriendsRepoProtocol(Protocol):

    def create_friend_request(self,user:User, friend: User) -> Friends: ...

    def update_friend_request(self, friends: Friends) -> bool: ...

    def get_friendships(self, user_id: User) -> Friends: ...