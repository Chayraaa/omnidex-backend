from datetime import datetime, timezone

from app.database_models.card_battle_model import CardBattleGameModel
from app.extensions import db
from app.domain_models.card_battle import CardBattleGame
from app.domain_models.user import User
from app.repositories.interfaces.storage.card_battle_repo_interface import CardBattleGameRepoInterface
from app.services.games.card_battle.card_battle import GameState


class SqlCardBattleRepo:
    def __init__(self):
        self.session = db.session

    @staticmethod
    def _to_domain(model: CardBattleGameModel) -> CardBattleGame:
        return CardBattleGame(
            id=model.id,
            name=model.name,
            player1_id=model.player1_id,
            player2_id=model.player2_id,
            game_state=GameState.from_json(model.game_state),
            created_at=model.created_at,
        )

    def get_card_battle_game(self, game_id: int) -> CardBattleGame:
        model = self.session.get(CardBattleGameModel, game_id)
        if not model:
            return None
        return self._to_domain(model)

    def get_card_battle_games_by_player(self, player: User) -> list[CardBattleGame]:
        models1 = self.session.query(CardBattleGameModel).filter_by(player1_id=player.id).all()
        models2 = self.session.query(CardBattleGameModel).filter_by(player2_id=player.id).all()
        return [self._to_domain(m) for m in models1 + models2]

    def create_card_battle_game(self, name: str, player1: User | None, player2: User | None,
                                game_state: GameState) -> CardBattleGame:
        id1 = player1.id if player1 else None
        id2 = player2.id if player2 else None
        model = CardBattleGameModel(name=name, player1_id=id1, player2_id=id2, game_state=game_state.to_json(), created_at=datetime.now(timezone.utc))
        self.session.add(model)
        self.session.commit()
        return self._to_domain(model)

    def update_card_battle_game(self, game: CardBattleGame) -> CardBattleGame:
        model = self.session.get(CardBattleGameModel, game.id)
        if not model:
            return None
        model.name = game.name
        model.game_state = game.game_state.to_json()
        model.player1_id = game.player1_id
        model.player2_id = game.player2_id
        self.session.commit()
        return self._to_domain(model)

    def delete_card_battle_game(self, game: CardBattleGame) -> None:
        model = self.session.get(CardBattleGameModel, game.id)
        if model:
            self.session.delete(model)
            self.session.commit()

    def get_games_by_player_ids(self, player_ids: list[int]) -> list[CardBattleGame]:
        models = self.session.query(CardBattleGameModel).filter(
            (CardBattleGameModel.player1_id.in_(player_ids)) |
            (CardBattleGameModel.player2_id.in_(player_ids))
        ).all()
        return [self._to_domain(m) for m in models]