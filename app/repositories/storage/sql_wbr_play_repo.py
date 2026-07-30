from app.database_models.wbr_play_model import WBRPlayModel
from app.extensions import db


class SqlWBRPlayRepo:

    def record_play(self, user_id: int, streak: int, highscore: int, won: bool, played_at) -> None:
        play = WBRPlayModel(
            user_id=user_id,
            streak=streak,
            highscore=highscore,
            won=won,
            played_at=played_at,
        )
        db.session.add(play)
        db.session.commit()

    def get_plays_by_user_ids(self, user_ids: list[int]) -> list[dict]:
        rows = db.session.query(WBRPlayModel).filter(
            WBRPlayModel.user_id.in_(user_ids)
        ).all()
        return [
            {
                "userId": r.user_id,
                "streak": r.streak,
                "highscore": r.highscore,
                "won": r.won,
                "playedAt": r.played_at.isoformat() if r.played_at else None,
            }
            for r in rows
        ]
