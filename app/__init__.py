from flask import Flask

# Here everything for app creation is inited.
def create_app():
    app = Flask(__name__)

    # Add all the routes here (see health as example)
    from .routes.health import health
    app.register_blueprint(health, url_prefix="/api")

    # Inject services here (LISA, Wikipedia)
    # Example:
    # from .services.external_api_service import ExternalAPIService
    # app.external_api = ExternalAPIService()
    # Usage in routes:
    # from flask import current_app
    # current_app.external_api.service_mock(param)

    return app