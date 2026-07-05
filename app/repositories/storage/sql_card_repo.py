from app.database_models.card_model import CardModel
from app.extensions import db
from app.repositories.interfaces.storage.card_repo_protocol import CardRepoProtocol


class SqlCardRepo(CardRepoProtocol):
    def create_card(
        self,
        *,
        user_id: int,
        name: str,
        image_key: str,
        card_summary: str | None,
        category: str | None = None,
        confidence: float | None = None,
        description: str | None = None,
        source_title: str | None = None,
        source_url: str | None = None,
        alternatives_json: str | None = None,
    ) -> tuple[int, str | None]:
        card = CardModel(
            user_id=user_id,
            name=name,
            image_key=image_key,
            card_summary=card_summary,
            category=category.lower() if category else None,
            confidence=confidence,
            description=description,
            source_title=source_title,
            source_url=source_url,
            alternatives_json=alternatives_json,
        )
        db.session.add(card)
        db.session.commit()
        created_at = card.created_at.isoformat() if card.created_at else None
        return int(card.id), created_at

    def card_name_exists(self, *, user_id: int, name: str) -> bool:
        return (
            db.session.query(CardModel.id)
            .filter(CardModel.user_id == user_id, CardModel.name == name)
            .first()
            is not None
        )

    def get_cards_by_friends(self, user_ids: list[int]):
        return (
            db.session.query(CardModel)
            .filter(CardModel.user_id.in_(user_ids))
            .order_by(CardModel.created_at.desc())
            .all()
        )

    def count_cards(self, user_id: int) -> int:
        return (
            db.session.query(CardModel).filter(CardModel.user_id == user_id).count()
        )
    def count_cards_by_category(self, user_id: int, category: str) -> int:
        return (
            db.session.query(CardModel).filter(CardModel.user_id == user_id, CardModel.category == category).count()
        )