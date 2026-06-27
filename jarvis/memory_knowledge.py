"""Environment and machine facts synced into long-term memory."""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from typing import Any

from jarvis.config import DATA_DIR

logger = logging.getLogger("jarvis.memory_knowledge")

ENV_NAMESPACE = "environment"
TAG_ENV = "environment-fact"
TAG_ENV_KEY = "env-key:"
TAG_USER_PREFERENCE = "user-preference"
TAG_MACHINE = "machine-fact"

ENVIRONMENT_PREFERENCE_DEFS: tuple[dict[str, Any], ...] = (
    {
        "key": "pref-linux-commands",
        "label": "Linux / shell commands",
        "hint": "How ARIA should format shell examples and CLI help.",
        "default": (
            "User prefers Linux shell commands (bash, coreutils) over PowerShell "
            "or Windows-style syntax."
        ),
        "type": "preference",
        "tags": ["workflow"],
    },
    {
        "key": "pref-ollama-local",
        "label": "Local Ollama",
        "hint": "Assume on-machine models via Ollama when suggesting inference.",
        "default": "User uses Ollama for local LLM inference and prefers on-machine models.",
        "type": "preference",
        "tags": ["ollama", "workflow"],
    },
    {
        "key": "pref-privacy-local",
        "label": "Privacy / local-first",
        "hint": "Bias toward private, on-device workflows over cloud APIs.",
        "default": (
            "User dislikes cloud dependence and prefers local, private, "
            "on-device AI when possible."
        ),
        "type": "preference",
        "tags": ["privacy"],
    },
)


def _env_key(key: str) -> str:
    return f"{TAG_ENV_KEY}{key}"


def preference_defs() -> list[dict[str, Any]]:
    return [dict(d) for d in ENVIRONMENT_PREFERENCE_DEFS]


def load_environment_preferences() -> dict[str, str]:
    """User-editable stack preferences (chat_settings); seeds defaults once."""
    from jarvis.config import _load_chat_settings, _write_chat_settings

    data = _load_chat_settings()
    raw = data.get("environment_preferences")
    prefs: dict[str, str] = dict(raw) if isinstance(raw, dict) else {}
    changed = False
    for spec in ENVIRONMENT_PREFERENCE_DEFS:
        key = spec["key"]
        if key not in prefs:
            prefs[key] = spec["default"]
            changed = True
    if changed:
        data["environment_preferences"] = prefs
        _write_chat_settings(data)
    return prefs


def save_environment_preferences(prefs: dict[str, str]) -> dict[str, str]:
    from jarvis.config import _load_chat_settings, _write_chat_settings

    allowed = {spec["key"] for spec in ENVIRONMENT_PREFERENCE_DEFS}
    cleaned: dict[str, str] = {}
    for key, value in prefs.items():
        if key not in allowed:
            continue
        cleaned[key] = (value or "").strip()
    data = _load_chat_settings()
    merged = load_environment_preferences()
    merged.update(cleaned)
    data["environment_preferences"] = merged
    _write_chat_settings(data)
    return merged


def environment_preferences_payload() -> dict[str, Any]:
    """Catalog + current values for the Memory tab API."""
    prefs = load_environment_preferences()
    items = []
    for spec in ENVIRONMENT_PREFERENCE_DEFS:
        key = spec["key"]
        items.append({
            "key": key,
            "label": spec["label"],
            "hint": spec.get("hint", ""),
            "type": spec.get("type", "preference"),
            "tags": list(spec.get("tags") or []),
            "default": spec["default"],
            "content": prefs.get(key, spec["default"]),
        })
    return {"ok": True, "preferences": items}


def _docker_container_names() -> list[str]:
    if not shutil.which("docker"):
        return []
    try:
        r = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode != 0:
            return []
        return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    except (OSError, subprocess.TimeoutExpired):
        return []


def _system_ram_gb() -> float | None:
    try:
        with open("/proc/meminfo", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return round(kb / (1024 * 1024), 1)
    except (OSError, ValueError):
        pass
    try:
        import psutil  # type: ignore

        return round(psutil.virtual_memory().total / (1024**3), 1)
    except Exception:
        return None


def _cpu_model() -> str | None:
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or None


def collect_machine_facts() -> list[dict[str, Any]]:
    """Auto-detected machine/stack facts (overwritten on sync)."""
    from jarvis.environment import snapshot
    from jarvis.ollama_health import check_ollama

    snap = snapshot(include_resources=True)
    ollama = check_ollama()
    facts: list[dict[str, Any]] = []

    def add(key: str, content: str, entry_type: str = "fact", extra_tags: list[str] | None = None):
        facts.append({
            "key": key,
            "content": content.strip(),
            "type": entry_type,
            "tags": [TAG_ENV, TAG_MACHINE, _env_key(key), *(extra_tags or [])],
        })

    uname = platform.uname()
    add(
        "platform",
        f"User's machine runs {uname.system} {uname.release} ({uname.machine}), hostname {uname.node}.",
    )

    cpu = _cpu_model()
    ram = _system_ram_gb()
    if cpu and ram:
        add("hardware", f"User's laptop/PC has CPU {cpu} and {ram} GB RAM.")
    elif cpu:
        add("hardware", f"User's machine CPU: {cpu}.")
    elif ram:
        add("hardware", f"User's machine has {ram} GB RAM.")

    gpu = snap.get("gpu") or {}
    if gpu.get("name"):
        vram = gpu.get("vram_mb") or gpu.get("free_vram_mb")
        suffix = f" ({vram} MB VRAM)" if vram else ""
        add("gpu", f"User's GPU is {gpu['name']}{suffix}.")

    disk = snap.get("disk_free_gb")
    if disk:
        add("disk", f"Jarvis data disk has {disk} GB free under {DATA_DIR}.")

    if ollama.get("running"):
        models = ollama.get("models") or []
        if models:
            top = ", ".join(models[:12])
            more = f" (+{len(models) - 12} more)" if len(models) > 12 else ""
            add("ollama-models", f"User runs Ollama locally with models: {top}{more}.", extra_tags=["ollama"])
        else:
            add("ollama", "User runs Ollama locally for LLM inference.", entry_type="preference", extra_tags=["ollama"])
    else:
        add("ollama-offline", "Ollama is not currently running on this machine.", extra_tags=["ollama"])

    containers = _docker_container_names()
    if containers:
        add(
            "docker-containers",
            f"Docker containers running on this machine: {', '.join(containers[:20])}"
            + (f" (+{len(containers) - 20} more)" if len(containers) > 20 else "")
            + ".",
            extra_tags=["docker"],
        )
    elif shutil.which("docker"):
        add("docker", "User has Docker installed on this machine.", extra_tags=["docker"])

    profile = snap.get("profile")
    if profile:
        add("jarvis-profile", f"Jarvis profile active: {profile}.", extra_tags=["jarvis"])

    return facts


def collect_preference_facts() -> list[dict[str, Any]]:
    """User-edited preferences from chat_settings."""
    prefs = load_environment_preferences()
    facts: list[dict[str, Any]] = []
    for spec in ENVIRONMENT_PREFERENCE_DEFS:
        key = spec["key"]
        content = (prefs.get(key) or "").strip()
        if not content:
            continue
        facts.append({
            "key": key,
            "content": content,
            "type": spec.get("type", "preference"),
            "tags": [TAG_ENV, TAG_USER_PREFERENCE, _env_key(key), *(spec.get("tags") or [])],
        })
    return facts


def collect_environment_facts() -> list[dict[str, Any]]:
    return collect_machine_facts() + collect_preference_facts()


def _find_env_entry(memory_store, key: str) -> dict | None:
    if hasattr(memory_store, "find_by_env_key"):
        return memory_store.find_by_env_key(key)
    tag = _env_key(key)
    for e in memory_store.list_entries(namespace=ENV_NAMESPACE):
        if tag in (e.get("tags") or []):
            return e
    return None


def _upsert_env_fact(memory_store, fact: dict) -> str:
    """Return 'added', 'updated', or 'unchanged'."""
    key = fact["key"]
    existing = _find_env_entry(memory_store, key)
    content = fact["content"]
    if existing:
        if (existing.get("content") or "").strip() == content:
            return "unchanged"
        memory_store.update(existing["id"], content=content)
        return "updated"
    memory_store.add(
        fact["type"],
        content,
        tags=fact["tags"],
        namespace=ENV_NAMESPACE,
    )
    return "added"


def _should_sync() -> bool:
    interval_h = int(os.getenv("JARVIS_ENV_MEMORY_SYNC_HOURS", "24"))
    if interval_h <= 0:
        return False
    from jarvis.config import _load_chat_settings

    data = _load_chat_settings()
    meta = data.get("environment_memory") or {}
    last = meta.get("synced_at")
    if not last:
        return True
    try:
        prev = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
        age_h = (datetime.now(timezone.utc) - prev).total_seconds() / 3600
        return age_h >= interval_h
    except (TypeError, ValueError):
        return True


def _mark_synced(count: int) -> None:
    from jarvis.config import _load_chat_settings, _write_chat_settings

    data = _load_chat_settings()
    data["environment_memory"] = {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "fact_count": count,
    }
    _write_chat_settings(data)


def sync_environment_memory(memory_store, *, force: bool = False, machine_only: bool = False) -> dict:
    """Upsert machine facts (auto) and user preferences (from settings)."""
    if not force and not _should_sync():
        return {"ok": True, "skipped": True, "reason": "recent"}

    added = updated = 0
    for fact in collect_machine_facts():
        result = _upsert_env_fact(memory_store, fact)
        if result == "added":
            added += 1
        elif result == "updated":
            updated += 1

    if not machine_only:
        pref_keys = {spec["key"] for spec in ENVIRONMENT_PREFERENCE_DEFS}
        for fact in collect_preference_facts():
            result = _upsert_env_fact(memory_store, fact)
            if result == "added":
                added += 1
            elif result == "updated":
                updated += 1
        # Drop cleared preferences from memory
        for e in memory_store.list_entries(namespace=ENV_NAMESPACE):
            tags = e.get("tags") or []
            if TAG_USER_PREFERENCE not in tags:
                continue
            env_key = next((t[8:] for t in tags if t.startswith(TAG_ENV_KEY)), "")
            if env_key in pref_keys:
                prefs = load_environment_preferences()
                if not (prefs.get(env_key) or "").strip():
                    memory_store.delete_id(e["id"])

    total = len(collect_machine_facts()) + len(collect_preference_facts())
    _mark_synced(total)
    logger.info("Environment memory sync: added=%d updated=%d", added, updated)
    return {"ok": True, "added": added, "updated": updated, "total": total}


def save_environment_preferences_to_memory(memory_store, prefs: dict[str, str]) -> dict:
    """Persist preferences to settings and sync only preference rows to memory."""
    merged = save_environment_preferences(prefs)
    added = updated = removed = 0
    active_keys = set()
    for spec in ENVIRONMENT_PREFERENCE_DEFS:
        key = spec["key"]
        content = (merged.get(key) or "").strip()
        if not content:
            existing = _find_env_entry(memory_store, key)
            if existing and memory_store.delete_id(existing["id"]):
                removed += 1
            continue
        active_keys.add(key)
        fact = {
            "key": key,
            "content": content,
            "type": spec.get("type", "preference"),
            "tags": [TAG_ENV, TAG_USER_PREFERENCE, _env_key(key), *(spec.get("tags") or [])],
        }
        result = _upsert_env_fact(memory_store, fact)
        if result == "added":
            added += 1
        elif result == "updated":
            updated += 1
    return {"ok": True, "added": added, "updated": updated, "removed": removed, "preferences": merged}
