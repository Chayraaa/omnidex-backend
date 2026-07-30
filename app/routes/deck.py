from flask import Blueprint, request, current_app
from app import login_required, validate
from app.domain_models.user import User
from app.http_cache import json_no_store

decks = Blueprint("decks", __name__)

@decks.route("", methods=["GET"])
@login_required
@validate
def get_my_decks(user: User):
    user_decks = current_app.deck_service.get_user_decks(user.id)
    return json_no_store({
        "decks": [
            {
                "id": deck.id,
                "name": deck.name,
                "deck": deck.deck,
                "is_main": deck.is_main,
            } for deck in user_decks
        ]
    }, 200)

@decks.route("", methods=["POST"])
@login_required
@validate
def create_deck(user: User):
    data = request.get_json()
    name = data.get("name")
    deck_content = data.get("deck")
    
    if not name or not deck_content:
        return json_no_store({"error": "Name and deck content are required"}, 400)
    
    deck = current_app.deck_service.create_deck(user.id, name, deck_content)
    return json_no_store({
        "message": "Deck created successfully",
        "deck": {
            "id": deck.id,
            "name": deck.name,
            "deck": deck.deck,
            "is_main": deck.is_main,
        }
    }, 201)

@decks.route("/<int:deck_id>", methods=["PUT"])
@login_required
@validate
def update_deck(user: User, deck_id: int):
    data = request.get_json()
    name = data.get("name")
    deck_content = data.get("deck")
    
    try:
        updated_deck = current_app.deck_service.update_deck(user.id, deck_id, name, deck_content)
        return json_no_store({
            "message": "Deck updated successfully",
            "deck": {
                "id": updated_deck.id,
                "name": updated_deck.name,
                "deck": updated_deck.deck,
                "is_main": updated_deck.is_main,
            }
        }, 200)
    except ValueError as e:
        return json_no_store({"error": str(e)}, 400)

@decks.route("/<int:deck_id>/set-main", methods=["POST"])
@login_required
@validate
def set_main_deck(user: User, deck_id: int):
    try:
        deck = current_app.deck_service.set_main_deck(user.id, deck_id)
        return json_no_store({
            "message": "Main deck updated",
            "deck": {
                "id": deck.id,
                "name": deck.name,
                "deck": deck.deck,
                "is_main": deck.is_main,
            }
        }, 200)
    except ValueError as e:
        return json_no_store({"error": str(e)}, 400)

@decks.route("/<int:deck_id>", methods=["DELETE"])
@login_required
@validate
def delete_deck(user: User, deck_id: int):
    try:
        current_app.deck_service.delete_deck(user.id, deck_id)
        return json_no_store({"message": "Deck deleted successfully"}, 200)
    except ValueError as e:
        return json_no_store({"error": str(e)}, 400)
