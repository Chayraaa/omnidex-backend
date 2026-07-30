from typing import Protocol

from app.domain_models.card_battle import CardBattleGame
from app.domain_models.user import User
from app.services.games.card_battle.card_battle import GameState


class CardBattleGameRepoInterface(Protocol):
    def __init__(self):
        ...

    def get_card_battle_game(self, game_id: int) -> CardBattleGame:
        ...

    def get_card_battle_games_by_player(self, player: User) -> list[CardBattleGame]:
        ...

    def create_card_battle_game(self, name: str, player1: User | None, player2: User | None, game_state: GameState) -> CardBattleGame:
        ...

    def update_card_battle_game(self, game: CardBattleGame) -> CardBattleGame:
        ...

    def delete_card_battle_game(self, game: CardBattleGame) -> None:
        ...

    def get_games_by_player_ids(self, player_ids: list[int]) -> list[CardBattleGame]:
        ...