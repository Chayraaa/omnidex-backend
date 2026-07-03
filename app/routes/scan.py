import base64
import binascii

from flask import Blueprint, request, current_app

from app import validate, login_required
from app.domain_models.user import User
from app.http_cache import json_no_store
from app.services.recognition_errors import RecognitionUnavailable, LowConfidence, InvalidRecognitionResponse
from app.services.scan_errors import ScanInputInvalid, ScanRecognitionFailed, ScanCreationFailed

scan = Blueprint("scans", __name__)


@scan.route("", methods=["POST"])
@login_required
@validate
def create_scan_route(user: User):
    data = request.get_json() or {}
    image_value = data.get("image")

    try:
        image_data = _parse_base64_image(image_value)
        scan_result = current_app.scan_service.create_scan(user.id, image_data)
    except ValueError as exc:
        return json_no_store({"error": "Invalid base64 image payload.", "details": str(exc)}, 400)
    except ScanInputInvalid as exc:
        return json_no_store({"error": str(exc)}, 400)
    except ScanRecognitionFailed as exc:
        if exc.reason == "low_confidence":
            return json_no_store({
                "error": str(exc),
                "label": exc.label,
                "confidence": exc.confidence,
                "minimum_confidence": exc.minimum_confidence,
            }, 422)
        if exc.reason == "recognition_unavailable":
            return json_no_store({"error": str(exc)}, 503)
        return json_no_store({"error": str(exc)}, 502)
    except ScanCreationFailed as exc:
        return json_no_store({"error": str(exc)}, 500)

    return json_no_store(scan_result.to_dict(), 200)



def _parse_base64_image(image_value: str) -> bytes:
    if not isinstance(image_value, str) or not image_value.strip():
        raise ValueError("Image field is required and must be a base64 string.")

    if "," in image_value:
        _, base64_value = image_value.split(",", 1)
    else:
        base64_value = image_value

    try:
        return base64.b64decode(base64_value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Could not decode image bytes") from exc
