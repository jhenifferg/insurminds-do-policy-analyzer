"""OpenAI-compatible Chat Completions adapter using only the standard library."""

import json
import time
from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OpenAIRequestError(RuntimeError):
    """Sanitized provider/transport error that does not echo policy contents."""


class OpenAIChatClient:
    """Adapter for OpenAI or Gemini's OpenAI-compatible endpoint."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: int = 120,
        max_tokens: int | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("API key is required")
        if not model.strip():
            raise ValueError("Model name is required")
        self.api_key = api_key.strip()
        self.model = model.strip()
        self.endpoint = base_url.rstrip("/") + "/chat/completions"
        self.timeout_seconds = timeout_seconds
        self.max_tokens = max_tokens

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
        result = self._complete(system_prompt, user_prompt, json_mode=True)
        if not isinstance(result, str):
            raise OpenAIRequestError("The model returned no JSON text")
        return result

    def complete_text(self, *, system_prompt: str, user_prompt: str) -> str:
        result = self._complete(system_prompt, user_prompt, json_mode=False)
        if not isinstance(result, str):
            raise OpenAIRequestError("The model returned no text")
        return result

    def _complete(self, system_prompt: str, user_prompt: str, *, json_mode: bool) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "InsurMinds/1.0",
            },
            method="POST",
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    response_body = response.read()
                break
            except HTTPError as exc:
                error_detail = _http_error_detail(exc)
                if exc.code == 503 and attempt < 2:
                    time.sleep(1 * (2**attempt))
                    continue
                if exc.code == 503:
                    message = "Model provider is temporarily unavailable (HTTP 503)."
                    if error_detail:
                        message += f" Provider says: {error_detail}"
                    else:
                        message += " Try another available model or try again later."
                else:
                    message = f"Model provider API returned HTTP {exc.code}"
                    if error_detail:
                        message += f": {error_detail}"
                raise OpenAIRequestError(message) from exc
            except (URLError, TimeoutError, OSError) as exc:
                raise OpenAIRequestError("Could not connect to the model provider API") from exc
        try:
            data = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OpenAIRequestError("Model provider API returned an invalid response") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise OpenAIRequestError("Model provider response has an unexpected shape") from exc
        if not isinstance(content, str) or not content.strip():
            raise OpenAIRequestError("Model provider API returned an empty response")
        return content


def _http_error_detail(error: HTTPError) -> str:
    """Extract only the provider's short error message, never echo request data."""
    try:
        body = json.loads(error.read().decode("utf-8"))
        detail = body.get("error", {}).get("message", "")
    except (AttributeError, UnicodeDecodeError, JSONDecodeError):
        return ""
    if not isinstance(detail, str):
        return ""
    return " ".join(detail.split())[:400]


__all__ = ["OpenAIChatClient", "OpenAIRequestError"]
