import logging
import os

from flask import Flask

def setup_logging(app: Flask):
    if app.debug:
        return
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

def setup_database(app: Flask):
    from .extensions import db
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI",
                                                           "postgresql://user:password@localhost:5432/mydb")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.logger.info(f"Connecting to database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    db.init_app(app)

    # Add all the models here
    from .models.user import User

    with app.app_context():
        db.create_all()


# Inject services here (LISA, Wikipedia)
# Example:
# from .services.external_api_service import ExternalAPIService
# app.external_api = ExternalAPIService()
# Usage in routes:
# from flask import current_app
# current_app.external_api.service_mock(param)
def setup_services(app: Flask):
    from .services.password_service import PasswordService
    app.password_service = PasswordService()


# Add all the routes here (see health as example)
def setup_routes(app: Flask):
    from .routes.health import health
    app.register_blueprint(health, url_prefix="/api/status")
    from .routes.user import users
    app.register_blueprint(users, url_prefix="/api/users")


# Here everything for app creation is inited.
def create_app():
    app = Flask(__name__)

    setup_logging(app)
    setup_database(app)
    setup_routes(app)
    setup_services(app)

    return app
