import os
import pathlib
import sys
import types
import unittest

os.environ.setdefault("JWT_SECRET", "test-secret")

# Prevent app/__init__.py side effects during tests.
if "app" not in sys.modules:
    app_package = types.ModuleType("app")
    app_package.__path__ = [str(pathlib.Path(__file__).resolve().parents[1] / "app")]
    sys.modules["app"] = app_package

def _missing_lisa_config() -> list[str]:
    required = ("LISA_BASE_URL", "LISA_API_KEY", "LISA_TEST_IMAGE_PATH")
    return [name for name in required if not os.environ.get(name)]


@unittest.skipIf(
    bool(_missing_lisa_config()),
    "Set LISA_BASE_URL, LISA_API_KEY, and LISA_TEST_IMAGE_PATH to run real LISA API integration tests.",
)
class LisaApiClientIntegrationTests(unittest.TestCase):
    def test_real_lisa_api_returns_recognition_result(self):
        from app.repositories.external.lisa_api_client import LisaApiClient
        from app.services.recognition_service import RecognitionService

        image_path = pathlib.Path(os.environ["LISA_TEST_IMAGE_PATH"])
        self.assertTrue(image_path.is_file(), f"Test image does not exist: {image_path}")

        service = RecognitionService(LisaApiClient(), minimum_confidence=0.0)

        result = service.recognize_image(image_path.read_bytes())

        self.assertIsInstance(result.label, str)
        self.assertTrue(result.label.strip())
        self.assertIsInstance(result.confidence, float)
        self.assertGreaterEqual(result.confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
