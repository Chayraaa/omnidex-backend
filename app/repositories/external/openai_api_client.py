import os
import json
import base64
from typing import Any

import requests

from app.repositories.interfaces.external.recognition_adapter_protocol import RecognitionAdapterProtocol
from app.services.recognition_errors import RecognitionUnavailable, InvalidRecognitionResponse
from app.utils.image_processing import compress_image


class OpenAIApiClient(RecognitionAdapterProtocol):
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float | None = None,
        model: str | None = None,
        image_max_size: int | None = None,
        image_detail: str | None = None,
    ):
        self.base_url = (base_url or os.environ.get("AI_BASE_URL", "")).strip().rstrip("/")
        self.api_key = (api_key or os.environ.get("AI_API_KEY", "")).strip()
        self.model = (model or os.environ.get("AI_MODEL", "gpt-4o-mini")).strip()

        timeout_raw = timeout_seconds if timeout_seconds is not None else os.environ.get("AI_TIMEOUT_SECONDS", "10")
        self.timeout_seconds = float(timeout_raw)

        image_max_size_raw = image_max_size if image_max_size is not None else os.environ.get("AI_IMAGE_MAX_SIZE", "512")
        self.image_max_size = int(image_max_size_raw)

        self.image_detail = (image_detail or os.environ.get("AI_IMAGE_DETAIL", "low")).strip()

        if not self.base_url:
            raise ValueError("AI_BASE_URL environment variable is required")
        if not self.api_key:
            raise ValueError("AI_API_KEY environment variable is required")

    def recognize_image(self, image_data: bytes) -> dict[str, Any]:
        if not image_data:
            raise InvalidRecognitionResponse("No image data provided for recognition")

        payload = self._request_completion(image_data)
        return self._normalize_payload(self._extract_assistant_payload(payload))

    def _request_completion(self, image_data: bytes) -> dict[str, Any]:
        compressed_image = compress_image(image_data, max_size=self.image_max_size)
        image_b64 = base64.b64encode(compressed_image).decode("utf-8")
        prompt = (
            "Analysiere das Bild und erkenne das Hauptobjekt. "
            "Gib die Antwort ausschließlich als JSON zurück. "
            "Verwende dabei folgende Struktur: "
            '{"label": "Objektname auf Deutsch", "confidence": 0.0, '
            '"alternatives": [{"label": "alternatives Objekt", "confidence": 0.0}], '
            '"category_hint": "Kategorie oder null"}\n\n'
            "Regeln:\n"
            "- Verwende ausschließlich deutsche Begriffe\n"
            "- Keine Erklärungen, kein Text außerhalb von JSON\n"
            "- Keine englischen Begriffe verwenden\n"
            "- Wenn unbekannt, gib 'Unbekannt' zurück"
        )

        request_payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                                "detail": self.image_detail
                            },
                        },
                    ],
                }
            ],
            "response_format": {"type": "json_object"},
        }

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                json=request_payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            print(f"DEBUG: OpenAI completion request failed: {exc}")
            raise RecognitionUnavailable("OpenAI completion request failed") from exc

        return self._read_json_response(response, "OpenAI completion")

    def _read_json_response(self, response: requests.Response, operation: str) -> Any:
        if response.status_code >= 400:
            print(f"DEBUG: {operation} failed with status {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")
        else:
            print(f"DEBUG: {operation} successful with status {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")
            
        if response.status_code >= 500:
            raise RecognitionUnavailable(f"{operation} returned server error: {response.status_code}")
        if response.status_code >= 400:
            raise InvalidRecognitionResponse(f"{operation} rejected request: HTTP {response.status_code}")

        try:
            return response.json()
        except ValueError as exc:
            print(f"DEBUG: {operation} returned non-JSON response: {response.text}")
            raise InvalidRecognitionResponse(f"{operation} returned non-JSON response") from exc

    def _auth_headers(self) -> dict[str, str]:
        token = self.api_key
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        return {"Authorization": f"Bearer {token}"}

    def _extract_assistant_payload(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise InvalidRecognitionResponse("OpenAI completion payload must be a JSON object")

        content = self._extract_assistant_content(payload)
        if isinstance(content, dict):
            return content
        if not isinstance(content, str) or not content.strip():
            raise InvalidRecognitionResponse("OpenAI completion response did not include assistant content")

        return self._parse_json_content(content)

    def _extract_assistant_content(self, payload: dict[str, Any]) -> Any:
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
            for message in reversed(messages):
                if isinstance(message, dict) and message.get("role") == "assistant":
                    return message.get("content")

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
            raise InvalidRecognitionResponse("OpenAI assistant content must contain a JSON object")
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
        raise InvalidRecognitionResponse("OpenAI assistant content did not contain valid JSON")

    def _normalize_payload(self, payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise InvalidRecognitionResponse("OpenAI payload must be a JSON object")

        candidates = self._extract_candidates(payload)
        if not candidates:
            raise InvalidRecognitionResponse("No recognition candidates found in OpenAI payload")

        candidates.sort(
            key=lambda item: item.get("confidence")
            if isinstance(item.get("confidence"), (int, float))
            else -1.0,
            reverse=True,
        )

        primary = candidates[0]
        label = primary.get("label")
        confidence = primary.get("confidence")
        if not isinstance(label, str) or not label.strip():
            raise InvalidRecognitionResponse("Primary recognition candidate is missing a label")
        if not isinstance(confidence, (int, float)):
            raise InvalidRecognitionResponse("Primary recognition candidate is missing numeric confidence")

        alternatives = []
        for candidate in candidates[1:]:
            alternative_label = candidate.get("label")
            if not isinstance(alternative_label, str) or not alternative_label.strip():
                continue
            alternative_confidence = candidate.get("confidence")
            if isinstance(alternative_confidence, (int, float)):
                alternatives.append({
                    "label": alternative_label,
                    "confidence": float(alternative_confidence),
                })
            else:
                alternatives.append({"label": alternative_label})

        return {
            "label": label.strip(),
            "confidence": float(confidence),
            "alternatives": alternatives,
            "category_hint": self._extract_category_hint(payload, primary),
            "provider_raw": payload,
        }

    def _extract_candidates(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        sources: list[Any] = []

        if isinstance(payload.get("predictions"), list):
            sources.append(payload.get("predictions"))
        if isinstance(payload.get("results"), list):
            sources.append(payload.get("results"))
        if isinstance(payload.get("candidates"), list):
            sources.append(payload.get("candidates"))
        if isinstance(payload.get("items"), list):
            sources.append(payload.get("items"))

        nested_data = payload.get("data")
        if isinstance(nested_data, dict):
            for key in ("predictions", "results", "candidates", "items"):
                if isinstance(nested_data.get(key), list):
                    sources.append(nested_data.get(key))

        label = payload.get("label")
        confidence = payload.get("confidence", payload.get("score", payload.get("probability")))
        if isinstance(label, str) and isinstance(confidence, (int, float)):
            sources.append([payload])

        candidates: list[dict[str, Any]] = []
        for source in sources:
            for raw_candidate in source:
                if not isinstance(raw_candidate, dict):
                    continue
                normalized = self._normalize_candidate(raw_candidate)
                if normalized is not None:
                    candidates.append(normalized)

        return candidates

    @staticmethod
    def _normalize_candidate(raw_candidate: dict[str, Any]) -> dict[str, Any] | None:
        label = raw_candidate.get("label", raw_candidate.get("name", raw_candidate.get("class")))
        if not isinstance(label, str) or not label.strip():
            return None

        confidence = raw_candidate.get(
            "confidence",
            raw_candidate.get("score", raw_candidate.get("probability")),
        )
        if isinstance(confidence, str):
            try:
                confidence = float(confidence)
            except ValueError:
                confidence = None

        normalized: dict[str, Any] = {"label": label.strip()}
        if isinstance(confidence, (int, float)):
            normalized["confidence"] = float(confidence)
        return normalized

    @staticmethod
    def _extract_category_hint(payload: dict[str, Any], primary_candidate: dict[str, Any]) -> str | None:
        for source in (primary_candidate, payload, payload.get("data", {})):
            if not isinstance(source, dict):
                continue
            value = source.get("category_hint", source.get("category"))
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None
