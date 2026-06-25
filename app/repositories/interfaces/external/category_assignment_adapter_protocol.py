from typing import Any, Protocol


class CategoryAssignmentAdapterProtocol(Protocol):
    def assign_category(self, prompt: str) -> dict[str, Any]: ...

