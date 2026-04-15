from flask import Blueprint

from app import validate, login_required
from app.domain_models.user import User

scan = Blueprint("scan", __name__)


# user_id is required when having @login_required decorator. Has the user object
@scan.route("/login_test", methods=["GET"])
@login_required
@validate
def scan_route(user: User):
    return {"message": f"Hello, {user.name}!"}, 200