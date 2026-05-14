from app.database_models.card_model import CardModel
from app.extensions import db
from app.repositories.interfaces.storage.card_repo_protocol import CardRepoProtocol


class SqlCardRepo(CardRepoProtocol):
    def create_card(self, *, user_id: int, name: str, image_key: str, card_summary: str | None) -> int:
        card = CardModel(
            user_id=user_id,
            name=name,
            image_key=image_key,
            card_summary=card_summary,
        )
        db.session.add(card)
        db.session.commit()
        return int(card.id)

    def card_name_exists(self, *, user_id: int, name: str) -> bool:
        return (
            db.session.query(CardModel.id)
            .filter(CardModel.user_id == user_id, CardModel.name == name)
            .first()
            is not None
        )
