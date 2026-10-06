"""Groq adapter using the OpenAI-compatible Chat Completions API."""

from .openai_client import OpenAIChatClient


class GroqChatClient(OpenAIChatClient):
    """Chat Completions client for Groq-hosted language models."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str = "https://api.groq.com/openai/v1",
        timeout_seconds: int = 120,
        max_tokens: int = 2500,
    ) -> None:
        super().__init__(
            api_key,
            model,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            max_tokens=max_tokens,
        )


__all__ = ["GroqChatClient"]
