import logging
import os
from functools import wraps

import yaml
from authlib.integrations.flask_client import OAuth
from flask import Flask, request, current_app
from openapi_core.contrib.flask import FlaskOpenAPIRequest
from openapi_core.exceptions import OpenAPIError
from openapi_core.validation.request.exceptions import InvalidRequestBody
from openapi_core.validation.schemas.exceptions import InvalidSchemaValue
from werkzeug.middleware.proxy_fix import ProxyFix

from app.repositories.units_of_work.sql_unit import SqlUnitOfWork
from app.services.auth_service import AuthService
from app.services.image_service import ImageService
from app.services.password_service import PasswordService
from app.services.google_oauth_service import GoogleOauthService
from app.services.recognition_service import RecognitionService
from app.services.scan_service import ScanService
from app.services.collection_service import CollectionService
from app.services.summary_service import SummaryService
from app.services.category_service import CategoryService
from app.services.label_translation_service import LabelTranslationService
from app.services.user_service import UserService
from app.repositories.external.wiki_repo import WikiRepo
from app.repositories.external.openai_api_client import OpenAIApiClient
from app.repositories.external.openai_summary_api_client import OpenAISummaryApiClient
from app.repositories.external.openai_label_translation_api_client import OpenAILabelTranslationApiClient
from app.services.friends_service import FriendsService
from app.repositories.external.openai_category_api_client import OpenAICategoryApiClient
from app.repositories.external.openai_wbr_api_client import OpenAIWBRApiClient
from app.repositories.external.what_beats_rock import WhatBeatsRock
from app.extensions import db, migrate
from openapi_core import OpenAPI
from app.services.achievement_service import AchievementService
from app.services.wiki_service import WikiService
from app.http_cache import json_no_store

# Add all the db database_models here
from app.database_models.user_model import UserModel
from app.database_models.achievement_model import AchievementModel
from app.database_models.card_model import CardModel
from app.database_models.refresh_token_model import RefreshTokenModel
from app.database_models.friends_model import FriendsModel
from app.database_models.category_model import CategoryModel
from app.database_models.first_discovered_model import FirstDiscoveredModel
from app.database_models.user_achievement_model import UserAchievementModel
from app.database_models.wbr_model import WBRModel

# Open API file path
api_url = "/static/omnidex-api.yaml"


def setup_logging(app: Flask):
    if app.debug:
        return
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


def setup_openapi(app: Flask):
    yaml_path = os.path.join(app.root_path, "static", "omnidex-api.yaml")
    with open(yaml_path, "r") as f:
        spec = yaml.safe_load(f)

    app.openapi_spec = OpenAPI.from_dict(spec)


def setup_oauth(app: Flask):
    app.config["SECRET_KEY"] = os.getenv("JWT_SECRET")
    oauth = OAuth(app)

    google = oauth.register(
        name='google',
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile"
        }
    )
    app.google = google


def setup_database(app: Flask):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI",
                                                           "postgresql://user:password@localhost:5432/mydb")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.logger.info(f"Connecting to database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    db.init_app(app)
    migrate.init_app(app, db)


########################
# REGULAR EDITING HERE #
########################

def setup_services(app: Flask):
    # Defines the unit of work we are using since some repositories depend on each other.
    # E.g., you can't store the user in a database without the cards in the database.
    # When you, e.g., want to change from a database to a file-based storage, you would need to change the unit of work,
    # not the repositories defined for the services
    # storage_unit_of_work = SqlUnitOfWork()
    storage_unit_of_work = SqlUnitOfWork()

    app.password_service = PasswordService()
    app.achievement_service = AchievementService(
        storage_unit_of_work.user_achievement_repo,
        storage_unit_of_work.achievement_repo,
        storage_unit_of_work.card_repo,
    )
    # This is a user management service that you can give different implementations to
    # A service could also take another service as a dependency. Though make sure to prevent circular dependencies.
    app.user_service = UserService(
        storage_unit_of_work.user_repo,
        storage_unit_of_work.friends_repo,
        achievement_service = app.achievement_service
    )
    app.auth_service = AuthService(storage_unit_of_work.user_repo, storage_unit_of_work.refresh_token_repo)
    app.image_service = ImageService(storage_unit_of_work.image_storage, storage_unit_of_work.image_repo,
                                     base_url=os.environ.get("BASE_URL", "http://127.0.0.1:5000"))
    app.wiki_service = WikiService(WikiRepo())
    openai_adapter = OpenAIApiClient()
    openai_summary_adapter = OpenAISummaryApiClient()
    openai_category_adapter = OpenAICategoryApiClient()
    openai_label_translation_adapter = OpenAILabelTranslationApiClient()
    app.recognition_service = RecognitionService(openai_adapter)
    app.summary_service = SummaryService(openai_summary_adapter)
    app.category_service = CategoryService(openai_category_adapter)
    app.label_translation_service = LabelTranslationService(openai_label_translation_adapter)
    app.scan_service = ScanService(
        app.recognition_service,
        app.wiki_service,
        app.summary_service,
        storage_unit_of_work.image_storage,
        storage_unit_of_work.card_repo,
        base_url=os.environ.get("BASE_URL", "http://127.0.0.1:5000"),
        category_service=app.category_service,
        label_translation_service=app.label_translation_service,
        achievement_service=app.achievement_service,
        moderation_repo=storage_unit_of_work.moderation_repo
    )
    app.collection_service = CollectionService(
        storage_unit_of_work.collection_repo,
        base_url=os.environ.get("BASE_URL", "http://127.0.0.1:5000"),
    )
    app.google_oauth_service = GoogleOauthService(storage_unit_of_work.user_repo,
                                                  storage_unit_of_work.refresh_token_repo,
                                                  app.achievement_service)
    app.friends_service = FriendsService(
        storage_unit_of_work.friends_repo,
        storage_unit_of_work.user_repo,
        storage_unit_of_work.card_repo,
        base_url=os.environ.get("BASE_URL", "http://127.0.0.1:5000")
    )
    openai_wbr_adapter = OpenAIWBRApiClient()
    app.wbr_service = WhatBeatsRock(storage_unit_of_work.user_repo, openai_wbr_adapter)


# Add all the routes here (see health as example)
def setup_routes(app: Flask):
    from .routes.health import health
    app.register_blueprint(health, url_prefix="/v1/status")
    from .routes.user import users
    app.register_blueprint(users, url_prefix="/v1/users")
    from .routes.scan import scan
    app.register_blueprint(scan, url_prefix="/v1/scans")
    from .routes.image import image
    app.register_blueprint(image, url_prefix="/v1/images")
    from .routes.wiki import wiki
    app.register_blueprint(wiki, url_prefix="/v1/wiki")
    from .routes.collection import collection
    app.register_blueprint(collection, url_prefix="/v1/collections")
    from .routes.achievement import achievements
    app.register_blueprint(achievements, url_prefix="/v1/achievements")
    from .routes.friends import friends
    app.register_blueprint(friends, url_prefix="/v1/friends")
    from .routes.wbr import wbr
    app.register_blueprint(wbr, url_prefix="/v1/wbr")


########################
########################

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        # Get the token from the Authorization header
        token = request.headers.get("Authorization")
        if not token:
            return json_no_store({"error": "Token missing"}, 401)

        # Check if the token is in the correct format
        parts = token.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return json_no_store({"error": "Invalid Authorization header"}, 401)

        # Parsing and verification of the token
        token = parts[1]
        user_id = PasswordService.verify_token(token)
        if not user_id:
            return json_no_store({"error": "Invalid or expired token"}, 401)

        # Query the user from the database
        user = current_app.user_service.get_user(user_id)
        if not user:
            return json_no_store({"error": "User not found"}, 401)

        # Return the user object to the route handler
        return f(user=user, *args, **kwargs)

    return decorated


# Validation decorator
# AI used for beautifying output when validation failed
def validate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        openapi = current_app.openapi_spec

        try:
            openapi_request = FlaskOpenAPIRequest(request)
            openapi.validate_request(openapi_request)
        except InvalidRequestBody as e:
            if isinstance(e.__cause__, InvalidSchemaValue):
                errors = [err.message for err in e.__cause__.schema_errors]
            else:
                errors = [str(e.__cause__)]
            return json_no_store({
                "error": "Request body validation failed",
                "fields": errors
            }, 400)
        except OpenAPIError as e:
            return json_no_store({
                "error": "Request validation failed",
                "details": str(e)
            }, 400)

        return f(*args, **kwargs)

    return decorated


def open_api_page(app):
    from flask_swagger_ui import get_swaggerui_blueprint

    swagger_url = "/docs"

    swagger_ui = get_swaggerui_blueprint(
        swagger_url,
        api_url,
    )

    app.register_blueprint(swagger_ui, url_prefix=swagger_url)


# Here everything for app creation is inited.
def create_app(skip_services=None):
    if skip_services is None:
        skip_services = os.environ.get("SKIP_SERVICES") == "1"

    app = Flask(__name__)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    setup_logging(app)
    setup_openapi(app)
    setup_oauth(app)
    setup_database(app)
    if not skip_services:
        setup_services(app)
        setup_routes(app)
        open_api_page(app)

    return app
