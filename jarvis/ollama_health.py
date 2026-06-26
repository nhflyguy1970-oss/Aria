import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.request

_MLLAMA_SUPPORT: bool | None = None


def ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def _hosts_to_try() -> list[str]:
    hosts = []
    env = os.getenv("OLLAMA_HOST", "").rstrip("/")
    if env:
        hosts.append(env)
    for h in ("http://127.0.0.1:11434", "http://localhost:11434"):
        if h not in hosts:
            hosts.append(h)
    return hosts


def _list_via_cli() -> list[str]:
    ollama = shutil.which("ollama")
    if not ollama:
        return []
    try:
        result = subprocess.run(
            [ollama, "list"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return []
        models = []
        for line in result.stdout.strip().splitlines()[1:]:
            name = line.split()[0] if line.strip() else ""
            if name and name != "NAME":
                models.append(name)
        return models
    except Exception:
        return []


def _list_via_http(host: str) -> tuple[list[str], str | None]:
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=5) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            return models, None
    except Exception as e:
        return [], str(e)


def check_ollama() -> dict:
    """Check if Ollama is reachable and which models are installed."""
    result = {
        "running": False,
        "host": ollama_host(),
        "models": [],
        "error": None,
        "source": None,
    }

    for host in _hosts_to_try():
        models, err = _list_via_http(host)
        if models:
            result["running"] = True
            result["host"] = host
            result["models"] = models
            result["source"] = "http"
            return result
        result["error"] = err

    cli_models = _list_via_cli()
    if cli_models:
        result["running"] = True
        result["models"] = cli_models
        result["source"] = "cli"
        result["error"] = None
        return result

    return result


def models_missing(required: list[str], installed: list[str]) -> list[str]:
    missing = []
    installed_lower = {m.lower() for m in installed}
    for req in required:
        base = req.split(":")[0].lower()
        if not any(i.lower().startswith(base) for i in installed_lower):
            missing.append(req)
    return missing


def ollama_version() -> tuple[int, int, int] | None:
    """Return (major, minor, patch) from Ollama API or CLI, or None if unknown."""
    for host in _hosts_to_try():
        try:
            with urllib.request.urlopen(f"{host}/api/version", timeout=5) as resp:
                data = json.loads(resp.read().decode())
                ver = str(data.get("version", "")).strip()
                parts = ver.split(".")
                if len(parts) >= 2:
                    return int(parts[0]), int(parts[1]), int(parts[2] if len(parts) > 2 else 0)
        except Exception:
            continue
    ollama = shutil.which("ollama")
    if ollama:
        try:
            result = subprocess.run(
                [ollama, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            text = (result.stdout or result.stderr or "").strip()
            if m := re.search(r"(\d+)\.(\d+)\.(\d+)", text):
                return int(m.group(1)), int(m.group(2)), int(m.group(3))
        except Exception:
            pass
    return None


def supports_mllama(*, refresh: bool = False) -> bool:
    """True if Ollama can load llama3.2-vision (mllama). Broken on 0.30.x — use 0.24.x."""
    global _MLLAMA_SUPPORT
    if _MLLAMA_SUPPORT is not None and not refresh:
        return _MLLAMA_SUPPORT

    ver = ollama_version()
    if ver:
        major, minor, _patch = ver
        # Ollama 0.30.x release notes: llama3.2-vision (mllama) not yet supported.
        if major == 0 and minor >= 30:
            _MLLAMA_SUPPORT = False
            return False
        if major > 0 or (major == 0 and minor >= 24 and minor < 30):
            _MLLAMA_SUPPORT = True
            return True

    _MLLAMA_SUPPORT = _probe_mllama_support()
    return _MLLAMA_SUPPORT


def _probe_mllama_support() -> bool:
    """One-shot API probe when version string looks pre-0.4 (e.g. 0.30.7)."""
    err = ""
    try:
        host = ollama_host()
        body = json.dumps({
            "model": "llama3.2-vision:11b",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": False,
            "options": {"num_predict": 1},
        }).encode()
        req = urllib.request.Request(
            f"{host}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        err = str(data.get("error", "")).lower()
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode())
            err = str(payload.get("error", exc.reason or "")).lower()
        except Exception:
            err = str(exc).lower()
    except Exception as exc:
        err = str(exc).lower()

    if not err:
        return True
    return "mllama" not in err and "unknown model architecture" not in err


def requires_mllama(model: str) -> bool:
    base = model.split(":")[0].lower().replace("_", ".")
    return base.startswith("llama3.2-vision") or base == "llama3.2-vision"
