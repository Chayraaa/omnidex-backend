import pathlib
import sys
import types
import unittest

from flask import Flask


def _install_lightweight_app_package():
    app_package = sys.modules.get("app")
    if app_package is None:
        app_package = types.ModuleType("app")
        app_package.__path__ = [str(pathlib.Path(__file__).resolve().parents[1] / "app")]
        sys.modules["app"] = app_package

    def _login_required(fn):
        def _wrapped(*args, **kwargs):
            return fn(user=types.SimpleNamespace(id=1, name="Tester"), *args, **kwargs)

        _wrapped.__name__ = fn.__name__
        return _wrapped

    app_package.login_required = _login_required
    app_package.validate = lambda fn: fn


_install_lightweight_app_package()

from app.routes.collection import collection  # noqa: E402
from app.routes.health import health  # noqa: E402
from app.routes.image import image  # noqa: E402
from app.routes.scan import scan  # noqa: E402
from app.routes.wiki import wiki  # noqa: E402


class _Dto:
    def __init__(self, payload):
        self.payload = payload

    def to_dict(self):
        return dict(self.payload)


class _CollectionService:
    def __init__(self):
        self.updated = False
        self.detail = _Dto(
            {
                "id": 1,
                "label": "cat",
                "category": "Tiere",
                "card_summary": "Cat summary",
            }
        )

    def get_user_collection(self, **kwargs):
        return [
            _Dto(
                {
                    "id": 1,
                    "label": "cat",
                    "category": "Tiere",
                    "card_summary": "Cat summary",
                }
            )
        ]

    def get_collection_entry_detail(self, **kwargs):
        return self.detail

    def update_collection_entry_category(self, **kwargs):
        self.updated = True
        self.detail = _Dto({**self.detail.to_dict(), "category": kwargs["category"]})
        return self.detail


class _ImageService:
    def get_image_stream(self, key):
        return b"image-bytes"


class _WikiService:
    def __init__(self, summary="Cat summary"):
        self.summary = summary

    def get_summary(self, title):
        return self.summary


class CacheRouteHeaderTests(unittest.TestCase):
    def _app(self):
        test_app = Flask(__name__)
        test_app.collection_service = _CollectionService()
        test_app.image_service = _ImageService()
        test_app.wiki_service = _WikiService()
        test_app.register_blueprint(collection, url_prefix="/v1/collections")
        test_app.register_blueprint(health, url_prefix="/v1/status")
        test_app.register_blueprint(image, url_prefix="/v1/image")
        test_app.register_blueprint(scan, url_prefix="/v1/scan")
        test_app.register_blueprint(wiki, url_prefix="/v1/wiki")
        return test_app

    def test_collection_list_uses_private_revalidation_and_304(self):
        app = self._app()
        client = app.test_client()

        response = client.get("/v1/collections/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "private, no-cache")
        self.assertEqual(response.headers["Vary"], "Authorization")
        etag = response.headers["ETag"]

        cached = client.get("/v1/collections/me", headers={"If-None-Match": etag})
        self.assertEqual(cached.status_code, 304)
        self.assertEqual(cached.get_data(), b"")

    def test_collection_category_patch_rejects_stale_if_match(self):
        app = self._app()
        client = app.test_client()

        response = client.patch(
            "/v1/collections/me/1/category",
            json={"category": "Pflanze"},
            headers={"If-Match": '"stale"'},
        )

        self.assertEqual(response.status_code, 412)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertFalse(app.collection_service.updated)

    def test_image_route_uses_private_cache_and_304(self):
        app = self._app()
        client = app.test_client()

        response = client.get("/v1/image/cards/1/cat.jpeg")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "private, max-age=86400, must-revalidate")
        etag = response.headers["ETag"]

        cached = client.get("/v1/image/cards/1/cat.jpeg", headers={"If-None-Match": etag})
        self.assertEqual(cached.status_code, 304)
        self.assertEqual(cached.get_data(), b"")

    def test_wiki_route_uses_public_cache_and_304(self):
        app = self._app()
        client = app.test_client()

        response = client.get("/v1/wiki/summary/cat")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "public, max-age=86400, must-revalidate")
        self.assertEqual(response.headers["Vary"], "Accept")
        etag = response.headers["ETag"]

        cached = client.get("/v1/wiki/summary/cat", headers={"If-None-Match": etag})
        self.assertEqual(cached.status_code, 304)
        self.assertEqual(cached.get_data(), b"")

    def test_wiki_not_found_uses_short_negative_cache(self):
        app = self._app()
        app.wiki_service = _WikiService(summary="No article found")
        client = app.test_client()

        response = client.get("/v1/wiki/summary/not-real")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["Cache-Control"], "public, max-age=300, must-revalidate")

    def test_scan_invalid_payload_is_no_store(self):
        app = self._app()
        client = app.test_client()

        response = client.post("/v1/scan", json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_health_is_no_store(self):
        app = self._app()
        client = app.test_client()

        response = client.get("/v1/status/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")


if __name__ == "__main__":
    unittest.main()
