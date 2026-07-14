# Engineering note — Execution pipeline verification (P1)

**Problem ID:** `exec-routing-2026-07-14`  
**Date:** 2026-07-14  
**Mode:** Daily Use (architecture frozen)

## Observed symptom

`Show me the Docker Compose documentation.` completed correctly with high CPU and little GPU activity. That path is Reference Engine (extractive local docs) — non-LLM by design. The open question was whether *lightweight chat* still preferred AMD historically.

## Root cause (measured)

1. **Reference/Runtime/Greeting do not use chat models.** High CPU is document scoring / aggregation, not LLM GPU work.
2. **Benchmark-driven policy existed but was unwired.** `execution_policy` / `execution_benchmark` never fed the gateway hot path; personalization/`JARVIS_GPU_PREFER` heuristics won instead.
3. **Lightweight discovery false positives.** Size hint `"4b"` matched `"14b"`, so huge models polluted lightweight benches.
4. **Current Ollama is CUDA-bound.** AMD ROCm is present on the host, but chat benchmarks compete on **CPU vs NVIDIA**; AMD is included when `JARVIS_GPU_PREFER=amd|both`.

## Measured winners (2026-07-14T14:03:11, quick)

| Workload | Model | Hardware | Warm ms | tok/s |
|----------|-------|----------|---------|-------|
| lightweight | qwen2.5-coder:1.5b-base | nvidia | 221 | 209 |
| coding | deepseek-coder:latest | nvidia | 204 | 306 |
| reasoning | qwen2.5:7b | nvidia | 887 | 66 |
| vision | moondream:latest | nvidia | 148 | 291 |
| voice | (Whisper / env) | cpu | — | — |

NVIDIA beat CPU on every Ollama workload tested. AMD was not a measurable chat device under the running Ollama binding — **not** a hardcoded loss.

## Fix

- Wire `apply_policy_to_route` into `gateway.chat_with_usage` / `stream_chat` with device options.
- `select_route(..., lock_model=True)` so personalization/low-VRAM cannot replace benchmark winners.
- Mission Control Inference panel shows winners + request classes.
- Conversation Trace records `execution` metadata (no CoT).
- Permanent `docs/ROUTING_MATRIX.md` + `docs/EXECUTION_BENCHMARK_REPORT.md`.

## Regression

`tests/test_execution_routing.py` — discovery, policy, gateway lock, Trace execution, matrix coverage.
