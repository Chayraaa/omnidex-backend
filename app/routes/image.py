from flask import Blueprint, current_app
import mimetypes

from app.http_cache import PRIVATE_IMAGE_CACHE, bytes_response_with_etag

image = Blueprint("images", __name__)

@image.route("/<path:key>", methods=["GET"])
def get_image(key):
    image_data = current_app.image_service.get_image_stream(key)

    mime_type, _ = mimetypes.guess_type(key)

    return bytes_response_with_etag(
        image_data,
        mimetype=mime_type or "application/octet-stream",
        cache_control=PRIVATE_IMAGE_CACHE,
    )