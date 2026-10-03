"""Tests for the HTTP adapter without making external API calls."""

import json
from io import BytesIO
from urllib.error import HTTPError

import pytest
from unittest.mock import patch

from src.llm import OpenAIChatClient, OpenAIRequestError


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({
            "choices": [{"message": {"content": '{"ok": true}'}}]
        }).encode()


def test_json_request_uses_json_mode_and_extracts_chat_content():
    client = OpenAIChatClient("secret-for-test", "test-model")
    with patch("src.llm.openai_client.urlopen", return_value=FakeResponse()) as request:
        result = client.complete_json(system_prompt="system", user_prompt="return JSON")

    payload = json.loads(request.call_args.args[0].data)
    assert result == '{"ok": true}'
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["model"] == "test-model"


def test_gemini_compatible_endpoint_uses_gemini_base_url():
    client = OpenAIChatClient(
        "gemini-test-key",
        "gemini-2.5-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    with patch("src.llm.openai_client.urlopen", return_value=FakeResponse()) as request:
        client.complete_json(system_prompt="system", user_prompt="return JSON")

    assert request.call_args.args[0].full_url == (
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    )


def test_temporary_503_is_retried_with_bounded_backoff():
    client = OpenAIChatClient("gemini-test-key", "gemini-test")
    unavailable = HTTPError("https://test", 503, "busy", {}, None)
    with (
        patch("src.llm.openai_client.urlopen", side_effect=[unavailable, FakeResponse()]) as request,
        patch("src.llm.openai_client.time.sleep") as sleep,
    ):
        result = client.complete_json(system_prompt="system", user_prompt="return JSON")

    assert result == '{"ok": true}'
    assert request.call_count == 2
    sleep.assert_called_once_with(1)


def test_final_503_includes_provider_message_without_exposing_payload():
    client = OpenAIChatClient("gemini-test-key", "gemini-test")
    def unavailable():
        return HTTPError(
            "https://test",
            503,
            "busy",
            {},
            BytesIO(b'{"error":{"message":"The model is overloaded."}}'),
        )
    with (
        patch("src.llm.openai_client.urlopen", side_effect=[unavailable() for _ in range(3)]),
        patch("src.llm.openai_client.time.sleep"),
    ):
        with pytest.raises(OpenAIRequestError) as exc_info:
            client.complete_json(system_prompt="system", user_prompt="sensitive policy")
    assert "temporarily unavailable (HTTP 503)" in str(exc_info.value)
    assert "The model is overloaded." in str(exc_info.value)
    assert "sensitive policy" not in str(exc_info.value)
