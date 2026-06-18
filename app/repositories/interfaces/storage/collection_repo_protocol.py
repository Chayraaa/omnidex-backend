from typing import Protocol


class CollectionRepoProtocol(Protocol):
    def find_by_user(
        self,
        *,
        user_id: int,
        query: str | None = None,
        sort: str = "newest",
        category: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list: ...

    def find_by_id_for_user(self, *, user_id: int, entry_id: int): ...
