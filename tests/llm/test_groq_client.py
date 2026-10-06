"""Tests for the Groq adapter without external API calls."""

import json
from unittest.mock import patch

from src.llm import GroqChatClient


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({
            "choices": [{"message": {"content": '{"ok": true}'}}]
        }).encode()


def test_groq_uses_groq_openai_compatible_endpoint():
    client = GroqChatClient("gsk-test-key", "openai/gpt-oss-20b")
    with patch("src.llm.openai_client.urlopen", return_value=FakeResponse()) as call:
        result = client.complete_json(system_prompt="system", user_prompt="return JSON")

    request = call.call_args.args[0]
    payload = json.loads(request.data)
    assert result == '{"ok": true}'
    assert request.full_url == "https://api.groq.com/openai/v1/chat/completions"
    assert request.get_header("Authorization") == "Bearer gsk-test-key"
    assert payload["model"] == "openai/gpt-oss-20b"
    assert payload["response_format"] == {"type": "json_object"}
