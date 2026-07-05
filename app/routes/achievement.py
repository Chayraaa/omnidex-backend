from flask import Blueprint, jsonify, request
from app import login_required, validate
from app.services.achievement_service import AchievementService
from app.repositories.storage.sql_achievement_repo import SqlAchievementRepo
from app.repositories.storage.sql_card_repo import SqlCardRepo
from app.repositories.storage.sql_user_achievements_repo import SqlUserAchievementRepo

achievements = Blueprint("achievements", __name__)

achievement_service = AchievementService(
    user_achievement_repo=SqlUserAchievementRepo(),
    achievement_repo=SqlAchievementRepo(),
    card_repo=SqlCardRepo(),
)

@achievements.route("", methods=["GET"])
def get_achievements():
    results = achievement_service.get_all_achievements()
    return jsonify([a.__dict__ for a in results]), 200


@achievements.route("/progress", methods=["GET"])
@login_required
def get_achievement_progress(user):
    if user is None:
        return jsonify({"error": "User not found"}), 404

    results = achievement_service.get_current_progress(user)
    return jsonify([r.__dict__ for r in results]), 200
