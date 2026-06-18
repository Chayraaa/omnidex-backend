from flask import Blueprint, request, current_app

from app import login_required, validate
from app.domain_models.user import User
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
        return {"error": "limit and offset must be integers"}, 400

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
        return {"error": str(exc)}, 400
    except InvalidCollectionCategory as exc:
        return {"error": str(exc)}, 400
    except InvalidCollectionPagination as exc:
        return {"error": str(exc)}, 400

    return {"items": [entry.to_dict() for entry in entries]}, 200


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
        return {"error": "Collection entry not found"}, 404

    return entry.to_dict(), 200
