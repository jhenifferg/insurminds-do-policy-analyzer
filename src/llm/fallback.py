"""Provider fallback for transient or unavailable LLM providers."""

from .gemini_client import GeminiRequestError
from .openai_client import OpenAIRequestError


class FallbackChatClient:
    """Try the primary client and use a configured fallback on API failure."""

    def __init__(self, primary, fallback) -> None:
        self.primary = primary
        self.fallback = fallback
        self.used_fallback = False

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
        try:
            return self.primary.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except (GeminiRequestError, OpenAIRequestError):
            self.used_fallback = True
            return self.fallback.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

    def complete_text(self, *, system_prompt: str, user_prompt: str) -> str:
        try:
            return self.primary.complete_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except (GeminiRequestError, OpenAIRequestError):
            self.used_fallback = True
            return self.fallback.complete_text(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )


__all__ = ["FallbackChatClient"]
