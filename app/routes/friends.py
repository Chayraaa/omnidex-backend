from flask import Blueprint, request, jsonify, current_app
from app.services.friends_service import FriendsService
from app.domain_models.user import User
from app.repositories.storage.sql_friends_repo import SqlFriendsRepo
from app.repositories.storage.sql_user_repo import SqlUserRepo
from app.repositories.storage.sql_card_repo import SqlCardRepo

from app.__init__ import login_required
from flask import g

friends = Blueprint("friends", __name__)



# Service factory
def get_friends_service():
    return current_app.friends_service


# SEND FRIEND REQUEST
@friends.route("/requests/<friend_code>", methods=["POST"])
@login_required
def send_friend_request(user: User, friend_code):
    service = get_friends_service()
    
    if not service.create_friend_request(user, friend_code):
        return jsonify({
            "success": False,
            "error": "Invalid friend code or request already exists"
        }), 400

    return jsonify({
        "success": True,
        "message": "Friend request sent successfully"
    }), 201



@friends.route("/requests/<int:sender_id>", methods=["PATCH"])
@login_required
def update_friend_request(user: User, sender_id):
    service = get_friends_service()

    status = request.get_json().get("status")


    if status == "ACCEPTED":
        success = service.accept_friend_request(user, sender_id)
        success_message = "Friend request accepted"
        error_message = "Request already handled or does not exist"

    elif status == "DECLINED":
        success = service.decline_friend_request(user, sender_id)
        success_message = "Friend request declined"
        error_message = "Request already handled or does not exist"

    else:
        return jsonify({
            "success": False,
            "error": "Status must be ACCEPTED or DECLINED"
        }), 400

    if not success:
        return jsonify({
            "success": False,
            "error": error_message
        }), 400

    return jsonify({
        "success": True,
        "message": success_message
    }), 200


@friends.route("/requests", methods=["GET"])
@login_required
def get_incoming_requests(user: User):
    service = get_friends_service()

    return jsonify({
        "success": True,
        "requests": service.get_incoming_requests(user)
    })


# REMOVE FRIEND
@friends.route("/<int:user_id>", methods=["DELETE"])
@login_required
def remove_friend(user: User, user_id):
    service = get_friends_service()

    if not service.remove_friend(user, user_id):
        return jsonify({
            "success": False,
            "error": "User is not in friend list"
        }), 400

    return jsonify({
        "success": True,
        "message": "Friend removed successfully"
    })


# GET FRIEND LIST
@friends.route("", methods=["GET"])
@login_required
def get_friends(user: User):
    service = get_friends_service()

    friends_list = service.get_friends(user)

    return jsonify({
        "success": True,
        "friends": [
            {
                "friendId": f["friend_id"],
                "name": f["name"],
                "pictureUrl": f["profile_picture_key"],
                "status": f["status"]
            }
            for f in friends_list
        ]
    })

@friends.route("/feed", methods=["GET"])
@login_required
def get_friends_feed(user: User):
    service = get_friends_service()
    feed = service.get_friends_feed(user)
    print(feed)
    return jsonify({
        "success": True,
        "feed": feed
    }), 200