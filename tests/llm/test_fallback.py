"""Tests for the Gemini -> Groq fallback without external API calls."""

from unittest.mock import Mock

from src.llm import FallbackChatClient, GeminiRequestError


def test_fallback_uses_groq_when_primary_provider_fails():
    primary = Mock()
    primary.complete_json.side_effect = GeminiRequestError("Gemini unavailable")
    fallback = Mock()
    fallback.complete_json.return_value = '{"ok": true}'

    client = FallbackChatClient(primary, fallback)

    assert client.complete_json(system_prompt="s", user_prompt="u") == '{"ok": true}'
    assert client.used_fallback is True
    fallback.complete_json.assert_called_once_with(system_prompt="s", user_prompt="u")


def test_fallback_keeps_primary_result_when_available():
    primary = Mock()
    primary.complete_json.return_value = '{"primary": true}'
    fallback = Mock()

    client = FallbackChatClient(primary, fallback)

    assert client.complete_json(system_prompt="s", user_prompt="u") == '{"primary": true}'
    assert client.used_fallback is False
    fallback.complete_json.assert_not_called()
