# Routing Matrix

Permanent production routing policy derived from measured execution benchmarks.
AMD/NVIDIA/CPU are selected only when they win measurements for that workload.

**Benchmark date:** 2026-07-14T14:03:11

| Request class | Capability | Primary model | Fallback model | Primary HW | Fallback HW | Provider | Expected latency | Winner | Policy |
|---------------|------------|---------------|----------------|------------|-------------|----------|------------------|--------|--------|
| classification | classification | `qwen2.5-coder:1.5b-base` | `qwen3:1.7b` | `nvidia` | `nvidia` | ollama | 221.4 | True | benchmark |
| code | code | `deepseek-coder:latest` | `qwen2.5-coder:1.5b-base` | `nvidia` | `nvidia` | ollama | 203.6 | True | benchmark |
| coding | coding | `deepseek-coder:latest` | `qwen2.5-coder:1.5b-base` | `nvidia` | `nvidia` | ollama | 203.6 | True | benchmark |
| documentation | reference | `None` | `qwen3:1.7b` | `cpu` | `nvidia` | local_docs | None | False | non_llm |
| formatting | formatting | `qwen2.5-coder:1.5b-base` | `qwen3:1.7b` | `nvidia` | `nvidia` | ollama | 221.4 | True | benchmark |
| greeting | greeting | `None` | `qwen3:1.7b` | `cpu` | `nvidia` | none | None | False | non_llm |
| intent | intent | `qwen2.5-coder:1.5b-base` | `qwen3:1.7b` | `nvidia` | `nvidia` | ollama | 221.4 | True | benchmark |
| learning | learning | `qwen2.5-coder:1.5b-base` | `qwen3:1.7b` | `nvidia` | `nvidia` | ollama | 221.4 | True | benchmark |
| memory | memory | `qwen2.5-coder:1.5b-base` | `qwen3:1.7b` | `nvidia` | `nvidia` | ollama | 221.4 | True | benchmark |

### Memory operations (non-LLM path)

| User phrasing | Action | Handler | HW | Notes |
|---------------|--------|---------|----|-------|
| Remember that… | `remember` | MemoryEngine | cpu | Write user fact/preference |
| Actually… / Update… / Change… | `memory_correct` | MemoryEngine | cpu | Supersede prior topic fact |
| Forget… | `memory_forget` | MemoryEngine | cpu | Precise topic delete |
| What is my…? | `memory_search` | MemoryEngine | cpu | Spoken answer (fact mode) |
| What do you know about me? | `memory_about_user` | MemoryEngine | cpu | Evolving summary |
| What preferences…? | `memory_about_user` | MemoryEngine | cpu | Preferences only |
| Search memory for… | `memory_search` | MemoryEngine | cpu | Ranked list; journal demoted |

Canonical behavior: [MEMORY_RETRIEVAL_BEHAVIOR.md](MEMORY_RETRIEVAL_BEHAVIOR.md).
| planning | planning | `qwen2.5:7b` | `deepseek-r1:7b` | `nvidia` | `nvidia` | ollama | 886.6 | True | benchmark |
| reasoning | reasoning | `qwen2.5:7b` | `deepseek-r1:7b` | `nvidia` | `nvidia` | ollama | 886.6 | True | benchmark |
| reference | reference | `None` | `qwen3:1.7b` | `cpu` | `nvidia` | local_docs | None | False | non_llm |
| runtime | runtime | `None` | `qwen3:1.7b` | `cpu` | `nvidia` | mission_control | None | False | non_llm |
| search_reference | reference | `None` | `qwen3:1.7b` | `cpu` | `nvidia` | local_docs | None | False | non_llm |
| vision | vision | `moondream:latest` | `moondream:latest` | `nvidia` | `cpu` | ollama | 148.0 | True | benchmark |
| voice | voice | `None` | `None` | `cpu` | `cpu` | local | None | True | benchmark |
