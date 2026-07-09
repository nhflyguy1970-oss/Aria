"""Tests for interfaces and training workspace."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from jarvis.interfaces.openwebui import inference_url, openwebui_url
from jarvis.training.workspace import training_status


class TestInterfaces(unittest.TestCase):
    def test_openwebui_url_default(self):
        self.assertTrue(openwebui_url().startswith("http"))

    @patch.dict("os.environ", {"JARVIS_LITELLM_URL": "http://127.0.0.1:4000"}, clear=False)
    @patch("jarvis.inference.gateway.litellm_available", return_value=False)
    def test_inference_url_falls_back_ollama(self, _litellm):
        url = inference_url()
        self.assertIn("11434", url)


class TestTrainingWorkspace(unittest.TestCase):
    def test_training_status_shape(self):
        status = training_status()
        self.assertIn("packages", status)
        self.assertIn("ready", status)


if __name__ == "__main__":
    unittest.main()
