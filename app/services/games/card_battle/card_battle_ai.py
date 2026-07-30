"""
Heuristic search AI for the card battler.

Strategy
--------
On its turn, the AI:
  1. Enumerates every legal combination of "what to do with my hand this
     turn" -- play the one allowed fighter, equip pieces onto board
     fighters (including one just played this turn), or sell cards for
     money -- by replaying each candidate combination against a *deep
     copy* of the real GameState using the actual engine functions
     (`play_card` / `sell_card`). That means all of the engine's own
     legality rules (cost checks, one-fighter-per-turn, etc.) are
     enforced for free -- the AI can never "cheat".
  2. Scores each resulting hypothetical GameState with `_score_leaf`,
     which runs the engine's own `_evaluate` (and `_check_for_winner`)
     combat resolution against a throwaway copy to see who'd be ahead
     "if the round ended right now".
  3. Replays the single best-scoring combination against the *real*
     game state.
  4. Decides whether to `pass_round` (commit to combat) or `end_turn`
     (keep playing / bank money for later) with a small heuristic.

The opponent's hand and draw pile CONTENTS are never inspected -- only
what's public: their board, money, grave, and the *length* of their
hand/draw pile (the same info the game's own __str__ shows).

Adjust the import below to point at wherever your engine module
(the file with GameState, CardContainer, play_card, sell_card,
end_turn, pass_round, _evaluate, _check_for_winner) actually lives.
"""

from __future__ import annotations

import copy
import time
from typing import NamedTuple, Optional

from app.domain_models.card import Card, BattleType
from app.services.games.card_battle.event_publisher import game_event_publisher
from app.services.games.card_battle.card_battle import (
    GameState,
    CardContainer,
    play_card,
    sell_card,
    end_turn,
    pass_round,
    _evaluate,
    _check_for_winner,
)

# --- tunable weights for the evaluation function -----------------------

BOARD_POWER_WEIGHT = 2.0   # surviving attack+health on the board
DRAW_PILE_WEIGHT = 5.0     # draw pile length == effective "life total"
MONEY_WEIGHT = 0.1         # small nudge to not hoard unspent money
BOARD_COUNT_WEIGHT = 1.5   # having more surviving bodies is generally good
WIN_BONUS = 100_000.0      # dominate the score if this line wins/loses outright
HAND_COUNT_WEIGHT = 0.2


class Action(NamedTuple):
    """One atomic move considered by the search, referencing the
    ORIGINAL hand by position (`hand_pos`) and, for equipment, the
    board position it targets (`target_pos`) at the time it's applied."""
    kind: str  # "play_fighter" | "play_equipment" | "sell" | "skip"
    hand_pos: int
    target_pos: Optional[int] = None

    def describe(self, hand_snapshot: list[Card]) -> str:
        card = hand_snapshot[self.hand_pos]
        if self.kind == "play_fighter":
            return f"Play fighter '{card.name}'"
        if self.kind == "play_equipment":
            return f"Equip '{card.name}' onto board slot {self.target_pos}"
        if self.kind == "sell":
            return f"Sell '{card.name}'"
        return f"Skip '{card.name}'"


class Plan(NamedTuple):
    actions: tuple[Action, ...]
    score: float


def _hand(state: GameState, player: int) -> list[Card]:
    return state.p1_hand if player == 1 else state.p2_hand


def _board(state: GameState, player: int) -> list[CardContainer]:
    return state.p1_board if player == 1 else state.p2_board


def _fighter_played(state: GameState, player: int) -> bool:
    return state.p1_fighter_played if player == 1 else state.p2_fighter_played


def _money(state: GameState, player: int) -> int:
    return state.p1_money if player == 1 else state.p2_money


def _score_leaf(state: GameState, player: int) -> float:
    """
    Score a fully-decided hypothetical turn by running the engine's own
    combat resolution against a throwaway copy: "how does this look if
    the round ended right now?"
    """
    sim = copy.deepcopy(state)
    sim = _evaluate(sim)
    sim = _check_for_winner(sim)

    my_won = sim.p1_has_won if player == 1 else sim.p2_has_won
    their_won = sim.p2_has_won if player == 1 else sim.p1_has_won
    if my_won:
        return WIN_BONUS
    if their_won:
        return -WIN_BONUS

    my_board = _board(sim, player)
    their_board = _board(sim, 1 if player == 2 else 2)
    my_draw_len = len(sim.p1_draw if player == 1 else sim.p2_draw)
    their_draw_len = len(sim.p2_draw if player == 1 else sim.p1_draw)
    my_money = _money(sim, player)
    my_hand = _hand(sim, player)

    my_power = sum(c.attack + c.health for c in my_board)
    their_power = sum(c.attack + c.health for c in their_board)

    score = (my_power - their_power) * BOARD_POWER_WEIGHT
    score += (my_draw_len - their_draw_len) * DRAW_PILE_WEIGHT
    score += (len(my_board) - len(their_board)) * BOARD_COUNT_WEIGHT
    score += my_money * MONEY_WEIGHT
    score += len(my_hand) * HAND_COUNT_WEIGHT
    return score


def _search(
    state: GameState,
    player: int,
    hand_snapshot: list[Card],
    pos: int,
    removed_before: int,
) -> Plan:
    """
    Depth-first search over "what to do with each hand card", processed
    in a fixed order (`hand_snapshot`).

    `removed_before` tracks how many earlier hand cards have already
    been consumed (played/sold) this turn, so we can find the card at
    `hand_snapshot[pos]` inside `state`'s current (shrinking) hand list:
    it sits at `live_index = pos - removed_before`, since removals never
    reorder the remaining cards.
    """
    if pos == len(hand_snapshot):
        return Plan(actions=(), score=_score_leaf(state, player))

    live_hand = _hand(state, player)
    live_index = pos - removed_before
    card = live_hand[live_index]
    money = _money(state, player)
    board = _board(state, player)
    fighter_played = _fighter_played(state, player)

    best: Optional[Plan] = None

    def consider(action: Action, next_state: GameState, next_removed_before: int):
        nonlocal best
        sub = _search(next_state, player, hand_snapshot, pos + 1, next_removed_before)
        actions = (action,) + sub.actions
        if best is None or sub.score > best.score:
            best = Plan(actions=actions, score=sub.score)

    # Option: skip.
    consider(
        Action("skip", pos),
        copy.deepcopy(state),
        removed_before,
    )

    # Option: sell.
    sell_state = copy.deepcopy(state)
    sell_state = sell_card(sell_state, _hand(sell_state, player)[live_index], player)
    consider(Action("sell", pos), sell_state, removed_before + 1)

    # Option: play.
    if card.battle_type == BattleType.FIGHTER:
        if not fighter_played and money >= card.cost:
            play_state = copy.deepcopy(state)
            play_state = play_card(
                play_state, _hand(play_state, player)[live_index], player
            )
            consider(Action("play_fighter", pos), play_state, removed_before + 1)
    else:
        if money >= card.cost:
            for target_pos in range(len(board)):
                equip_state = copy.deepcopy(state)
                equip_card = _hand(equip_state, player)[live_index]
                equip_target = _board(equip_state, player)[target_pos]
                equip_state = play_card(
                    equip_state, equip_card, player, equip_to=equip_target
                )
                consider(
                    Action("play_equipment", pos, target_pos),
                    equip_state,
                    removed_before + 1,
                )

    assert best is not None
    return best


def _apply_plan(state: GameState, player: int, plan: Plan, hand_snapshot: list[Card], on_step=None) -> GameState:
    """Replay a winning Plan against the REAL game state."""
    removed_before = 0
    for action in plan.actions:
        live_index = action.hand_pos - removed_before
        hand = _hand(state, player)
        if live_index >= len(hand):
            # Defensive: shouldn't happen if the plan was built correctly.
            continue
        card = hand[live_index]

        if action.kind == "skip":
            continue
        if action.kind == "sell":
            state = sell_card(state, card, player)
            removed_before += 1
        elif action.kind == "play_fighter":
            state = play_card(state, card, player)
            removed_before += 1
        elif action.kind == "play_equipment":
            board = _board(state, player)
            if action.target_pos is None or action.target_pos >= len(board):
                continue
            target = board[action.target_pos]
            state = play_card(state, card, player, equip_to=target)
            removed_before += 1
        
        if on_step:
            on_step(state)
            time.sleep(3)

    return state


def _decide_pass_or_end(state: GameState, player: int) -> GameState:
    """
    Simple heuristic for what to do once we're out of good plays:
      - If the opponent has already passed, mirror them and pass too --
        waiting further gains nothing since they won't act again until
        combat resolves.
      - If we have no more affordable plays left in hand, pass rather
        than sit idle.
      - Otherwise, end our turn to bank money / see what's drawn next
        round before committing to combat.
    Tune this freely -- it's intentionally simple.
    """
    opponent = 2 if player == 1 else 1
    opponent_passed = state.p2_passed if player == 1 else state.p1_passed
    if opponent_passed:
        return pass_round(state, player)

    hand = _hand(state, player)
    money = _money(state, player)
    fighter_played = _fighter_played(state, player)
    board = _board(state, player)

    can_still_play = any(
        card.cost <= money
        and (
            (card.battle_type == BattleType.FIGHTER and not fighter_played)
            or (card.battle_type != BattleType.FIGHTER and board)
        )
        for card in hand
    )
    if not can_still_play:
        return pass_round(state, player)

    return end_turn(state, player)


def take_ai_turn(game_state: GameState, player: int = 2, on_step=None) -> GameState:
    """
    Play out the AI's actions for its current turn: search for the best
    combination of plays for its hand, commit them, then pass or end
    turn. Returns the (mutated) game_state.
    """
    hand_snapshot = list(_hand(game_state, player))
    if not hand_snapshot:
        state = _decide_pass_or_end(game_state, player)
        if on_step:
            on_step(state)
        return state

    search_root = copy.deepcopy(game_state)
    plan = _search(search_root, player, hand_snapshot, pos=0, removed_before=0)

    time.sleep(3)
    game_state = _apply_plan(game_state, player, plan, hand_snapshot, on_step=on_step)
    game_state = _decide_pass_or_end(game_state, player)
    time.sleep(3)
    if on_step:
        on_step(game_state)
    return game_state


# Temporary test entry:
if __name__ == "__main__":
    from app.services.games.card_battle.card_battle import start_game

    cards: list[Card] = [
        Card(0, "Test Card 1", "", 0, 0, BattleType.FIGHTER, 20, 50, 2),
        Card(1, "Test Card 2", "", 0, 0, BattleType.FIGHTER, 25, 45, 2),
        Card(2, "Test Card 3", "", 0, 0, BattleType.EQUIPMENT, 30, 40, 3),
        Card(3, "Test Card 4", "", 0, 0, BattleType.FIGHTER, 15, 60, 1),
        Card(4, "Test Card 5", "", 0, 0, BattleType.FIGHTER, 35, 35, 3),
        Card(5, "Test Card 6", "", 0, 0, BattleType.FIGHTER, 40, 30, 4),
        Card(6, "Test Card 7", "", 0, 0, BattleType.EQUIPMENT, 10, 70, 1),
        Card(7, "Test Card 8", "", 0, 0, BattleType.FIGHTER, 45, 25, 5),
        Card(8, "Test Card 9", "", 0, 0, BattleType.FIGHTER, 28, 42, 3),
        Card(9, "Test Card 10", "", 0, 0, BattleType.EQUIPMENT, 22, 48, 2),
    ]

    game = start_game(cards, list(cards))
    print(game)

    play_card(game, game.p1_hand[0], 1)
    end_turn(game, 1)
    print(game)

    game = take_ai_turn(game, player=2)
    print(game)
    pass_round(game, 1)
    print(game)