import os
import requests
from typing import Any

from app.repositories.interfaces.external.wbr_adapter_protocol import WBRAdapterProtocol


class OpenAIWBRApiClient(WBRAdapterProtocol):
    def __init__(
            self,
            base_url: str | None = None,
            api_key: str | None = None,
            timeout_seconds: float | None = None,
            model: str | None = None,
    ):
        self.base_url = (base_url or os.environ.get("AI_BASE_URL", "")).strip().rstrip("/")
        self.api_key = (api_key or os.environ.get("AI_API_KEY", "")).strip()
        self.model = (model or os.environ.get("AI_WBR_MODEL", os.environ.get("AI_MODEL", "gpt-4o-mini"))).strip()
        timeout_raw = timeout_seconds
        if timeout_raw is None:
            timeout_raw = os.environ.get("AI_WBR_TIMEOUT_SECONDS", os.environ.get("AI_TIMEOUT_SECONDS", "10"))
        self.timeout_seconds = float(timeout_raw)

        if not self.base_url:
            raise ValueError("AI_BASE_URL environment variable is required")
        if not self.api_key:
            raise ValueError("AI_API_KEY environment variable is required")

    def evaluate_match(self, attacker: str, defender: str) -> tuple[bool, str]:
        prompt = f"""
        Du bist ein kreativer und fairer Schiedsrichter eines Spiels.

        Deine Aufgabe ist zu entscheiden, ob "{attacker}" "{defender}" besiegt.

        Bewerte die Verbindung zwischen den beiden Begriffen anhand von:
        - Allgemeinwissen
        - logischem Denken
        - kreativen, aber verständlichen Zusammenhängen
        - typischen Eigenschaften der Dinge

        Sei offen für clevere Lösungen, aber akzeptiere keine völlig erfundenen oder extrem unwahrscheinlichen Szenarien.
        
        Sprachstil:
        - Schreibe wie ein deutscher Muttersprachler.
        - Verwende natürliche Alltagssprache.
        - Vermeide wörtliche Übersetzungen aus dem Englischen.
        - Verwende keine ungewöhnlichen oder künstlich klingenden Formulierungen.
        - Wenn ein einfaches deutsches Wort reicht, benutze dieses.
        - Schreibe kurze Sätze, die auch in einem Gespräch natürlich klingen.
        
        Bevorzuge:
        - direkte Eigenschaften (Material, Verhalten, Naturgesetze, Stärke, Schwächen)
        - einfache und intuitive Erklärungen
        - Zusammenhänge, die andere Menschen nachvollziehen können

        Vermeide:
        - abstrakte Wortspiele
        - reine Bedeutungen oder Verwendungszwecke
        - zusätzliche Personen, Werkzeuge oder erfundene Situationen
        - hinweise auf besiegen in deiner Erklärung. Es ist klar, dass es darum geht.

        Beispiele:
        - Feuer besiegt Eis, weil Hitze Eis schmilzt.
        - Schere besiegt Papier, weil sie es schneiden kann.
        - Katze besiegt Brief, weil sie Papier zerreißen kann.
        - Schmetterling besiegt keine Katze, weil die Katze deutlich stärker und schneller ist.

        Entscheide zuerst intern, ob "{attacker}" gewinnt.
        Danach gib eine kurze Begründung aus, die genau zu dieser Entscheidung passt.

        Antworte ausschließlich mit gültigem JSON:

        {{
          "beats": true,
          "message": "Kurze Erklärung auf Deutsch."
        }}

        Die Werte müssen zusammenpassen:
        - beats=true: Die Nachricht erklärt, warum "{attacker}" gewinnt.
        - beats=false: Die Nachricht erklärt, warum "{attacker}" verliert.
        """

        payload = {
            "model": self.model,
            "stream": False,
            "temperature": 0.5,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            "response_format": {
                "type": "json_object"
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                json=payload,
                timeout=self.timeout_seconds,
            )
        except requests.RequestException as exc:
            print(f"DEBUG: OpenAI WBR request failed: {exc}")
            return False, "Fehler bei der Verbindung zur AI."

        body = self._read_json_response(response)
        if not body:
            return False, "Fehler bei der Verarbeitung der AI-Antwort."

        content = self._extract_assistant_content(body)
        if not content:
            return False, "AI hat keine gültige Antwort geliefert."

        try:
            import json
            data = json.loads(content)
            return bool(data.get("beats", False)), str(data.get("message", "Keine Begründung geliefert."))
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            print(f"DEBUG: Failed to parse OpenAI WBR response content: {exc}")
            return False, "Fehler beim Parsen der AI-Antwort."

    def _read_json_response(self, response: requests.Response) -> Any:
        if response.status_code >= 400:
            print(f"DEBUG: OpenAI WBR failed with status {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")
        else:
            print(f"DEBUG: OpenAI WBR successful with status {response.status_code}")
            print(f"DEBUG: Response body: {response.text}")

        if response.status_code >= 400:
            return None
        try:
            return response.json()
        except ValueError as exc:
            print(f"DEBUG: OpenAI WBR returned non-JSON response: {response.text}")
            return None

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
                    return message.get("content")
        return None
