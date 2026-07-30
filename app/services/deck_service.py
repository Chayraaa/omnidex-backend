from app.domain_models.deck import Deck
from app.repositories.interfaces.storage.deck_repo_protocol import DeckRepoProtocol


class DeckService:
    def __init__(self, deck_repo: DeckRepoProtocol):
        self.deck_repo = deck_repo

    def get_user_decks(self, user_id: int) -> list[Deck]:
        return self.deck_repo.get_all_by_user(user_id)

    def create_deck(self, user_id: int, name: str, deck_content: str) -> Deck:
        return self.deck_repo.create(user_id, name, deck_content)

    def update_deck(self, user_id: int, deck_id: int, name: str | None = None, deck_content: str | None = None) -> Deck:
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck or deck.user_id != user_id:
            raise ValueError("Deck not found or does not belong to user")
        
        updated_deck = self.deck_repo.update(deck_id, name, deck_content)
        if not updated_deck:
             raise ValueError("Failed to update deck")
        return updated_deck

    def set_main_deck(self, user_id: int, deck_id: int) -> Deck:
        result = self.deck_repo.set_main(user_id, deck_id)
        if not result:
            raise ValueError("Deck not found or does not belong to user")
        return result

    def delete_deck(self, user_id: int, deck_id: int) -> bool:
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck or deck.user_id != user_id:
            raise ValueError("Deck not found or does not belong to user")
        
        return self.deck_repo.delete(deck_id)
