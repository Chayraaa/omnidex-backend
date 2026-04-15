from flask import Blueprint, jsonify, request

# This route monitors the health of the application

health = Blueprint("health", __name__)

@health.route("/health", methods=["GET"])
def status():
    return {"status": "ok"}, 200