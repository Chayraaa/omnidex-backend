import logging

from flask import Blueprint, request, current_app, Response
from app import validate, login_required
from app.domain_models.user import User
from app.http_cache import json_no_store
from app.services.games.card_battle.event_publisher import game_event_publisher

logger = logging.getLogger(__name__)

card_battle_route = Blueprint("card_battle", __name__)

@card_battle_route.route("/lobby", methods=["POST"])
@login_required
@validate
def create_lobby(user: User):
    data = request.get_json() or {}
    player2_id = data.get("player2_id") # Can be None for AI
    name = data.get("name", f"{user.name}'s Game")
    
    game = current_app.card_battle_interaction_service.create_lobby(user.id, player2_id, name)
    
    return json_no_store({
        "game_id": game.id,
        "name": game.name,
        "message": "Lobby created"
    }, 201)

@card_battle_route.route("/lobbies", methods=["GET"])
@login_required
@validate
def get_lobbies(user: User):
    games = current_app.card_battle_interaction_service.get_user_games(user.id)
    return json_no_store({
        "games": [{
            "game_id": g.id,
            "name": g.name,
            "player1_id": g.player1_id,
            "player2_id": g.player2_id,
            "game_state": g.game_state.to_dict()
        } for g in games]
    }, 200)

@card_battle_route.route("/<int:game_id>/play", methods=["POST"])
@login_required
@validate
def play_card(user: User, game_id: int):
    data = request.get_json() or {}
    card_id = data.get("card_id")
    target_pos = data.get("target_pos")
    
    try:
        game = current_app.card_battle_interaction_service.play_card(game_id, user.id, card_id, target_pos)
        return json_no_store({"game_state": game.game_state.to_dict()}, 200)
    except ValueError as e:
        return json_no_store({"error": str(e)}, 400)

@card_battle_route.route("/<int:game_id>/sell", methods=["POST"])
@login_required
@validate
def sell_card(user: User, game_id: int):
    data = request.get_json() or {}
    card_id = data.get("card_id")

    try:
        game = current_app.card_battle_interaction_service.sell_card(game_id, user.id, card_id)
        return json_no_store({"game_state": game.game_state.to_dict()}, 200)
    except ValueError as e:
        return json_no_store({"error": str(e)}, 400)

@card_battle_route.route("/<int:game_id>/end-turn", methods=["POST"])
@login_required
@validate
def end_turn(user: User, game_id: int):
    try:
        game = current_app.card_battle_interaction_service.end_turn(game_id, user.id)
        return json_no_store({"game_state": game.game_state.to_dict()}, 200)
    except ValueError as e:
        return json_no_store({"error": str(e)}, 400)

@card_battle_route.route("/<int:game_id>/pass", methods=["POST"])
@login_required
@validate
def pass_round(user: User, game_id: int):
    try:
        game = current_app.card_battle_interaction_service.pass_round(game_id, user.id)
        return json_no_store({"game_state": game.game_state.to_dict()}, 200)
    except ValueError as e:
        return json_no_store({"error": str(e)}, 400)

@card_battle_route.route("/<int:game_id>/leave", methods=["POST"])
@login_required
@validate
def leave_game(user: User, game_id: int):
    try:
        current_app.card_battle_interaction_service.leave_game(game_id, user.id)
        return json_no_store({"message": "Lobby left"}, 200)
    except ValueError as e:
        return json_no_store({"error": str(e)}, 400)

@card_battle_route.route("/<int:game_id>/state", methods=["GET"])
@login_required
@validate
def get_game_state(user: User, game_id: int):
    game = current_app.card_battle_interaction_service.card_battle_repo.get_card_battle_game(game_id)
    if not game:
        return json_no_store({"error": "Game not found"}, 404)
    return json_no_store({"game_state": game.game_state.to_dict()}, 200)

@card_battle_route.route("/<int:game_id>/stream", methods=["GET"])
@login_required
def stream(user: User, game_id: int):
    app = current_app._get_current_object()
    logger.debug(f"[SSE] stream: user {user.id} opened SSE for game {game_id}")

    def event_stream():
        with app.app_context():
            for event in game_event_publisher.listen(game_id):
                if event in ("initial", "update"):
                    logger.debug(f"[SSE] stream: fetching state for '{event}' event, game {game_id}")
                    game = app.card_battle_interaction_service.card_battle_repo.get_card_battle_game(game_id)
                    if game:
                        logger.debug(f"[SSE] stream: sending state to user {user.id} for game {game_id} "
                                     f"(p1_turn={game.game_state.p1_turn})")
                        yield f"data: {game.game_state.to_json()}\n\n"
                    else:
                        logger.warning(f"[SSE] stream: game {game_id} not found on '{event}' event")
                elif event == "keep-alive":
                    yield ": keep-alive\n\n"

    return Response(event_stream(), mimetype="text/event-stream")
