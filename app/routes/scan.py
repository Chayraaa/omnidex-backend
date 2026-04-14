from flask import Blueprint, current_app
from app.__init__ import login_required
from app.extensions import db
from app.models.user import User

scan = Blueprint("scan", __name__)


# user_id is required when having @login_required decorator. Has the id of the user.
@scan.route("/login_test", methods=["GET"])
@login_required
def scan_route(user_id: int):
    # A user can be retrieved like this:
    user = db.session.query(User).filter_by(id=user_id).first()
    return {"message": f"Hello, {user.name}!"}