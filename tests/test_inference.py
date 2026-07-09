"""Tests for intelligent inference routing."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from jarvis.inference.gateway import chat_with_usage, gateway_status, litellm_available
from jarvis.inference.policy import InferenceRoute, select_route


class TestInferencePolicy(unittest.TestCase):
    @patch.dict("os.environ", {"JARVIS_INFERENCE_GATEWAY": "ollama"}, clear=False)
    def test_select_route_ollama_mode(self):
        route = select_route("qwen2.5:7b", role="general")
        self.assertEqual(route.backend, "ollama")
        self.assertEqual(route.model, "qwen2.5:7b")
        self.assertTrue(route.local)

    @patch.dict("os.environ", {"JARVIS_CLOUD_INFERENCE": "1"}, clear=False)
    @patch("jarvis.inference.gateway.litellm_available", return_value=True)
    def test_cloud_model_uses_litellm(self, _litellm):
        route = select_route("gpt-4o-mini", role="general")
        self.assertEqual(route.backend, "litellm")
        self.assertTrue(route.cloud)

    @patch("jarvis.inference.policy._low_vram", return_value=True)
    @patch.dict("os.environ", {"JARVIS_INFERENCE_GATEWAY": "ollama"}, clear=False)
    def test_low_vram_adjusts_model(self, _low):
        with patch("jarvis.model_store.model_for", return_value="qwen2.5:7b"):
            route = select_route("qwen2.5:14b", role="general")
        self.assertEqual(route.backend, "ollama")
        self.assertEqual(route.model, "qwen2.5:7b")


class TestInferenceGateway(unittest.TestCase):
    @patch("jarvis.inference.gateway._ollama_chat_with_usage", return_value=("hello", {"backend": "ollama"}))
    def test_chat_with_usage_defaults_to_ollama(self, mock_ollama):
        text, usage = chat_with_usage("qwen2.5:7b", [{"role": "user", "content": "hi"}])
        self.assertEqual(text, "hello")
        mock_ollama.assert_called_once()

    @patch("jarvis.inference.gateway._litellm_chat_with_usage", return_value=("cloud", {"backend": "litellm"}))
    def test_chat_with_usage_honors_route(self, mock_litellm):
        route = InferenceRoute(backend="litellm", model="gpt-4o-mini", reason="test", cloud=True)
        text, usage = chat_with_usage("gpt-4o-mini", [{"role": "user", "content": "hi"}], route=route)
        self.assertEqual(text, "cloud")
        mock_litellm.assert_called_once()

    def test_gateway_status_shape(self):
        status = gateway_status()
        self.assertIn("gateway_mode", status)
        self.assertIn("litellm_available", status)

    @patch("urllib.request.urlopen")
    def test_litellm_available_true(self, mock_urlopen):
        mock_urlopen.return_value.__enter__.return_value.status = 200
        self.assertTrue(litellm_available())


if __name__ == "__main__":
    unittest.main()
