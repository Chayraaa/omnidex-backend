from flask import Blueprint, request, jsonify, current_app
from app.services.friends_service import FriendsService
from app.domain_models.user import User
from app.repositories.storage.sql_friends_repo import SqlFriendsRepo
from app.repositories.storage.sql_user_repo import SqlUserRepo
from app.__init__ import login_required
from flask import g

friends = Blueprint("friends", __name__)



# Service factory 
def get_friends_service():
    friends_repo = SqlFriendsRepo()
    user_repo = SqlUserRepo()

    return FriendsService(
        friends_repo,
        user_repo,
        current_app.notification_service
    )


# SEND FRIEND REQUEST
@friends.route("/requests/send/<friend_code>", methods=["POST"])
@login_required
def send_friend_request(user, friend_code):
    service = get_friends_service()
    result = service.create_friend_request(user, friend_code)

    if not result:
        return jsonify({"success": False, "message": "Could not send request"}), 400

    return jsonify({"success": True}), 201



# ACCEPT FRIEND REQUEST
@friends.route("/requests/accept/<int:sender_id>", methods=["POST"])
@login_required
def accept_friend_request(user: User, sender_id):
    service = get_friends_service()

    result = service.accept_friend_request(user, sender_id)

    if not result:
        return jsonify({"success": False, "message": "Could not accept request"}), 400

    return jsonify({"success": True})


# DECLINE FRIEND REQUEST
@friends.route("/requests/decline/<int:sender_id>", methods=["POST"])
@login_required
def decline_friend_request(user: User,sender_id):
    service = get_friends_service()

    result = service.decline_friend_request(user, sender_id)

    if not result:
        return jsonify({"success": False, "message": "Could not decline request"}), 400

    return jsonify({"success": True})

@friends.route("/requests", methods=["GET"])
@login_required
def get_incoming_requests(user: User):
    service = get_friends_service()

    requests = service.get_incoming_requests(user)

    return jsonify({
        "success": True,
        "requests": [
            {
                "sender_id": r["sender_id"],
                "status": r["status"]
            }
            for r in requests
        ]
    })


# REMOVE FRIEND
@friends.route("/<int:user_id>", methods=["DELETE"])
@login_required
def remove_friend(user: User, user_id):
    service = get_friends_service()

    result = service.remove_friend(user, user_id)

    if not result:
        return jsonify({"success": False, "message": "Could not remove friend"}), 400

    return jsonify({"success": True})


# GET FRIEND LIST
@friends.route("/", methods=["GET"])
@login_required
def get_friends(user:User):
    service = get_friends_service()

    friends = service.get_friends(user)

    return jsonify({
        "success": True,
        "friends": [
            {
                "friend_id": f["friend_id"],
                "status": f["status"]
            }
            for f in friends
        ]
    })