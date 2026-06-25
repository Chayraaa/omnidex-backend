import json

from app.domain_models.collection_entry_dto import (
    CollectionEntrySummaryDto,
    CollectionEntryDetailDto,
)
from app.repositories.interfaces.storage.collection_repo_protocol import CollectionRepoProtocol
from app.services.collection_errors import (
    CollectionEntryNotFound,
    InvalidCollectionSort,
    InvalidCollectionCategory,
    InvalidCollectionPagination,
)


class CollectionService:
    ALLOWED_SORTS = {"newest", "oldest", "alphabetical"}
    ALLOWED_CATEGORIES = {
        "Pflanze",
        "Insekten",
        "Tiere",
        "Nahrung",
        "Unbekannt",
        "Technik",
        "Mechanik",
        "Gestein",
        "Gegenstände",
    }

    def __init__(self, collection_repo: CollectionRepoProtocol, base_url: str):
        self.collection_repo = collection_repo
        self.base_url = base_url.rstrip("/")

    def get_user_collection(
        self,
        user_id: int,
        query: str | None = None,
        sort: str = "newest",
        category: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[CollectionEntrySummaryDto]:
        self._validate_user(user_id)
        self._validate_sort(sort)
        self._validate_category(category)
        self._validate_pagination(limit, offset)

        cards = self.collection_repo.find_by_user(
            user_id=user_id,
            query=query,
            sort=sort,
            category=category,
            limit=limit,
            offset=offset,
        )

        return [
            CollectionEntrySummaryDto(
                id=card.id,
                label=card.name,
                category=card.category,
                card_summary=card.card_summary,
                image_url=self._build_image_url(card.image_key),
                created_at=card.created_at.isoformat() if card.created_at else None,
                confidence=card.confidence,
            )
            for card in cards
        ]

    def get_collection_entry_detail(self, user_id: int, entry_id: int) -> CollectionEntryDetailDto:
        self._validate_user(user_id)
        if entry_id <= 0:
            raise CollectionEntryNotFound()

        card = self.collection_repo.find_by_id_for_user(user_id=user_id, entry_id=entry_id)
        if card is None:
            raise CollectionEntryNotFound()

        return self._to_detail_dto(card)

    def update_collection_entry_category(
        self,
        user_id: int,
        entry_id: int,
        category: str,
    ) -> CollectionEntryDetailDto:
        self._validate_user(user_id)
        if entry_id <= 0:
            raise CollectionEntryNotFound()
        self._validate_category(category)

        card = self.collection_repo.update_category_for_user(
            user_id=user_id,
            entry_id=entry_id,
            category=category,
        )
        if card is None:
            raise CollectionEntryNotFound()

        return self._to_detail_dto(card)

    def _to_detail_dto(self, card) -> CollectionEntryDetailDto:
        return CollectionEntryDetailDto(
            id=card.id,
            label=card.name,
            category=card.category,
            confidence=card.confidence,
            card_summary=card.card_summary,
            description=card.description,
            source_title=card.source_title,
            source_url=card.source_url,
            alternatives=self._parse_alternatives(card.alternatives_json),
            image_url=self._build_image_url(card.image_key),
            created_at=card.created_at.isoformat() if card.created_at else None,
        )

    @classmethod
    def _validate_sort(cls, sort: str):
        if sort not in cls.ALLOWED_SORTS:
            raise InvalidCollectionSort(
                f"Invalid sort value '{sort}'. Allowed: {', '.join(sorted(cls.ALLOWED_SORTS))}"
            )

    @classmethod
    def _validate_category(cls, category: str | None):
        if category is None:
            return
        if category not in cls.ALLOWED_CATEGORIES:
            raise InvalidCollectionCategory(
                f"Invalid category '{category}'. Allowed: {', '.join(sorted(cls.ALLOWED_CATEGORIES))}"
            )

    @staticmethod
    def _validate_pagination(limit: int | None, offset: int | None):
        if limit is not None and limit < 0:
            raise InvalidCollectionPagination("limit must be >= 0")
        if offset is not None and offset < 0:
            raise InvalidCollectionPagination("offset must be >= 0")

    @staticmethod
    def _validate_user(user_id: int):
        if user_id <= 0:
            raise CollectionEntryNotFound()

    @staticmethod
    def _parse_alternatives(alternatives_json: str | None) -> list[dict]:
        if not alternatives_json:
            return []
        try:
            parsed = json.loads(alternatives_json)
        except (TypeError, ValueError):
            return []
        if not isinstance(parsed, list):
            return []
        sanitized = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            label = item.get("label")
            confidence = item.get("confidence")
            if isinstance(label, str):
                sanitized.append({"label": label, "confidence": confidence})
        return sanitized

    def _build_image_url(self, image_key: str | None) -> str | None:
        if not isinstance(image_key, str) or not image_key.strip():
            return None
        if image_key.startswith("http://") or image_key.startswith("https://"):
            return image_key
        return f"{self.base_url}/api/image/{image_key.lstrip('/')}"
