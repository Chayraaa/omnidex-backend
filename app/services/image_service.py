import base64
from io import BytesIO
from typing import BinaryIO
from uuid import uuid4

from app.domain_models.user import User
from app.repositories.interfaces.storage.image_repo_protocol import ImageRepoProtocol
from app.repositories.interfaces.storage.image_storage_protocol import ImageStorageProtocol


def base64_to_binary_io(data_url: str):
    # Split header + data
    header, b64_data = data_url.split(",", 1)

    # Decode base64 → bytes
    file_bytes = base64.b64decode(b64_data)

    # Wrap as file-like object
    return BytesIO(file_bytes)


class ImageService:
    def __init__(self, storage: ImageStorageProtocol, image_repo: ImageRepoProtocol):
        self.storage = storage
        self.image_repo = image_repo

    def save_image(self, user: User, image_base64: str, is_profile_picture: bool = False) -> bool:
        key = f"{'profile_pictures' if is_profile_picture else 'cards'}/{user.id}/{uuid4()}.jpeg"
        converted_image: BinaryIO = base64_to_binary_io(image_base64)
        self.storage.save_image(key, converted_image)
        if is_profile_picture:
            self.image_repo.save_user_image(key, user.id)
        else:
            self.image_repo.save_card_image(key, user.id)
        return True

    def get_user_image_url(self, user: User) -> str:
        if not self.image_repo.has_profile_picture(user.id):
            return ""
        return self.storage.get_url(self.image_repo.get_user_key_by_id(user.id))

    def get_card_image_url(self, user: User) -> list[str]:
        keys = self.image_repo.get_card_keys_by_user_id(user.id)
        urls = [self.storage.get_url(key) for key in keys]
        return urls
