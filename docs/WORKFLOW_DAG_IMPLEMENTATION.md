# Workflow DAG / Pipelines Implementation

**Pipelines are a subsystem of Automation — not a separate Workflows product.**

| Concept | Owns |
|---------|------|
| **Automation** | When work runs (rules, schedules, triggers) |
| **Pipelines (DAGs)** | Multi-step *how* (ordered/branching steps) |
| **Skills** | Reusable procedures (single callable units) |
| **Learned workflows** | Mined sequences → optional promote to Pipeline draft |
| **View Paths** | UI navigation macros only |
| **Activity Center** | Durable events |
| **Job Center** | Live execution tracking |
| **Mission Control** | Infrastructure health |

## Architecture

```
Automation Rule (workflow_dag_run)
        │
        ▼
pipelines.engine.run_pipeline
        │
        ├─► actions.execute_action  → Automation Action Registry (+ builtins)
        ├─► runs.record_pipeline_run → durable history
        ├─► jobs.start/update/finish → Job Center (automation queue)
        └─► activity_bridge.publish_run_event → Activity Center payload
```

Core modules (`jarvis/automation/pipelines/`):

| Module | Role |
|--------|------|
| `templates.py` | Built-in templates (honest Morning Routine, Doc Ingest, Evening Wrap) |
| `storage.py` | CRUD, favorites, usage stats, export, anti-spam create |
| `actions.py` | Registry-backed step execution + gated experimental |
| `engine.py` | DAG walk, conditions, retries, timeouts, dry-run, explain |
| `runs.py` | Durable run history (`pipeline_runs.json`) |
| `jobs.py` | Live Job Center bridge |
| `nl.py` | NL → reviewable draft (never auto-save/run) |
| `promote.py` | Learned → DAG draft (never automatic) |
| `canvas.py` | Read-only visualization (not an n8n clone) |

Compatibility: `jarvis/intelligence/workflow_engine.py` delegates to Pipelines.

## Pipeline model

```json
{
  "id": "abc123",
  "name": "Morning Routine",
  "version": 1,
  "entry": "brief",
  "variables": {},
  "tags": ["daily"],
  "steps": [
    {
      "id": "brief",
      "name": "Daily briefing",
      "action": "briefing",
      "params": {},
      "on_success": ["memory"],
      "on_failure": ["memory"],
      "retries": 1,
      "timeout_sec": 60,
      "when": ""
    }
  ]
}
```

Storage: `DATA_DIR/automation_product/workflow_dags/{id}.json`

## Automation integration

- Registry action: `workflow_dag_run` (params: `workflow_id`, optional `variables`)
- Implemented in `automation_engine._default_run`
- Also: `skill_run`, `workflow_learned_run`, `ha_scene`, `journal_log`
- Schedule from Automation Home → Rule Editor with params preserved

## Run lifecycle

1. Queued / Running (Job Center entry)
2. Per-step progress (pct, current_step)
3. Retries / skips (`when`) / timeouts
4. Terminal: `succeeded` | `partial_success` | `failed` | `dry_run` | `cancelled` | `permission_required`
5. Activity event + durable `pipeline_runs.json` + automation `run_history.json`

## Run inspector

UI: Automation → Pipelines → Details / after Run.

Shows step list, filters, expandable logs, variables, success/failure summaries, Job Center + Activity deep links, retry-from-failed.

## Action Registry

Pipeline steps use the **same** Automation Action Registry. No duplicate catalogs.

Builtins (`builtin:log|set|fail|graph_note|health_check`) are pipeline-local helpers only.

Experimental (`agent_step`, `vision_analyze`) require `approve_experimental=true`.

## Pipeline editor

JSON + form steps + read-only canvas tab. **No visual canvas product.** Version bumps on edit.

## CRUD

Create (from template / NL draft / promote), Read, Rename, Delete, Duplicate, Search/Sort/Filter, Favorites, Bulk delete, Export, Version history meta.

Template create **reuses** same template+name to prevent spam.

## History

`DATA_DIR/automation_product/pipeline_runs.json` — survives restart.

## Promotion

Learned workflow → reviewable DAG draft → user Save → optional Schedule → Run. Never auto.

## Natural language drafting

`POST /api/automation/pipelines/nl` → draft  
`POST /api/automation/pipelines/nl/save` requires `confirm=true`

## Chat + Command Palette

Chat: list/explain/run/history pipelines (via `automation_handlers`)  
Palette: `act:pipelines-list`, `act:pipelines-nl`, `act:pipelines-history`

## Experimental features

- **Agent step** — bounded stub, approval + budget required
- **Vision step** — gated stub, approval required
- **Canvas** — visualize existing pipelines only

## APIs (primary)

| Method | Path |
|--------|------|
| GET | `/api/automation/pipelines` |
| POST | `/api/automation/pipelines/from-template` |
| GET/POST/DELETE | `/api/automation/pipelines/{id}` |
| POST | `/api/automation/pipelines/{id}/run` (`dry_run` / `confirm`) |
| GET | `/api/automation/pipelines/{id}/explain` |
| GET | `/api/automation/pipelines/{id}/canvas` |
| GET | `/api/automation/pipeline-runs` |
| GET | `/api/automation/pipeline-runs/{run_id}` |
| POST | `/api/automation/pipelines/nl` |
| POST | `/api/automation/pipelines/promote-learned` |

Legacy intelligence routes still work and delegate to the same engine.

## Testing

```bash
pytest tests/test_workflow_dag_pipelines.py tests/test_intelligence_platform.py -q
```

## Migration notes

- DAG files already live under `automation_product/workflow_dags/` (Automation migration)
- Templates are richer; bootstrap reuses by name
- Morning Routine performs real registry actions (briefing, memory, docs, graph, health)
