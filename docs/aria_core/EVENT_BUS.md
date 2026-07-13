# Aria Core Event Bus — Phase 4

**Status:** Active  
**Package:** `aria_core.event_bus`  
**Rule:** Publish events only. No organ moves. In-process only.

## Purpose

The Event Bus is the circulatory system of Aria Core.

```text
Publishers (Governor, Capability Bus, MC)
  → aria_core.event_bus
    → Subscribers (Timeline bridge, MC Events tab, future)
```

## Properties

- In-process only (no broker, no network)
- `safe_publish` never fails callers
- Ring buffer observability (`ARIA_CORE_EVENT_RING`, default 1000)
- Wildcard subscribe (`*`)

## Mission Control

**Events** tab → live events, subscribers, publishers, rates, latency, errors, ring replay, filter/search.

Timeline attaches via `aiplatform.mission_control.event_bus_bridge.attach_timeline_subscriber()`.

## Publishers (Phase 4)

| Source | Events |
|--------|--------|
| Learning Governor | LearningProposed, LearningAccepted, LearningRejected |
| Capability Bus | MemoryCreated, ReferenceLookup, Reasoning*, Plan*, Inference*, Tool*, Repair*, Recovery* |
| Mission Control | ApplicationStarted/Stopped, StartupPhaseChanged |

## Contracts

See [`EVENT_CONTRACTS.md`](EVENT_CONTRACTS.md) and `aria_core.event_contracts`.
