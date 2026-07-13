from typing import Protocol, Any


class RecognitionAdapterProtocol(Protocol):
    def recognize_image(self, image_data: bytes) -> dict[str, Any]: ...
