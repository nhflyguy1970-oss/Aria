# Mission Control — ACM Cognitive Dashboard

**Date:** 2026-07-15  
**Decision:** A010  
**Payload owner:** `aria_core.memory_manager.mission_control_panel` → `acm_bridge.acm_dashboard`

## Intent

Keep Mission Control layout where practical. Replace the underlying cognitive model.
The Memory tab becomes an **ACM Cognitive Dashboard** — exposes cognition, never
implementation details of legacy stores.

## Payload (authoritative PRIMARY)

| Field | Meaning |
|-------|---------|
| `title` | `ACM Cognitive Dashboard` |
| `authoritative` | `acm` |
| `identity` | who_am_i summary + confidence |
| `experiences` / `concepts` / `associations` / `goals` | organ counts |
| `organs` | identity, remembering, learning, reflection, … |
| `dispatch` | last intent / primary organ / termination |
| `confidence` / `uncertainty` / `provenance` | cognitive policies + last status |
| `memory_health` / `cognitive_health` | ACM reachability / flags |
| `cognitive_activity` / `organ_activity` | encode/recall/cool/revise counters |
| `recent_cognitive_events` | recent experience summaries (ids + short text) |
| `reconstruction_metrics` / `memory_growth` | growth & recall metrics |
| Compatibility | `entry_count`, `statistics`, `counters`, `health` for existing UI |

`legacy_disconnected: true` under PRIMARY.

## ROLLBACK

When `ARIA_ACM_ROLLBACK=1`, panel returns the legacy operational view titled
`Aria Core Memory (ROLLBACK)` for emergency only.

## UI host note

AI-Platform Mission Control markup may still label the tab “Memory”. Aria’s
payload is ACM-native; Platform label polish is out of Aria-only scope unless
requested.
