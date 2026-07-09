"""Tests for platform migration cutover."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from jarvis.platform_cutover import (
    apply_cutover_state_on_startup,
    backfill_memory,
    current_mode,
    enable_platform_authoritative,
    rollback_to_legacy,
    status,
    verify_readiness,
)


def _ready_env(legacy: Path, platform: Path) -> dict[str, str]:
    return {
        "JARVIS_PLATFORM_ATTACHED": "1",
        "JARVIS_PLATFORM_MEMORY_ATTACHED": "1",
        "JARVIS_PLATFORM_SEMANTIC_MEMORY_ATTACHED": "1",
        "JARVIS_PLATFORM_KNOWLEDGE_RETRIEVAL_ATTACHED": "1",
        "JARVIS_LEGACY_DATA_DIR": str(legacy),
        "JARVIS_PLATFORM_DATA_DIR": str(platform),
    }


def _ready_state() -> dict:
    return {
        "backfill_completed_at": "2026-07-09T12:00:00Z",
        "backfill_stats": {"mirrored": 2, "errors": 0, "total": 2},
    }


def _mock_metrics():
    memory_metrics = MagicMock()
    memory_metrics.to_dict.return_value = {"verification_failures": 0}
    semantic_metrics = MagicMock()
    semantic_metrics.to_dict.return_value = {
        "verification_failures": 0,
        "read_verification_failures": 0,
        "embedding_verification_failures": 0,
    }
    knowledge_metrics = MagicMock()
    knowledge_metrics.to_dict.return_value = {
        "retrieval_verification_failures": 0,
        "shadow_retrieval_comparisons": 10,
        "retrieval_agreements": 10,
    }
    app = MagicMock(required_memory_namespaces=["aria", "profile"])
    return memory_metrics, semantic_metrics, knowledge_metrics, app


class TestPlatformCutover(unittest.TestCase):
    def test_default_mode_dual_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            cutover_file = Path(tmp) / "cutover.json"
            with patch("jarvis.platform_cutover._CUTOVER_FILE", cutover_file):
                self.assertEqual(current_mode(), "dual_write")

    def test_apply_cutover_state_on_startup_hydrates_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            cutover_file = Path(tmp) / "cutover.json"
            cutover_file.write_text(
                json.dumps({"mode": "platform_authoritative"}),
                encoding="utf-8",
            )
            with patch("jarvis.platform_cutover._CUTOVER_FILE", cutover_file):
                with patch.dict("os.environ", {}, clear=True):
                    result = apply_cutover_state_on_startup()
                    self.assertTrue(result.get("applied"))
                    self.assertEqual(
                        __import__("os").environ.get("JARVIS_PLATFORM_DATA_AUTHORITATIVE"),
                        "1",
                    )

    def test_rollback_restores_legacy(self):
        with tempfile.TemporaryDirectory() as tmp:
            cutover_file = Path(tmp) / "cutover.json"
            legacy = Path(tmp) / "legacy"
            legacy.mkdir()
            with patch("jarvis.platform_cutover._CUTOVER_FILE", cutover_file):
                with patch.dict("os.environ", {"JARVIS_LEGACY_DATA_DIR": str(legacy)}, clear=False):
                    result = rollback_to_legacy()
                    self.assertTrue(result.get("ok"))
                    self.assertEqual(current_mode(), "dual_write")

    def test_status_shape(self):
        with patch("jarvis.platform_cutover.verify_readiness", return_value={"ready": False}):
            snap = status()
            self.assertIn("mode", snap)
            self.assertIn("verification", snap)

    def test_verify_readiness_blocks_without_attachment(self):
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "legacy"
            platform = Path(tmp) / "platform"
            legacy.mkdir()
            platform.mkdir()
            cutover_file = Path(tmp) / "cutover.json"
            with patch("jarvis.platform_cutover._CUTOVER_FILE", cutover_file):
                with patch.dict("os.environ", _ready_env(legacy, platform), clear=False):
                    with patch.dict("os.environ", {"JARVIS_PLATFORM_ATTACHED": "0"}, clear=False):
                        result = verify_readiness(persist=False)
            self.assertFalse(result.get("ready"))
            self.assertTrue(any("not attached" in b for b in result.get("blockers") or []))

    def test_verify_readiness_ready_when_layers_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "legacy"
            platform = Path(tmp) / "platform"
            legacy.mkdir()
            platform.mkdir()
            cutover_file = Path(tmp) / "cutover.json"
            cutover_file.write_text(json.dumps(_ready_state()), encoding="utf-8")
            memory_metrics, semantic_metrics, knowledge_metrics, app = _mock_metrics()
            with patch("jarvis.platform_cutover._CUTOVER_FILE", cutover_file):
                with patch.dict("os.environ", _ready_env(legacy, platform), clear=False):
                    with patch(
                        "aiplatform.applications.memory.metrics.metrics_view",
                        return_value=memory_metrics,
                    ):
                        with patch(
                            "aiplatform.applications.semantic.metrics.metrics_view",
                            return_value=semantic_metrics,
                        ):
                            with patch(
                                "aiplatform.applications.knowledge_retrieval.metrics.metrics_view",
                                return_value=knowledge_metrics,
                            ):
                                with patch(
                                    "aiplatform.applications.manager.manager.get",
                                    return_value=app,
                                ):
                                    with patch(
                                        "aiplatform.applications.memory.validator.namespace_status",
                                        return_value=(["aria"], ["aria"], []),
                                    ):
                                        with patch(
                                            "jarvis.platform_cutover.verify_data_parity",
                                            return_value={
                                                "ok": True,
                                                "legacy_count": 2,
                                                "mirrored": 2,
                                            },
                                        ):
                                            result = verify_readiness(persist=False)
            self.assertTrue(result.get("ready"), result.get("blockers"))

    def test_enable_blocked_without_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            cutover_file = Path(tmp) / "cutover.json"
            with patch("jarvis.platform_cutover._CUTOVER_FILE", cutover_file):
                with patch(
                    "jarvis.platform_cutover.verify_readiness",
                    return_value={"ready": False, "blockers": ["test blocker"]},
                ):
                    result = enable_platform_authoritative()
            self.assertFalse(result.get("ok"))
            self.assertEqual(result.get("error"), "cutover blocked")

    def test_enable_success_when_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            legacy = Path(tmp) / "legacy"
            platform = Path(tmp) / "platform"
            legacy.mkdir()
            platform.mkdir()
            cutover_file = Path(tmp) / "cutover.json"
            cutover_file.write_text(json.dumps(_ready_state()), encoding="utf-8")
            with patch("jarvis.platform_cutover._CUTOVER_FILE", cutover_file):
                with patch.dict("os.environ", _ready_env(legacy, platform), clear=False):
                    with patch(
                        "jarvis.platform_cutover.verify_readiness",
                        return_value={"ready": True, "blockers": []},
                    ):
                        result = enable_platform_authoritative()
                        self.assertTrue(result.get("ok"))
                        self.assertEqual(current_mode(), "platform_authoritative")

    def test_backfill_memory_dry_run(self):
        mock_mem = MagicMock()
        mock_mem.list_entries.return_value = [{"id": "1"}, {"id": "2"}]
        mock_assistant = MagicMock(memory=mock_mem)
        with patch.dict("os.environ", {"JARVIS_PLATFORM_MEMORY_ATTACHED": "1"}, clear=False):
            with patch("jarvis.assistant_instance.get_assistant", return_value=mock_assistant):
                result = backfill_memory(dry_run=True)
        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("entries"), 2)


if __name__ == "__main__":
    unittest.main()
