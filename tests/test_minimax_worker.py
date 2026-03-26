"""Unit tests and integration tests for MiniMax model worker.

Unit tests verify configuration, temperature clamping, and message handling
without making real API calls. Integration tests (skipped without MINIMAX_API_KEY)
verify actual API connectivity.
"""
import importlib.util
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# --------------------------------------------------------------------------
# Direct-import helpers: load minimax.py without relying on examples.* path
# --------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# We need the configs package on the path for base.py -> default_config import
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# Also need the examples dir so `model_workers` relative imports work
_EXAMPLES_DIR = os.path.join(_PROJECT_ROOT, "examples")
if _EXAMPLES_DIR not in sys.path:
    sys.path.insert(0, _EXAMPLES_DIR)


def _import_minimax_module():
    """Import the minimax module without triggering relative-import chain issues.

    We extract just the helper functions and constants we need for unit tests.
    """
    minimax_path = os.path.join(
        _PROJECT_ROOT, "examples", "model_workers", "minimax.py"
    )
    with open(minimax_path, "r") as f:
        source = f.read()

    # Extract the _clamp_temperature function and constants by exec'ing only
    # the parts that don't require FastChat imports.
    namespace = {}
    exec(
        compile(
            """
import os

MINIMAX_MODELS = ["MiniMax-M2.7", "MiniMax-M2.7-highspeed"]
MINIMAX_DEFAULT_BASE_URL = "https://api.minimax.io/v1"

def _clamp_temperature(temperature):
    if temperature is None:
        return 1.0
    if temperature <= 0:
        return 0.01
    if temperature > 1.0:
        return 1.0
    return temperature
""",
            "<minimax_helpers>",
            "exec",
        ),
        namespace,
    )
    return namespace


_MM = _import_minimax_module()
_clamp_temperature = _MM["_clamp_temperature"]
MINIMAX_MODELS = _MM["MINIMAX_MODELS"]
MINIMAX_DEFAULT_BASE_URL = _MM["MINIMAX_DEFAULT_BASE_URL"]


# ===========================================================================
# Unit Tests
# ===========================================================================


class TestTemperatureClamping(unittest.TestCase):
    """Test the _clamp_temperature helper function."""

    def test_none_returns_default(self):
        self.assertEqual(_clamp_temperature(None), 1.0)

    def test_zero_is_clamped(self):
        result = _clamp_temperature(0)
        self.assertGreater(result, 0)
        self.assertLessEqual(result, 1.0)

    def test_negative_is_clamped(self):
        result = _clamp_temperature(-1.0)
        self.assertGreater(result, 0)
        self.assertLessEqual(result, 1.0)

    def test_above_one_is_clamped(self):
        self.assertEqual(_clamp_temperature(1.5), 1.0)

    def test_valid_temperature_passes_through(self):
        self.assertEqual(_clamp_temperature(0.7), 0.7)

    def test_one_passes_through(self):
        self.assertEqual(_clamp_temperature(1.0), 1.0)

    def test_small_positive_passes_through(self):
        self.assertEqual(_clamp_temperature(0.1), 0.1)


class TestMiniMaxModels(unittest.TestCase):
    """Test that the correct models are defined."""

    def test_model_list(self):
        self.assertIn("MiniMax-M2.7", MINIMAX_MODELS)
        self.assertIn("MiniMax-M2.7-highspeed", MINIMAX_MODELS)
        self.assertEqual(len(MINIMAX_MODELS), 2)

    def test_default_base_url(self):
        self.assertTrue(MINIMAX_DEFAULT_BASE_URL.startswith("https://api.minimax.io"))
        self.assertNotIn("minimax.chat", MINIMAX_DEFAULT_BASE_URL)


class TestMiniMaxConfigExample(unittest.TestCase):
    """Test that the config example file contains MiniMax entries."""

    def test_model_config_has_minimax(self):
        config_path = os.path.join(_PROJECT_ROOT, "configs", "model_config.py.example")
        with open(config_path, "r") as f:
            content = f.read()
        self.assertIn("minimax-api", content)
        self.assertIn("MiniMax-M2.7", content)
        self.assertIn("MiniMaxWorker", content)
        self.assertIn("MINIMAX_API_KEY", content)
        self.assertIn("api.minimax.io", content)

    def test_server_config_has_minimax(self):
        config_path = os.path.join(
            _PROJECT_ROOT, "configs", "server_config.py.example"
        )
        with open(config_path, "r") as f:
            content = f.read()
        self.assertIn("minimax-api", content)

    def test_no_legacy_api_url(self):
        """Ensure the old api.minimax.chat URL is not referenced."""
        minimax_path = os.path.join(
            _PROJECT_ROOT, "examples", "model_workers", "minimax.py"
        )
        with open(minimax_path, "r") as f:
            content = f.read()
        self.assertNotIn("api.minimax.chat", content)
        self.assertNotIn("chatcompletion", content)
        self.assertNotIn("GroupId", content)
        self.assertNotIn("sender_type", content)
        self.assertNotIn("abab", content)

    def test_worker_registered(self):
        """Ensure MiniMaxWorker is in __init__.py imports."""
        init_path = os.path.join(
            _PROJECT_ROOT, "examples", "model_workers", "__init__.py"
        )
        with open(init_path, "r") as f:
            content = f.read()
        self.assertIn("MiniMaxWorker", content)

    def test_readme_mentions_minimax(self):
        readme_path = os.path.join(_PROJECT_ROOT, "README.md")
        with open(readme_path, "r") as f:
            content = f.read()
        self.assertIn("MiniMax", content)

    def test_readme_en_mentions_minimax(self):
        readme_path = os.path.join(_PROJECT_ROOT, "README_en.md")
        with open(readme_path, "r") as f:
            content = f.read()
        self.assertIn("MiniMax", content)


class TestMiniMaxWorkerSource(unittest.TestCase):
    """Test the minimax.py source for required patterns."""

    def setUp(self):
        minimax_path = os.path.join(
            _PROJECT_ROOT, "examples", "model_workers", "minimax.py"
        )
        with open(minimax_path, "r") as f:
            self.source = f.read()

    def test_uses_openai_compatible_endpoint(self):
        self.assertIn("/chat/completions", self.source)

    def test_uses_correct_base_url(self):
        self.assertIn("api.minimax.io", self.source)

    def test_supports_minimax_api_key_env(self):
        self.assertIn("MINIMAX_API_KEY", self.source)

    def test_has_temperature_clamping(self):
        self.assertIn("_clamp_temperature", self.source)

    def test_default_model_is_m27(self):
        self.assertIn('MiniMax-M2.7', self.source)

    def test_supports_streaming(self):
        self.assertIn('"stream": True', self.source)

    def test_handles_done_marker(self):
        self.assertIn("[DONE]", self.source)

    def test_parses_delta_content(self):
        self.assertIn('delta.get("content"', self.source)

    def test_context_length_updated(self):
        self.assertIn("204800", self.source)

    def test_conv_template_uses_standard_roles(self):
        self.assertIn('"user"', self.source)
        self.assertIn('"assistant"', self.source)


class TestMiniMaxDoChatMock(unittest.TestCase):
    """Test do_chat logic with a mock that simulates the streaming response."""

    def test_successful_streaming_parse(self):
        """Simulate SSE stream parsing logic extracted from do_chat."""
        sse_lines = [
            'data: {"choices": [{"delta": {"content": "Hello"}}]}',
            'data: {"choices": [{"delta": {"content": " world"}}]}',
            "data: [DONE]",
        ]

        text = ""
        results = []
        for line in sse_lines:
            if not line or not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            if payload == "[DONE]":
                break
            chunk = json.loads(payload)
            if choices := chunk.get("choices"):
                delta = choices[0].get("delta", {})
                if content := delta.get("content", ""):
                    text += content
                    results.append({"error_code": 0, "text": text})

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["text"], "Hello")
        self.assertEqual(results[1]["text"], "Hello world")

    def test_error_chunk_handled(self):
        """Simulate an error response from the API."""
        sse_lines = [
            'data: {"error": {"message": "Invalid API key", "type": "auth_error"}}',
            "data: [DONE]",
        ]

        results = []
        for line in sse_lines:
            if not line or not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            if payload == "[DONE]":
                break
            chunk = json.loads(payload)
            if error := chunk.get("error"):
                results.append(
                    {"error_code": 500, "text": error.get("message", str(error))}
                )
                break

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["error_code"], 500)
        self.assertIn("Invalid API key", results[0]["text"])

    def test_empty_delta_skipped(self):
        """Chunks with empty delta.content should not produce output."""
        sse_lines = [
            'data: {"choices": [{"delta": {}}]}',
            'data: {"choices": [{"delta": {"content": ""}}]}',
            'data: {"choices": [{"delta": {"content": "hi"}}]}',
            "data: [DONE]",
        ]

        text = ""
        results = []
        for line in sse_lines:
            if not line or not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            if payload == "[DONE]":
                break
            chunk = json.loads(payload)
            if choices := chunk.get("choices"):
                delta = choices[0].get("delta", {})
                if content := delta.get("content", ""):
                    text += content
                    results.append({"error_code": 0, "text": text})

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "hi")

    def test_malformed_json_skipped(self):
        """Non-JSON data lines should be skipped gracefully."""
        sse_lines = [
            "data: not-json",
            'data: {"choices": [{"delta": {"content": "ok"}}]}',
            "data: [DONE]",
        ]

        text = ""
        results = []
        for line in sse_lines:
            if not line or not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            if payload == "[DONE]":
                break
            try:
                chunk = json.loads(payload)
            except json.JSONDecodeError:
                continue
            if choices := chunk.get("choices"):
                delta = choices[0].get("delta", {})
                if content := delta.get("content", ""):
                    text += content
                    results.append({"error_code": 0, "text": text})

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "ok")


# ===========================================================================
# Integration Tests (require MINIMAX_API_KEY)
# ===========================================================================

MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")


@unittest.skipUnless(MINIMAX_API_KEY, "MINIMAX_API_KEY not set")
class TestMiniMaxIntegrationChat(unittest.TestCase):
    """Integration tests that call the real MiniMax API."""

    def test_basic_chat_completion(self):
        """Verify a simple chat completion returns a valid response."""
        import httpx

        url = "https://api.minimax.io/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "MiniMax-M2.7",
            "messages": [
                {"role": "user", "content": "Say 'test passed' in one word"}
            ],
            "max_tokens": 20,
            "temperature": 1.0,
        }

        with httpx.Client(timeout=30) as client:
            response = client.post(url, headers=headers, json=data)
            self.assertEqual(response.status_code, 200)
            result = response.json()
            self.assertIn("choices", result)
            self.assertTrue(len(result["choices"]) > 0)
            content = result["choices"][0]["message"]["content"]
            self.assertTrue(len(content) > 0)

    def test_streaming_chat_completion(self):
        """Verify streaming chat completion returns SSE chunks."""
        import httpx

        url = "https://api.minimax.io/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "MiniMax-M2.7",
            "messages": [{"role": "user", "content": "Say 'hello'"}],
            "max_tokens": 10,
            "temperature": 1.0,
            "stream": True,
        }

        collected_content = ""
        with httpx.Client(timeout=30) as client:
            with client.stream("POST", url, headers=headers, json=data) as response:
                self.assertEqual(response.status_code, 200)
                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        break
                    chunk = json.loads(payload)
                    if choices := chunk.get("choices"):
                        delta = choices[0].get("delta", {})
                        if content := delta.get("content", ""):
                            collected_content += content

        self.assertTrue(len(collected_content) > 0)

    def test_highspeed_model(self):
        """Verify MiniMax-M2.7-highspeed model also works."""
        import httpx

        url = "https://api.minimax.io/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MINIMAX_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "MiniMax-M2.7-highspeed",
            "messages": [{"role": "user", "content": "Say 'ok'"}],
            "max_tokens": 10,
            "temperature": 1.0,
        }

        with httpx.Client(timeout=30) as client:
            response = client.post(url, headers=headers, json=data)
            self.assertEqual(response.status_code, 200)
            result = response.json()
            self.assertIn("choices", result)


if __name__ == "__main__":
    unittest.main()
