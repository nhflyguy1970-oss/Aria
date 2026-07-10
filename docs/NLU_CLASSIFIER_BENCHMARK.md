# NLU Classifier Benchmark

**Selected model:** `qwen2.5:1.5b`  
**Selected device:** `cpu`

Selection criteria: lowest average latency with successful JSON classification on the classifier workload, minimizing disruption to main inference.

Run `python scripts/benchmark_nlu_classifier.py` on the workstation to measure CPU, NVIDIA, and AMD placement with locally available Ollama models. Results are written to `jarvis/data/nlu_placement.json`.

Override with environment variables:

- `JARVIS_NLU_MODEL`
- `JARVIS_NLU_DEVICE`

| Model | Device | Notes |
|-------|--------|-------|
| qwen2.5:1.5b | cpu | Default — keeps GPU free for main chat/inference |
| smollm:360m | cpu | Fastest when available |
| qwen2.5:0.5b | cpu | Minimal memory footprint |

**Why CPU by default:** The NLU classifier is a short JSON-only call (~50–120 tokens). Running it on CPU avoids VRAM contention with the primary inference model and eliminates queueing behind GPU workloads. Re-benchmark after hardware changes; if a secondary AMD GPU is idle, the script may select `amd` when latency is lower without impacting primary inference.
