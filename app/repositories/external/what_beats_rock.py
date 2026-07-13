from app.database_models.wbr_model import WBRModel
from app.domain_models.card import Card
from app.domain_models.wbr import WBR
from app.extensions import db
from app.domain_models.user import User
from app.repositories.interfaces.external.what_beats_rock_protocol import WhatBeatsRockProtocol
from app.repositories.interfaces.storage.user_repo_protocol import UserRepoProtocol
from app.repositories.interfaces.external.wbr_adapter_protocol import WBRAdapterProtocol
from app.services.wbr_errors import DuplicateCardError


class WhatBeatsRock(WhatBeatsRockProtocol):
    def __init__(self, user_repo: UserRepoProtocol, wbr_adapter: WBRAdapterProtocol):
        self.user_repo = user_repo
        self.wbr_adapter = wbr_adapter

    def does_beat(self, attacker: Card, user: User) -> tuple[bool, str]:
        wbr_model = db.session.get(WBRModel, user.id)
        if wbr_model is None:
            wbr_model = WBRModel(user_id=user.id, id=user.id)
            db.session.add(wbr_model)
            db.session.commit()
        
        # Check history
        history_list = wbr_model.history.split(",") if wbr_model.history else []
        if str(attacker.id) in history_list:
            raise DuplicateCardError("Du hast diese Karte bereits in diesem Streak verwendet!")

        defender_name = self.get_current_defender_name(user)
        beats, message = self.wbr_adapter.evaluate_match(attacker.name, defender_name)

        if beats:
            wbr_model.streak += 1
            wbr_model.defender_id = attacker.id
            # Update history
            history_list.append(str(attacker.id))
            wbr_model.history = ",".join(history_list)
        else:
            self.reset_streak(user)

        db.session.commit()
        return beats, message

    def get_current_defender(self, user: User) -> int:
        wbr_model = db.session.get(WBRModel, user.id)
        if wbr_model is None or wbr_model.defender_id is None:
            return -1
        return wbr_model.defender_id

    def get_current_defender_name(self, user: User) -> str:
        wbr_model = db.session.get(WBRModel, user.id)
        if wbr_model is None or wbr_model.defender is None:
            return "Stein"
        return wbr_model.defender.name

    def get_streak(self, user: User) -> int:
        wbr_model = db.session.get(WBRModel, user.id)
        if wbr_model is None:
            return 0
        return wbr_model.streak

    def reset_streak(self, user: User) -> None:
        wbr_model = db.session.get(WBRModel, user.id)
        if wbr_model is None:
            return
        wbr_model.streak = 0
        wbr_model.defender_id = None
        wbr_model.history = None
        db.session.commit()

