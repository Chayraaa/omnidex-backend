from app.domain_models.card import Card
from app.domain_models.user import User
from app.domain_models.category import Category
from app.database_models.card_model import CardModel
from app.extensions import db


class SqlCardRepo:
    def get_card(self, card: Card) -> Card | None:
        db_obj = db.session.get(CardModel, card)
        if not db_obj:
            return None
        return Card(db_obj.id, db_obj.name, db_obj.image_key, db_obj.user_id, db_obj.category_id)

    def get_card_by_name(self, name: str) -> Card | None:
        db_obj = db.session.query(CardModel).filter_by(name=name).first()
        if not db_obj:
            return None
        return Card(db_obj.id, db_obj.name, db_obj.image_key, db_obj.user_id, db_obj.category_id)

    def create_card(self, name: str, image_key: str, user: User, category: Category) -> bool:
        db_obj = CardModel(name=name, image_key=image_key, user_id=user.id, category_id=category.id)
        db.session.add(db_obj)
        db.session.commit()
        return True

    def update_card(self, card: Card) -> bool:
        db_obj = db.session.get(CardModel, card.id)
        db_obj.name = card.name
        db_obj.image_key = card.image_key
        db_obj.user_id = card.user_id
        db_obj.category_id = card.category_id
        db.session.commit()
        return True