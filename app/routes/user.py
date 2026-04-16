from flask import Blueprint, request, current_app

from app import validate, login_required
from app.domain_models.user import User

# This route handles user creation, modification, deletion, login, and logout
users = Blueprint("users", __name__)


# Creates a user and adds it to the database
@users.route("/create", methods=["POST"])
@validate
def create_user():
    data = request.get_json()
    name = data.get("name")
    password = data.get("password")

    if current_app.user_service.create_user(name, password):
        return {"message": "User created successfully."}, 201
    else:
        return {"message": "User already exists."}, 400


# Handles the login. It checks password and username, returns a jwt token which is subsequently checked in the
# login_required decorator.
@users.route("/login", methods=["POST"])
@validate
def login():
    data = request.get_json()
    name = data.get("name")
    password = data.get("password")

    token = current_app.auth_service.authenticate_user(name, password)
    if not token:
        return {"message": "Invalid credentials."}, 401

    return {
        "message": "Login successful. Use token for authentication.",
        "token": token
    }, 200


@users.route("/set_profile_picture", methods=["POST"])
@validate
@login_required
def set_profile_picture(user: User):
    data: dict = request.get_json()
    image = data.get("image")

    current_app.image_service.save_image(user, image, True)
    return {"message": "Profile picture set successfully."}, 200


@users.route("/get_profile_picture", methods=["POST"])
@validate
def get_profile_picture():
    data = request.get_json()
    user_id = data.get("user_id")

    url = current_app.image_service.get_user_image_url(User(id=user_id, name="", hashed_password=""))
    return {"url": url}, 200
