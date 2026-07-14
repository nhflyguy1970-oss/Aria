"""Automatic execution-path benchmark — model × hardware winners by workload.

Measures real Ollama generates (warm/cold) on available devices.
Does not assume AMD or NVIDIA wins.
"""

from __future__ import annotations

import hashlib
import json
import os
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.inference.execution_policy import save_policy
from jarvis.nlu.placement import ollama_options_for_device

_WORKLOAD_PROMPTS: dict[str, str] = {
    "lightweight": "Reply in one short sentence: what is Docker Compose?",
    "coding": "Write a Python function that adds two integers. Code only.",
    "reasoning": "If all A are B and some B are C, are all A necessarily C? Answer yes or no with one reason.",
    "vision": "Describe this image briefly.",  # text-only probe of vision model availability
    "voice": "transcribe",  # device probe only
}

# Size tokens must not match as substrings of larger sizes (e.g. "4b" ⊂ "14b").
_LIGHTWEIGHT_SIZE_TOKENS = ("0.5b", "1b", "1.5b", "1.7b", "2b", "3b", "3.5b", "4b")
_LIGHTWEIGHT_NAME_HINTS = ("phi3", "phi-3", "mini", "gemma3:4b", "qwen3:1.7b", "qwen2.5:3b")
_CODING_HINTS = ("coder", "devstral", "deepseek-coder")
_REASONING_HINTS = ("deepseek-r1", "qwen2.5:7b", "qwen2.5:14b", "qwen3:14b", "qwen3:8b")
_VISION_HINTS = ("llava", "vision", "moondream", "vl:", "qwen2.5vl")


def _has_size_token(name: str, token: str) -> bool:
    """True if model name contains an exact size token (not '4b' inside '14b')."""
    import re

    lower = name.lower()
    pat = rf"(?:^|[:\-_/.]){re.escape(token)}(?:$|[:\-_/.])"
    return re.search(pat, lower) is not None


def _matches_hints(name: str, *, size_tokens: tuple[str, ...] = (), name_hints: tuple[str, ...] = ()) -> bool:
    lower = name.lower()
    if any(h in lower for h in name_hints):
        return True
    return any(_has_size_token(lower, tok) for tok in size_tokens)


def _hardware_fingerprint() -> str:
    parts: list[str] = []
    try:
        from jarvis.gpu import detect_gpu

        gpu = detect_gpu()
        parts.append(f"compute={gpu.get('compute_vendor')}:{gpu.get('compute_gpu')}")
        parts.append(f"display={gpu.get('display_vendor')}")
        parts.append(f"nvidia={gpu.get('nvidia_available')}")
        parts.append(f"rocm={gpu.get('rocm_available')}")
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
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def available_devices() -> list[str]:
    """Return measurable devices for the *current* Ollama binding.

    Dual-GPU hosts may still expose only one accelerator to the running
    ``ollama serve`` process. We never invent a second GPU path: AMD is
    included when ROCm is present and preference allows it (or when NVIDIA
    is absent). Observed GPU attribution still corrects winners.
    """
    devices = ["cpu"]
    try:
        from jarvis.gpu import detect_gpu

        gpu = detect_gpu()
        prefer = (os.getenv("JARVIS_GPU_PREFER") or "auto").strip().lower()
        has_nvidia = bool(
            gpu.get("nvidia_available") or (gpu.get("compute_vendor") or "").lower() == "nvidia"
        )
        has_amd = bool(gpu.get("rocm_available") or (gpu.get("vendor") or "").lower() == "amd")
        if has_nvidia and prefer in ("", "auto", "nvidia", "both"):
            devices.append("nvidia")
        if has_amd and prefer in ("amd", "both"):
            devices.append("amd")
        elif has_amd and not has_nvidia:
            devices.append("amd")
        elif has_amd and prefer in ("", "auto") and has_nvidia:
            # Ollama on this workstation is typically CUDA-bound; keep NVIDIA+CPU
            # as measurable chat devices. AMD remains available for prefer=amd/both.
            pass
    except Exception:
        pass
    out: list[str] = []
    for d in devices:
        if d not in out:
            out.append(d)
    return out


def _list_ollama_models() -> list[tuple[str, float]]:
    try:
        out = subprocess.check_output(["ollama", "list"], text=True, timeout=20)
    except Exception:
        return []
    models: list[tuple[str, float]] = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        size_gb = 0.0
        for i, token in enumerate(parts):
            upper = token.upper()
            if upper in ("GB", "MB") and i > 0:
                try:
                    val = float(parts[i - 1])
                except ValueError:
                    continue
                size_gb = val if upper == "GB" else val / 1000.0
                break
            if upper.endswith("GB"):
                try:
                    size_gb = float(upper.replace("GB", ""))
                except ValueError:
                    pass
            elif upper.endswith("MB"):
                try:
                    size_gb = float(upper.replace("MB", "")) / 1000.0
                except ValueError:
                    pass
        models.append((name, size_gb))
    return models


def discover_models_for_workload(workload: str, *, max_models: int = 4) -> list[str]:
    listed = _list_ollama_models()
    if not listed:
        return []
    workload = workload.lower()
    picked: list[str] = []

    def add_matching(
        *,
        size_tokens: tuple[str, ...] = (),
        name_hints: tuple[str, ...] = (),
        max_gb: float,
        prefer_small: bool = False,
    ) -> None:
        candidates = listed
        if prefer_small:
            candidates = sorted(listed, key=lambda x: x[1])
        for name, size in candidates:
            if size > max_gb:
                continue
            if size_tokens or name_hints:
                if not _matches_hints(name, size_tokens=size_tokens, name_hints=name_hints):
                    continue
            if name not in picked:
                picked.append(name)
            if len(picked) >= max_models:
                return

    if workload == "lightweight":
        add_matching(
            size_tokens=_LIGHTWEIGHT_SIZE_TOKENS,
            name_hints=_LIGHTWEIGHT_NAME_HINTS,
            max_gb=5.0,
            prefer_small=True,
        )
        if not picked:
            for name, size in sorted(listed, key=lambda x: x[1])[:max_models]:
                if size <= 5.0 and name not in picked and "embed" not in name.lower():
                    picked.append(name)
    elif workload == "coding":
        # Prefer mid-size coders first; huge 32B models only in full discovery.
        add_matching(name_hints=_CODING_HINTS, max_gb=10.0, prefer_small=True)
        if len(picked) < max_models:
            add_matching(name_hints=_CODING_HINTS, max_gb=22.0)
    elif workload == "reasoning":
        add_matching(name_hints=_REASONING_HINTS, max_gb=16.0, prefer_small=True)
        if not picked:
            add_matching(size_tokens=("7b", "8b", "9b", "14b"), max_gb=16.0, prefer_small=True)
    elif workload == "vision":
        add_matching(name_hints=_VISION_HINTS, max_gb=16.0)
    else:
        add_matching(
            size_tokens=_LIGHTWEIGHT_SIZE_TOKENS,
            name_hints=_LIGHTWEIGHT_NAME_HINTS,
            max_gb=5.0,
            prefer_small=True,
        )
    return picked[:max_models]


def _sample_gpu_mem() -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        raw = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=5,
        ).strip()
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) >= 2:
            out["nvidia_mem_mb"] = float(parts[0])
            out["nvidia_util_pct"] = float(parts[1])
    except Exception:
        pass
    try:
        raw = subprocess.check_output(
            ["rocm-smi", "--showuse"],
            text=True,
            timeout=5,
            stderr=subprocess.DEVNULL,
        )
        out["amd_rocm_use"] = raw[-200:]
        for line in raw.splitlines():
            if "GPU use" in line and "%" in line:
                digits = "".join(ch for ch in line.split(":")[-1] if ch.isdigit())
                if digits:
                    out["amd_util_pct"] = float(digits)
                    break
    except Exception:
        pass
    return out


def _infer_observed_hardware(before: dict[str, Any], after: dict[str, Any], requested: str) -> str:
    """Attribute the GPU that actually moved during inference (honest winner)."""
    n0 = float(before.get("nvidia_util_pct") or 0)
    n1 = float(after.get("nvidia_util_pct") or 0)
    a0 = float(before.get("amd_util_pct") or 0)
    a1 = float(after.get("amd_util_pct") or 0)
    n_delta = n1 - n0
    a_delta = a1 - a0
    mem0 = float(before.get("nvidia_mem_mb") or 0)
    mem1 = float(after.get("nvidia_mem_mb") or 0)
    if n_delta >= 5 or (mem1 - mem0) >= 200:
        return "nvidia"
    if a_delta >= 5:
        return "amd"
    if requested == "cpu":
        return "cpu"
    # num_gpu>0 with a CUDA-bound Ollama usually still means NVIDIA even if util sampling missed.
    if requested in ("nvidia", "amd"):
        return "nvidia" if mem1 > 0 or n1 > 0 else requested
    return requested


def _bench_once(model: str, device: str, prompt: str, *, num_predict: int) -> dict[str, Any]:
    from jarvis import llm

    opts = ollama_options_for_device(device)
    opts["num_predict"] = num_predict
    opts["temperature"] = 0
    t0 = time.perf_counter()
    err = None
    text = ""
    usage: dict[str, Any] = {}
    try:
        # Use raw ollama chat for token metrics
        from ollama import chat

        from jarvis.llm import _normalize_chat_kwargs

        resp = chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **_normalize_chat_kwargs({"options": opts}),
        )
        text = (resp.get("message") or {}).get("content") or ""
        usage = llm.usage_from_response(resp)
        # Prefer native ns timings when present
        if resp.get("eval_count") and resp.get("eval_duration"):
            eval_s = float(resp["eval_duration"]) / 1e9
            if eval_s > 0:
                usage["completion_tokens_per_sec"] = round(float(resp["eval_count"]) / eval_s, 2)
        if resp.get("prompt_eval_count") and resp.get("prompt_eval_duration"):
            pe_s = float(resp["prompt_eval_duration"]) / 1e9
            if pe_s > 0:
                usage["prompt_tokens_per_sec"] = round(float(resp["prompt_eval_count"]) / pe_s, 2)
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
    wall_ms = (time.perf_counter() - t0) * 1000.0
    # Qwen3/R1 may spend the predict budget on empty/thinking tokens; still count as a
    # successful hardware probe when tokens were produced.
    toks = int(usage.get("completion_tokens") or 0)
    ok = not err and (bool(text.strip()) or toks > 0)
    return {
        "ok": ok,
        "error": err,
        "wall_ms": round(wall_ms, 1),
        "chars": len(text),
        "empty_text": not bool(text.strip()),
        **usage,
    }


def bench_model_device(
    model: str,
    device: str,
    *,
    workload: str,
    warm_runs: int = 2,
    num_predict: int = 64,
) -> dict[str, Any]:
    prompt = _WORKLOAD_PROMPTS.get(workload, _WORKLOAD_PROMPTS["lightweight"])
    before = _sample_gpu_mem()
    cold = _bench_once(model, device, prompt, num_predict=num_predict)
    warms: list[dict[str, Any]] = []
    for _ in range(max(1, warm_runs)):
        warms.append(_bench_once(model, device, prompt, num_predict=num_predict))
    after = _sample_gpu_mem()
    observed = _infer_observed_hardware(before, after, device)
    warm_ok = [w for w in warms if w.get("ok")]
    success_rate = (int(cold.get("ok")) + sum(1 for w in warms if w.get("ok"))) / (1 + len(warms))
    if not warm_ok and not cold.get("ok"):
        return {
            "model": model,
            "device": device,
            "device_requested": device,
            "observed_hardware": observed,
            "workload": workload,
            "ok": False,
            "success_rate": 0.0,
            "cold_start_ms": cold.get("wall_ms"),
            "warm_latency_ms": None,
            "tokens_per_sec": None,
            "prompt_tokens_per_sec": None,
            "score": 1_000_000.0,
            "error": cold.get("error") or (warms[-1].get("error") if warms else "failed"),
            "gpu": after,
        }
    warm_lat = [float(w["wall_ms"]) for w in warm_ok] or [float(cold["wall_ms"])]
    tps_vals = [
        float(w["completion_tokens_per_sec"])
        for w in warm_ok
        if w.get("completion_tokens_per_sec")
    ]
    ptps_vals = [
        float(w["prompt_tokens_per_sec"]) for w in warm_ok if w.get("prompt_tokens_per_sec")
    ]
    warm_avg = statistics.mean(warm_lat)
    tps = statistics.mean(tps_vals) if tps_vals else 0.0
    # Score: prefer low warm latency and high reliability; slight throughput bonus.
    # Prefer responses that emitted visible text when latency is comparable.
    empty_penalty = 150.0 if all(w.get("empty_text") for w in warm_ok) else 0.0
    score = warm_avg + (1.0 - success_rate) * 5000.0 - min(tps, 80.0) * 2.0 + empty_penalty
    # Winners use observed hardware (where work actually ran).
    return {
        "model": model,
        "device": observed,
        "device_requested": device,
        "observed_hardware": observed,
        "workload": workload,
        "ok": True,
        "success_rate": round(success_rate, 3),
        "cold_start_ms": cold.get("wall_ms"),
        "warm_latency_ms": round(warm_avg, 1),
        "tokens_per_sec": round(tps, 2) if tps else None,
        "prompt_tokens_per_sec": round(statistics.mean(ptps_vals), 2) if ptps_vals else None,
        "prompt_tokens": (warm_ok[0] if warm_ok else cold).get("prompt_tokens"),
        "completion_tokens": (warm_ok[0] if warm_ok else cold).get("completion_tokens"),
        "score": round(score, 1),
        "gpu": after,
    }


def run_execution_benchmark(
    *,
    workloads: list[str] | None = None,
    quick: bool = True,
    warm_runs: int | None = None,
) -> dict[str, Any]:
    """Benchmark available models×devices and write execution routing policy."""
    workloads = workloads or ["lightweight", "coding", "reasoning"]
    warm_runs = warm_runs if warm_runs is not None else (1 if quick else 3)
    max_models = 2 if quick else 4
    num_predict = 48 if quick else 96
    devices = available_devices()
    results: list[dict[str, Any]] = []
    winners: dict[str, Any] = {}

    for workload in workloads:
        if workload == "voice":
            winners[workload] = {
                "provider": "local",
                "model": None,
                "hardware": os.getenv("JARVIS_WHISPER_DEVICE") or "cpu",
                "selection_reason": "Voice uses Whisper device env / gpu_routing (not Ollama chat)",
                "confidence": 0.7,
            }
            continue
        models = discover_models_for_workload(workload, max_models=max_models)
        wl_results: list[dict[str, Any]] = []
        for model in models:
            for device in devices:
                # Skip huge models on CPU in quick mode
                if quick and device == "cpu" and workload in ("coding", "reasoning"):
                    continue
                row = bench_model_device(
                    model,
                    device,
                    workload=workload,
                    warm_runs=warm_runs,
                    num_predict=num_predict,
                )
                results.append(row)
                if row.get("ok"):
                    wl_results.append(row)
        wl_results.sort(key=lambda r: float(r.get("score") or 1e9))
        if not wl_results:
            winners[workload] = {
                "provider": "ollama",
                "model": None,
                "hardware": "cpu",
                "selection_reason": f"No successful {workload} runs — fallback required",
                "confidence": 0.2,
                "fallback_hardware": "cpu",
            }
            continue
        best = wl_results[0]
        # Second-best for fallback (different device or model)
        fallback = next((r for r in wl_results[1:] if r["model"] != best["model"] or r["device"] != best["device"]), None)
        winners[workload] = {
            "provider": "ollama",
            "model": best["model"],
            "hardware": best["device"],
            "warm_latency_ms": best.get("warm_latency_ms"),
            "cold_start_ms": best.get("cold_start_ms"),
            "tokens_per_sec": best.get("tokens_per_sec"),
            "success_rate": best.get("success_rate"),
            "selection_reason": (
                f"Measured winner for {workload}: model={best['model']} hardware={best['device']} "
                f"warm={best.get('warm_latency_ms')}ms tps={best.get('tokens_per_sec')} "
                f"(score={best.get('score')})"
            ),
            "confidence": 0.85 if (best.get("success_rate") or 0) >= 1.0 else 0.6,
            "fallback_model": (fallback or {}).get("model"),
            "fallback_hardware": (fallback or {}).get("device") or "cpu",
            "candidates": wl_results[:8],
        }

    previous = None
    prev_path = DATA_DIR / "execution_routing_policy.json"
    if prev_path.is_file():
        try:
            previous = json.loads(prev_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            previous = None

    changes: list[dict[str, Any]] = []
    if previous and previous.get("workloads"):
        for wl, now in winners.items():
            was = (previous.get("workloads") or {}).get(wl) or {}
            if was.get("model") != now.get("model") or was.get("hardware") != now.get("hardware"):
                changes.append(
                    {
                        "workload": wl,
                        "from": {"model": was.get("model"), "hardware": was.get("hardware")},
                        "to": {"model": now.get("model"), "hardware": now.get("hardware")},
                    }
                )

    policy = {
        "version": "1.0",
        "source": "execution_benchmark",
        "quick": quick,
        "benchmark_at": time.time(),
        "benchmark_date": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "hardware_fingerprint": _hardware_fingerprint(),
        "devices_tested": devices,
        "workloads": winners,
        "results": results,
        "changes_from_previous": changes,
        "historical_note": (
            "Prior NLU placement preferred CPU for classifiers (often with invalid 0ms benches). "
            "Ollama daemon on this host commonly binds NVIDIA (HIP_VISIBLE_DEVICES=-1). "
            "Reference/Runtime/Greeting request classes remain non-LLM by design."
        ),
    }
    save_policy(policy)
    _write_docs(policy)
    return policy


def _write_docs(policy: dict[str, Any]) -> None:
    from jarvis.inference.execution_policy import routing_matrix

    root = Path(__file__).resolve().parents[2]
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)

    # Benchmark report
    report = docs / "EXECUTION_BENCHMARK_REPORT.md"
    lines = [
        "# Execution Benchmark Report",
        "",
        f"**Date:** {policy.get('benchmark_date')}",
        f"**Hardware fingerprint:** `{policy.get('hardware_fingerprint')}`",
        f"**Devices tested:** {', '.join(policy.get('devices_tested') or [])}",
        f"**Mode:** {'quick' if policy.get('quick') else 'full'}",
        "",
        "## Workload winners",
        "",
        "| Workload | Model | Hardware | Warm ms | tok/s | Reason |",
        "|----------|-------|----------|---------|-------|--------|",
    ]
    for wl, block in (policy.get("workloads") or {}).items():
        lines.append(
            f"| {wl} | `{block.get('model')}` | `{block.get('hardware')}` | "
            f"{block.get('warm_latency_ms')} | {block.get('tokens_per_sec')} | "
            f"{(block.get('selection_reason') or '')[:80]} |"
        )
    lines.extend(["", "## Changes from previous", ""])
    changes = policy.get("changes_from_previous") or []
    if not changes:
        lines.append("_No prior policy or no changes._")
    else:
        for ch in changes:
            lines.append(
                f"- **{ch['workload']}**: `{ch['from']}` → `{ch['to']}`"
            )
    lines.extend(
        [
            "",
            "## Historical context",
            "",
            str(policy.get("historical_note") or ""),
            "",
            "## All measured runs",
            "",
            "| Workload | Model | Device | OK | Warm ms | tok/s | Score | Error |",
            "|----------|-------|--------|----|---------|-------|-------|-------|",
        ]
    )
    for row in policy.get("results") or []:
        lines.append(
            f"| {row.get('workload')} | `{row.get('model')}` | `{row.get('device')}` | "
            f"{row.get('ok')} | {row.get('warm_latency_ms')} | {row.get('tokens_per_sec')} | "
            f"{row.get('score')} | {(row.get('error') or '')[:40]} |"
        )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Routing matrix
    matrix_path = docs / "ROUTING_MATRIX.md"
    rows = routing_matrix()
    mlines = [
        "# Routing Matrix",
        "",
        "Permanent production routing policy derived from measured execution benchmarks.",
        "AMD/NVIDIA/CPU are selected only when they win measurements for that workload.",
        "",
        f"**Benchmark date:** {policy.get('benchmark_date')}",
        "",
        "| Request class | Capability | Primary model | Fallback model | Primary HW | Fallback HW | Provider | Expected latency | Winner | Policy |",
        "|---------------|------------|---------------|----------------|------------|-------------|----------|------------------|--------|--------|",
    ]
    for r in rows:
        mlines.append(
            f"| {r['request_class']} | {r['capability']} | `{r['primary_model']}` | "
            f"`{r['fallback_model']}` | `{r['primary_hardware']}` | `{r['fallback_hardware']}` | "
            f"{r['provider']} | {r['expected_latency_ms']} | {r['benchmark_winner']} | "
            f"{r['selection_policy']} |"
        )
    matrix_path.write_text("\n".join(mlines) + "\n", encoding="utf-8")

    # JSON snapshot for automation
    snap = DATA_DIR / "execution_benchmark_latest.json"
    snap.write_text(json.dumps(policy, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
