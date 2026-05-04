from flask import Blueprint, jsonify, request, current_app

wiki = Blueprint("wiki", __name__, url_prefix="/wiki")

@wiki.route("/summary/<title>", methods=["GET"])
def get_wikipedia_summary(title):
    service = current_app.wiki_service
    summary = service.get_summary(title)

    if summary is None:
        return jsonify({"error": "Article not found"}), 404
    return jsonify({"extract": summary}), 200
