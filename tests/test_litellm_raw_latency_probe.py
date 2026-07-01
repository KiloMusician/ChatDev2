import json
import unittest
from unittest.mock import patch

from tools.litellm_raw_latency_probe import (
    _probe_ollama_generate,
    _probe_openai_compatible,
    _resolve_prompts,
)


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class LiteLLMRawLatencyProbeTests(unittest.TestCase):
    def test_resolve_prompts_uses_preset_when_requested(self) -> None:
        system_prompt, user_prompt = _resolve_prompts(
            preset="pygame-stub",
            system_prompt="ignored-system",
            user_prompt="ignored-user",
        )

        self.assertIn("short Python file named game.py", system_prompt)
        self.assertEqual(user_prompt, "Make the smallest possible pygame stub.")

    @patch("tools.litellm_raw_latency_probe.urllib.request.urlopen")
    def test_probe_openai_compatible_success(self, mock_urlopen) -> None:
        mock_urlopen.return_value = _FakeResponse(
            {"choices": [{"message": {"content": "hello world"}}]}
        )

        result = _probe_openai_compatible(
            base_url="http://127.0.0.1:4000/v1",
            api_key="local",
            model="ecosystem-coder-fast",
            system_prompt="system",
            user_prompt="user",
            max_tokens=100,
            timeout_seconds=1,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["model"], "ecosystem-coder-fast")
        self.assertTrue(result["has_content"])
        self.assertIn("hello world", result["content_preview"])

    @patch("tools.litellm_raw_latency_probe.urllib.request.urlopen")
    def test_probe_ollama_generate_success(self, mock_urlopen) -> None:
        mock_urlopen.return_value = _FakeResponse(
            {"response": "print('hello')", "done": True}
        )

        result = _probe_ollama_generate(
            base_url="http://127.0.0.1:11434",
            model="qwen3:8b",
            system_prompt="system",
            user_prompt="user",
            timeout_seconds=1,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["model"], "qwen3:8b")
        self.assertTrue(result["has_content"])
        self.assertEqual(result["done"], True)
        self.assertIn("print('hello')", result["content_preview"])


if __name__ == "__main__":
    unittest.main()
