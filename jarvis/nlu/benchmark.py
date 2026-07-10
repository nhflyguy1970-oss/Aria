"""Adaptive classifier benchmarking — auto-discover models and hardware placement."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.nlu.placement import _PLACEMENT_FILE, ollama_options_for_device, save_placement

_STALE_DAYS = int(os.getenv("JARVIS_NLU_BENCHMARK_STALE_DAYS", "30"))
_BENCHMARK_PROMPTS: tuple[tuple[str, str], ...] = (
    ("What GPU am I using?", "runtime"),
    ("What is a GPU?", "knowledge"),
    ("Show Docker Compose documentation.", "reference"),
    ("How do I configure Docker Compose?", "reference"),
    ("Search my memory for Docker.", "memory"),
    ("Search the web for Docker.", "web_search"),
)

_MODEL_HINTS = (
    "smollm",
    "gemma",
    "qwen2.5",
    "qwen3",
    "llama3.2",
    "llama3.1",
    "phi",
    "tinyllama",
    "0.5b",
    "1b",
    "1.5b",
    "1.7b",
    "2b",
    "3b",
)
_MAX_MODEL_SIZE_GB = float(os.getenv("JARVIS_NLU_MAX_MODEL_GB", "4.0"))


def _hardware_fingerprint() -> str:
    parts: list[str] = []
    try:
        from jarvis.gpu import detect_gpu

        gpu = detect_gpu()
        parts.append(f"gpu={gpu.get('vendor')}:{gpu.get('name')}")
    except Exception:
        parts.append("gpu=unknown")
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("model name"):
                    parts.append(line.strip())
                    break
    except OSError:
        pass
    blob = "|".join(parts)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def discover_classifier_models() -> list[str]:
    """Discover lightweight local models suitable for intent classification."""
    try:
        out = subprocess.check_output(["ollama", "list"], text=True, timeout=15)
    except Exception:
        return []
    models: list[str] = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        size_gb = 0.0
        for token in parts[1:]:
            if token.upper().endswith("GB"):
                try:
                    size_gb = float(token.upper().replace("GB", ""))
                except ValueError:
                    pass
        lower = name.lower()
        if size_gb > _MAX_MODEL_SIZE_GB:
            continue
        if any(h in lower for h in _MODEL_HINTS) or size_gb <= 2.5:
            models.append(name)
    return sorted(set(models))


def _devices_to_try() -> list[str]:
    devices = ["cpu"]
    try:
        from jarvis.gpu import detect_gpu

        vendor = (detect_gpu().get("vendor") or "").lower()
        if vendor == "nvidia":
            devices.append("nvidia")
        elif vendor == "amd":
            devices.append("amd")
    except Exception:
        pass
    return devices


def _score_json(raw: str) -> tuple[bool, str | None]:
    import re

    text = (raw or "").strip()
    m = re.search(r"\{[^{}]*\}", text, re.S)
    if not m:
        return False, None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return False, None
    intent = str(data.get("intent") or "").lower()
    return bool(intent), intent


def _bench_model_device(model: str, device: str) -> dict[str, Any]:
    from jarvis import llm

    opts = ollama_options_for_device(device)
    system = (
        'Reply JSON only: {"intent":"runtime","action":"status","subject":"gpu","confidence":0.9}'
    )
    latencies: list[float] = []
    json_ok = 0
    accuracy_hits = 0
    cold_ms = None
    for idx, (prompt, expected) in enumerate(_BENCHMARK_PROMPTS):
        t0 = time.perf_counter()
        try:
            raw = llm.ask_with_system(model, system, prompt, options=opts)
            ok, intent = _score_json(raw)
        except Exception:
            ok, intent = False, None
        ms = (time.perf_counter() - t0) * 1000.0
        if idx == 0:
            cold_ms = ms
        latencies.append(ms)
        json_ok += int(ok)
        if intent == expected or (expected == "reference" and intent == "documentation"):
            accuracy_hits += 1
    warm = latencies[1:] or latencies
    avg = sum(latencies) / len(latencies) if latencies else 9999.0
    warm_avg = sum(warm) / len(warm) if warm else avg
    json_rate = json_ok / max(len(_BENCHMARK_PROMPTS), 1)
    acc_rate = accuracy_hits / max(len(_BENCHMARK_PROMPTS), 1)
    score = warm_avg + (1.0 - json_rate) * 500 + (1.0 - acc_rate) * 300
    if device != "cpu":
        score += 50
    return {
        "model": model,
        "device": device,
        "avg_latency_ms": round(avg, 1),
        "warm_latency_ms": round(warm_avg, 1),
        "cold_start_ms": round(cold_ms or avg, 1),
        "json_correct_rate": round(json_rate, 3),
        "intent_accuracy": round(acc_rate, 3),
        "score": round(score, 1),
    }


def run_benchmark(*, force: bool = False) -> dict[str, Any]:
    models = discover_classifier_models()
    if not models:
        models = ["qwen2.5:1.5b"]
    results: list[dict[str, Any]] = []
    for model in models:
        for device in _devices_to_try():
            try:
                results.append(_bench_model_device(model, device))
            except Exception:
                continue
    if not results:
        placement = {
            "model": "structure",
            "device": "cpu",
            "source": "benchmark_fallback",
            "selection_reason": "No Ollama models available; using structural NLU only",
            "benchmark_at": time.time(),
            "hardware_fingerprint": _hardware_fingerprint(),
            "version": "1.0",
            "results": [],
        }
        save_placement(placement)
        return placement
    results.sort(key=lambda r: r["score"])
    winner = results[0]
    device = winner["device"]
    reason = (
        f"Lowest composite score (latency {winner['warm_latency_ms']}ms warm, "
        f"accuracy {int(winner['intent_accuracy'] * 100)}%, JSON {int(winner['json_correct_rate'] * 100)}%). "
    )
    if device == "cpu":
        reason += "CPU chosen to keep primary GPU free for main inference."
    elif device == "amd":
        reason += "AMD GPU chosen as least disruptive dedicated classifier device."
    else:
        reason += "NVIDIA GPU chosen based on measured lowest classifier latency."
    placement = {
        "model": winner["model"],
        "device": device,
        "source": "benchmark",
        "selection_reason": reason,
        "benchmark_at": time.time(),
        "benchmark_date": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "average_latency_ms": winner["warm_latency_ms"],
        "hardware_fingerprint": _hardware_fingerprint(),
        "version": "1.0",
        "results": results,
        "force": force,
    }
    save_placement(placement)
    _write_report(placement)
    return placement


def _write_report(placement: dict[str, Any]) -> None:
    path = DATA_DIR.parent / "docs" / "NLU_CLASSIFIER_BENCHMARK.md"
    if not path.parent.is_dir():
        path = Path(__file__).resolve().parents[2] / "docs" / "NLU_CLASSIFIER_BENCHMARK.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    w = placement
    lines = [
        "# NLU Classifier Benchmark",
        "",
        f"**Model:** `{w.get('model')}`",
        f"**Device:** `{w.get('device')}`",
        f"**Date:** {w.get('benchmark_date', '—')}",
        f"**Average latency:** {w.get('average_latency_ms')} ms",
        f"**Reason:** {w.get('selection_reason', '')}",
        "",
        "| Model | Device | Warm ms | Accuracy | JSON | Score |",
        "|-------|--------|---------|----------|------|-------|",
    ]
    for row in w.get("results") or []:
        lines.append(
            f"| {row.get('model')} | {row.get('device')} | {row.get('warm_latency_ms')} | "
            f"{row.get('intent_accuracy')} | {row.get('json_correct_rate')} | {row.get('score')} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def should_rebenchmark() -> bool:
    if os.getenv("JARVIS_NLU_FORCE_BENCHMARK", "").strip().lower() in ("1", "true", "yes"):
        return True
    if not _PLACEMENT_FILE.is_file():
        return True
    try:
        data = json.loads(_PLACEMENT_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return True
    if data.get("hardware_fingerprint") != _hardware_fingerprint():
        return True
    age = time.time() - float(data.get("benchmark_at") or 0)
    if age > _STALE_DAYS * 86400:
        return True
    known = set(discover_classifier_models())
    bench_models = {r.get("model") for r in data.get("results") or []}
    if known - bench_models:
        return True
    return False


def ensure_benchmark() -> dict[str, Any]:
    from jarvis.nlu.placement import placement_config

    if os.getenv("JARVIS_NLU_MODEL"):
        return placement_config()
    if should_rebenchmark():
        return run_benchmark()
    return placement_config()
