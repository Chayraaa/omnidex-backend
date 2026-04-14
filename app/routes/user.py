from flask import Blueprint, request

from app.extensions import db
from app.models.user import User

# This route handles user creation, modification, deletion, login, and logout
users = Blueprint("users", __name__)


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

