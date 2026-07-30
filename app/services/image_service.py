import base64
from io import BytesIO
from typing import BinaryIO
from uuid import uuid4

from app.domain_models.user import User
from app.repositories.interfaces.storage.image_repo_protocol import ImageRepoProtocol
from app.repositories.interfaces.storage.image_storage_protocol import ImageStorageProtocol


def base64_to_binary_io(data_url: str):
    _, b64_data = data_url.split(",", 1)
    file_bytes = base64.b64decode(b64_data)
    return BytesIO(file_bytes)


class ImageService:
    def __init__(self, storage: ImageStorageProtocol, image_repo: ImageRepoProtocol, base_url: str = "http://127.0.0.1:5000", image_path: str = "v1/images"):
        self.storage = storage
        self.image_repo = image_repo
        self.base_url = base_url.rstrip("/")
        self.image_path = image_path.lstrip("/").rstrip("/")

    def save_image(self, user: User, image_base64: str, is_profile_picture: bool = False) -> bool:
        if is_profile_picture and user.profile_picture_key:
            old_key = self._extract_minio_key(user.profile_picture_key)
            if old_key:
                try:
                    self.storage.delete_image(old_key)
                except Exception:
                    pass
        extension = _infer_data_url_extension(image_base64)
        key = f"{'profile_pictures' if is_profile_picture else 'cards'}/{user.id}/{uuid4()}.{extension}"
        converted_image: BinaryIO = base64_to_binary_io(image_base64)
        self.storage.save_image(key, converted_image)
        if is_profile_picture:
            self.image_repo.save_user_image(f"{self.base_url}/{self.image_path}/{key}", user.id)
        return True

    def delete_user_images(self, user: User) -> None:
        if user.profile_picture_key:
            minio_key = self._extract_minio_key(user.profile_picture_key)
            if minio_key:
                try:
                    self.storage.delete_image(minio_key)
                except Exception:
                    pass
        for key in self.image_repo.get_card_keys_by_user_id(user.id):
            minio_key = self._extract_minio_key(key)
            if minio_key:
                try:
                    self.storage.delete_image(minio_key)
                except Exception:
                    pass

    def _extract_minio_key(self, url: str) -> str | None:
        prefix = f"{self.base_url}/{self.image_path}/"
        if url.startswith(prefix):
            return url[len(prefix):]
        if not url.startswith("http://") and not url.startswith("https://"):
            return url.lstrip("/")
        return None

    def get_user_image_url(self, user: User) -> str:
        if not self.image_repo.has_profile_picture(user.id):
            return ""
        key = self.image_repo.get_user_key_by_id(user.id)
        return f"{key}"

    def get_card_image_url(self, user: User) -> list[str]:
        keys = self.image_repo.get_card_keys_by_user_id(user.id)
        urls = [_build_image_url_from_key(self.base_url, self.image_path, key) for key in keys]
        return urls

    def get_image_stream(self, key: str):
        return self.storage.get_image(key)


def _infer_data_url_extension(data_url: str) -> str:
    if not isinstance(data_url, str):
        return "jpeg"
    header = data_url.split(",", 1)[0].lower()
    if "image/png" in header:
        return "png"
    if "image/webp" in header:
        return "webp"
    return "jpeg"


def _build_image_url_from_key(base_url: str, image_path: str, key: str) -> str:
    if key.startswith("http://") or key.startswith("https://"):
        return key
    return f"{base_url}/{image_path}/{key.lstrip('/')}"
