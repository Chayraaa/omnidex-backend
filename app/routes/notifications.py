from flask import Blueprint, current_app, jsonify

from app import validate, login_required

notifications = Blueprint("notifications", __name__)


@notifications.route("/", methods=["GET"])
@login_required
def get_notifications(user):
    service = current_app.notification_service

    result = service.get_for_user(user.id)

    return jsonify({
        "success": True,
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None
            }
            for n in result
        ]
    }), 200