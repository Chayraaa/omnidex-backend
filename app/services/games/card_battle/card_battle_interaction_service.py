import logging
import random
from app.repositories.interfaces.storage.card_battle_repo_interface import CardBattleGameRepoInterface
from app.repositories.interfaces.storage.card_repo_protocol import CardRepoProtocol
from app.repositories.interfaces.storage.deck_repo_protocol import DeckRepoProtocol
from app.repositories.interfaces.storage.friends_repo_protocol import FriendsRepoProtocol
from app.repositories.interfaces.storage.user_repo_protocol import UserRepoProtocol
from app.services.games.card_battle import card_battle, card_battle_ai
from app.services.games.card_battle.event_publisher import game_event_publisher
from app.domain_models.card import BattleType

logger = logging.getLogger(__name__)


class CardBattleInteractionService:
    def __init__(self, card_battle_repo: CardBattleGameRepoInterface, user_repo: UserRepoProtocol,
                 deck_repo: DeckRepoProtocol, card_repo: CardRepoProtocol, friends_repo: FriendsRepoProtocol):
        self.card_battle_repo = card_battle_repo
        self.user_repo = user_repo
        self.deck_repo = deck_repo
        self.card_repo = card_repo
        self.friends_repo = friends_repo

    def create_lobby(self, player1_id: int | None, player2_id: int | None, name: str = "Card Battle"):
        user1 = self.user_repo.get_user(player1_id) if player1_id is not None else None
        user2 = self.user_repo.get_user(player2_id) if player2_id is not None else None

        deck1_cards = self._get_user_deck_cards(player1_id, player2_id)
        deck2_cards = self._get_user_deck_cards(player2_id, player1_id)

        game_state = card_battle.start_game(deck1_cards, deck2_cards)
        game = self.card_battle_repo.create_card_battle_game(name, user1, user2, game_state)
        logger.debug(f"[SYNC] create_lobby: game {game.id} created, p1={player1_id}, p2={player2_id}")
        self._notify(game)
        # If P1 is AI, it must act first since p1_turn=True at game start
        self._handle_ai_if_needed(game)
        return game

    def _get_user_deck_cards(self, user_id: int | None, opponent_id: int | None = None):
        if user_id is None:
            # Generate AI deck based on opponent's cards and their friends' cards
            if opponent_id is None:
                return []

            all_cards = self.card_repo.get_all_by_user(opponent_id)
            friend_ids = self.friends_repo.get_friend_ids(opponent_id)
            if friend_ids:
                all_cards = all_cards + self.card_repo.get_cards_by_friends(friend_ids)
            if not all_cards:
                return []
            
            fighters = [c for c in all_cards if c.battle_type == BattleType.FIGHTER]
            equipment = [c for c in all_cards if c.battle_type == BattleType.EQUIPMENT]
            
            random.shuffle(fighters)
            random.shuffle(equipment)
            
            # Aim for 12 fighters and 8 equipment, duplicating if not enough cards
            ai_deck = []
            while len(ai_deck) < 20:
                remaining = 20 - len(ai_deck)
                random.shuffle(fighters)
                random.shuffle(equipment)
                fighter_count = min(round(remaining * 0.6), len(fighters), remaining)
                equipment_count = min(remaining - fighter_count, len(equipment))
                ai_deck.extend(fighters[:fighter_count])
                ai_deck.extend(equipment[:equipment_count])
                # If we still need cards and have no cards at all, break to avoid infinite loop
                if fighter_count == 0 and equipment_count == 0:
                    break

            return ai_deck

        deck = self.deck_repo.get_main_by_user(user_id)
        if deck is None:
            decks = self.deck_repo.get_all_by_user(user_id)
            if not decks:
                return []
            deck = decks[0]

        card_ids = [int(cid) for cid in deck.deck.split(",") if cid]
        return self.card_repo.get_cards_by_ids(card_ids)

    def _get_player_num(self, game, user_id: int) -> int:
        if game.player1_id == user_id:
            return 1
        if game.player2_id == user_id:
            return 2
        raise ValueError("User not in game")

    def _notify(self, game):
        logger.debug(f"[SYNC] _notify: broadcasting state for game {game.id} "
                     f"(p1_turn={game.game_state.p1_turn}, "
                     f"p1_passed={game.game_state.p1_passed}, "
                     f"p2_passed={game.game_state.p2_passed})")
        game_event_publisher.publish(game.id)

    def _handle_ai_if_needed(self, game):
        # If it's AI turn, make them play
        state = game.game_state
        logger.debug(f"[SYNC] _handle_ai_if_needed: game {game.id}, "
                     f"p1_turn={state.p1_turn}, p1_id={game.player1_id}, p2_id={game.player2_id}")

        def on_step(new_state):
            logger.debug(f"[SYNC] AI on_step: saving intermediate state for game {game.id}")
            game.game_state = new_state
            self.card_battle_repo.update_card_battle_game(game)
            self._notify(game)

        if state.p1_turn and game.player1_id is None:
            logger.debug(f"[SYNC] _handle_ai_if_needed: triggering AI for player 1, game {game.id}")
            game.game_state = card_battle_ai.take_ai_turn(game.game_state, player=1, on_step=on_step)
            self._handle_ai_if_needed(game)  # Check if it's still AI turn
        elif not state.p1_turn and game.player2_id is None:
            logger.debug(f"[SYNC] _handle_ai_if_needed: triggering AI for player 2, game {game.id}")
            game.game_state = card_battle_ai.take_ai_turn(game.game_state, player=2, on_step=on_step)
            self._handle_ai_if_needed(game)

    def play_card(self, game_id: int, user_id: int, card_id: int, target_pos: int | None = None):
        game = self.card_battle_repo.get_card_battle_game(game_id)
        player_num = self._get_player_num(game, user_id)

        # Find card in hand
        hand = game.game_state.p1_hand if player_num == 1 else game.game_state.p2_hand
        card = next((c for c in hand if c.id == card_id), None)
        if not card:
            raise ValueError("Card not in hand")

        target = None
        if target_pos is not None:
            board = game.game_state.p1_board if player_num == 1 else game.game_state.p2_board
            if target_pos < len(board):
                target = board[target_pos]

        logger.debug(f"[ACTION] play_card: game={game_id}, player={player_num}, "
                     f"card={card.name}(id={card_id}), target_pos={target_pos}")
        game.game_state = card_battle.play_card(game.game_state, card, player_num, equip_to=target)
        self.card_battle_repo.update_card_battle_game(game)
        self._notify(game)
        # Note: play_card does NOT trigger AI — the player may still have more cards to play.
        # AI is triggered only after end_turn or pass_round.
        return game

    def sell_card(self, game_id: int, user_id: int, card_id: int):
        game = self.card_battle_repo.get_card_battle_game(game_id)
        player_num = self._get_player_num(game, user_id)

        hand = game.game_state.p1_hand if player_num == 1 else game.game_state.p2_hand
        card = next((c for c in hand if c.id == card_id), None)
        if not card:
            raise ValueError("Card not in hand")

        logger.debug(f"[ACTION] sell_card: game={game_id}, player={player_num}, card={card.name}(id={card_id})")
        game.game_state = card_battle.sell_card(game.game_state, card, player_num)
        self.card_battle_repo.update_card_battle_game(game)
        self._notify(game)
        return game

    def end_turn(self, game_id: int, user_id: int):
        game = self.card_battle_repo.get_card_battle_game(game_id)
        player_num = self._get_player_num(game, user_id)

        logger.debug(f"[ACTION] end_turn: game={game_id}, player={player_num}, "
                     f"p1_turn_before={game.game_state.p1_turn}")
        game.game_state = card_battle.end_turn(game.game_state, player_num)
        logger.debug(f"[ACTION] end_turn: p1_turn_after={game.game_state.p1_turn}")
        self.card_battle_repo.update_card_battle_game(game)
        self._notify(game)
        self._handle_ai_if_needed(game)
        return game

    def pass_round(self, game_id: int, user_id: int):
        game = self.card_battle_repo.get_card_battle_game(game_id)
        player_num = self._get_player_num(game, user_id)

        logger.debug(f"[ACTION] pass_round: game={game_id}, player={player_num}, "
                     f"p1_passed={game.game_state.p1_passed}, p2_passed={game.game_state.p2_passed}")
        game.game_state = card_battle.pass_round(game.game_state, player_num)
        logger.debug(f"[ACTION] pass_round result: p1_passed={game.game_state.p1_passed}, "
                     f"p2_passed={game.game_state.p2_passed}, p1_turn={game.game_state.p1_turn}")
        self.card_battle_repo.update_card_battle_game(game)
        self._notify(game)
        self._handle_ai_if_needed(game)
        return game

    def leave_game(self, game_id: int, user_id: int):
        game = self.card_battle_repo.get_card_battle_game(game_id)
        player_num = self._get_player_num(game, user_id)
        
        if player_num == 1:
            game.player1_id = None
        else:
            game.player2_id = None
            
        if game.player1_id is None and game.player2_id is None:
            self.card_battle_repo.delete_card_battle_game(game)
            return None
        
        self.card_battle_repo.update_card_battle_game(game)
        self._notify(game)
        self._handle_ai_if_needed(game)
        return game

    def get_user_games(self, user_id: int):
        user = self.user_repo.get_user(user_id)
        if not user:
            raise ValueError("User not found")
        return self.card_battle_repo.get_card_battle_games_by_player(user)