# ARIA local model benchmark — October 2026

Correctness on ARIA's own workloads first; speed and memory second. Raw
results: `/home/jeff/aria-assessments/2026-10-08-phase3-benchmark/`
(`results.jsonl`, `summary.json`, `hardware.json`). Harness:
`scripts/benchmark_local_models.py`; tasks and scorers:
`jarvis/inference/quality_benchmark.py` (unit-tested).

## Conditions

* ARIA's Ollama 0.34.4 on the RTX 3060 12 GB (CUDA); one model resident at a
  time, unloaded after each. Fly Tying Reference's endpoints were only polled
  (idle throughout) and never used. The RX 7600 was **not** benchmarked: its
  only Ollama service belongs to Fly Tying Reference.
* temperature 0, seed 42, num_ctx 4096; thinking disabled where the model
  allows it (deepseek-r1 always thinks, so it got a larger output budget).
* 52 tasks: reasoning 10, JSON routing 10, native tool routing 10, memory 6,
  evidence 6, coding 6 (hidden unit tests run in an isolated interpreter),
  vision 4. Scored by code, never by another model.
* Latency is p50 wall time over short-answer tasks with the model warm;
  samples disturbed by external model reloads (see "Measurement notes") are
  excluded. Cold load is the first request's load time.

## Results (passed / total)

| Model | Reason | JSON route | Tool route | Memory | Evidence | Code | Vision | p50 ms | tok/s | VRAM MiB | Cold load s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **gemma4:12b** (current conversation) | 8/10 | 10/10 | 9/10 | 6/6 | 6/6 | 6/6 | 4/4 | 413 | 42 | 8617 | 40 |
| qwen3.5:9b | 7/10 | 9/10 | 9/10 | 6/6 | 6/6 | 6/6 | 4/4 | 303 | 59 | 5235 | 32 |
| qwen3:8b | 8/10 | 9/10 | 1/10 | 5/6 | 6/6 | 5/6 | – | 154 | 64 | 5995 | 25 |
| qwen3:14b | 7/10 | 10/10 | 0/10 | 6/6 | 6/6 | 5/6 | – | 256 | 39 | 9839 | 43 |
| **deepseek-r1:14b** (current reasoning) | 9/10 | – | – | 6/6 | 6/6 | – | – | 8964 | 35 | 9799 | 27 |
| ministral-3:8b | 6/10 | 10/10 | 9/10 | 6/6 | 6/6 | – | 4/4 | 271 | 64 | 6037 | 35 |
| granite4.2:8b | 8/10 | 8/10 | 8/10 | 6/6 | 6/6 | – | – | 181 | 62 | 6362 | 26 |
| **qwen2.5:7b** (current research) | 7/10 | 10/10 | 8/10 | 6/6 | 6/6 | – | – | 128 | 75 | 4888 | 23 |
| qwen3.5:4b | 8/10 | 10/10 | 9/10 | 5/6 | 6/6 | – | 4/4 | 210 | 92 | 2983 | 30 |
| qwen3:4b-instruct-2507 | 8/10 | 10/10 | 8/10 | 6/6 | 5/6 | – | – | 109 | 107 | 3685 | 23 |
| granite4.2:3b | 9/10 | 7/10 | 8/10 | 5/6 | 6/6 | – | – | 184 | 116 | 2772 | 19 |
| **qwen3:1.7b** (current fast chat) | 9/10 | 9/10 | 0/10 | 5/6 | 6/6 | – | – | 57 | 207 | 2123 | 25 |
| **qwen2.5-coder:1.5b-base** (current router / tool calling / summarization) | – | **0/10** | **unsupported** | 1/6 | – | – | – | 328 | 204 | 1289 | 21 |
| **qwen2.5-coder:14b** (current coder) | – | 10/10 | – | – | – | 6/6 | – | 312 | 38 | 9799 | 29 |
| qwen2.5-coder:7b | – | 10/10 | – | – | – | 6/6 | – | 135 | 75 | 4888 | 24 |
| **qwen2.5vl:7b** (current vision) | – | – | – | – | – | – | 4/4 | – | 127 | 5592 | 28 |
| qwen3-vl:4b-instruct | – | – | – | – | – | – | 4/4 | – | 172 | 3364 | 25 |
| llama3.2-vision:11b | – | – | – | – | – | – | **cannot load** | – | – | – | – |

## Findings

1. **The router role is broken today.** `qwen2.5-coder:1.5b-base` — the model
   behind `router`, `tool_calling` and `summarization` — is a base completion
   model: 0/10 on JSON routing (it continues the user's text instead of
   answering), no tool-calling capability (Ollama reports none; every
   tool-router call fails and falls back), 1/6 on memory-grounded answers.
   ARIA's deterministic rules have been carrying routing.
2. **gemma4:12b is a strong, well-rounded default**: best or tied on every
   category, including vision and coding, at 0.4 s p50. No measured reason to
   replace it.
3. **qwen3 (8B/14B) cannot be trusted with native tool calls here** — with
   thinking disabled they mostly return neither text nor a tool call
   (0–1/10). qwen3.5 and ministral-3 do not have this problem.
4. **"10 days after Thursday"** defeated 10 of 12 models (only gemma4 and
   deepseek-r1 answered Sunday) — date arithmetic should stay deterministic in
   ARIA rather than delegated to a model.
5. **The coding suite is too easy to separate the coders** (four models at
   6/6). It confirms competence, not a ranking.
6. **llama3.2-vision:11b is installed but unusable** with this Ollama
   (`unknown model architecture: 'mllama'`).
7. **Model swaps cost 20–43 s** (cold load from disk). With one 12 GB card, a
   router or helper that does not fit beside the main model is reloaded on
   every turn; residency matters as much as speed.

## Recommendations (none applied — production defaults unchanged)

| Role | Now | Recommendation | Evidence / condition |
|---|---|---|---|
| conversation, general, planning | gemma4:12b | **Keep** | Top or tied everywhere. |
| reasoning (deep) | deepseek-r1:14b | **Keep** for explicit deep reasoning | 9/10, but 9 s p50 and 9.8 GB: not for routine turns. |
| router, summarization | qwen2.5-coder:1.5b-base | **Change → qwen3:1.7b** (approval needed) | 9/10 JSON routing vs 0/10; 2.1 GB fits beside gemma4 (≈10.7 of 12 GB), so no per-turn reload; 57 ms. |
| tool_calling (native) | qwen2.5-coder:1.5b-base | **Change → qwen3.5:4b** only if it can stay resident (e.g. a second GPU worker); otherwise route via JSON with qwen3:1.7b | 9/10 native tools; 3.0 GB does not fit beside gemma4 on the 3060. |
| coder | qwen2.5-coder:14b | **Keep**; evaluate qwen2.5-coder:7b on a harder suite | Tied 6/6; 7B is half the VRAM and 2× faster. |
| research | qwen2.5:7b | **Keep** | 10/10 routing, 6/6 evidence and memory. |
| vision | qwen2.5vl:7b | **Keep for now**; consider gemma4:12b (already resident) or qwen3-vl:4b after a harder image suite | All 4/4 on simple images; using the resident gemma4 avoids a 28 s swap. |
| fast_chat | qwen3:1.7b | **Keep** | 207 tok/s, 9/10 reasoning. |
| — | llama3.2-vision:11b | Exclude from routing | Fails to load. |

The RX 7600 (Vulkan) is the natural home for a resident 3–4 B helper
(qwen3.5:4b ≈ 3 GB) — the assessment's Phase 6 — but that needs a dedicated
ARIA endpoint and an ownership decision; Fly Tying Reference owns the only
service on it today.

## Measurement notes

* Early in the run, unmocked tests from a concurrent test-suite run sent real
  requests to the production Ollama with short timeouts; each aborted a
  gemma4 load and forced ~40 s reloads. Accuracy was unaffected; the affected
  latency samples (load > 5 s) are excluded above. The tests were stopped
  during the benchmark; the offending test is identified in the Phase 3 report.
* A first pass skipped most models because Ollama unloads asynchronously; the
  harness now waits for the unload to complete. All models were then measured.
* Small corpus, single seed: differences of one task are not significant.
