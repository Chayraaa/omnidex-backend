from flask import Blueprint, request, current_app

from app import validate

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
