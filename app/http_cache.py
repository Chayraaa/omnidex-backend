import hashlib
import json
from typing import Any

from flask import Response, jsonify, request


PUBLIC_WIKI_CACHE = "public, max-age=86400, must-revalidate"
PUBLIC_NEGATIVE_CACHE = "public, max-age=300, must-revalidate"
PRIVATE_IMAGE_CACHE = "private, max-age=86400, must-revalidate"
PRIVATE_REVALIDATE_CACHE = "private, no-cache"
NO_STORE = "no-store"


def make_json_etag(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return make_bytes_etag(encoded)


def make_bytes_etag(data: bytes) -> str:
    return f'"{hashlib.sha256(data).hexdigest()}"'


def json_response_with_etag(
    payload: Any,
    *,
    cache_control: str,
    status: int = 200,
    vary: str | None = None,
) -> Response:
    etag = make_json_etag(payload)
    if status == 200 and _request_etag_matches(etag):
        return _not_modified_response(etag, cache_control, vary)

    response = jsonify(payload)
    response.status_code = status
    return apply_cache_headers(response, cache_control=cache_control, etag=etag, vary=vary)


def json_response_with_cache_headers(
    payload: Any,
    *,
    cache_control: str,
    status: int = 200,
    vary: str | None = None,
) -> Response:
    response = jsonify(payload)
    response.status_code = status
    return apply_cache_headers(response, cache_control=cache_control, vary=vary)


def bytes_response_with_etag(
    data: bytes,
    *,
    mimetype: str,
    cache_control: str,
    status: int = 200,
    vary: str | None = None,
) -> Response:
    etag = make_bytes_etag(data)
    if _request_etag_matches(etag):
        return _not_modified_response(etag, cache_control, vary)

    response = Response(data, status=status, mimetype=mimetype)
    return apply_cache_headers(response, cache_control=cache_control, etag=etag, vary=vary)


def json_no_store(payload: Any, status: int = 200) -> Response:
    response = jsonify(payload)
    response.status_code = status
    return apply_cache_headers(response, cache_control=NO_STORE)


def add_no_store(response: Response) -> Response:
    return apply_cache_headers(response, cache_control=NO_STORE)


def apply_cache_headers(
    response: Response,
    *,
    cache_control: str,
    etag: str | None = None,
    vary: str | None = None,
) -> Response:
    response.headers["Cache-Control"] = cache_control
    if etag is not None:
        response.headers["ETag"] = etag
    if vary is not None:
        response.headers["Vary"] = vary
    return response


def if_match_satisfied(current_etag: str) -> bool:
    if_match = request.headers.get("If-Match")
    if not if_match:
        return True
    return _etag_header_matches(if_match, current_etag)


def precondition_failed_response() -> Response:
    return apply_cache_headers(Response(status=412), cache_control=NO_STORE)


def _not_modified_response(etag: str, cache_control: str, vary: str | None) -> Response:
    response = Response(status=304)
    return apply_cache_headers(response, cache_control=cache_control, etag=etag, vary=vary)


def _request_etag_matches(etag: str) -> bool:
    if request.method not in {"GET", "HEAD"}:
        return False
    return _etag_header_matches(request.headers.get("If-None-Match"), etag)


def _etag_header_matches(header_value: str | None, current_etag: str) -> bool:
    if not header_value:
        return False
    candidates = [value.strip() for value in header_value.split(",")]
    if "*" in candidates:
        return True
    normalized_current = _normalize_etag(current_etag)
    return any(_normalize_etag(candidate) == normalized_current for candidate in candidates)


def _normalize_etag(etag: str) -> str:
    value = etag.strip()
    if value.startswith("W/"):
        value = value[2:].strip()
    return value
