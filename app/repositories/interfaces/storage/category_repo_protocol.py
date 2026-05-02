from typing import Protocol
from app.domain_models.category import Category


class CategoryRepoProtocol(Protocol):

    def get_category(self, category_id: int) -> Category | None: ...

    def get_category_by_name(self, name: str) -> Category | None: ...
