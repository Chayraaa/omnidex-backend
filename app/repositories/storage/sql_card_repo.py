from app.database_models.card_model import CardModel
from app.domain_models.card import Card, BattleType
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
            battle_type: str | None = None,
            attack: int | None = None,
            health: int | None = None,
            cost: int | None = None,
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
            battle_type=battle_type if battle_type else BattleType.FIGHTER.value,
            attack=attack if attack is not None else 10,
            health=health if health is not None else 10,
            cost=cost if cost is not None else 1,
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

    def get_cards_by_friends(self, user_ids: list[int]) -> list[Card]:
        models = (
            db.session.query(CardModel)
            .filter(CardModel.user_id.in_(user_ids))
            .order_by(CardModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def count_cards(self, user_id: int) -> int:
        return (
            db.session.query(CardModel).filter(CardModel.user_id == user_id).count()
        )

    def count_cards_by_category(self, user_id: int, category: str) -> int:
        return (
            db.session.query(CardModel).filter(CardModel.user_id == user_id, CardModel.category == category).count()
        )

    def get_card_by_id(self, card_id: int) -> Card | None:
        model = db.session.query(CardModel).filter(CardModel.id == card_id).first()
        if not model:
            return None
        return self._to_domain(model)

    def get_cards_by_ids(self, card_ids: list[int]) -> list[Card]:
        models = db.session.query(CardModel).filter(CardModel.id.in_(card_ids)).all()
        # Maintain order and handle duplicates if card_ids has them
        model_map = {m.id: m for m in models}
        return [self._to_domain(model_map[cid]) for cid in card_ids if cid in model_map]

    def get_all_by_user(self, user_id: int) -> list[Card]:
        models = db.session.query(CardModel).filter(CardModel.user_id == user_id).all()
        return [self._to_domain(model) for model in models]

    def _to_domain(self, model: CardModel) -> Card:
        return Card(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            image_key=model.image_key,
            category_id=model.category_id,
            card_summary=model.card_summary,
            category=model.category,
            confidence=model.confidence,
            description=model.description,
            source_title=model.source_title,
            source_url=model.source_url,
            alternatives_json=model.alternatives_json,
            created_at=model.created_at,
            battle_type=BattleType(model.battle_type),
            attack=model.attack,
            health=model.health,
            cost=model.cost
        )