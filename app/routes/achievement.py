from flask import Blueprint, jsonify, request
from app import login_required, validate
from database_models.achievement_model import AchievementModel
from services.achievement_service import AchievementService

achievements = Blueprint("achievements", __name__)

@achievements.route("", methods=["GET"])
def get_achievements():
    achievements = AchievementService.get_all_achievements()
    if achievements is None:
        return jsonify({"error": "Article not found"}), 404
    return jsonify({"achievements": achievements}), 200

@achievements.route("/progress/<int:userId>", methods=["GET"])
@login_required
def get_achievement_progress(userId):
    data = request.get_json()
    userId = data.get("userId")
    if userId is None:
        return jsonify({"error": "User not found"}), 404
    results = AchievementService.get_achievement_progress(userId)
    return jsonify({"achievement progress": results}), 200


@achievements.route("/progress/<int:userId>", methods=["PATCH"])
@login_required
def update_achievement_progress(userId):
    data = request.get_json()
    userId = data.get("userId")
    if userId is None:
        return jsonify({"error": "User not found"}), 404
    results = AchievementService.get_achievement_progress(userId)
    return jsonify({"Achievement progress updated"}), 200