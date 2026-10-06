"""Gemini GenerateContent REST adapter using only the Python standard library."""

import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class GeminiRequestError(RuntimeError):
    """Sanitized Gemini API or transport error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class GeminiGenerateContentClient:
    """Minimal Gemini REST client implementing the LLM protocols used by agents."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: int = 120,
        max_attempts: int = 3,
        thinking_budget: int | None = None,
        thinking_level: str | None = None,
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
        # Tentativas em caso de HTTP 503 (alta demanda); espera 1s, 2s, 4s, 8s...
        self.max_attempts = max(1, max_attempts)
        # Só modelos 2.5 aceitam thinkingBudget; 0 desliga o raciocínio e acelera a resposta.
        self.thinking_budget = thinking_budget
        # Modelos 3.x usam thinkingLevel ("low" = raciocínio curto). Se a API recusar, é removido.
        self.thinking_level = thinking_level
        self.thinking_unsupported = False
        self.retries = 0  # quantas vezes foi preciso repetir por HTTP 503

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
        return self._complete(system_prompt, user_prompt, json_mode=True)

    def complete_text(self, *, system_prompt: str, user_prompt: str) -> str:
        return self._complete(system_prompt, user_prompt, json_mode=False)

    def _thinking_config(self) -> dict | None:
        if self.thinking_unsupported:
            return None
        if self.thinking_budget is not None and "2.5" in self.model:
            return {"thinkingBudget": self.thinking_budget}
        if self.thinking_level and "gemini-3" in self.model:
            return {"thinkingLevel": self.thinking_level}
        return None

    def _post(self, payload: dict) -> bytes:
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "x-goog-api-key": self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        for attempt in range(self.max_attempts):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    return response.read()
            except HTTPError as exc:
                detail = _error_detail(exc)
                if exc.code == 503 and attempt < self.max_attempts - 1:
                    self.retries += 1
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
                raise GeminiRequestError(message, exc.code) from exc
            except (URLError, TimeoutError, OSError) as exc:
                raise GeminiRequestError("Could not connect to the Gemini API") from exc
        raise GeminiRequestError("Gemini request failed")  # pragma: no cover

    def _complete(self, system_prompt: str, user_prompt: str, *, json_mode: bool) -> str:
        generation_config = {}
        if json_mode:
            generation_config["responseMimeType"] = "application/json"
        thinking = self._thinking_config()
        if thinking:
            generation_config["thinkingConfig"] = thinking
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": generation_config,
        }
        try:
            response_body = self._post(payload)
        except GeminiRequestError as exc:
            if thinking and exc.status_code == 400 and "think" in str(exc).lower():
                # O modelo não aceita esse ajuste: repete sem ele e lembra para as próximas chamadas.
                self.thinking_unsupported = True
                generation_config.pop("thinkingConfig", None)
                response_body = self._post(payload)
            else:
                raise

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
