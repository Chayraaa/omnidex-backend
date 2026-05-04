from flask import Blueprint, jsonify, request
from app.services.wiki_service import WikiService
from app.repositories.external.wiki_repo import WikiRepo

wiki = Blueprint("wiki", __name__, url_prefix="/api/wiki")

def get_wiki_service() -> WikiService:
    wiki_repo = WikiRepo()
    return WikiService(wiki_repo = wiki_repo)

@wiki.route("/summary/<title>", methods=["GET"])
def get_wikipedia_summary(title):
    try:
        service = get_wiki_service()
        summary = service.get_summary(title)

        if summary is None:
            return jsonify({"error": "Article not found"}), 404
        return jsonify({"extract": summary}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
