from flask import Blueprint, current_app, Response
import mimetypes

image = Blueprint("image", __name__)

@image.route("/<path:key>", methods=["GET"])
def get_image(key):
    response = current_app.image_service.get_image_stream(key)
    mime_type, _ = mimetypes.guess_type(key)

    return Response(
        response,
        mimetype=mime_type or "application/octet-stream"
    )
