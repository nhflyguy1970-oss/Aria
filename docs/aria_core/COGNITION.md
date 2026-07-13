# Aria Core Cognition — Phase 6

**Status:** Active  
**Owner:** `aria_core.cognition` (`aria_core.cognitive_orchestrator`)

## Role

Coordinates which cognitive organs participate in a Cap Bus request.
Does **not** perform Memory / Knowledge / Planning / Reasoning work.

```text
Application → Capability Bus → Cognitive Orchestrator → existing organs
```

## Phase 6 policy

Passthrough: one primary organ per verb (identical to prior Cap Bus behavior).
Other organs are recorded as skipped for observability.

## Events

CognitionStarted · CapabilitySelected · CapabilitySkipped ·  
PlanningRequested · ReasoningRequested · ReferenceRequested ·  
MemoryRequested · KnowledgeRequested · LearningRequested ·  
CognitionCompleted

## Mission Control

**Cognition** tab — pipeline, order, skipped, latency, decision metadata.
No chain-of-thought.
