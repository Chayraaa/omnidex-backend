import os
from typing import Any

import requests

from app.repositories.interfaces.external.summary_adapter_protocol import SummaryAdapterProtocol
from app.services.summary_errors import SummaryUnavailable, InvalidSummaryResponse


class OpenAISummaryApiClient(SummaryAdapterProtocol):
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        model: str | None = None,
    ):
        self.base_url = (base_url or os.environ.get("AI_BASE_URL", "")).strip().rstrip("/")
        self.api_key = (api_key or os.environ.get("AI_API_KEY", "")).strip()
        self.model = (model or os.environ.get("AI_SUMMARY_MODEL", os.environ.get("AI_MODEL", "gpt-4o-mini"))).strip()
        timeout_raw = timeout_seconds
        if timeout_raw is None:
            timeout_raw = os.environ.get("AI_SUMMARY_TIMEOUT_SECONDS", os.environ.get("AI_TIMEOUT_SECONDS", "10"))
        self.timeout_seconds = float(timeout_raw)

        if not self.base_url:
            raise ValueError("AI_BASE_URL environment variable is required")
        if not self.api_key:
            raise ValueError("AI_API_KEY environment variable is required")

    def summarize_text(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise InvalidSummaryResponse("Summary prompt must be a non-empty string")

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "user", "content": [{"type": "text", "text": prompt}]},
            ],
        }
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            print(f"DEBUG: OpenAI summary request failed: {exc}")
            raise SummaryUnavailable("OpenAI summary request failed") from exc
        body = self._read_json_response(response)
        content = self._extract_assistant_content(body)
        if isinstance(content, str) and content.strip():
            return content.strip()
        raise InvalidSummaryResponse("OpenAI summary response did not include assistant content")

    def _read_json_response(self, response: requests.Response) -> Any:
        if response.status_code >= 400:
            print(f"DEBUG: OpenAI summary failed with status {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")
        else:
            print(f"DEBUG: OpenAI summary successful with status {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")

        if response.status_code >= 500:
            raise SummaryUnavailable(f"OpenAI summary returned server error: {response.status_code}")
        if response.status_code >= 400:
            raise InvalidSummaryResponse(f"OpenAI summary rejected request: HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            print(f"DEBUG: OpenAI summary returned non-JSON response: {response.text}")
            raise InvalidSummaryResponse("OpenAI summary returned non-JSON response") from exc

    def _auth_headers(self) -> dict[str, str]:
        token = self.api_key
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        return {"Authorization": f"Bearer {token}"}

    def _extract_assistant_content(self, payload: Any) -> str | None:
        if not isinstance(payload, dict):
            return None

        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
                text = first_choice.get("text")
                if isinstance(text, str):
                    return text

        message = payload.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content

        messages = payload.get("messages")
        if isinstance(messages, list):
            for message_obj in reversed(messages):
                if not isinstance(message_obj, dict) or message_obj.get("role") != "assistant":
                    continue
                content = message_obj.get("content")
                if isinstance(content, str):
                    return content

        content = payload.get("content")
        if isinstance(content, str):
            return content
        return None
