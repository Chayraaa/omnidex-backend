import json
import random
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from math import ceil

from app.domain_models.card import Card, BattleType

@dataclass
class CardContainer:
    card: Card
    health: int
    attack: int
    equipment: list[Card]

    def __str__(self):
        equipment_text = (
            "\n".join(
                f"{item.name} (+{item.attack}/{item.health})"
                for item in self.equipment
            )
            if self.equipment
            else "None"
        )

        return (
            f"{self.card.name}, "
            f"Type: {self.card.battle_type.value}, "
            f"Attack: {self.attack}, "
            f"Health: {self.health}, "
            f"Equipment: "
            f"{equipment_text}"
        )

    def __repr__(self):
        return self.__str__()


@dataclass
class GameState:
    p1_hand: list[Card]
    p2_hand: list[Card]
    p1_draw: list[Card]
    p2_draw: list[Card]
    p1_grave: list[Card]
    p2_grave: list[Card]
    p1_board: list[CardContainer]
    p2_board: list[CardContainer]
    p1_money: int
    p2_money: int
    p1_turn: bool
    p1_passed: bool
    p2_passed: bool
    p1_fighter_played: bool
    p2_fighter_played: bool
    p1_has_won: bool
    p2_has_won: bool
    p1_passed_first: bool = True

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def to_dict(self) -> dict:
        def factory(x):
            result = {}
            for k, v in x:
                if isinstance(v, Enum):
                    result[k] = v.value
                elif isinstance(v, datetime):
                    result[k] = v.isoformat()
                else:
                    result[k] = v
            return result
        return asdict(self, dict_factory=factory)

    @staticmethod
    def from_json(data: str) -> "GameState":
        d = json.loads(data)

        def card(c):
            created_at = c.get("created_at")
            return Card(
                id=c["id"],
                name=c["name"],
                image_key=c["image_key"],
                user_id=c["user_id"],
                category_id=c["category_id"],
                battle_type=BattleType(c["battle_type"]),
                attack=c["attack"],
                health=c["health"],
                cost=c["cost"],
                created_at=datetime.fromisoformat(created_at) if created_at else None,
            )

        def container(c):
            return CardContainer(
                card=card(c["card"]),
                health=c["health"],
                attack=c["attack"],
                equipment=[card(e) for e in c["equipment"]],
            )

        return GameState(
            p1_hand=[card(c) for c in d["p1_hand"]],
            p2_hand=[card(c) for c in d["p2_hand"]],
            p1_draw=[card(c) for c in d["p1_draw"]],
            p2_draw=[card(c) for c in d["p2_draw"]],
            p1_grave=[card(c) for c in d["p1_grave"]],
            p2_grave=[card(c) for c in d["p2_grave"]],
            p1_board=[container(c) for c in d["p1_board"]],
            p2_board=[container(c) for c in d["p2_board"]],
            p1_money=d["p1_money"],
            p2_money=d["p2_money"],
            p1_turn=d["p1_turn"],
            p1_passed=d["p1_passed"],
            p2_passed=d["p2_passed"],
            p1_fighter_played=d["p1_fighter_played"],
            p2_fighter_played=d["p2_fighter_played"],
            p1_has_won=d["p1_has_won"],
            p2_has_won=d["p2_has_won"],
            p1_passed_first=d.get("p1_passed_first", True),
        )

    def __str__(self):
        return (
            "=== Game State ===\n"
            f"P1 Hand:            {self.p1_hand}\n"
            f"P2 Hand:            {self.p2_hand}\n"
            f"P1 Draw:            {len(self.p1_draw)} cards\n"
            f"P2 Draw:            {len(self.p2_draw)} cards\n"
            f"P1 Grave:           {len(self.p1_grave)} cards\n"
            f"P2 Grave:           {len(self.p2_grave)} cards\n"
            "\n"
            f"P1 Board:           {self.p1_board}\n"
            f"P2 Board:           {self.p2_board}\n"
            "\n"
            f"P1 Money:           {self.p1_money}\n"
            f"P2 Money:           {self.p2_money}\n"
            "\n"
            f"P1 Turn:            {self.p1_turn}\n"
            f"P1 Passed:          {self.p1_passed}\n"
            f"P2 Passed:          {self.p2_passed}\n"
            f"P1 Fighter Played:  {self.p1_fighter_played}\n"
            f"P2 Fighter Played:  {self.p2_fighter_played}\n"
            f"P1 Has Won:         {self.p1_has_won}\n"
            f"P2 Has Won:         {self.p2_has_won}\n"
            "==================="
        )

    def __repr__(self):
        return self.__str__()


def _draw(game_state: GameState) -> GameState:
    game_state.p1_hand += game_state.p1_draw[:5]
    game_state.p2_hand += game_state.p2_draw[:5]
    game_state.p1_draw = game_state.p1_draw[5:]
    game_state.p2_draw = game_state.p2_draw[5:]
    return game_state

def _is_player_turn(game_state: GameState, player: int) -> bool:
    if player == 1 and game_state.p2_passed:
        return True
    if player == 2 and game_state.p1_passed:
        return True
    if player != 1 and game_state.p1_turn:
        return False
    if player != 2 and not game_state.p1_turn:
        return False
    return True

def _evaluate(game_state: GameState) -> GameState:
    # find the shorter board and longer board
    shorter_board = game_state.p1_board if len(game_state.p1_board) <= len(game_state.p2_board) else game_state.p2_board
    shorter_board_player = 1 if len(game_state.p1_board) <= len(game_state.p2_board) else 2
    longer_board = game_state.p1_board if len(game_state.p1_board) > len(game_state.p2_board) else game_state.p2_board
    longer_board_player = 1 if len(game_state.p1_board) > len(game_state.p2_board) else 2

    # evaluate the fight
    for index, card_container in enumerate(shorter_board):
        opponent_container = longer_board[index]
        card_container.health -= opponent_container.attack
        opponent_container.health -= card_container.attack

    # damage the player
    leftover_fighters = len(longer_board) - len(shorter_board)
    if shorter_board_player == 1:
        for _ in range(leftover_fighters):
            if game_state.p1_draw:
                game_state.p1_draw.pop(0)
    else:
        for _ in range(leftover_fighters):
            if game_state.p2_draw:
                game_state.p2_draw.pop(0)

    # kill fighters with <= 0 hp
    shorter_board_container = game_state.p1_board if shorter_board_player == 1 else game_state.p2_board
    shorter_board_grave = game_state.p1_grave if shorter_board_player == 1 else game_state.p2_grave
    for card_container in list(shorter_board):
        if card_container.health <= 0:
            shorter_board_container.remove(card_container)
            shorter_board_grave.append(card_container.card)

    longer_board_container = game_state.p1_board if longer_board_player == 1 else game_state.p2_board
    longer_board_grave = game_state.p1_grave if longer_board_player == 1 else game_state.p2_grave
    for card_container in list(longer_board):
        if card_container.health <= 0:
            longer_board_container.remove(card_container)
            longer_board_grave.append(card_container.card)

    return game_state

def _check_for_winner(game_state: GameState) -> GameState:
    p1_out = not game_state.p1_draw
    p2_out = not game_state.p2_draw
    if p1_out and p2_out:
        p1_cards = len(game_state.p1_hand) + len(game_state.p1_board)
        p2_cards = len(game_state.p2_hand) + len(game_state.p2_board)
        if p1_cards > p2_cards:
            game_state.p1_has_won = True
            game_state.p2_has_won = False
        elif p2_cards > p1_cards:
            game_state.p1_has_won = False
            game_state.p2_has_won = True
        else:
            game_state.p1_has_won = True
            game_state.p2_has_won = True
    elif p1_out:
        game_state.p1_has_won = False
        game_state.p2_has_won = True
    elif p2_out:
        game_state.p1_has_won = True
        game_state.p2_has_won = False
    return game_state

def start_game(p1_deck: list[Card], p2_deck: list[Card]) -> GameState:
    game_state = GameState([], [], [], [], [], [], [], [], 0, 0, True, False, False, False, False, False, False)
    # random.seed(2)
    # Prepare game
    game_state.p1_draw = p1_deck
    game_state.p2_draw = p2_deck
    random.shuffle(game_state.p1_draw)
    random.shuffle(game_state.p2_draw)
    game_state.p1_money = 5
    game_state.p2_money = 5
    game_state.p1_turn = True
    game_state.p1_passed = False
    game_state.p2_passed = False
    game_state.p1_fighter_played = False
    game_state.p2_fighter_played = False
    game_state.p1_grave = []
    game_state.p2_grave = []

    # Draw first hands
    game_state = _draw(game_state)
    return game_state


def play_card(game_state: GameState, card: Card, player: int, equip_to: CardContainer | None = None) -> GameState:
    if not _is_player_turn(game_state, player):
        return game_state
    if player == 1:
        # Check if cost can be paid
        if game_state.p1_money < card.cost:
            return game_state
        # Check if fighter has already been played
        if card.battle_type == BattleType.FIGHTER:
            if game_state.p1_fighter_played:
                return game_state
            game_state.p1_fighter_played = True
            # Play the fighter
            game_state.p1_money -= card.cost
            card_container = CardContainer(card, card.health, card.attack, [])
            game_state.p1_hand.remove(card)
            game_state.p1_board.append(card_container)
        else:
            # Equip card
            if equip_to is None:
                return game_state
            if equip_to not in game_state.p1_board:
                return game_state
            game_state.p1_money -= card.cost
            equip_to.equipment.append(card)
            equip_to.attack += card.attack
            equip_to.health += card.health
            game_state.p1_hand.remove(card)
    else:
        # Check if cost can be paid
        if game_state.p2_money < card.cost:
            return game_state
        # Check if fighter has already been played
        if card.battle_type == BattleType.FIGHTER:
            if game_state.p2_fighter_played:
                return game_state
            game_state.p2_fighter_played = True
            # Play the fighter
            game_state.p2_money -= card.cost
            card_container = CardContainer(card, card.health, card.attack, [])
            game_state.p2_hand.remove(card)
            game_state.p2_board.append(card_container)
        else:
            # Equip card
            if equip_to is None:
                return game_state
            if equip_to not in game_state.p2_board:
                return game_state
            game_state.p2_money -= card.cost
            equip_to.equipment.append(card)
            equip_to.attack += card.attack
            equip_to.health += card.health
            game_state.p2_hand.remove(card)

    return game_state

def end_turn(game_state: GameState, player: int) -> GameState:
    if not _is_player_turn(game_state, player):
        return game_state
    if player == 1:
        game_state.p1_turn = False
        game_state.p1_fighter_played = False
        game_state.p2_money += 2
    else:
        game_state.p1_turn = True
        game_state.p2_fighter_played = False
        game_state.p1_money += 2
    return game_state

def sell_card(game_state: GameState, card: Card, player: int) -> GameState:
    if not _is_player_turn(game_state, player):
        return game_state
    if player == 1:
        game_state.p1_hand.remove(card)
        game_state.p1_grave.append(card)
        game_state.p1_money += max(card.cost - 1, 1)
    else:
        game_state.p2_hand.remove(card)
        game_state.p2_grave.append(card)
        game_state.p2_money += max(card.cost - 1, 1)
    return game_state

def pass_round(game_state: GameState, player: int) -> GameState:
    if not _is_player_turn(game_state, player):
        return game_state

    neither_passed_yet = not game_state.p1_passed and not game_state.p2_passed

    if player == 1:
        if neither_passed_yet:
            game_state.p1_passed_first = True
        game_state.p1_turn = False
        game_state.p1_passed = True
        game_state.p1_fighter_played = False
    else:
        if neither_passed_yet:
            game_state.p1_passed_first = False
        game_state.p1_turn = True
        game_state.p2_passed = True
        game_state.p2_fighter_played = False

    if game_state.p1_passed and game_state.p2_passed:
        game_state = _evaluate(game_state)
        game_state = _check_for_winner(game_state)
        game_state.p1_passed = False
        game_state.p2_passed = False
        game_state.p1_turn = game_state.p1_passed_first
        game_state = _draw(game_state)
        game_state.p1_money += 2
        game_state.p2_money += 2

    return game_state
