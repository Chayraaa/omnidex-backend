from flask import Blueprint, request, current_app
from app import validate, login_required
from app.domain_models.user import User
from app.http_cache import json_no_store
from app.domain_models.card import Card
from app.services.wbr_errors import DuplicateCardError

wbr = Blueprint("wbr", __name__)


@wbr.route("/play", methods=["POST"])
@login_required
@validate
def play_wbr(user: User):
    data = request.get_json() or {}
    card_id = data.get("card_id")

    if not card_id:
        return json_no_store({"error": "card_id is required"}, 400)

    card_model = current_app.collection_service.collection_repo.find_by_id_for_user(
        user_id=user.id, entry_id=card_id
    )

    if not card_model:
        return json_no_store({"error": "Card not found in your collection"}, 404)

    attacker = Card(
        id=card_model.id,
        name=card_model.name,
        image_key=card_model.image_key,
        user_id=card_model.user_id,
        category_id=card_model.category_id
    )

    try:
        beats, message = current_app.wbr_service.does_beat(attacker, user)
    except DuplicateCardError as e:
        return json_no_store({
            "error": "Duplicate card",
            "message": str(e)
        }, 409)

    streak = current_app.wbr_service.get_streak(user)
    highscore = current_app.wbr_service.get_highscore(user)
    new_defender = current_app.wbr_service.get_current_defender(user)

    return json_no_store({
        "beats": beats,
        "message": message,
        "streak": streak,
        "highscore": highscore,
        "new_defender": new_defender
    }, 200)


@wbr.route("/status", methods=["GET"])
@login_required
def get_wbr_status(user: User):
    streak = current_app.wbr_service.get_streak(user)
    highscore = current_app.wbr_service.get_highscore(user)
    defender = current_app.wbr_service.get_current_defender(user)

    return json_no_store({
        "streak": streak,
        "highscore": highscore,
        "defender": defender
    }, 200)
