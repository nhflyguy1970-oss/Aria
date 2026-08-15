"""Subprocess environment boundary — prevent secret leakage to child processes.

M1 establishes the allowlist/denylist architecture. Does not migrate jarvis.env.
Tools must use `build_subprocess_env()` instead of `os.environ.copy()`.
"""

from __future__ import annotations

import os
from typing import Iterable

# Keys that must never be inherited by arbitrary tool/subprocess children.
SECRET_ENV_DENYLIST: frozenset[str] = frozenset(
    {
        "JARVIS_API_KEY",
        "JARVIS_AUTOMATION_SECRET",
        "JARVIS_HA_TOKEN",
        "HOME_ASSISTANT_TOKEN",
        "JARVIS_HA_PASSWORD",
        "JARVIS_UNCENSORED_PASSWORD",
        "JARVIS_JOURNAL_AT_REST_PASSWORD",
        "JARVIS_GRAPH_PASSWORD",
        "JARVIS_MESHY_API_KEY",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENROUTER_API_KEY",
        "GOOGLE_API_KEY",
        "HF_TOKEN",
        "HUGGING_FACE_HUB_TOKEN",
        "POSTGRES_PASSWORD",
        "PGVECTOR_DATABASE_URL",
        "DATABASE_URL",
        "NEO4J_PASSWORD",
        "MEMGRAPH_PASSWORD",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "GITHUB_TOKEN",
        "GH_TOKEN",
    }
)

# Safe baseline for tool runners (extend carefully; never add secrets here).
BASE_ENV_ALLOWLIST: frozenset[str] = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TERM",
        "TMPDIR",
        "TMP",
        "TEMP",
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONUNBUFFERED",
        "JARVIS_SANDBOX",
        "JARVIS_DATA_DIR",
        "DISPLAY",
        "WAYLAND_DISPLAY",
        "XDG_RUNTIME_DIR",
        "XDG_DATA_HOME",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
        "SSH_AUTH_SOCK",
        "COLORTERM",
        "EDITOR",
        "VISUAL",
        "PWD",
        "OLDPWD",
    }
)


def is_secret_env_key(key: str) -> bool:
    k = (key or "").strip()
    if not k:
        return False
    if k in SECRET_ENV_DENYLIST:
        return True
    upper = k.upper()
    if upper.endswith(("_TOKEN", "_SECRET", "_PASSWORD", "_API_KEY", "_APIKEY")):
        return True
    if "PASSWORD" in upper or "SECRET" in upper:
        # Catch PGVECTOR_DATABASE_URL-style already listed; also generic
        if upper.endswith("_URL") and ("POSTGRES" in upper or "DATABASE" in upper or "MYSQL" in upper):
            return True
    return False


def build_subprocess_env(
    *,
    extra: dict[str, str] | None = None,
    allow: Iterable[str] | None = None,
    inherit_non_secret: bool = False,
) -> dict[str, str]:
    """Build a child process environment without Aria secrets.

    Default: allowlist-only (safe). Set inherit_non_secret=True only for
    host-like shells that need broader env, still applying denylist.
    """
    allow_set = set(BASE_ENV_ALLOWLIST)
    if allow:
        allow_set.update(allow)

    env: dict[str, str] = {}
    if inherit_non_secret:
        for k, v in os.environ.items():
            if is_secret_env_key(k):
                continue
            if v is None:
                continue
            env[k] = v
    else:
        for k in allow_set:
            if is_secret_env_key(k):
                continue
            v = os.environ.get(k)
            if v:
                env[k] = v

    if extra:
        for k, v in extra.items():
            if is_secret_env_key(k):
                continue
            env[k] = v

    if "PATH" not in env:
        env["PATH"] = "/usr/bin:/bin"
    return env


def copy_process_env(*, extra: dict[str, str] | None = None) -> dict[str, str]:
    """Copy the process environment with secret keys removed.

    Use this instead of os.environ.copy() when spawning host-like children
    (ComfyUI, Ollama, ffmpeg, Electron, Aria restart). Children that need
    a secret must receive only that secret via `extra` after an explicit
    decision — never the whole environment.
    """
    env = {k: v for k, v in os.environ.items() if not is_secret_env_key(k)}
    if extra:
        for k, v in extra.items():
            if is_secret_env_key(k):
                continue
            if v is None or v == "":
                env.pop(k, None)
            else:
                env[k] = v
    return env


def scrub_mapping(data: dict) -> dict:
    """Return a copy with secret-shaped keys redacted (for logs/diagnostics)."""
    out = {}
    for k, v in data.items():
        if is_secret_env_key(str(k)):
            out[k] = "[REDACTED]"
        else:
            out[k] = v
    return out
