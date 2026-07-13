# Aria Core Capability Bus — Phase 3

**Status:** Active  
**Package:** `aria_core.capability_bus`  
**Rule:** Capabilities → Aria Core → existing implementation. No organ moves.

## Purpose

The Capability Bus is the nervous system between applications and organs.

```text
Applications  →  Capability Bus verbs  →  Aria Core modules  →  jarvis / aiplatform
```

## Verbs

| Verb | Delegates to |
|------|----------------|
| `remember` | `MemoryStore.add` |
| `recall` | `MemoryStore.search` / `get` |
| `learn` | `learning_governor.propose/commit` |
| `reason` | `aria_core.reasoning.chat` |
| `plan` | `jarvis.agents.coordinator` (status/access) |
| `reference` | `reference_engine.search_reference` |
| `search` | `jarvis.knowledge.search` |
| `infer` | `jarvis.llm.generate_text` |
| `execute_tool` | `handlers.registry.call_action` |
| `schedule` | jobs / handler queues (observe) |
| `observe` | MC `collect_overview` |
| `notify` | MC notifications |
| `diagnose` | `workstation.operations.diagnose` |
| `repair` | `recover_safe` |
| `backup` | hint/status only (Phase 3) |
| `recover` | `recover_safe` |

## Registry & contracts

- Registry: `aria_core.capability_registry`
- Contracts: `aria_core.capability_contracts`
- Docs: [`CAPABILITY_CONTRACTS.md`](CAPABILITY_CONTRACTS.md)

## Mission Control

Tab **Capabilities** loads `get_tab("capabilities")` → `aria_core.capabilities.mission_control_panel()`.

Shows: capability, health, owner, consumers, provider, implementation, dependency graph.

## Applications

Do **not** migrate yet. Future entrypoint:

```python
from aria_core.applications import capability_interface
# or
from aria_core.capabilities import remember, recall, reason
```

## Non-goals

- Moving memory/knowledge/learning/planning/runtime
- Changing Mission Control behavior beyond visibility
- Running backup scripts from the bus (hint only)
