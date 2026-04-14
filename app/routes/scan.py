from flask import Blueprint
from app.__init__ import login_required
from app.models.user import User

scan = Blueprint("scan", __name__)


# user_id is required when having @login_required decorator. Has the user object
@scan.route("/login_test", methods=["GET"])
@login_required
def scan_route(user: User):
    return {"message": f"Hello, {user.name}!"}, 200