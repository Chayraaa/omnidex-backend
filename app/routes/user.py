from flask import Blueprint, request, current_app

from app.extensions import db
from app.database_models.user_model import UserModel

# This route handles user creation, modification, deletion, login, and logout
users = Blueprint("users", __name__)


# Verification that user and password were provided in the request
def verify_json_for_user_pass(data):
    name = data["name"]
    password = data["password"]
    if not name or not password:
        return {"message": "Name and password are required."}, 400
    if not isinstance(name, str) and not isinstance(password, str):
        return {"message": "Name and password must be strings."}, 400
    return name, password


# Creates a user and adds it to the database
@users.route("/create", methods=["POST"])
def create_user():
    data = request.get_json()
    validated_data = verify_json_for_user_pass(data)
    if isinstance(validated_data[0], dict):
        return validated_data[0], validated_data[1]
    name, password = validated_data

    if current_app.user_service.create_user(name, password):
        return {"message": "User created successfully."}, 201
    else:
        return {"message": "User already exists."}, 400


# Handles the login. It checks password and username, returns a jwt token which is subsequently checked in the
# login_required decorator.
@users.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    validated_data = verify_json_for_user_pass(data)
    if isinstance(validated_data[0], dict):
        return validated_data[0], validated_data[1]
    name, password = validated_data

    user = db.session.query(UserModel).filter_by(name=name).first()
    if not user or not user.check_password(password):
        return {"message": "Invalid credentials."}, 401

    token = current_app.password_service.generate_token(user.id)
    return {
        "message": "Login successful. Use token for authentication.",
        "token": token
    }, 200
