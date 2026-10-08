#!/usr/bin/env python3
"""Benchmark installed local models on ARIA workloads (see quality_benchmark).

Safety rules, because the GPU is shared:
  * only ARIA's Ollama endpoint is used (default http://127.0.0.1:11434);
    Fly Tying Reference's endpoints are only *read* (/api/ps) to stay out of
    their way — never sent a request that loads or runs anything;
  * the run will not start, and stops between models, if Fly Tying has a model
    loaded or ARIA reports itself busy;
  * a model is skipped if it does not fit in free VRAM with a safety margin;
  * every model is unloaded when its tasks finish.

Nothing is downloaded and no production setting is changed. Results go to
--out as results.jsonl (one line per task) and summary.json.
"""

from __future__ import annotations

import argparse
import base64
import json
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jarvis.inference import quality_benchmark as qb  # noqa: E402

ARIA_OLLAMA = "http://127.0.0.1:11434"
FLYTYING = ("http://127.0.0.1:11435", "http://127.0.0.1:11436")
ARIA_HEALTH = "http://127.0.0.1:8765/api/health"
VRAM_MARGIN_MIB = 1200

GENERAL = ["reasoning", "routing", "tool_routing", "memory", "evidence"]
PLAN: list[tuple[str, list[str]]] = [
    ("gemma4:12b", GENERAL + ["coding", "vision"]),
    ("qwen3.5:9b", GENERAL + ["coding", "vision"]),
    ("qwen3:8b", GENERAL + ["coding"]),
    ("qwen3:14b", GENERAL + ["coding"]),
    ("deepseek-r1:14b", ["reasoning", "memory", "evidence"]),
    ("qwen3.5:4b", GENERAL + ["vision"]),
    ("qwen3:4b-instruct-2507-q4_K_M", GENERAL),
    ("granite4.2:8b", GENERAL),
    ("granite4.2:3b", GENERAL),
    ("ministral-3:8b", GENERAL + ["vision"]),
    ("qwen2.5:7b", GENERAL),
    ("qwen3:1.7b", GENERAL),
    ("qwen2.5-coder:1.5b-base", ["routing", "tool_routing", "memory"]),
    ("qwen2.5-coder:14b", ["coding", "routing"]),
    ("qwen2.5-coder:7b", ["coding", "routing"]),
    ("qwen2.5vl:7b", ["vision"]),
    ("qwen3-vl:4b-instruct-q4_K_M", ["vision"]),
    ("llama3.2-vision:11b", ["vision"]),
]
# Models whose reasoning cannot be switched off get room to think.
ALWAYS_THINKS = ("deepseek-r1",)


def _get(url: str, timeout: float = 5.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _post(path: str, body: dict, timeout: float = 600.0) -> dict:
    req = urllib.request.Request(
        f"{ARIA_OLLAMA}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def flytying_busy() -> list[str]:
    loaded = []
    for url in FLYTYING:
        try:
            loaded += [f"{url} {m['name']}" for m in _get(f"{url}/api/ps").get("models") or []]
        except Exception:
            pass  # not running = not busy
    return loaded


def aria_busy() -> bool:
    try:
        return bool(_get(ARIA_HEALTH).get("busy"))
    except Exception:
        return False


def gpu_sample() -> tuple[int, int, int]:
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
         "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=10,
    ).stdout.strip().splitlines()[0]
    used, total, util = (int(x.strip()) for x in out.split(","))
    return used, total, util


class GpuSampler:
    def __init__(self) -> None:
        self.samples: list[tuple[int, int]] = []
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                used, _total, util = gpu_sample()
                self.samples.append((used, util))
            except Exception:
                pass
            self._stop.wait(1.0)

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._t.join(timeout=5)

    def summary(self) -> dict:
        if not self.samples:
            return {}
        return {
            "peak_mem_mib": max(s[0] for s in self.samples),
            "mean_util_pct": round(statistics.mean(s[1] for s in self.samples), 1),
            "peak_util_pct": max(s[1] for s in self.samples),
        }


def model_size_mib(model: str) -> int:
    for m in _get(f"{ARIA_OLLAMA}/api/tags").get("models") or []:
        if m["name"] == model:
            return int(m["size"]) // (1024 * 1024)
    return 0


def capabilities(model: str) -> set[str]:
    try:
        return set(_post("/api/show", {"model": model}, timeout=30).get("capabilities") or [])
    except Exception:
        return set()


def run_task(model: str, task: qb.Task, caps: set[str], images: dict[str, str]) -> dict:
    thinks = model.startswith(ALWAYS_THINKS)
    messages = []
    if task.system:
        messages.append({"role": "system", "content": task.system})
    user: dict = {"role": "user", "content": task.prompt}
    if task.images:
        user["images"] = [
            base64.b64encode(Path(images[name]).read_bytes()).decode() for name in task.images
        ]
    messages.append(user)
    body: dict = {
        "model": model,
        "messages": messages,
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": 0,
            "seed": 42,
            "num_ctx": 4096,
            "num_predict": 1536 if thinks else task.max_tokens,
        },
    }
    if "thinking" in caps and not thinks:
        body["think"] = False
    if task.tools:
        body["tools"] = task.tools
    record = {"model": model, "task": task.id, "category": task.category}
    t0 = time.perf_counter()
    try:
        resp = _post("/api/chat", body)
    except Exception as exc:  # noqa: BLE001 - an error is a result
        record.update(passed=False, error=f"{type(exc).__name__}: {str(exc)[:200]}",
                      wall_ms=round((time.perf_counter() - t0) * 1000, 1))
        return record
    wall = (time.perf_counter() - t0) * 1000
    message = resp.get("message") or {}
    text = message.get("content") or ""
    if task.tools:
        calls = [
            {"name": (c.get("function") or {}).get("name"),
             "arguments": (c.get("function") or {}).get("arguments") or {}}
            for c in message.get("tool_calls") or []
        ]
        passed = bool(task.score_tool and task.score_tool(calls))
        record["tool_calls"] = calls[:2]
    else:
        passed = bool(task.score(text))
    eval_count = resp.get("eval_count") or 0
    eval_ns = resp.get("eval_duration") or 0
    record.update(
        passed=passed,
        wall_ms=round(wall, 1),
        load_ms=round((resp.get("load_duration") or 0) / 1e6, 1),
        prompt_ms=round((resp.get("prompt_eval_duration") or 0) / 1e6, 1),
        output_tokens=eval_count,
        tokens_per_s=round(eval_count / (eval_ns / 1e9), 2) if eval_ns else None,
        output=text[:400],
    )
    return record


def unload(model: str, *, wait_s: float = 90.0) -> None:
    """Unload and wait until Ollama has actually released it.

    Ollama unloads asynchronously; checking free VRAM straight after the
    request saw the previous model still resident and skipped the next one.
    """
    try:
        _post("/api/generate", {"model": model, "keep_alive": 0}, timeout=60)
    except Exception:
        pass
    deadline = time.time() + wait_s
    while time.time() < deadline:
        try:
            loaded = {m["name"] for m in _get(f"{ARIA_OLLAMA}/api/ps").get("models") or []}
        except Exception:
            loaded = set()
        if model not in loaded:
            time.sleep(2)  # let the driver return the memory
            return
        time.sleep(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="", help="comma-separated model subset")
    ap.add_argument("--suites", default="", help="comma-separated suite subset")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    images = qb.make_vision_images(out / "images")
    only = {m for m in args.only.split(",") if m}
    suites_only = {s for s in args.suites.split(",") if s}

    busy = flytying_busy()
    if busy:
        print(f"Fly Tying Reference has models loaded ({busy}); not starting.", flush=True)
        return 2
    if aria_busy():
        print("ARIA reports busy; not starting.", flush=True)
        return 2
    installed = {m["name"] for m in _get(f"{ARIA_OLLAMA}/api/tags").get("models") or []}
    meta: dict = {"started": time.time(), "models": {}, "skipped": {}}
    results_path = out / "results.jsonl"

    for model, suites in PLAN:
        if only and model not in only:
            continue
        if model not in installed:
            meta["skipped"][model] = "not installed"
            continue
        busy = flytying_busy()
        if busy or aria_busy():
            meta["stopped_early"] = f"yielded to other GPU users: {busy or 'ARIA busy'}"
            print(meta["stopped_early"], flush=True)
            break
        # Anything of ours still resident from an earlier run goes first.
        try:
            for m in _get(f"{ARIA_OLLAMA}/api/ps").get("models") or []:
                unload(m["name"])
        except Exception:
            pass
        used, total, _ = gpu_sample()
        size = model_size_mib(model)
        if size + VRAM_MARGIN_MIB > total - used:
            meta["skipped"][model] = f"needs ~{size} MiB + margin, {total - used} MiB free"
            continue
        caps = capabilities(model)
        tasks = [t for s in suites if (not suites_only or s in suites_only) for t in qb.SUITES[s]]
        if "tools" not in caps:
            unsupported = [t for t in tasks if t.tools]
            tasks = [t for t in tasks if not t.tools]
            for t in unsupported:
                rec = {"model": model, "task": t.id, "category": t.category, "passed": False,
                       "error": "unsupported: model reports no tools capability"}
                with open(results_path, "a") as fh:
                    fh.write(json.dumps(rec) + "\n")
        if "vision" not in caps:
            tasks = [t for t in tasks if not t.images]
        print(f"== {model}: {len(tasks)} tasks (caps={sorted(caps)})", flush=True)
        records = []
        with GpuSampler() as sampler:
            for task in tasks:
                rec = run_task(model, task, caps, images)
                records.append(rec)
                with open(results_path, "a") as fh:
                    fh.write(json.dumps(rec) + "\n")
            try:
                ps = _get(f"{ARIA_OLLAMA}/api/ps").get("models") or []
                loaded = next((m for m in ps if m["name"] == model), {})
            except Exception:
                loaded = {}
        unload(model)
        passed = sum(1 for r in records if r.get("passed"))
        meta["models"][model] = {
            "capabilities": sorted(caps),
            "tasks": len(records),
            "passed": passed,
            "cold_load_ms": records[0].get("load_ms") if records else None,
            "size_vram_mib": int(loaded.get("size_vram") or 0) // (1024 * 1024),
            "size_total_mib": int(loaded.get("size") or 0) // (1024 * 1024),
            **sampler.summary(),
        }
        print(f"   {passed}/{len(records)} passed; {meta['models'][model]}", flush=True)

    meta["finished"] = time.time()
    all_results = [json.loads(line) for line in results_path.read_text().splitlines() if line]
    summary = {"meta": meta, "by_model": qb.summarise(all_results)}
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(meta["models"], indent=1), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
