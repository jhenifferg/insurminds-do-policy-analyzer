"""Tests for the native Gemini REST adapter without external API calls."""

import json
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import patch

import pytest

from src.llm import GeminiGenerateContentClient, GeminiRequestError


class FakeGeminiResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({
            "candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}]
        }).encode()


def test_json_request_uses_native_gemini_generate_content_api():
    client = GeminiGenerateContentClient("test-key", "gemini-3.7-flash")
    with patch("src.llm.gemini_client.urlopen", return_value=FakeGeminiResponse()) as call:
        result = client.complete_json(system_prompt="system", user_prompt="return JSON")

    request = call.call_args.args[0]
    payload = json.loads(request.data)
    assert result == '{"ok": true}'
    assert request.full_url.endswith("/models/gemini-3.7-flash:generateContent")
    assert request.get_header("X-goog-api-key") == "test-key"
    assert payload["systemInstruction"]["parts"][0]["text"] == "system"
    assert payload["generationConfig"]["responseMimeType"] == "application/json"


def test_native_gemini_503_retries_and_surfaces_google_diagnostic():
    def unavailable():
        return HTTPError(
            "https://test",
            503,
            "busy",
            {},
            BytesIO(b'{"error":{"message":"The model is overloaded."}}'),
        )

    client = GeminiGenerateContentClient("test-key", "gemini-3.7-flash")
    with (
        patch("src.llm.gemini_client.urlopen", side_effect=[unavailable() for _ in range(3)]) as call,
        patch("src.llm.gemini_client.time.sleep"),
        pytest.raises(GeminiRequestError, match="The model is overloaded"),
    ):
        client.complete_json(system_prompt="system", user_prompt="return JSON")
    assert call.call_count == 3
