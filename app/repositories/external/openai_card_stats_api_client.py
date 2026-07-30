import os
import json
from typing import Any

import requests

from app.repositories.interfaces.external.card_stats_adapter_protocol import CardStatsAdapterProtocol
from app.services.recognition_errors import RecognitionUnavailable, InvalidRecognitionResponse


class OpenAICardStatsApiClient(CardStatsAdapterProtocol):
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        model: str | None = None,
    ):
        self.base_url = (base_url or os.environ.get("AI_BASE_URL", "")).strip().rstrip("/")
        self.api_key = (api_key or os.environ.get("AI_API_KEY", "")).strip()
        self.model = (model or os.environ.get("AI_STATS_MODEL", os.environ.get("AI_MODEL", "gpt-4o-mini"))).strip()
        timeout_raw = timeout_seconds
        if timeout_raw is None:
            timeout_raw = os.environ.get("AI_STATS_TIMEOUT_SECONDS", os.environ.get("AI_TIMEOUT_SECONDS", "10"))
        self.timeout_seconds = float(timeout_raw)

        if not self.base_url:
            raise ValueError("AI_BASE_URL environment variable is required")
        if not self.api_key:
            raise ValueError("AI_API_KEY environment variable is required")

    def classify_card(self, label: str, description: str) -> dict[str, Any]:
        prompt = (
            f"Classify the following object as a 'fighter' or 'equipment' for a card game.\n"
            f"Object: {label}\n"
            f"Description: {description}\n\n"
            f"Rules:\n"
            f"- A 'fighter' is a living being (e.g., butterfly), robot, figurine, stuffed animal, vehicle/model (e.g., Star Trek USS Enterprise), or any entity that could potentially move and fight if it were animated or came to life.\n"
            f"- 'equipment' is a static object, tool, or weapon that doesn't have a persona or the ability to move independently. If in doubt, prefer 'fighter'.\n"
            f"- Provide a wide variety of stats (attack and health) based on the perceived power, size, and durability of the object. Do not stick to low values; use the full range if appropriate.\n"
            f"- Fighter stats (attack and health) must be between 5 and 100, rounded up to the nearest 5 (5, 10, 15, ..., 100).\n"
            f"- Equipment stats (attack and health) must be between 5 and 50, rounded up to the nearest 5 (5, 10, 15, ..., 50).\n"
            f"- Return ONLY a JSON object with the following keys: 'battle_type' (string: 'fighter' or 'equipment'), 'attack' (int), 'health' (int)."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
        }

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            raise RecognitionUnavailable("OpenAI stats request failed") from exc

        body = self._read_json_response(response)
        content = self._extract_assistant_content(body)
        
        try:
            return json.loads(content)
        except (ValueError, TypeError):
            raise InvalidRecognitionResponse("OpenAI stats response is not valid JSON")

    def _read_json_response(self, response: requests.Response) -> Any:
        if response.status_code >= 500:
            raise RecognitionUnavailable(f"OpenAI stats returned server error: {response.status_code}")
        if response.status_code >= 400:
            raise InvalidRecognitionResponse(f"OpenAI stats rejected request: HTTP {response.status_code}")
        try:
            return response.json()
        except ValueError as exc:
            raise InvalidRecognitionResponse("OpenAI stats returned non-JSON response") from exc

    def _auth_headers(self) -> dict[str, str]:
        token = self.api_key
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        return {"Authorization": f"Bearer {token}"}

    def _extract_assistant_content(self, payload: Any) -> str:
        if not isinstance(payload, dict):
            raise InvalidRecognitionResponse("OpenAI payload must be a JSON object")

        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str):
                        return content
        raise InvalidRecognitionResponse("OpenAI stats response did not include assistant content")
