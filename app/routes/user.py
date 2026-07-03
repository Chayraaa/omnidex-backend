from authlib.integrations.base_client import MismatchingStateError
from flask import Blueprint, request, current_app, url_for, redirect

from app import validate, login_required
from app.domain_models.user import User
from app.http_cache import add_no_store, json_no_store

# This route handles user creation, modification, deletion, login, and logout
users = Blueprint("users", __name__)


# Creates a user and adds it to the database
@users.route("/create", methods=["POST"])
@validate
def create_user():
    data = request.get_json()
    email = (data.get("email") or "").strip().replace(" ", "")
    name = data.get("name")
    password = data.get("password")

    if current_app.user_service.create_user(name, email, password):
        return json_no_store({"message": "User created successfully."}, 201)
    else:
        return json_no_store({"message": "User already exists."}, 400)


# Handles the login. It checks password and username, returns a jwt token which is subsequently checked in the
# login_required decorator.
@users.route("/login", methods=["POST"])
# @validate
def login():
    data = request.get_json()
    email = (data.get("email") or "").strip().replace(" ", "")
    password = data.get("password")
    refresh = (data.get("refresh_token") or "")

    if refresh != "":
        res = current_app.auth_service.refresh_session(refresh)
    else:
        res = current_app.auth_service.authenticate_local(email, password)
    if not res:
        return json_no_store({"message": "Invalid credentials."}, 401)

    token, refresh, user = res

    return json_no_store({
        "message": "Login successful. Use token for authentication.",
        "user_id": user.id if isinstance(user, User) else user,
        "access_token": token,
        "refresh_token": refresh,
    }, 200)


@users.route("/google/login", methods=["GET"])
@validate
def google_login():
    redirect_uri = url_for("users.google_callback", _external=True)
    return add_no_store(current_app.google.authorize_redirect(redirect_uri))


@users.route("/google/callback", methods=["GET"])
@validate
def google_callback():
    try:
        token = current_app.google.authorize_access_token()
    except MismatchingStateError:
        return json_no_store({
            "error": "oauth_state_mismatch",
            "message": "Login session expired or invalid state. Please try again."
        }, 400)

    if not token:
        return json_no_store({"error": "Failed to authorize with Google"}, 400)

    user_info = token.get("userinfo")
    if not user_info:
        return json_no_store({"error": "Failed to fetch user info from Google"}, 400)

    jwt, refresh, user_id = current_app.google_oauth_service.authenticate_user(user_info)
    if not jwt:
        return json_no_store({"error": "Failed to authenticate user"}, 400)

    return redirect(
    f"omnidexfrontend://auth/google/callback"
    f"?accessToken={jwt}"
    f"&refreshToken={refresh}"
    f"&user_id={user_id}"
)


@users.route("/set_profile_picture", methods=["POST"])
@validate
@login_required
def set_profile_picture(user: User):
    data: dict = request.get_json()
    image = data.get("image")

    current_app.image_service.save_image(user, image, True)
    return json_no_store({"message": "Profile picture set successfully."}, 200)


@users.route("/get_profile_picture/<int:user_id>", methods=["GET"])
@validate
def get_profile_picture(user_id: int):
    url = current_app.image_service.get_user_image_url(User(id=user_id, name="", hashed_password=""))
    return json_no_store({"url": url}, 200)


@users.route("/<int:userId>", methods=["GET"])
@login_required
@validate
def get_user(user, userId: int):
    user = current_app.user_service.get_user(userId)

    if not user:
        return json_no_store({"message": "User not found"}, 404)

    return json_no_store({
        "user": {
            "id": user.id,
            "name": user.name,
            "profile_picture_key": user.profile_picture_key,
            "email": user.email,
            "friend_code": user.friend_code
        }
    }, 200)
