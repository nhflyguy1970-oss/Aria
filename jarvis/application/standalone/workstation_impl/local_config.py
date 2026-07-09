"""Detect Jeff's existing services and write workstation defaults to jarvis.env."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from jarvis.env_loader import PROJECT_ROOT

ENV_FILE = PROJECT_ROOT / "data" / "jarvis.env"


def _docker_names() -> set[str]:
    if not Path("/usr/bin/docker").exists():
        return set()
    try:
        proc = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            return set()
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    except Exception:
        return set()


def _http_ok(url: str) -> bool:
    import urllib.request

    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def detect_local_services() -> dict[str, Any]:
    """Infer container names and URLs from the live machine."""
    names = _docker_names()
    detected: dict[str, Any] = {}

    ai_root = Path(os.getenv("AI_ROOT", str(PROJECT_ROOT.parent)))
    if (ai_root / "compose").is_dir():
        detected["AI_ROOT"] = str(ai_root)

    openwebui_container = "open-webui" if "open-webui" in names else "ai-open-webui"
    if openwebui_container in names or _http_ok("http://127.0.0.1:3000/health"):
        detected["JARVIS_OPENWEBUI_URL"] = "http://127.0.0.1:3000"
        detected["JARVIS_OPENWEBUI_CONTAINER"] = openwebui_container

    if "ai-postgres" in names:
        detected["POSTGRES_HOST"] = "127.0.0.1"
        detected["POSTGRES_PORT"] = "5432"
        detected["POSTGRES_USER"] = "postgres"
        detected["POSTGRES_PASSWORD"] = "postgres"
        detected["POSTGRES_DB"] = "aiplatform"
        detected["PGVECTOR_DATABASE_URL"] = (
            "postgresql://postgres:postgres@127.0.0.1:5432/aiplatform"
        )
        detected["EMBEDDING_VECTOR_STORE"] = "pgvector"

    if "ai-redis" in names:
        detected["REDIS_HOST"] = "127.0.0.1"
        detected["REDIS_PORT"] = "6379"

    qdrant_container = "ai-qdrant" if "ai-qdrant" in names else ""
    if qdrant_container:
        detected["QDRANT_URL"] = "http://127.0.0.1:6333"
        detected["JARVIS_QDRANT_CONTAINER"] = qdrant_container
    elif "vectordb" in names:
        detected["JARVIS_VECTOR_BACKEND"] = "pgvector"
        detected["EMBEDDING_VECTOR_STORE"] = "pgvector"

    if "ai-litellm" in names or _http_ok("http://127.0.0.1:4000/health/readiness"):
        detected["JARVIS_LITELLM_URL"] = "http://127.0.0.1:4000"

    if "ai-n8n" in names:
        detected["JARVIS_N8N_URL"] = "http://127.0.0.1:5678"
        detected["JARVIS_N8N_CONTAINER"] = "ai-n8n"

    if _http_ok("http://127.0.0.1:9090/-/healthy"):
        detected["JARVIS_PROMETHEUS_URL"] = "http://127.0.0.1:9090"

    if _http_ok("http://127.0.0.1:3001/api/health"):
        detected["JARVIS_GRAFANA_URL"] = "http://127.0.0.1:3001"

    autostart = ["postgres", "redis", "open_webui"]
    if detected.get("JARVIS_LITELLM_URL"):
        autostart.append("litellm")
    if "ai-qdrant" in names:
        autostart.extend(["qdrant", "n8n", "prometheus", "grafana"])
    detected["JARVIS_AUTOSTART_SERVICES"] = ",".join(dict.fromkeys(autostart))
    detected["JARVIS_DOCKER_PROFILES"] = "data,inference,monitoring,automation"
    detected["JARVIS_AUTO_RECOVER_OPTIONAL"] = "1"
    detected["JARVIS_FIRST_RUN_MODELS"] = "1"
    return detected


def _upsert_env_line(lines: list[str], key: str, value: str) -> list[str]:
    pattern = re.compile(rf"^(# export )?{re.escape(key)}=")
    out: list[str] = []
    replaced = False
    for line in lines:
        if pattern.match(line.strip()):
            out.append(f'export {key}="{value}"')
            replaced = True
        else:
            out.append(line)
    if not replaced:
        if out and out[-1].strip():
            out.append("")
        out.append(f'export {key}="{value}"')
    return out


def apply_local_defaults(*, dry_run: bool = False) -> dict[str, Any]:
    """Write detected defaults into data/jarvis.env."""
    detected = detect_local_services()
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    if ENV_FILE.is_file():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    else:
        example = PROJECT_ROOT / "jarvis.env.example"
        lines = example.read_text(encoding="utf-8").splitlines() if example.is_file() else []

    written: dict[str, str] = {}
    for key, value in detected.items():
        if not str(value).strip():
            continue
        if re.search(rf"^export {re.escape(key)}=", "\n".join(lines), re.M):
            continue
        lines = _upsert_env_line(lines, key, str(value))
        written[key] = str(value)

    if written and not dry_run:
        ENV_FILE.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        for key, value in written.items():
            os.environ[key] = value

    return {"ok": True, "written": written, "detected": detected}
