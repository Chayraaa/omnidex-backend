from math import ceil
from typing import Any

from app.domain_models.card import BattleType
from app.repositories.interfaces.external.card_stats_adapter_protocol import CardStatsAdapterProtocol


class CardStatsService:
    def __init__(self, adapter: CardStatsAdapterProtocol):
        self.adapter = adapter

    def classify_card(self, label: str, description: str) -> dict[str, Any]:
        try:
            result = self.adapter.classify_card(label, description)
        except Exception:
            # Fallback for classification failure
            return {
                "battle_type": BattleType.FIGHTER,
                "attack": 10,
                "health": 10,
                "cost": 1
            }
        
        battle_type_str = result.get("battle_type", "fighter").lower()
        attack = result.get("attack", 10)
        health = result.get("health", 10)
        
        if battle_type_str == "equipment":
            bt = BattleType.EQUIPMENT
            max_stat = 50
        else:
            bt = BattleType.FIGHTER
            max_stat = 100
            
        attack = min(max(5, self._round_up_5(attack)), max_stat)
        health = min(max(5, self._round_up_5(health)), max_stat)
        
        # Simple cost calculation based on stats
        cost = max(1, ceil((attack + health) / 20))
        
        return {
            "battle_type": bt,
            "attack": attack,
            "health": health,
            "cost": cost
        }

    @staticmethod
    def _round_up_5(n: int) -> int:
        if not isinstance(n, (int, float)):
            return 10
        return int(ceil(n / 5.0) * 5)
