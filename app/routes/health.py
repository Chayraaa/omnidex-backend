from flask import Blueprint

from app.http_cache import json_no_store

# This route monitors the health of the application

health = Blueprint("health", __name__)

@health.route("/health", methods=["GET"])
def status():
    return json_no_store({"status": "ok"}, 200)
