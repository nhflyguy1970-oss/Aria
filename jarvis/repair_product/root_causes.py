"""Root cause library — group recurring failures with known workarounds."""

from __future__ import annotations

from typing import Any

from jarvis.repair_product import store

# Seed library (expanded by learning)
_SEED: dict[str, dict[str, Any]] = {
    "provider_ollama:provider_offline": {
        "title": "Ollama Offline / Timeout",
        "possible_causes": [
            "Provider process stopped",
            "GPU unavailable / VRAM exhausted",
            "Model still loading",
            "Port conflict on 11434",
            "Firewall / bind address",
            "Wrong configuration",
        ],
        "workarounds": [
            "Restart Ollama via Guided Repair",
            "Unload unused models to free VRAM",
            "Confirm OLLAMA_HOST",
        ],
        "related_modules": ["provider_ollama", "docker_services"],
    },
    "search_index:search_unhealthy": {
        "title": "Search Index Corrupt / Unhealthy",
        "possible_causes": [
            "Interrupted shutdown while indexing",
            "Partial write",
            "Disk full during index",
            "Schema mismatch after upgrade",
        ],
        "workarounds": [
            "Rebuild search index (documents preserved)",
            "Verify disk space first",
        ],
        "related_modules": ["search_index", "documents_index", "caches_temp"],
    },
    "scheduler:scheduler_down": {
        "title": "Proactive Scheduler Stopped",
        "possible_causes": [
            "Thread crashed",
            "Process restart left thread dead",
            "Exception in scheduler loop",
        ],
        "workarounds": ["Restart scheduler thread"],
        "related_modules": ["scheduler"],
    },
    "docker_services:docker_issue": {
        "title": "Docker Service Unhealthy",
        "possible_causes": [
            "Container exited",
            "Compose misconfiguration",
            "Host resource pressure",
            "Volume permission error",
        ],
        "workarounds": ["Safe Docker repair via Guided Repair", "Inspect docker compose logs"],
        "related_modules": ["docker_services"],
    },
}


def lookup(module_id: str, code: str = "") -> dict[str, Any] | None:
    key = f"{module_id}:{code or 'unknown'}"
    lib = store.root_cause_library()
    if key in lib:
        return lib[key]
    if key in _SEED:
        return _SEED[key]
    # fuzzy module-level
    for k, v in {**_SEED, **lib}.items():
        if k.startswith(module_id + ":"):
            return v
    return None


def ensure_seeded() -> None:
    lib = store.root_cause_library()
    changed = False
    for k, v in _SEED.items():
        if k not in lib:
            lib[k] = {**v, "from_seed": True}
            changed = True
    if changed:
        store.save_root_cause_library(lib)


def record_outcome(module_id: str, code: str, *, success: bool, plan_steps: str = "", environment: str = "") -> dict[str, Any]:
    ensure_seeded()
    key = f"{module_id}:{code or 'unknown'}"
    lib = store.root_cause_library()
    art = lib.get(key) or dict(_SEED.get(key) or {"title": key, "possible_causes": [], "workarounds": []})
    art.setdefault("previous_successful_repairs", [])
    art.setdefault("common_environments", [])
    art["attempts"] = int(art.get("attempts") or 0) + 1
    if success:
        art["successes"] = int(art.get("successes") or 0) + 1
        if plan_steps and plan_steps not in art["previous_successful_repairs"]:
            art["previous_successful_repairs"] = ([*art["previous_successful_repairs"], plan_steps])[-15:]
    else:
        art["failures"] = int(art.get("failures") or 0) + 1
    if environment and environment not in art["common_environments"]:
        art["common_environments"] = ([*art["common_environments"], environment])[-10:]
    lib[key] = art
    store.save_root_cause_library(lib)
    return art


def list_all() -> list[dict[str, Any]]:
    ensure_seeded()
    lib = store.root_cause_library()
    rows = [{"id": k, **v} for k, v in lib.items()]
    rows.sort(key=lambda r: int(r.get("attempts") or 0), reverse=True)
    return rows
