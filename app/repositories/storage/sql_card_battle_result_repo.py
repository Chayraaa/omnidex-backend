from datetime import datetime, timezone

from app.database_models.card_battle_result_model import CardBattleResultModel
from app.extensions import db


class SqlCardBattleResultRepo:

    def record_result(self, game_id: int, player1_id: int | None, player2_id: int | None, player1_won: bool) -> None:
        result = CardBattleResultModel(
            game_id=game_id,
            player1_id=player1_id,
            player2_id=player2_id,
            player1_won=player1_won,
            played_at=datetime.now(timezone.utc),
        )
        db.session.add(result)
        db.session.commit()

    def has_result_for_game(self, game_id: int) -> bool:
        return db.session.query(CardBattleResultModel).filter_by(game_id=game_id).first() is not None

    def get_results_by_player_ids(self, player_ids: list[int]) -> list[dict]:
        rows = db.session.query(CardBattleResultModel).filter(
            (CardBattleResultModel.player1_id.in_(player_ids)) |
            (CardBattleResultModel.player2_id.in_(player_ids))
        ).all()

        results = []
        for r in rows:
            for pid in player_ids:
                if r.player1_id == pid:
                    results.append({
                        "gameId": r.game_id,
                        "userId": pid,
                        "opponentId": r.player2_id,
                        "won": r.player1_won,
                        "playedAt": r.played_at.isoformat() if r.played_at else None,
                    })
                elif r.player2_id == pid:
                    results.append({
                        "gameId": r.game_id,
                        "userId": pid,
                        "opponentId": r.player1_id,
                        "won": not r.player1_won,
                        "playedAt": r.played_at.isoformat() if r.played_at else None,
                    })
        return results
