"""Models product + restored model_store coverage."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from jarvis.model_store import (
    CANONICAL_ROLES,
    LEGACY_ROLE_ALIASES,
    canonical_role,
    get_all_settings,
    update_models,
    apply_preset,
)
from jarvis.models_product.switch import apply_model_change, describe_switch_contract, SCOPE_OPS_TEMPORARY
from jarvis.models_product.catalog import build_model_card, build_catalog
from jarvis.models_product.vram_advisor import advise_vram
from jarvis.models_product.recommender import recommend_stacks
from jarvis.models_product.providers import validate_provider, list_providers
from jarvis.models_product.policy import check_permission, save_policy, load_policy, DEFAULT_POLICY
from jarvis.models_product.home import models_home_snapshot, export_config
from jarvis.models_product.task_coach import suggest_for_prompt
from jarvis.models_product.packs import save_pack, list_packs, apply_pack
from jarvis.models_product.activity_bridge import emit_model_event
from jarvis.mission_control_ops.inference_actions import run_inference_action


def test_canonical_roles_and_aliases():
    assert "conversation" in CANONICAL_ROLES
    assert canonical_role("general") == "conversation"
    assert canonical_role("coder") == "coding"
    assert set(LEGACY_ROLE_ALIASES) == {"general", "coder", "embed"}


def test_get_all_settings_shape(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.model_store.SETTINGS_FILE", tmp_path / "model_settings.json")
    monkeypatch.setattr("jarvis.model_store._installed", lambda: ["qwen2.5:7b", "nomic-embed-text"])
    settings = get_all_settings()
    assert "active" in settings
    assert "roles" in settings
    assert "conversation" in settings["active"] or "general" in settings["active"]


def test_update_models_persists(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.model_store.SETTINGS_FILE", tmp_path / "model_settings.json")
    monkeypatch.setattr("jarvis.model_store._installed", lambda: ["qwen2.5:7b", "deepseek-coder:latest"])
    out = update_models("standard", {"conversation": "qwen2.5:7b", "coding": "deepseek-coder:latest"})
    assert out["standard"]["conversation"] == "qwen2.5:7b"
    assert out["standard"]["general"] == "qwen2.5:7b"  # legacy sync


def test_apply_preset(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.model_store.SETTINGS_FILE", tmp_path / "model_settings.json")
    monkeypatch.setattr("jarvis.model_store._installed", lambda: ["qwen2.5:7b", "qwen3:1.7b", "nomic-embed-text", "moondream:latest", "comfyui"])
    out = apply_preset("fast", "standard")
    assert out["customized"] is True


def test_switch_role_default(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.model_store.SETTINGS_FILE", tmp_path / "model_settings.json")
    monkeypatch.setattr("jarvis.model_store._installed", lambda: ["qwen2.5:7b"])
    monkeypatch.setattr("jarvis.models_product.policy._POLICY_FILE", tmp_path / "policy.json")
    out = apply_model_change({"scope": "role_default", "role": "conversation", "model": "qwen2.5:7b"})
    assert out["ok"] is True
    assert out["persistent"] is True


def test_switch_rejects_ops_temporary():
    out = apply_model_change({"scope": SCOPE_OPS_TEMPORARY, "model": "x"})
    assert out["ok"] is False


def test_switch_contract():
    c = describe_switch_contract()
    assert c["authoritative_api"] == "POST /api/models/switch"
    assert "warm_model" in c["mission_control"]


def test_mc_switch_uses_models_api(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.model_store.SETTINGS_FILE", tmp_path / "model_settings.json")
    monkeypatch.setattr("jarvis.model_store._installed", lambda: ["qwen2.5:7b"])
    monkeypatch.setattr("jarvis.models_product.policy._POLICY_FILE", tmp_path / "policy.json")
    out = run_inference_action("switch_model", confirmed=True, model="qwen2.5:7b")
    assert out["ok"] is True
    assert out.get("models_api", {}).get("ok") is True
    assert "preferred_model.txt" not in str(out)


def test_model_card_and_catalog(monkeypatch):
    monkeypatch.setattr("jarvis.models_product.catalog._free_vram_gb", lambda: 8.0)
    monkeypatch.setattr("jarvis.models_product.catalog._loaded_names", lambda: set())
    card = build_model_card("qwen2.5:7b", installed=["qwen2.5:7b"], free_vram_gb=8.0)
    assert card["friendly_name"]
    assert card["installed"] is True
    assert "estimated_vram_gb" in card
    monkeypatch.setattr(
        "jarvis.model_store.get_all_settings",
        lambda: {"installed": ["qwen2.5:7b"], "active": {"conversation": "qwen2.5:7b"}},
    )
    cat = build_catalog(q="qwen", capability="chat")
    assert cat["ok"] is True
    assert cat["count"] >= 1


def test_recommender(monkeypatch):
    monkeypatch.setattr("jarvis.model_store._installed", lambda: ["qwen2.5:7b", "nomic-embed-text"])
    monkeypatch.setattr(
        "jarvis.model_store.get_all_settings",
        lambda: {"installed": ["qwen2.5:7b"], "hardware": {}, "missing_active": []},
    )
    stacks = recommend_stacks()
    assert stacks["auto_apply"] is False
    assert any(s["id"] == "balanced" for s in stacks["stacks"])


def test_home_snapshot(monkeypatch):
    monkeypatch.setattr(
        "jarvis.models_product.home.get_all_settings",
        lambda: {
            "active": {
                "conversation": "qwen2.5:7b",
                "coding": "qwen2.5:7b",
                "vision": "moondream:latest",
                "image": "comfyui",
                "embedding": "nomic-embed-text",
            },
            "installed": ["qwen2.5:7b"],
            "ollama_running": True,
            "missing_active": [],
            "hardware": {},
            "choices": ["qwen2.5:7b"],
        },
    )
    monkeypatch.setattr("jarvis.models_product.home.get_missing_models", lambda: [])
    monkeypatch.setattr(
        "jarvis.models_product.providers.wizard_status",
        lambda: {"ok": True, "providers": [], "results": {}},
    )
    monkeypatch.setattr(
        "jarvis.models_product.providers.validate_provider",
        lambda *_a, **_k: {"ok": True, "provider": "ollama"},
    )
    monkeypatch.setattr(
        "jarvis.models_product.recommender.recommend_stacks",
        lambda: {"ok": True, "auto_apply": False, "stacks": []},
    )
    monkeypatch.setattr(
        "jarvis.models_product.catalog.build_catalog",
        lambda **_k: {"ok": True, "cards": [], "count": 0, "loaded_models": []},
    )
    monkeypatch.setattr(
        "jarvis.models_product.catalog.build_model_card",
        lambda *a, **k: {"tag": "qwen2.5:7b", "friendly_name": "Qwen", "capabilities": []},
    )
    monkeypatch.setattr("jarvis.models_product.vram_advisor.advise_vram", lambda *a, **k: {"ok": True})
    monkeypatch.setattr("jarvis.models_product.pull_manager.get_pull_state", lambda: {"active": None, "history": []})
    monkeypatch.setattr("jarvis.models_product.packs.list_packs", lambda: {"ok": True, "packs": []})
    monkeypatch.setattr(
        "jarvis.resource_router.ollama_loaded_models",
        lambda: [],
    )
    snap = models_home_snapshot()
    assert snap["product"] == "models"
    assert "roles" in snap
    assert "catalog" in snap
    assert snap["boundaries"]["owns"]


def test_export_config(monkeypatch):
    monkeypatch.setattr(
        "jarvis.models_product.home.get_all_settings",
        lambda: {"mode": "standard", "standard": {}, "uncensored": {}},
    )
    out = export_config()
    assert out["version"] == 1


def test_task_coach():
    out = suggest_for_prompt("Please refactor this Python function")
    assert out["auto_switch"] is False
    assert any(s["kind"] == "coding" for s in out["suggestions"])


def test_packs(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.models_product.packs._PACKS", tmp_path / "packs.json")
    monkeypatch.setattr("jarvis.model_store.SETTINGS_FILE", tmp_path / "model_settings.json")
    monkeypatch.setattr("jarvis.model_store._installed", lambda: ["qwen2.5:7b"])
    monkeypatch.setattr("jarvis.models_product.policy._POLICY_FILE", tmp_path / "policy.json")
    save_pack({"id": "dev", "name": "Dev", "roles": {"conversation": "qwen2.5:7b"}})
    assert list_packs()["packs"]
    out = apply_pack("dev")
    assert out["ok"] is True


def test_activity_emit():
    evt = emit_model_event("model_switched", message="test")
    assert evt["category"] == "models"
    assert evt["fix"]


def test_inference_requires_confirm():
    out = run_inference_action("warm_model", confirmed=False, model="x")
    assert out["error"] == "confirmation_required"
