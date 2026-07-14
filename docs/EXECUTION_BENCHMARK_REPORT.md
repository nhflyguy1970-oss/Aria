# Execution Benchmark Report

**Date:** 2026-07-14T14:03:11
**Hardware fingerprint:** `34c2b99303d77a6c`
**Devices tested:** cpu, nvidia
**Mode:** quick

## Workload winners

| Workload | Model | Hardware | Warm ms | tok/s | Reason |
|----------|-------|----------|---------|-------|--------|
| lightweight | `qwen2.5-coder:1.5b-base` | `nvidia` | 221.4 | 208.93 | Measured winner for lightweight: model=qwen2.5-coder:1.5b-base hardware=nvidia w |
| coding | `deepseek-coder:latest` | `nvidia` | 203.6 | 305.72 | Measured winner for coding: model=deepseek-coder:latest hardware=nvidia warm=203 |
| reasoning | `qwen2.5:7b` | `nvidia` | 886.6 | 66.13 | Measured winner for reasoning: model=qwen2.5:7b hardware=nvidia warm=886.6ms tps |
| vision | `moondream:latest` | `nvidia` | 148.0 | 291.43 | Measured winner for vision: model=moondream:latest hardware=nvidia warm=148.0ms  |
| voice | `None` | `cpu` | None | None | Voice uses Whisper device env / gpu_routing (not Ollama chat) |

## Changes from previous

_No prior policy or no changes._

## Historical context

Prior NLU placement preferred CPU for classifiers (often with invalid 0ms benches). Ollama daemon on this host commonly binds NVIDIA (HIP_VISIBLE_DEVICES=-1). Reference/Runtime/Greeting request classes remain non-LLM by design.

## All measured runs

| Workload | Model | Device | OK | Warm ms | tok/s | Score | Error |
|----------|-------|--------|----|---------|-------|-------|-------|
| lightweight | `qwen2.5-coder:1.5b-base` | `cpu` | True | 642.1 | 24.45 | 593.2 |  |
| lightweight | `qwen2.5-coder:1.5b-base` | `nvidia` | True | 221.4 | 208.93 | 61.4 |  |
| lightweight | `qwen3:1.7b` | `cpu` | True | 3501.9 | 14.56 | 3622.8 |  |
| lightweight | `qwen3:1.7b` | `nvidia` | True | 398.0 | 197.05 | 388.0 |  |
| coding | `deepseek-coder:latest` | `nvidia` | True | 203.6 | 305.72 | 43.6 |  |
| coding | `qwen2.5-coder:1.5b-base` | `nvidia` | True | 244.5 | 201.07 | 84.5 |  |
| reasoning | `deepseek-r1:7b` | `nvidia` | True | 892.3 | 66.11 | 910.1 |  |
| reasoning | `qwen2.5:7b` | `nvidia` | True | 886.6 | 66.13 | 754.3 |  |
| vision | `llava:13b` | `cpu` | True | 15177.1 | 3.24 | 15170.6 |  |
| vision | `llava:13b` | `nvidia` | True | 1230.6 | 42.87 | 1144.9 |  |
| vision | `moondream:latest` | `cpu` | True | 951.6 | 29.09 | 893.4 |  |
| vision | `moondream:latest` | `nvidia` | True | 148.0 | 291.43 | -12.0 |  |
