# Specialist Team (Multi-Agent) Implementation

**Specialist Teams orchestrate Aria’s existing organs — not a CrewAI/AutoGen clone.**

| Layer | Role |
|-------|------|
| **Chat / Palette** | Propose → confirm → run |
| **Specialist Team** | Ordered/parallel orchestration of organs |
| **Automation** | Optional schedule via approved `agent_step` |
| **Pipelines** | Multi-step DAG execution (separate) |
| **Skills / Registry** | Reusable actions |
| **Activity + Job Center** | Events and live work |

## Architecture

```
propose_team / compose_team
        │
        ▼ (confirm required)
   run_team (jarvis.specialists.engine)
        │
        ├─ budgets + permissions
        ├─ execute.run_specialist (deep organs)
        ├─ scratchpad (durable)
        ├─ synthesizer (final answer)
        ├─ jobs + activity bridges
        └─ history (durable runs)
```

Package: `jarvis/specialists/`

| Module | Purpose |
|--------|---------|
| `catalog.py` | Specialist gallery + deep organ metadata |
| `composer.py` | Heuristic + optional LLM team composition |
| `params.py` | Role-specific parameter synthesis |
| `execute.py` | Deep integrations (CodingAgent, vision, drafts, …) |
| `engine.py` | Unified orchestrator |
| `scratchpad.py` | Durable notes/artifacts/failures |
| `history.py` | Run history |
| `synthesizer.py` | Final coherent answer |
| `budgets.py` | Runtime/step/cost/write gates |
| `jobs.py` / `activity.py` | Job Center + Activity |
| `critic.py` | Single revision loop |
| `parallel.py` | Read-only parallel contract |
| `platform_bridge.py` | Optional AI-Platform advisory bridge |
| `favorites.py` | Favorite / frequent teams |
| `routes.py` | `/api/specialists/*` |

## Unified orchestrator

Legacy stacks are **wrappers**:

- `jarvis.intelligence.multi_agent.run_multi_agent` → `run_team`
- `jarvis.agents.coordinator.run_agent_chain` → `run_team`

One terminology: **Specialist Team run**.

## Specialist model

Deep mappings (examples):

| Specialist | Organ |
|------------|-------|
| coder | CodingAgent (fallback `coding_read`) |
| vision | `describe_image` / `ocr_image` (never `vision_describe`) |
| writer | Draft generation (never auto `journal_log`) |
| researcher | unified + document + memory search |
| planner | Structured plan **proposal** (no silent task spam) |
| documents / graph / memory / home / operations | Real APIs |

## Execution lifecycle

1. Propose team (Chat/UI/API) — **no side effects**
2. User confirms
3. Job queued/running + Activity event
4. Specialists execute (serial, or parallel readers)
5. Optional single critic loop
6. Final synthesis
7. Durable history + scratchpad
8. Terminal status: `succeeded` | `partial_success` | `failed` | `cancelled` | `permission_required` | `timeout`

### Honest semantics

- Missing actions → **failure**, not “recovered”
- Checkpointed jobs → **full re-run** after restart (`resumable: false`)
- Aggregate `ok` only for success/partial_success
- Write specialists need `approve_writes`

## APIs

| Method | Path |
|--------|------|
| GET | `/api/specialists/gallery` |
| POST | `/api/specialists/propose` |
| POST | `/api/specialists/run` (`confirm=true`) |
| GET | `/api/specialists/runs` |
| GET | `/api/specialists/runs/{id}` |
| GET/POST | `/api/specialists/jobs`, `.../cancel` |
| POST | `/api/specialists/favorites` |
| POST | `/api/specialists/platform-bridge` |

Legacy: `/api/intelligence/agents/run`, `/api/agents/chain`, `/api/agent-jobs/*`

## Chat + Command Palette

- “Run specialists for …”, “Research this…”, “confirm specialists”
- Palette: `act:specialists-propose|gallery|history`

## Run Inspector

Automation Home → Specialist Teams → History / after run.

Shows goal, team, steps, synthesis, scratchpad, export, Job/Activity links.

## Automation integration

Experimental registry action `agent_step` runs an **approved Specialist Team** (not a stub).

## Budgets

`max_specialists`, `max_steps`, `max_runtime_sec`, `max_model_cost_units`, write approval, parallel/critic flags.

## Experimental

- Parallel **read-only** specialists
- Single critic revision (one pass)
- Optional AI-Platform coordinate bridge (advisory only)

## Testing

```bash
.venv/bin/pytest tests/test_specialists.py tests/test_agents.py -q
```

## Migration

1. Prefer `/api/specialists/*` and Chat propose→confirm
2. Old APIs remain as compatibility wrappers
3. UI language: “Specialist Team”, not “multi-agent swarm”
