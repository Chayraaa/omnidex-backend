import pathlib
import sys
import types
import unittest

from flask import Flask


if "app" not in sys.modules:
    app_package = types.ModuleType("app")
    app_package.__path__ = [str(pathlib.Path(__file__).resolve().parents[1] / "app")]
    sys.modules["app"] = app_package

from app.http_cache import (  # noqa: E402
    NO_STORE,
    PRIVATE_REVALIDATE_CACHE,
    if_match_satisfied,
    json_no_store,
    json_response_with_etag,
    make_json_etag,
)


class HttpCacheTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def test_json_response_includes_etag_and_cache_control(self):
        with self.app.test_request_context("/resource"):
            response = json_response_with_etag(
                {"label": "cat"},
                cache_control=PRIVATE_REVALIDATE_CACHE,
                vary="Authorization",
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "private, no-cache")
        self.assertEqual(response.headers["Vary"], "Authorization")
        self.assertTrue(response.headers["ETag"].startswith('"'))

    def test_matching_if_none_match_returns_304_without_body(self):
        payload = {"label": "cat"}
        etag = make_json_etag(payload)

        with self.app.test_request_context("/resource", headers={"If-None-Match": etag}):
            response = json_response_with_etag(
                payload,
                cache_control=PRIVATE_REVALIDATE_CACHE,
                vary="Authorization",
            )

        self.assertEqual(response.status_code, 304)
        self.assertEqual(response.get_data(), b"")
        self.assertEqual(response.headers["ETag"], etag)
        self.assertEqual(response.headers["Cache-Control"], "private, no-cache")

    def test_json_no_store_sets_cache_control(self):
        with self.app.test_request_context("/resource"):
            response = json_no_store({"ok": True}, 201)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers["Cache-Control"], NO_STORE)

    def test_if_match_accepts_current_etag_and_rejects_stale_etag(self):
        current = make_json_etag({"category": "Tiere"})

        with self.app.test_request_context("/resource", headers={"If-Match": current}):
            self.assertTrue(if_match_satisfied(current))

        with self.app.test_request_context("/resource", headers={"If-Match": '"stale"'}):
            self.assertFalse(if_match_satisfied(current))


if __name__ == "__main__":
    unittest.main()
