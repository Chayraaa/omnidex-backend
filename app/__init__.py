import logging
import os
from functools import wraps

from flask import Flask, request, jsonify
from sqlalchemy import inspect

from app.services.password_service import PasswordService
from app.extensions import db

# Add all the db models here
from app.models.user import User

def setup_logging(app: Flask):
    if app.debug:
        return
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

def setup_database(app: Flask):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI",
                                                           "postgresql://user:password@localhost:5432/mydb")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.logger.info(f"Connecting to database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    db.init_app(app)

    with app.app_context():
        inspector = inspect(db.engine)
        for table_name, table_obj in db.metadata.tables.items():
            if not inspector.has_table(table_name):
                try:
                    table_obj.create(db.engine)
                    app.logger.info(f"Created table: {table_name}")
                except Exception as e:
                    app.logger.error(f"Error creating table {table_name}")
            else:
                app.logger.info(f"Table {table_name} already exists")


# Inject services here (LISA, Wikipedia)
# Example:
# from .services.external_api_service import ExternalAPIService
# app.external_api = ExternalAPIService()
# Usage in routes:
# from flask import current_app
# current_app.external_api.service_mock(param)
def setup_services(app: Flask):
    app.password_service = PasswordService()


# Add all the routes here (see health as example)
def setup_routes(app: Flask):
    from .routes.health import health
    app.register_blueprint(health, url_prefix="/api/status")
    from .routes.user import users
    app.register_blueprint(users, url_prefix="/api/users")
    from .routes.scan import scan
    app.register_blueprint(scan, url_prefix="/api/scan")

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        # Get the token from the Authorization header
        token = request.headers.get("Authorization")
        print(request.headers)
        if not token:
            return jsonify({"error": "Token missing"}), 401

        # Check if the token is in the correct format
        parts = token.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header"}), 401

        # Parsing and verification of the token
        token = parts[1]
        user_id = PasswordService.verify_token(token)
        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Query the user from the database
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 401

        # Return the user object to the route handler
        return f(user=user, *args, **kwargs)

    return decorated

def open_api_page(app):
    from flask_swagger_ui import get_swaggerui_blueprint

    swagger_url = "/docs"
    api_url = "/static/omnidex-api.yaml"

    swagger_ui = get_swaggerui_blueprint(
        swagger_url,
        api_url,
    )

    app.register_blueprint(swagger_ui, url_prefix=swagger_url)

# Here everything for app creation is inited.
def create_app():
    app = Flask(__name__)

    setup_logging(app)
    setup_database(app)
    setup_services(app)
    setup_routes(app)
    open_api_page(app)

    return app
