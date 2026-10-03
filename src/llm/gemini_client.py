"""Gemini GenerateContent REST adapter using only the Python standard library."""

import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class GeminiRequestError(RuntimeError):
    """Sanitized Gemini API or transport error."""


class GeminiGenerateContentClient:
    """Minimal Gemini REST client implementing the LLM protocols used by agents."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: int = 120,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Gemini API key is required")
        if not model.strip():
            raise ValueError("Gemini model name is required")
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.endpoint = (
            f"{base_url.rstrip('/')}/models/{quote(self.model, safe='')}:generateContent"
        )
        self.timeout_seconds = timeout_seconds

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
        return self._complete(system_prompt, user_prompt, json_mode=True)

    def complete_text(self, *, system_prompt: str, user_prompt: str) -> str:
        return self._complete(system_prompt, user_prompt, json_mode=False)

    def _complete(self, system_prompt: str, user_prompt: str, *, json_mode: bool) -> str:
        generation_config = {}
        if json_mode:
            generation_config["responseMimeType"] = "application/json"
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": generation_config,
        }
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        response_body = None
        for attempt in range(3):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    response_body = response.read()
                break
            except HTTPError as exc:
                detail = _error_detail(exc)
                if exc.code == 503 and attempt < 2:
                    time.sleep(1 * (2**attempt))
                    continue
                if exc.code == 503:
                    message = "Gemini is temporarily unavailable (HTTP 503)."
                    if detail:
                        message += f" Google says: {detail}"
                    else:
                        message += " Try another Gemini model or try again later."
                else:
                    message = f"Gemini API returned HTTP {exc.code}"
                    if detail:
                        message += f": {detail}"
                raise GeminiRequestError(message) from exc
            except (URLError, TimeoutError, OSError) as exc:
                raise GeminiRequestError("Could not connect to the Gemini API") from exc

        try:
            data = json.loads(response_body.decode("utf-8"))
        except (AttributeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GeminiRequestError("Gemini API returned an invalid response") from exc
        try:
            parts = data["candidates"][0]["content"]["parts"]
            result = "".join(part["text"] for part in parts if isinstance(part.get("text"), str))
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            reason = data.get("promptFeedback", {}).get("blockReason")
            detail = f"Gemini blocked the prompt ({reason})" if reason else "Gemini response had an unexpected shape"
            raise GeminiRequestError(detail) from exc
        if not result.strip():
            raise GeminiRequestError("Gemini returned an empty response")
        return result


def _error_detail(error: HTTPError) -> str:
    try:
        body = json.loads(error.read().decode("utf-8"))
        detail = body.get("error", {}).get("message", "")
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        return ""
    if not isinstance(detail, str):
        return ""
    return " ".join(detail.split())[:400]


__all__ = ["GeminiGenerateContentClient", "GeminiRequestError"]
