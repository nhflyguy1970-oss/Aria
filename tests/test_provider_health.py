"""Provider Health — classification, recovery, watchdog, ownership."""

from __future__ import annotations

from pathlib import Path

from jarvis.provider_health.classify import classify_failure, operator_copy
from jarvis.provider_health.engine import diagnostics, product_status
from jarvis.provider_health.prefs import DEFAULTS, load_preferences, save_preferences
from jarvis.provider_health.probe import list_providers, ping_provider
from jarvis.provider_health.recovery import recover
from jarvis.provider_health.terminology import BOUNDARIES, FAILURE_CLASSES, TERMINOLOGY
from jarvis.provider_health.watchdog import begin_request, complete_request, note_token, stats


def test_terminology_boundaries():
    assert TERMINOLOGY["product"] == "Provider Health"
    assert "stream_watchdog" in BOUNDARIES["owns"]
    assert "inference_generation" in BOUNDARIES["does_not_own"]
    assert "chat_history" in BOUNDARIES["does_not_own"]
    assert "stream_stalled" in FAILURE_CLASSES


def test_classify_first_token_vs_idle():
    first = classify_failure(
        code="FIRST_PROGRESS_TIMEOUT",
        message="did not receive a model response",
        provider_alive=True,
        got_progress=False,
    )
    assert first["class"] == "first_token_timeout"
    idle = classify_failure(
        code="STREAM_IDLE_TIMEOUT",
        message="stopped receiving tokens",
        provider_alive=True,
        got_progress=True,
    )
    assert idle["class"] == "stream_stalled"
    down = classify_failure(
        code="STREAM_IDLE_TIMEOUT",
        message="stopped receiving tokens",
        provider_alive=False,
        got_progress=True,
    )
    assert down["class"] == "provider_disconnected"
    assert any(a["id"] == "restart_provider" for a in first["recommended_actions"])
    assert "Provider:" in operator_copy(first, provider="ollama", model="test")


def test_watchdog_timing():
    begin_request("t1", provider="ollama", model="m", prompt_chars=12)
    note_token("t1")
    note_token("t1")
    row = complete_request("t1", reason="done")
    assert row["token_count"] == 2
    assert row["first_token_at"]
    assert stats()["requests"] >= 1


def test_prefs_roundtrip(tmp_path, monkeypatch):
    from jarvis.provider_health import prefs as pref_mod

    monkeypatch.setattr(pref_mod, "PREFS_FILE", tmp_path / "prefs.json")
    save_preferences({"idle_timeout_ms": 60000, "auto_restart": False})
    loaded = load_preferences()
    assert loaded["idle_timeout_ms"] == 60000
    assert loaded["auto_restart"] is False
    assert "recovery_attempts" in DEFAULTS


def test_recover_classifies_and_logs(tmp_path, monkeypatch):
    from jarvis.provider_health import history as hist_mod
    from jarvis.provider_health import recovery as rec_mod

    monkeypatch.setattr(hist_mod, "HISTORY_FILE", tmp_path / "history.jsonl")
    monkeypatch.setattr(rec_mod, "ping_provider", lambda *a, **k: {
        "ok": True,
        "alive": True,
        "provider": "ollama",
        "state": "healthy",
        "probe": {"ok": True, "model": "x"},
    })
    monkeypatch.setattr(rec_mod, "_reconnect", lambda *a, **k: {"ok": True})
    out = recover(code="STREAM_IDLE_TIMEOUT", message="stopped receiving tokens", got_progress=True, auto=False)
    assert out["ok"]
    assert out["classified"]["class"] == "stream_stalled"
    assert out["usable"] is True


def test_product_status_and_diagnostics():
    st = product_status()
    assert st["ok"]
    assert st["product"] == "Provider Health"
    assert "health_score" in st
    d = diagnostics()
    assert d["ok"]
    assert "provider" in d


def test_list_providers_includes_ollama():
    providers = list_providers()
    ids = {p["id"] for p in providers}
    assert "ollama" in ids
    assert "openai" in ids


def test_client_timeout_classification_fixed():
    send = Path("jarvis/gui/static/chat_send.js").read_text(encoding="utf-8")
    assert 'idleCode = gotProgress ? "STREAM_IDLE_TIMEOUT" : "FIRST_PROGRESS_TIMEOUT"' in send
    assert 'event.type === "heartbeat"' in send
    assert "/api/provider/recover" in send


def test_server_emits_heartbeat():
    server = Path("jarvis/gui/server.py").read_text(encoding="utf-8")
    assert '"type": "heartbeat"' in server or "'type': 'heartbeat'" in server
    assert "note_heartbeat" in server
    assert "FIRST_PROGRESS_TIMEOUT" in server
    assert "first_progress_ms" in server


def test_docs_exist():
    doc = Path("docs/PROVIDER_HEALTH.md")
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "STREAM_IDLE_TIMEOUT" in text
    assert "heartbeat" in text


def test_api_module_registers():
    from jarvis.provider_health.api import register_product_routes

    assert callable(register_product_routes)


def test_dashboard_and_mission_bridges():
    from jarvis.provider_health.dashboard_bridge import dashboard_summary
    from jarvis.provider_health.mission_bridge import mission_panel

    dash = dashboard_summary()
    assert dash["ok"]
    assert "health_score" in dash
    mc = mission_panel()
    assert mc["product"] == "Provider Health"
    assert "failure_rate" in mc


def test_search_facet_registered():
    from jarvis.search_product.terminology import FACETS

    assert "provider_health" in FACETS
    from jarvis.search_product.intent import classify_intent

    hit = classify_intent("ollama stuck timeout provider health")
    assert "provider_health" in hit["intents"]
