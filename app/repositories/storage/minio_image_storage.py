from datetime import timedelta
from typing import BinaryIO

from minio import Minio


class MinioImageStorage:
    def __init__(self, bucket: str):
        self.client = Minio(
            endpoint="minio:9000",
            access_key="minio",
            secret_key="minio_password",
            secure=False
        )
        self.bucket = bucket
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def save_image(self, key: str, image_data: BinaryIO) -> str:
        self.client.put_object(
            self.bucket,
            key,
            image_data,
            length=-1,
            part_size=10 * 1024 * 1024
        )

        return key

    def get_url(self, key: str) -> str:
        return self.client.presigned_get_object(
            self.bucket,
            key,
            expires=timedelta(minutes=10)
        )
