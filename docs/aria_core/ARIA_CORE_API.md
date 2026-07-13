# Aria Core API — Phase 2

**Status:** Sovereign API surface (delegation only)  
**Package:** `aria_core` (Aria repository)  
**Rule:** Core API → existing implementation. No organ moves.

## Purpose

Aria Core is the architectural frame around the working machine. Callers should prefer `aria_core.*` so future migrations can change the organ without changing the API.

## Golden rule

Behavior through Core **must equal** behavior through the current implementation.

## Dependency direction (desired)

```text
Interfaces  →  Applications  →  Capabilities  →  Aria Core  →  jarvis / aiplatform
```

Reverse imports into Core from implementations should not be added. Existing cycles outside Core are documented below and deferred.

## Modules

| Module | Owner | Public API (Phase 2/3) | Delegates to | Future owner |
|--------|-------|----------------------|--------------|--------------|
| `aria_core.identity` | aria_core.identity | `profile_name`, `is_uncensored`, `system_prompt`, `identity_snapshot` | `jarvis.config` | same |
| `aria_core.memory` | aria_core.memory | `MemoryStore`, `create_memory_store` | `jarvis.modules.memory` | same |
| `aria_core.knowledge` | aria_core.knowledge | `registry`, `search` | `jarvis.knowledge` | same |
| `aria_core.learning` | aria_core.learning | `propose`, `commit`, `enabled`, `Proposal` | `jarvis.learning_governor` | same |
| `aria_core.reasoning` | aria_core.reasoning | `get_assistant`, `chat` | `jarvis.assistant` | same |
| `aria_core.planning` | aria_core.planning | `coordinator_available`, `get_coordinator` | `jarvis.agents` | same |
| `aria_core.reference` | aria_core.reference | `search_reference` | `jarvis.reference_engine` | same |
| `aria_core.runtime` | aria_core.runtime | `RuntimeClient`, `execution_mode` | `jarvis.runtime_client` | same |
| `aria_core.capabilities` | aria_core.capabilities | Capability Bus verbs + catalog | registry → organs | same |
| `aria_core.interfaces` | aria_core.interfaces | `describe_interfaces` | GUI/CLI/MC pointers | same |
| `aria_core.applications` | aria_core.applications | `get_host_module`, `capability_interface` | `jarvis.application.host` | same |
| `aria_core.platform` | aria_core.platform | `workstation_available`, `platform_snapshot` | `aiplatform.workstation` | same |
| `aria_core.services` | aria_core.services | `list_managed_services` | `jarvis.services` | same |
| `aria_core.operations` | aria_core.operations | `collect_overview`, `collect_mission_control` | `aiplatform.mission_control.aggregator` | same |
| `aria_core.infrastructure` | aria_core.infrastructure | `vram_guard_available` | `jarvis.vram_guard` | same |

## Phase 3 — Capability Bus

Applications should eventually call Capability Bus verbs (`remember`, `recall`, `learn`, …).
See [`CAPABILITY_BUS.md`](CAPABILITY_BUS.md) and [`CAPABILITY_CONTRACTS.md`](CAPABILITY_CONTRACTS.md).

```text
Caller / Application
  → aria_core.capability_bus.<verb>(...)
    → aria_core.<module> or soft-import
      → existing jarvis / aiplatform implementation
```

Mission Control **Capabilities** tab renders `mission_control_panel()` (visibility only).

## Phase 4 — Event Bus

In-process pub/sub circulatory system. See [`EVENT_BUS.md`](EVENT_BUS.md).

```text
Governor / Capability Bus / MC
  → aria_core.event_bus.safe_publish(...)
    → subscribers (Timeline bridge, MC Events tab)
```

Mission Control **Events** tab renders Event Bus live ring, rates, subscribers, publishers.

Full ownership metadata: `aria_core.ownership.OWNERSHIP`.

## Delegation path (example)

```text
Caller
  → aria_core.memory.MemoryStore(...)
    → jarvis.modules.memory.MemoryStore(...)
      → existing JSON/SQLite + Learning Governor passthrough on add
```

```text
Caller
  → aria_core.operations.collect_overview()
    → aiplatform.mission_control.aggregator.collect_overview()
```

## Consumers (Phase 2)

| Consumer | Status |
|----------|--------|
| Compatibility harness / tests | Use Core for ownership checks |
| Mission Control | Unchanged; **prepared** via `aria_core.operations` for future |
| Applications | Unchanged; **prepared** via `aria_core.applications` |
| Daily GUI/CLI | Unchanged (still call jarvis directly) |

## Existing circular / soft-coupling (documented, not fixed)

| Cycle / coupling | Notes |
|------------------|-------|
| MC aggregator soft-imports `jarvis.*` | Pre-existing; Phase 5 target |
| `RuntimeClient` ↔ MC in-process snapshot | Mitigated for confidence; broader cleanup later |
| `jarvis.workstation` ↔ `aiplatform.workstation` | Intentional shim |
| Dual-write memory/knowledge adapters | Intentional until cutover |

## Private vs public

- **Public:** functions exported by each `aria_core.<module>` listed above  
- **Private:** `aria_core._delegate`, ownership internals, audit helpers  

## How to extend safely

1. Add public function on the Core module  
2. Delegate immediately to existing implementation  
3. Update `OWNERSHIP` + this document  
4. Run `scripts/aria_core_compat.sh` (standard + uncensored)  

Do **not** move implementation bodies into `aria_core` in Phase 2.
