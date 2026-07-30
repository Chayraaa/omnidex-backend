from app.database_models.deck_model import DeckModel
from app.domain_models.deck import Deck
from app.extensions import db


class SqlDeckRepo:
    def get_all_by_user(self, user_id: int) -> list[Deck]:
        db_decks = db.session.query(DeckModel).filter_by(user_id=user_id).all()
        return [self._to_domain(db_deck) for db_deck in db_decks]

    def get_main_by_user(self, user_id: int) -> Deck | None:
        db_deck = db.session.query(DeckModel).filter_by(user_id=user_id, is_main=True).first()
        return self._to_domain(db_deck) if db_deck else None

    def get_by_id(self, deck_id: int) -> Deck | None:
        db_deck = db.session.get(DeckModel, deck_id)
        if db_deck:
            return self._to_domain(db_deck)
        return None

    def create(self, user_id: int, name: str, deck_content: str) -> Deck:
        db_deck = DeckModel(user_id=user_id, name=name, deck=deck_content)
        db.session.add(db_deck)
        db.session.commit()
        return self._to_domain(db_deck)

    def update(self, deck_id: int, name: str | None = None, deck_content: str | None = None) -> Deck | None:
        db_deck = db.session.get(DeckModel, deck_id)
        if db_deck:
            if name is not None:
                db_deck.name = name
            if deck_content is not None:
                db_deck.deck = deck_content
            db.session.commit()
            return self._to_domain(db_deck)
        return None

    def set_main(self, user_id: int, deck_id: int) -> Deck | None:
        # Clear existing main deck for user
        db.session.query(DeckModel).filter_by(user_id=user_id, is_main=True).update({"is_main": False})
        db_deck = db.session.get(DeckModel, deck_id)
        if db_deck and db_deck.user_id == user_id:
            db_deck.is_main = True
            db.session.commit()
            return self._to_domain(db_deck)
        db.session.commit()
        return None

    def delete(self, deck_id: int) -> bool:
        db_deck = db.session.get(DeckModel, deck_id)
        if db_deck:
            db.session.delete(db_deck)
            db.session.commit()
            return True
        return False

    def _to_domain(self, db_deck: DeckModel) -> Deck:
        return Deck(
            id=db_deck.id,
            user_id=db_deck.user_id,
            name=db_deck.name,
            deck=db_deck.deck,
            is_main=db_deck.is_main,
        )
