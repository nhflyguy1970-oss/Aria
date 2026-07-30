"""Ollama runtime helpers — probe model selection, bounded inference, benchmarks."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from typing import Any, Iterator

from jarvis.ollama_health import ollama_host

logger = logging.getLogger("jarvis.ollama_runtime")

_DEFAULT_PROBE_PROMPT = "Reply OK"
_PROBE_NUM_PREDICT = 8

# Chat streams hold this so background embed/index work cannot steal the sole
# OLLAMA_MAX_LOADED_MODELS=1 runner mid-turn (measured FIRST_PROGRESS_TIMEOUT cause).
# Cross-process: tray + serve are separate PIDs; a flag file coordinates them.
_chat_priority = 0
_chat_priority_lock = threading.Lock()


def _chat_priority_flag_path():
    from jarvis.config import DATA_DIR

    path = DATA_DIR / "runtime" / "chat_priority.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def chat_priority_active() -> bool:
    with _chat_priority_lock:
        if _chat_priority > 0:
            return True
    # Cross-process: another Aria PID may hold the flag while this process embeds.
    try:
        flag = _chat_priority_flag_path()
        if not flag.is_file():
            return False
        age = time.time() - flag.stat().st_mtime
        # Stale lock (>15m) must not block embeds forever after a crash.
        if age > 900:
            try:
                flag.unlink(missing_ok=True)
            except Exception:
                pass
            return False
        return True
    except Exception:
        return False


def begin_chat_priority() -> None:
    global _chat_priority
    with _chat_priority_lock:
        _chat_priority += 1
        if _chat_priority == 1:
            try:
                flag = _chat_priority_flag_path()
                flag.write_text(f"{os.getpid()}\n{time.time()}\n", encoding="utf-8")
            except Exception as exc:
                logger.debug("chat priority flag write failed: %s", exc)


def end_chat_priority() -> None:
    global _chat_priority
    with _chat_priority_lock:
        _chat_priority = max(0, _chat_priority - 1)
        if _chat_priority == 0:
            try:
                _chat_priority_flag_path().unlink(missing_ok=True)
            except Exception as exc:
                logger.debug("chat priority flag clear failed: %s", exc)


@contextmanager
def chat_priority_section() -> Iterator[None]:
    begin_chat_priority()
    try:
        yield
    finally:
        end_chat_priority()


def default_num_ctx() -> int:
    raw = os.getenv("JARVIS_OLLAMA_NUM_CTX", "8192").strip()
    try:
        return max(2048, int(raw))
    except ValueError:
        return 8192


def default_options(*, num_predict: int | None = None) -> dict[str, Any]:
    opts: dict[str, Any] = {"num_ctx": default_num_ctx()}
    if num_predict is not None:
        opts["num_predict"] = num_predict
    return opts


def probe_model_name() -> str:
    """Model used for health probes — matches daily chat model, not largest installed."""
    override = os.getenv("JARVIS_PROBE_OLLAMA_MODEL", "").strip()
    if override:
        return override
    try:
        from jarvis.llm import general_model

        return general_model()
    except Exception:
        return os.getenv("JARVIS_GENERAL_MODEL", "qwen2.5:7b").strip() or "qwen2.5:7b"


def _default_keep_alive() -> str | int:
    raw = (os.getenv("OLLAMA_KEEP_ALIVE") or "30m").strip()
    return raw or "30m"


def _http_generate(
    model: str,
    prompt: str,
    *,
    options: dict[str, Any] | None = None,
    timeout: float = 120,
    keep_alive: str | int | None = None,
) -> tuple[dict[str, Any], float]:
    host = ollama_host()
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": _default_keep_alive() if keep_alive is None else keep_alive,
        "options": options or default_options(num_predict=_PROBE_NUM_PREDICT),
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{host}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode())
    return payload, time.perf_counter() - started


def _model_base(name: str) -> str:
    return (name or "").strip().lower().split(":")[0]


def list_loaded_runners() -> list[dict[str, Any]]:
    host = ollama_host().rstrip("/")
    try:
        with urllib.request.urlopen(f"{host}/api/ps", timeout=2) as resp:
            rows = json.loads(resp.read().decode()).get("models") or []
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for row in rows:
        name = (row.get("name") or row.get("model") or "").strip()
        if not name:
            continue
        out.append(
            {
                "name": name,
                "size_vram": int(row.get("size_vram") or 0),
                "context_length": int(row.get("context_length") or 0),
            }
        )
    return out


def runner_info(model: str) -> dict[str, Any] | None:
    want = (model or "").strip()
    if not want:
        return None
    want_base = _model_base(want)
    for row in list_loaded_runners():
        name = row["name"]
        if _model_base(name) == want_base or name.lower() == want.lower():
            return row
    return None


def unload_model(model: str, *, timeout: float = 15) -> bool:
    name = (model or "").strip()
    if not name:
        return False
    host = ollama_host().rstrip("/")
    try:
        body = json.dumps({"model": name, "keep_alive": 0}).encode()
        req = urllib.request.Request(
            f"{host}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read(64)
        return True
    except Exception as exc:
        logger.debug("Unload %s failed: %s", name, exc)
        return False


def metrics_from_response(payload: dict[str, Any], elapsed_s: float) -> dict[str, Any]:
    load_ms = round((payload.get("load_duration") or 0) / 1e6, 1)
    prompt_ms = round((payload.get("prompt_eval_duration") or 0) / 1e6, 1)
    eval_ms = round((payload.get("eval_duration") or 0) / 1e6, 1)
    eval_count = int(payload.get("eval_count") or 0)
    tps = round(eval_count / (eval_ms / 1000), 1) if eval_ms > 0 and eval_count else 0.0
    return {
        "total_s": round(elapsed_s, 2),
        "load_ms": load_ms,
        "prompt_eval_ms": prompt_ms,
        "eval_ms": eval_ms,
        "eval_count": eval_count,
        "tokens_per_sec": tps,
        "cold_start": load_ms > 1000,
    }


def run_inference_probe(
    model: str | None = None,
    *,
    prompt: str = _DEFAULT_PROBE_PROMPT,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Bounded Ollama inference probe using the HTTP API (not CLI)."""
    name = model or probe_model_name()
    if timeout is None:
        timeout = float(os.getenv("JARVIS_OLLAMA_PROBE_TIMEOUT", "120"))
    try:
        payload, elapsed = _http_generate(name, prompt, timeout=timeout)
        text = (payload.get("response") or "").strip()
        metrics = metrics_from_response(payload, elapsed)
        ok = bool(text) and not payload.get("error")
        detail = text[:120] if text else (payload.get("error") or "empty response")
        return {
            "ok": ok,
            "detail": detail,
            "model": name,
            **metrics,
        }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()[:200]
        return {"ok": False, "detail": f"HTTP {exc.code}: {body}", "model": name}
    except TimeoutError:
        return {"ok": False, "detail": "ollama inference timed out", "model": name}
    except Exception as exc:
        return {"ok": False, "detail": str(exc)[:200], "model": name}


def warmup_chat_model(*, model: str | None = None) -> dict[str, Any]:
    """Load the default chat model into VRAM with workstation context limits."""
    name = model or probe_model_name()
    result = run_inference_probe(
        name,
        prompt="hi",
        timeout=float(os.getenv("JARVIS_OLLAMA_WARMUP_TIMEOUT", "180")),
    )
    if result.get("ok"):
        logger.info(
            "Chat model warmed: %s (load=%sms total=%ss)",
            name,
            result.get("load_ms"),
            result.get("total_s"),
        )
    else:
        logger.warning("Chat model warmup failed for %s: %s", name, result.get("detail"))
    return result


def benchmark_model(model: str, *, runs: int = 2) -> dict[str, Any]:
    """Measure cold then warm inference for diagnostics."""
    results: list[dict[str, Any]] = []
    for i in range(max(1, runs)):
        probe = run_inference_probe(model, timeout=180)
        probe["run"] = i + 1
        results.append(probe)
    return {"model": model, "runs": results}


def free_slot_for_chat_model(model: str) -> dict[str, Any]:
    """Unload embed squatters so chat can load under OLLAMA_MAX_LOADED_MODELS=1.

    Measured failure mode: nomic-embed occupies the only runner slot; qwen cold-load
    then takes ~45–70s and trips FIRST_PROGRESS_TIMEOUT before the first token.
    """
    want = (model or "").strip()
    if not want:
        return {"ok": False, "action": "noop", "detail": "no model"}

    loaded = [r["name"] for r in list_loaded_runners()]
    want_base = _model_base(want)
    if any(_model_base(n) == want_base or n.lower() == want.lower() for n in loaded):
        return {"ok": True, "action": "already_loaded", "loaded": loaded}

    unloaded: list[str] = []
    for name in loaded:
        low = name.lower()
        if "embed" in low or "nomic" in low:
            if unload_model(name):
                unloaded.append(name)
                logger.info("Unloaded %s to free Ollama slot for chat model %s", name, want)
    # Brief settle so the next chat load does not race a dying embed runner
    # (observed: ngl=0 / "no usable GPU" when chat starts mid-eviction).
    if unloaded:
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            still = [
                r["name"]
                for r in list_loaded_runners()
                if "embed" in r["name"].lower() or "nomic" in r["name"].lower()
            ]
            if not still:
                break
            time.sleep(0.2)
    return {
        "ok": True,
        "action": "freed" if unloaded else "noop",
        "unloaded": unloaded,
        "loaded_before": loaded,
    }


def ensure_chat_model_ready(
    model: str | None = None,
    *,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Make the chat model GPU-resident before the first-progress clock starts.

    Cold qwen2.5:7b load on this host is ~46s — just over the 45s FIRST_PROGRESS
    budget. Loading (or confirming residency) here keeps provider_stream itself
    under budget once tokens are requested.
    """
    name = (model or probe_model_name()).strip()
    if not name:
        return {"ok": False, "action": "noop", "detail": "no model"}
    if timeout is None:
        timeout = float(os.getenv("JARVIS_OLLAMA_WARMUP_TIMEOUT", "180"))
    t0 = time.perf_counter()
    freed = free_slot_for_chat_model(name)
    # Extra settle after embed eviction — measured race: chat llama-server starts
    # with ngl=0 ("no usable GPU") when CUDA is still releasing the embed runner.
    if freed.get("action") == "freed" or freed.get("unloaded"):
        time.sleep(float(os.getenv("JARVIS_OLLAMA_SLOT_SETTLE_S", "2.5")))
    info = runner_info(name)
    if info and int(info.get("size_vram") or 0) > 0:
        return {
            "ok": True,
            "action": "already_ready",
            "model": name,
            "size_vram": info.get("size_vram"),
            "freed": freed,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
        }

    # CPU-only / zero-VRAM runner is a known failure mode after embed races —
    # unload and reload so the next probe can bind CUDA.
    if info and int(info.get("size_vram") or 0) == 0:
        logger.warning("Chat model %s resident with size_vram=0 — reloading for GPU", name)
        unload_model(name)
        time.sleep(2.5)

    warm = warmup_chat_model(model=name)
    info = runner_info(name)
    if not info or int(info.get("size_vram") or 0) == 0:
        logger.warning("Warmup left %s without VRAM — one GPU retry after settle", name)
        if info:
            unload_model(name)
        time.sleep(3.0)
        free_slot_for_chat_model(name)
        time.sleep(1.0)
        warm = warmup_chat_model(model=name)
        info = runner_info(name)

    # Prefer GPU residency; accept any resident runner so chat can still proceed
    # (CPU path is slow but better than refusing the turn entirely).
    vram = int((info or {}).get("size_vram") or 0)
    ok = bool(info)
    if ok and vram <= 0:
        logger.warning(
            "Chat model %s resident without VRAM (CPU fallback) — proceeding anyway",
            name,
        )
    return {
        "ok": ok,
        "action": "warmed" if ok else "warmup_failed",
        "model": name,
        "size_vram": (info or {}).get("size_vram"),
        "freed": freed,
        "warmup": {k: warm.get(k) for k in ("ok", "load_ms", "total_s", "detail", "cold_start")},
        "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
        "cpu_fallback": bool(ok and vram <= 0),
    }
