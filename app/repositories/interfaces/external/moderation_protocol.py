from typing import Protocol


class ModerationProtocol(Protocol):

    def __init__(self): ...

    def is_safe(self, image: bytes) -> bool: ...