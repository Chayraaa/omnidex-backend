from flask import Blueprint, request, current_app

from app import login_required, validate
from app.domain_models.user import User
from app.http_cache import (
    PRIVATE_REVALIDATE_CACHE,
    if_match_satisfied,
    json_no_store,
    json_response_with_etag,
    make_json_etag,
    precondition_failed_response,
)
from app.services.collection_errors import (
    CollectionEntryNotFound,
    InvalidCollectionSort,
    InvalidCollectionCategory,
    InvalidCollectionPagination,
)

collection = Blueprint("collection", __name__)


@collection.route("/me", methods=["GET"])
@login_required
@validate
def get_my_collection(user: User):
    query = request.args.get("query")
    sort = request.args.get("sort", "newest")
    category = request.args.get("category")
    limit_raw = request.args.get("limit")
    offset_raw = request.args.get("offset")

    try:
        limit = int(limit_raw) if limit_raw is not None else None
        offset = int(offset_raw) if offset_raw is not None else None
    except ValueError:
        return json_no_store({"error": "limit and offset must be integers"}, 400)

    try:
        entries = current_app.collection_service.get_user_collection(
            user_id=user.id,
            query=query,
            sort=sort,
            category=category,
            limit=limit,
            offset=offset,
        )
    except InvalidCollectionSort as exc:
        return json_no_store({"error": str(exc)}, 400)
    except InvalidCollectionCategory as exc:
        return json_no_store({"error": str(exc)}, 400)
    except InvalidCollectionPagination as exc:
        return json_no_store({"error": str(exc)}, 400)

    payload = {"items": [entry.to_dict() for entry in entries]}
    return json_response_with_etag(
        payload,
        cache_control=PRIVATE_REVALIDATE_CACHE,
        vary="Authorization",
    )


@collection.route("/me/<int:entryId>", methods=["GET"])
@login_required
@validate
def get_collection_entry_detail(user: User, entryId: int):
    try:
        entry = current_app.collection_service.get_collection_entry_detail(
            user_id=user.id,
            entry_id=entryId,
        )
    except CollectionEntryNotFound:
        return json_no_store({"error": "Collection entry not found"}, 404)

    return json_response_with_etag(
        entry.to_dict(),
        cache_control=PRIVATE_REVALIDATE_CACHE,
        vary="Authorization",
    )


@collection.route("/me/<int:entryId>/category", methods=["PATCH"])
@login_required
@validate
def update_collection_entry_category(user: User, entryId: int):
    data = request.get_json() or {}
    category = data.get("category")

    try:
        if request.headers.get("If-Match"):
            current_entry = current_app.collection_service.get_collection_entry_detail(
                user_id=user.id,
                entry_id=entryId,
            )
            if not if_match_satisfied(make_json_etag(current_entry.to_dict())):
                return precondition_failed_response()

        entry = current_app.collection_service.update_collection_entry_category(
            user_id=user.id,
            entry_id=entryId,
            category=category,
        )
    except InvalidCollectionCategory as exc:
        return json_no_store({"error": str(exc)}, 400)
    except CollectionEntryNotFound:
        return json_no_store({"error": "Collection entry not found"}, 404)

    return json_no_store(entry.to_dict(), 200)
