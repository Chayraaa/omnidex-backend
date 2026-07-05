from flask import Blueprint, current_app

from app.http_cache import (
    PUBLIC_NEGATIVE_CACHE,
    PUBLIC_WIKI_CACHE,
    json_response_with_cache_headers,
    json_response_with_etag,
)

wiki = Blueprint("wiki", __name__, url_prefix="/wiki")

@wiki.route("/summary/<title>", methods=["GET"])
def get_wikipedia_summary(title):
    service = current_app.wiki_service
    summary = service.get_summary(title)

    if not summary or summary == "No article found":
        return json_response_with_cache_headers(
            {"error": "Article not found"},
            cache_control=PUBLIC_NEGATIVE_CACHE,
            status=404,
            vary="Accept-Encoding",
        )

    return json_response_with_etag(
        {"extract": summary},
        cache_control=PUBLIC_WIKI_CACHE,
        vary="Accept-Encoding",
    )
