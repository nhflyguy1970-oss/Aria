# Aria Core Reflex Layer — Phase 8

**Status:** Active  
**Owner:** `aria_core.reflex` (`aria_core.reflex_engine`)  
**Position:** Before Capability Bus, Cognitive Orchestrator, and all organs

## Why

Trivial interactions must never consume deep cognition.
Humans have reflexes. Aria does too.

## Flow

```text
User input
  → Reflex Engine (grammar + morphology + syntax features)
      → match?  return handler intent immediately
      → else    escalate to NLU / Cap Bus / Cognition
```

## Design

- Feature extraction via existing NLU structure analyzers (local, no LLM)
- Pattern **catalog** of stem/constraint rules — not a growing router regex list
- Deterministic, explainable, measurable
- Optional local intent model may be added later only if benchmarked faster than cognition

## Categories

social.greeting · social.checkin · social.farewell · social.ack · social.confirm · social.negate  
session.clear · session.interrupt · session.continue · session.repeat  
meta.help · meta.models · briefing.morning · ui.mission_control

## Events

ReflexMatched · ReflexEscalated · ReflexFailed · ReflexLatency

## Mission Control

**Reflex** tab → `aria_core.reflex.mission_control_panel()`

## Latency targets

| Class | Target |
|-------|--------|
| Greetings | <10 ms |
| Confirmations | <10 ms |
| Conversation control | <20 ms |
| UI commands | <50 ms |

## Non-goals

No organ transplants. No Cap Bus participation. No Cognition for matched reflexes.
