import pathlib
import sys
import types
import unittest
from dataclasses import dataclass
from datetime import datetime

# Prevent app/__init__.py side effects during unit tests.
if "app" not in sys.modules:
    app_package = types.ModuleType("app")
    app_package.__path__ = [str(pathlib.Path(__file__).resolve().parents[1] / "app")]
    sys.modules["app"] = app_package

from app.services.collection_errors import (
    CollectionEntryNotFound,
    InvalidCollectionCategory,
    InvalidCollectionSort,
)
from app.services.collection_service import CollectionService


@dataclass
class _FakeCard:
    id: int
    user_id: int
    name: str
    category: str | None
    card_summary: str | None
    image_key: str | None
    created_at: datetime
    confidence: float | None
    description: str | None = None
    source_title: str | None = None
    source_url: str | None = None
    alternatives_json: str | None = None


class _FakeCollectionRepo:
    def __init__(self, cards: list[_FakeCard]):
        self.cards = cards

    def find_by_user(
        self,
        *,
        user_id: int,
        query: str | None = None,
        sort: str = "newest",
        category: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[_FakeCard]:
        rows = [card for card in self.cards if card.user_id == user_id]

        if query:
            q = query.lower()
            rows = [
                card
                for card in rows
                if q in card.name.lower()
                or (card.card_summary and q in card.card_summary.lower())
                or (card.description and q in card.description.lower())
            ]
        if category:
            rows = [card for card in rows if card.category == category]

        if sort == "alphabetical":
            rows.sort(key=lambda card: (card.name, card.id))
        else:
            rows.sort(key=lambda card: (card.created_at, card.id), reverse=(sort == "newest"))

        if offset is not None:
            rows = rows[offset:]
        if limit is not None:
            rows = rows[:limit]

        return rows

    def find_by_id_for_user(self, *, user_id: int, entry_id: int):
        for card in self.cards:
            if card.user_id == user_id and card.id == entry_id:
                return card
        return None

    def update_category_for_user(self, *, user_id: int, entry_id: int, category: str):
        card = self.find_by_id_for_user(user_id=user_id, entry_id=entry_id)
        if card is None:
            return None
        card.category = category
        return card


class CollectionServiceTests(unittest.TestCase):
    def setUp(self):
        self.cards = [
            _FakeCard(
                id=1,
                user_id=1,
                name="rose",
                category="Pflanze",
                card_summary="Rose summary",
                image_key="cards/1/rose.jpg",
                created_at=datetime(2026, 5, 1, 12, 0, 0),
                confidence=0.9,
                description="A rose flower",
                source_title="Rose",
                source_url="https://example.org/rose",
                alternatives_json='[{"label":"flower","confidence":0.3}]',
            ),
            _FakeCard(
                id=2,
                user_id=1,
                name="cat",
                category="Tiere",
                card_summary="Cat summary",
                image_key="cards/1/cat.jpg",
                created_at=datetime(2026, 5, 2, 12, 0, 0),
                confidence=0.95,
                description="A cat mammal",
            ),
            _FakeCard(
                id=3,
                user_id=2,
                name="pizza",
                category="Nahrung",
                card_summary="Pizza summary",
                image_key="cards/2/pizza.jpg",
                created_at=datetime(2026, 5, 3, 12, 0, 0),
                confidence=0.88,
                description="A pizza dish",
            ),
        ]
        self.service = CollectionService(
            _FakeCollectionRepo(self.cards),
            base_url="http://127.0.0.1:5000",
        )

    def test_returns_only_entries_for_current_user(self):
        items = self.service.get_user_collection(user_id=1)
        self.assertEqual([item.id for item in items], [2, 1])

    def test_search_by_label_returns_matching_entries(self):
        items = self.service.get_user_collection(user_id=1, query="rose")
        self.assertEqual([item.label for item in items], ["rose"])

    def test_search_does_not_return_other_users_entries(self):
        items = self.service.get_user_collection(user_id=1, query="pizza")
        self.assertEqual(items, [])

    def test_sort_newest_returns_newest_first(self):
        items = self.service.get_user_collection(user_id=1, sort="newest")
        self.assertEqual([item.id for item in items], [2, 1])

    def test_sort_oldest_returns_oldest_first(self):
        items = self.service.get_user_collection(user_id=1, sort="oldest")
        self.assertEqual([item.id for item in items], [1, 2])

    def test_sort_alphabetical_returns_labels_ascending(self):
        items = self.service.get_user_collection(user_id=1, sort="alphabetical")
        self.assertEqual([item.label for item in items], ["cat", "rose"])

    def test_category_filter_returns_only_matching_category(self):
        items = self.service.get_user_collection(user_id=1, category="Pflanze")
        self.assertEqual([item.label for item in items], ["rose"])

    def test_invalid_sort_raises(self):
        with self.assertRaises(InvalidCollectionSort):
            self.service.get_user_collection(user_id=1, sort="random")

    def test_invalid_category_raises(self):
        with self.assertRaises(InvalidCollectionCategory):
            self.service.get_user_collection(user_id=1, category="ANIMAL")

    def test_detail_lookup_returns_entry_for_owner(self):
        detail = self.service.get_collection_entry_detail(user_id=1, entry_id=1)
        payload = detail.to_dict()
        self.assertEqual(payload["id"], 1)
        self.assertEqual(payload["label"], "rose")
        self.assertEqual(payload["image_url"], "http://127.0.0.1:5000/api/image/cards/1/rose.jpg")
        self.assertEqual(payload["alternatives"], [{"label": "flower", "confidence": 0.3}])
        self.assertNotIn("provider_raw", payload)

    def test_list_builds_public_image_urls_from_stored_keys(self):
        items = self.service.get_user_collection(user_id=1)
        self.assertEqual(items[0].image_url, "http://127.0.0.1:5000/api/image/cards/1/cat.jpg")

    def test_detail_lookup_does_not_return_entry_for_other_user(self):
        with self.assertRaises(CollectionEntryNotFound):
            self.service.get_collection_entry_detail(user_id=1, entry_id=3)

    def test_update_category_for_owner_returns_updated_detail(self):
        detail = self.service.update_collection_entry_category(
            user_id=1,
            entry_id=1,
            category="Tiere",
        )

        self.assertEqual(detail.category, "Tiere")
        self.assertEqual(self.cards[0].category, "Tiere")

    def test_update_category_does_not_update_other_users_entry(self):
        with self.assertRaises(CollectionEntryNotFound):
            self.service.update_collection_entry_category(
                user_id=1,
                entry_id=3,
                category="Tiere",
            )
        self.assertEqual(self.cards[2].category, "Nahrung")

    def test_update_category_rejects_invalid_category(self):
        with self.assertRaises(InvalidCollectionCategory):
            self.service.update_collection_entry_category(
                user_id=1,
                entry_id=1,
                category="ANIMAL",
            )


if __name__ == "__main__":
    unittest.main()
