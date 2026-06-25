from app.repositories.interfaces.storage.image_repo_protocol import ImageRepoProtocol
from app.repositories.interfaces.storage.image_storage_protocol import ImageStorageProtocol
from app.repositories.interfaces.storage.refresh_token_repo_protocol import RefreshTokenRepositoryProtocol
from app.repositories.interfaces.storage.user_repo_protocol import UserRepoProtocol
from app.repositories.interfaces.storage.card_repo_protocol import CardRepoProtocol
from app.repositories.interfaces.storage.collection_repo_protocol import CollectionRepoProtocol
from app.repositories.interfaces.storage.friends_repo_protocol import FriendsRepoProtocol
from app.repositories.interfaces.storage.notification_repo_protocol import NotificationRepoProtocol
from app.repositories.storage.minio_image_storage import MinioImageStorage
from app.repositories.storage.sql_image_repo import SqlImageRepo
from app.repositories.storage.sql_card_repo import SqlCardRepo
from app.repositories.storage.sql_collection_repo import SqlCollectionRepo
from app.repositories.storage.sql_refresh_token_repo import SqlRefreshTokenRepo
from app.repositories.storage.sql_user_repo import SqlUserRepo
from app.repositories.storage.sql_friends_repo import SqlFriendsRepo
from app.repositories.storage.sql_notification_repo import SqlNotificationRepo


# This is a unit of work. It groups repositories that depend on another.
# If you have multiple units of work that have the same use case but with different repositories as implementation,
# they need to have the same variable names.
class SqlUnitOfWork:
    def __init__(self):
        self.user_repo: UserRepoProtocol = SqlUserRepo()
        self.friends_repo: FriendsRepoProtocol = SqlFriendsRepo()
        self.image_repo: ImageRepoProtocol = SqlImageRepo()
        self.image_storage: ImageStorageProtocol = MinioImageStorage("images")
        self.refresh_token_repo: RefreshTokenRepositoryProtocol = SqlRefreshTokenRepo()
        self.notification_repo: NotificationRepoProtocol = SqlNotificationRepo()
        self.card_repo: CardRepoProtocol = SqlCardRepo()
        self.collection_repo: CollectionRepoProtocol = SqlCollectionRepo()
