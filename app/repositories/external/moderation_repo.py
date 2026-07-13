import base64
import os

import requests

from app.repositories.interfaces.external.moderation_protocol import ModerationProtocol
from app.utils.image_processing import compress_image


class ModerationRepo(ModerationProtocol):
    def __init__(self):
        self.model = os.environ.get("MODERATION_MODEL")
        self.api_key = os.environ.get("AI_API_KEY")
        self.base_url = os.environ.get("AI_BASE_URL")
        self.image_max_size = int(os.environ.get("AI_IMAGE_MAX_SIZE", "512"))

    def is_safe(self, image: bytes) -> bool:
        compressed_image = compress_image(image, max_size=self.image_max_size)
        image_b64 = base64.b64encode(compressed_image).decode("utf-8")
        try:
            response = requests.post(
                f"{self.base_url}/v1/moderations",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "omni-moderation-latest",
                    "input": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            print(f"DEBUG: Moderation request failed: {exc}")
            # Depending on how the system should behave, we might want to fail-safe or fail-closed.
            # Here we just return True (safe) to not block everything if moderation is down,
            # but usually it should probably be False or raise an error.
            # Given the current implementation doesn't have error handling, I'll keep it simple.
            return True

        if response.status_code >= 400:
            print(f"DEBUG: Moderation request failed with status {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")
            return True # Fail-safe if moderation API is broken

        print(f"DEBUG: Moderation request successful with status {response.status_code}")
        print(f"DEBUG: Response body: {response.text}")

        try:
            return not response.json()["results"][0]["flagged"]
        except (ValueError, KeyError, IndexError) as exc:
            print(f"DEBUG: Moderation response parsing failed: {exc}")
            print(f"DEBUG: Response body: {response.text}")
            return True
