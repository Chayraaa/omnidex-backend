import json
import os
from typing import Any

import requests

from app.repositories.interfaces.external.category_assignment_adapter_protocol import (
    CategoryAssignmentAdapterProtocol,
)
from app.services.category_errors import (
    CategoryAssignmentUnavailable,
    InvalidCategoryAssignmentResponse,
)


class LisaCategoryApiClient(CategoryAssignmentAdapterProtocol):
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        model: str | None = None,
    ):
        self.base_url = (base_url or os.environ.get("LISA_BASE_URL", "")).strip().rstrip("/")
        self.api_key = (api_key or os.environ.get("LISA_API_KEY", "")).strip()
        self.model = (
            model
            or os.environ.get("LISA_CATEGORY_MODEL", os.environ.get("LISA_SUMMARY_MODEL", os.environ.get("LISA_MODEL", "lisa-vision")))
        ).strip()

        timeout_raw = timeout_seconds
        if timeout_raw is None:
            timeout_raw = os.environ.get("LISA_CATEGORY_TIMEOUT_SECONDS", os.environ.get("LISA_TIMEOUT_SECONDS", "10"))
        self.timeout_seconds = float(timeout_raw)

        if not self.base_url:
            raise ValueError("LISA_BASE_URL environment variable is required")
        if not self.api_key:
            raise ValueError("LISA_API_KEY environment variable is required")

    def assign_category(self, prompt: str) -> dict[str, Any]:
        if not isinstance(prompt, str) or not prompt.strip():
            raise InvalidCategoryAssignmentResponse("Category prompt must be a non-empty string")

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt}]},
            ],
        }
        try:
            response = requests.post(
                f"{self.base_url}/api/chat/completions",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise CategoryAssignmentUnavailable("LISA category assignment request failed") from exc

        body = self._read_json_response(response)
        content = self._extract_assistant_content(body)
        print("LISA: Step 2 done")
        if isinstance(content, dict):
            return content
        if not isinstance(content, str) or not content.strip():
            raise InvalidCategoryAssignmentResponse("LISA category response did not include assistant content")
        return self._parse_json_content(content)

    def _read_json_response(self, response: requests.Response) -> Any:
        if response.status_code >= 500:
            raise CategoryAssignmentUnavailable(f"LISA category assignment returned server error: {response.status_code}")
        if response.status_code >= 400:
            raise InvalidCategoryAssignmentResponse(f"LISA category assignment rejected request: HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise InvalidCategoryAssignmentResponse("LISA category assignment returned non-JSON response") from exc

    def _auth_headers(self) -> dict[str, str]:
        token = self.api_key
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        return {"Authorization": f"Bearer {token}"}

    def _extract_assistant_content(self, payload: Any) -> Any:
        if not isinstance(payload, dict):
            return None

        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict) and "content" in message:
                    return message["content"]
                if "text" in first_choice:
                    return first_choice["text"]

        message = payload.get("message")
        if isinstance(message, dict) and "content" in message:
            return message["content"]

        messages = payload.get("messages")
        if isinstance(messages, list):
            for message_obj in reversed(messages):
                if isinstance(message_obj, dict) and message_obj.get("role") == "assistant":
                    return message_obj.get("content")

        if "content" in payload:
            return payload["content"]
        return None

    def _parse_json_content(self, content: str) -> dict[str, Any]:
        stripped = content.strip()
        if stripped.startswith("```"):
            stripped = stripped.strip("`").strip()
            if stripped.lower().startswith("json"):
                stripped = stripped[4:].strip()

        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = self._parse_embedded_json(stripped)

        if not isinstance(parsed, dict):
            raise InvalidCategoryAssignmentResponse("LISA category content must contain a JSON object")
        return parsed

    @staticmethod
    def _parse_embedded_json(content: str) -> Any:
        decoder = json.JSONDecoder()
        for index, char in enumerate(content):
            if char != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(content[index:])
                return parsed
            except json.JSONDecodeError:
                continue
        raise InvalidCategoryAssignmentResponse("LISA category content did not contain valid JSON")

