from flask import Blueprint, request, current_app

from app.extensions import db
from app.models.user import User

# This route handles user creation, modification, deletion, login, and logout
users = Blueprint("users", __name__)


# Creates a user and adds it to the database
@users.route("/create", methods=["POST"])
def create_user():
    data = request.get_json()
    name = data["name"]
    password = data["password"]
    if not name or not password:
        return {"message": "Name and password are required."}, 400
    if not isinstance(name, str) and not isinstance(password, str):
        return {"message": "Name and password must be strings."}, 400

    user = User(name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return {"message": "User created successfully."}, 201


# Handles the login. It checks password and username, returns a jwt token which is subsequently checked in the
# login_required decorator.
@users.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    name = data["name"]
    password = data["password"]
    if not name or not password:
        return {"message": "Name and password are required."}, 400
    if not isinstance(name, str) and not isinstance(password, str):
        return {"message": "Name and password must be strings."}, 400

    user = db.session.query(User).filter_by(name=name).first()
    if not user or not user.check_password(password):
        return {"message": "Invalid credentials."}, 401

    token = current_app.password_service.generate_token(user.id)
    return {
        "message": "Login successful. Use token for authentication.",
        "token": token
    }, 200
