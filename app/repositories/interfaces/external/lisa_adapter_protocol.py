from typing import Protocol, Any


class LisaAdapterProtocol(Protocol):
    def recognize_image(self, image_data: bytes) -> dict[str, Any]: ...
