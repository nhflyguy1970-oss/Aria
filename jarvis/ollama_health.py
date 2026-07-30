import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request

_MLLAMA_SUPPORT: bool | None = None

# Soft inference probe cache — tags alone cannot detect a wedged generate path.
_probe_lock = threading.Lock()
_probe_cache: dict = {
    "at": 0.0,
    "ok": None,  # True | False | None (never run)
    "detail": "",
    "model": "",
    "elapsed_s": None,
}
_PROBE_TTL = float(os.getenv("JARVIS_OLLAMA_HEALTH_PROBE_TTL", "120"))
_PROBE_TIMEOUT = float(os.getenv("JARVIS_OLLAMA_HEALTH_PROBE_TIMEOUT", "5"))
_PROBE_NUM_PREDICT = int(os.getenv("JARVIS_OLLAMA_HEALTH_PROBE_TOKENS", "1"))


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


_TAGS_CACHE: dict[str, object] = {"at": 0.0, "host": "", "models": [], "err": None}
_TAGS_TTL_S = float(os.getenv("JARVIS_OLLAMA_TAGS_TTL", "15"))


def _list_via_http(host: str) -> tuple[list[str], str | None]:
    now = time.time()
    if (
        _TAGS_CACHE.get("host") == host
        and _TAGS_CACHE.get("models")
        and (now - float(_TAGS_CACHE.get("at") or 0)) < _TAGS_TTL_S
    ):
        return list(_TAGS_CACHE.get("models") or []), _TAGS_CACHE.get("err")  # type: ignore[return-value]
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=5) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
            _TAGS_CACHE.update({"at": now, "host": host, "models": models, "err": None})
            return models, None
    except Exception as e:
        err = str(e)
        return [], err


def _loaded_runner_names(host: str) -> list[str]:
    """Models currently resident in Ollama (/api/ps). Empty on error."""
    try:
        with urllib.request.urlopen(f"{host.rstrip('/')}/api/ps", timeout=2) as resp:
            data = json.loads(resp.read().decode())
        names: list[str] = []
        for row in data.get("models") or []:
            name = (row.get("name") or row.get("model") or "").strip()
            if name:
                names.append(name)
        return names
    except Exception:
        return []


def _model_is_loaded(model: str, loaded: list[str]) -> bool:
    if not model or not loaded:
        return False
    want = model.lower().strip()
    want_base = want.split(":")[0]
    for name in loaded:
        low = (name or "").lower()
        if low == want or low.startswith(want_base):
            return True
    return False


def _soft_generate_probe(host: str, model: str, *, timeout: float) -> dict:
    """Cheap generate probe (1 token, short timeout). Never used on every health poll.

    Always pass workstation ``num_ctx``. Omitting it lets the Ollama daemon fall
    back to ``OLLAMA_CONTEXT_LENGTH`` (32768 here) × ``OLLAMA_NUM_PARALLEL`` (2) =
    ``-c 65536``, which reloads/evicts the chat runner and is a measured cause of
    alternating FIRST_PROGRESS_TIMEOUT.
    """
    options: dict = {"num_predict": max(1, _PROBE_NUM_PREDICT)}
    try:
        from jarvis.ollama_runtime import default_options

        options = dict(default_options(num_predict=max(1, _PROBE_NUM_PREDICT)))
    except Exception:
        options["num_ctx"] = int(os.getenv("JARVIS_OLLAMA_NUM_CTX", "8192") or 8192)
    body = json.dumps({
        "model": model,
        "prompt": "ping",
        "stream": False,
        "options": options,
    }).encode()
    req = urllib.request.Request(
        f"{host}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        elapsed = round(time.perf_counter() - started, 3)
        err = data.get("error")
        if err:
            return {"ok": False, "detail": str(err)[:160], "model": model, "elapsed_s": elapsed}
        # A completed generate with no HTTP error counts as healthy even if the model
        # returns an empty string for a 1-token ping.
        return {"ok": True, "detail": "generate ok", "model": model, "elapsed_s": elapsed}
    except TimeoutError:
        return {
            "ok": False,
            "detail": f"generate timed out after {timeout:.0f}s (daemon may be wedged)",
            "model": model,
            "elapsed_s": round(time.perf_counter() - started, 3),
        }
    except Exception as exc:
        # urlopen raises URLError on timeout on some Pythons
        msg = str(exc)
        if "timed out" in msg.lower() or "timeout" in msg.lower():
            return {
                "ok": False,
                "detail": f"generate timed out after {timeout:.0f}s (daemon may be wedged)",
                "model": model,
                "elapsed_s": round(time.perf_counter() - started, 3),
            }
        return {
            "ok": False,
            "detail": msg[:160],
            "model": model,
            "elapsed_s": round(time.perf_counter() - started, 3),
        }


def _probe_model_for_health(installed: list[str]) -> str:
    override = os.getenv("JARVIS_PROBE_OLLAMA_MODEL", "").strip()
    if override:
        return override
    try:
        from jarvis.llm import general_model

        name = (general_model() or "").strip()
        if name:
            return name
    except Exception:
        pass
    if installed:
        return installed[0]
    return os.getenv("JARVIS_GENERAL_MODEL", "qwen2.5:7b").strip() or "qwen2.5:7b"


def refresh_inference_probe(
    *,
    host: str | None = None,
    models: list[str] | None = None,
    force: bool = False,
) -> dict:
    """Run or return cached soft generate probe. Safe to call from status endpoints."""
    now = time.time()
    with _probe_lock:
        age = now - float(_probe_cache.get("at") or 0)
        if (
            not force
            and _probe_cache.get("ok") is not None
            and age < _PROBE_TTL
        ):
            return {
                "ok": _probe_cache["ok"],
                "detail": _probe_cache.get("detail") or "",
                "model": _probe_cache.get("model") or "",
                "elapsed_s": _probe_cache.get("elapsed_s"),
                "cached": True,
                "age_s": round(age, 1),
            }

    host = (host or ollama_host()).rstrip("/")
    model = _probe_model_for_health(models or [])
    try:
        from jarvis.ollama_runtime import chat_priority_active

        if chat_priority_active() and not force:
            return {
                "ok": True,
                "detail": "skipped soft probe — chat stream holds runner priority",
                "model": model,
                "elapsed_s": 0.0,
                "cached": True,
                "age_s": 0.0,
                "skipped_chat_priority": True,
            }
    except Exception:
        pass
    # Cold soft-probes are a systemic FIRST_PROGRESS_TIMEOUT cause: the 5s client
    # timeout aborts while Ollama keeps loading the chat model (~45s measured),
    # orphaning the runner and starving the real chat stream of its first token.
    # Only generate-probe when the model is already resident (or force=True).
    if not force:
        loaded = _loaded_runner_names(host)
        if not _model_is_loaded(model, loaded):
            detail = "inference not verified (chat model not loaded — skipped cold probe)"
            with _probe_lock:
                # Keep a prior live success sticky when we refuse to cold-load.
                # Expiry of probe TTL must not trigger an orphaned generate.
                if _probe_cache.get("ok") is True:
                    return {
                        "ok": True,
                        "detail": _probe_cache.get("detail") or "recent live inference ok",
                        "model": _probe_cache.get("model") or model,
                        "elapsed_s": _probe_cache.get("elapsed_s"),
                        "cached": True,
                        "age_s": round(time.time() - float(_probe_cache.get("at") or 0), 1),
                        "skipped_cold": True,
                    }
                _probe_cache["at"] = time.time()
                # Keep prior failure; otherwise leave unverified (None → degraded).
                if _probe_cache.get("ok") is not False:
                    _probe_cache["ok"] = None
                _probe_cache["detail"] = detail
                _probe_cache["model"] = model
                _probe_cache["elapsed_s"] = 0.0
            return {
                "ok": False,
                "detail": detail,
                "model": model,
                "elapsed_s": 0.0,
                "cached": False,
                "age_s": 0.0,
                "skipped_cold": True,
            }
    result = _soft_generate_probe(host, model, timeout=_PROBE_TIMEOUT)
    with _probe_lock:
        _probe_cache["at"] = time.time()
        _probe_cache["ok"] = bool(result.get("ok"))
        _probe_cache["detail"] = result.get("detail") or ""
        _probe_cache["model"] = result.get("model") or model
        _probe_cache["elapsed_s"] = result.get("elapsed_s")
    return {**result, "cached": False, "age_s": 0.0}


def note_inference_success(model: str = "") -> None:
    """Record a live chat/generate success so health can stay 'healthy' without re-probing."""
    with _probe_lock:
        _probe_cache["at"] = time.time()
        _probe_cache["ok"] = True
        _probe_cache["detail"] = "recent live inference ok"
        if model:
            _probe_cache["model"] = model
        _probe_cache["elapsed_s"] = 0.0


def note_inference_failure(detail: str = "", model: str = "") -> None:
    """Record a live inference failure (timeout/wedge) for honest degraded health."""
    with _probe_lock:
        _probe_cache["at"] = time.time()
        _probe_cache["ok"] = False
        _probe_cache["detail"] = (detail or "live inference failed")[:160]
        if model:
            _probe_cache["model"] = model
        _probe_cache["elapsed_s"] = None


def check_ollama(*, soft_probe: bool = True, force_probe: bool = False) -> dict:
    """Check Ollama reachability, installed models, and (optionally) generate liveness.

    health_state:
      - unavailable — tags/API unreachable
      - degraded — API up but generate probe failing / wedged
      - healthy — API up and generate probe succeeded (or recent live success)
    Soft probes are cached (default 120s) and use a short timeout (default 5s).
    """
    result = {
        "running": False,
        "host": ollama_host(),
        "models": [],
        "error": None,
        "source": None,
        "health_state": "unavailable",
        "probe": None,
    }

    for host in _hosts_to_try():
        models, err = _list_via_http(host)
        if models:
            result["running"] = True
            result["host"] = host
            result["models"] = models
            result["source"] = "http"
            break
        result["error"] = err
    else:
        cli_models = _list_via_cli()
        if cli_models:
            result["running"] = True
            result["models"] = cli_models
            result["source"] = "cli"
            result["error"] = None
        else:
            result["health_state"] = "unavailable"
            return result

    if not soft_probe and not force_probe:
        # Tags-only path for ultra-fast polls: use last probe cache if present.
        with _probe_lock:
            cached_ok = _probe_cache.get("ok")
            cached_detail = _probe_cache.get("detail") or ""
            age = time.time() - float(_probe_cache.get("at") or 0)
            probe_snap = {
                "ok": cached_ok,
                "detail": cached_detail,
                "model": _probe_cache.get("model") or "",
                "elapsed_s": _probe_cache.get("elapsed_s"),
                "cached": True,
                "age_s": round(age, 1) if _probe_cache.get("at") else None,
            }
        if cached_ok is True:
            result["health_state"] = "healthy"
        elif cached_ok is False:
            result["health_state"] = "degraded"
            result["error"] = cached_detail or "inference probe failed"
        else:
            # Reachable but never verified — do not advertise "ready".
            result["health_state"] = "degraded"
            result["error"] = "inference not verified yet"
        result["probe"] = probe_snap
        return result

    probe = refresh_inference_probe(
        host=result["host"],
        models=result["models"],
        force=force_probe,
    )
    result["probe"] = probe
    if probe.get("ok"):
        result["health_state"] = "healthy"
        result["error"] = None
    else:
        result["health_state"] = "degraded"
        result["error"] = probe.get("detail") or "generate probe failed"
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
