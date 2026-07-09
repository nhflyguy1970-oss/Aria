"""Ollama runtime helpers — probe model selection, bounded inference, benchmarks."""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

from jarvis.ollama_health import ollama_host

logger = logging.getLogger("jarvis.ollama_runtime")

_DEFAULT_PROBE_PROMPT = "Reply OK"
_PROBE_NUM_PREDICT = 8


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


def _http_generate(
    model: str,
    prompt: str,
    *,
    options: dict[str, Any] | None = None,
    timeout: float = 120,
) -> tuple[dict[str, Any], float]:
    host = ollama_host()
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
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
