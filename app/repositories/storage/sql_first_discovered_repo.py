from app.domain_models.first_discovered import FirstDiscovered
from app.database_models.first_discovered_model import FirstDiscoveredModel
from app.extensions import db
from app.domain_models.card import Card


class SqlFirstDiscoveredRepo:
    def get(self, card: Card) -> FirstDiscovered | None:
        db_obj = db.session.get(FirstDiscoveredModel, card)
        if not db_obj:
            return None
        return FirstDiscovered(card_id=db_obj.card)

    def create(self, card: Card) -> bool:
        db_obj = FirstDiscoveredModel(card=card)
        db.session.add(db_obj)
        db.session.commit()
        return True