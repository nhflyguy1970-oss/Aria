# Aria Core Learning — Phase 5

**Status:** Active  
**Owner:** `aria_core.learning` (`aria_core.learning_manager`)  
**Shim:** `jarvis.learning_governor` (compat only)

## Behavior (unchanged)

```text
propose → immediate commit → apply() → Memory/NLU writers
```

No filtering. No delayed commit. Bit-identical passthrough.

## Public API

| API | Role |
|-----|------|
| `propose_learning` / `propose` | Create proposal |
| `commit_learning` / `commit` | Immediate apply |
| `approve_learning` | Alias of commit (Phase 5) |
| `reject_learning` | Reject without apply |
| `replay_learning` | Re-surface history (no organ rewrite) |
| `learning_history` | History rows |
| `learning_statistics` | Aggregates for MC |

## Events

LearningProposed · LearningAccepted · LearningRejected · LearningCommitted · LearningReplayed · LearningRolledBack

## Mission Control

**Learning** tab → `aria_core.learning.mission_control_panel()`

## Non-goals

Memory / Knowledge / Planning / Runtime migration — **not** this phase.
