from flask import Blueprint, jsonify, request

health = Blueprint("health", __name__)

@health.route("/health", methods=["GET"])
def status():
    return jsonify({"status": "ok"})

@health.route("/echo", methods=["POST"])
def echo():
    data = request.json
    return jsonify(data)