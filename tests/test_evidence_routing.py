"""Evidence cues must reach Memory Authority (memory_about_user), not memory_search."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jarvis.nlu.mapping import resolve_memory_route
from jarvis.session import SessionContext

EVIDENCE_PROMPTS = [
    "Show me the evidence.",
    "Show the evidence.",
    "Show my memory evidence.",
    "What is the evidence?",
    "What evidence do you have?",
    "Show the history behind this memory.",
    "Show why this memory changed.",
]


@pytest.mark.parametrize("prompt", EVIDENCE_PROMPTS)
def test_resolve_memory_route_evidence_to_about_user(prompt: str) -> None:
    resolved = resolve_memory_route(prompt)
    assert resolved is not None, prompt
    assert resolved["action"] == "memory_about_user", (prompt, resolved)
    assert resolved["params"]["question"] == prompt
    assert "query" not in resolved["params"]


@pytest.mark.parametrize("prompt", EVIDENCE_PROMPTS)
def test_router_evidence_to_memory_about_user(prompt: str) -> None:
    with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
        mock_client.return_value = MagicMock()
        from jarvis.router import route

        intent = route(prompt, SessionContext(), None)
        assert intent.get("action") == "memory_about_user", (prompt, intent)
        assert intent.get("params", {}).get("question") == prompt


def test_evidence_live_path_preserves_acm_speech() -> None:
    """Show me the evidence. → ACM lineage speech unchanged in UI."""
    tmp = tempfile.mkdtemp(prefix="evidence_route_")
    os.environ["ARIA_ACM_SHADOW"] = "0"
    os.environ["ARIA_ACM_PRIMARY"] = "1"
    os.environ["ARIA_ACM_ROLLBACK"] = "0"
    os.environ["ARIA_ACM_LEGACY_READ_FALLBACK"] = "0"
    os.environ["ARIA_ACM_PERSIST_PATH"] = str(Path(tmp) / "ev.db")
    os.environ["ARIA_ACM_AUTO_PERSIST"] = "1"
    os.environ["ARIA_TEACHING_DEBUG"] = "0"

    from aria_core import acm_bridge, memory_manager
    from jarvis.behaviors.memory.engine import MemoryEngine
    from jarvis.router import route

    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()

    from aria_acm.acm.identity.assistant_profile import AssistantIdentityProfile

    eng = acm_bridge.get_engine()
    eng.identity.set_assistant_profile(AssistantIdentityProfile(name="ARIA", role="assistant"))

    class _Ctx:
        session = SessionContext()
        memory = None

        def refresh_system_prompt(self) -> None:
            return None

    for t in ("My favorite color is blue.", "My favorite color is green."):
        MemoryEngine.memory_about_user(_Ctx(), {"question": t}, t)

    prompt = "Show me the evidence."
    with patch("jarvis.runtime_introspection.get_runtime_client") as mock_client:
        mock_client.return_value = MagicMock()
        intent = route(prompt, SessionContext(), None)
    assert intent["action"] == "memory_about_user"
    assert intent["params"]["question"] == prompt

    captured: dict = {}
    real = acm_bridge.primary_cognitive_speak

    def wrap(request, *a, **k):
        out = real(request, *a, **k)
        captured["request"] = request
        captured["speech"] = out.get("speech")
        return out

    with patch.object(acm_bridge, "primary_cognitive_speak", side_effect=wrap):
        out = MemoryEngine.memory_about_user(_Ctx(), intent["params"], prompt)

    assert captured.get("request") == prompt
    speech = (captured.get("speech") or "").strip()
    assert "Evidence" in speech or "evidence" in speech.lower()
    assert "blue" in speech.lower() and "green" in speech.lower()
    assert "retired" in speech.lower() and "active" in speech.lower()
    assert out.get("message") == speech
    assert not (out.get("message") or "").startswith("•")

    # Prior explanation / about-me routes unchanged
    for keep in (
        "Why isn't blue active anymore?",
        "What do you know about me?",
    ):
        r = resolve_memory_route(keep)
        assert r is not None and r["action"] == "memory_about_user"
        assert r["params"]["question"] == keep

    memory_manager.reset_for_tests()
    acm_bridge.reset_for_tests()
