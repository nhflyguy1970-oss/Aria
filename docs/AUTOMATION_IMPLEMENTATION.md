# Automation Implementation

## Executive Summary

Automation is Aria’s **orchestration layer** for the AI Operating System.

It schedules and coordinates Skills, Rules, Workflows, local services, and external providers (Home Assistant) — without becoming Job Center, Activity Center, Mission Control, Zapier, or a View Path recorder.

| Concept | Owns |
|---------|------|
| **Automation** | Schedules and orchestrates work |
| **Skills** | Reusable procedures |
| **Rules** | Trigger → Action logic |
| **Workflows** | Multi-step pipelines (DAG + learned) |
| **View Paths** | UI navigation shortcuts only |
| **Job Center** | Live execution tracking |
| **Activity Center** | Durable events |
| **Mission Control** | Infrastructure health |
| **Home Assistant** | External automation provider |

## Architecture

```
Automation Home (UI)
        │
        ▼
 /api/automation/*  (product façade)
        │
 ┌──────┼──────────────┬────────────────┬─────────────┐
 ▼      ▼              ▼                ▼             ▼
rules  history     action registry   suggestions   webhook
engine  runs         catalog          learning      inbound
        │
        ├──► Activity Center (publish events)
        ├──► Job Center (long runs — deep-link)
        └──► Mission Control (health — deep-link)
```

### Storage (isolated namespaces)

| Store | Path |
|-------|------|
| Rules | `DATA_DIR/automation_product/rules.json` (+ legacy mirror) |
| Workflow DAGs | `DATA_DIR/automation_product/workflow_dags/` |
| Learned workflows | `DATA_DIR/automation_product/learned_workflows/` |
| Run history | `DATA_DIR/automation_product/run_history.json` |
| Suggestions | `DATA_DIR/automation_product/suggestions.json` |
| Mute list | `DATA_DIR/automation_product/muted.json` |
| View Paths | Browser `AriaUiPrefs.viewPaths` (client-only) |

Migration: `migrate_storage()` splits legacy `DATA_DIR/workflows/` without deleting sources.

## Automation Home

View: **Automation** (`#automationView`), shortcut **Ctrl+Shift+O**.

Shows: summary, rules, recent runs, failures, suggestions, skills, learned workflows, templates/DAGs, webhook health, search, NL draft.

## Honest execution

Statuses: `queued`, `waiting`, `running`, `paused`, `skipped`, `cancelled`, `succeeded`, `failed`, `dry_run`, `partial_success`, `timeout`, `permission_required`.

**Skipped ≠ success. Dry run ≠ executed.**

Every result includes `why`, `what_changed`, `what_did_not`.

## Action Registry

Versioned catalog in `jarvis/automation/registry.py` — permissions, confirmation, duration, activity/job flags, experimental gates (`agent_step`, `vision_analyze`, `browser_read`).

## Learning pipeline

Observe → Suggest → Explain → Preview → Dry Run → User Approval → Enable.

**Never auto-enable.** Scan creates suggestions only.

## Rule model

Kinds: interval, cron, watch/file/folder, planner, calendar, memory, documents, connections, providers, ha.

Editor supports preview, dry run, enable/disable, mute, export/import, version bump on save.

## Integrations

- Activity: `activity_bridge.publish_run_event`
- Dashboard: Run / Dry run on skills & learned workflows
- Command Palette: Automation Home, pause/resume, webhook, View Paths
- Chat: `automation_home`, pause/resume/failures + early router parity with skills/workflows
- HA webhook: header-only secret; docs corrected

## Accessibility

Automation Home uses labelled regions, live status, keyboard shortcuts, focusable panels. Rule editor uses native labels.

## Testing

`tests/test_automation_product.py` — execution honesty, migration isolation, registry, home snapshot, NL draft, suggestions, API wiring.

## Roadmap

- Richer cron (`*/5`)
- inotify watches
- Visual DAG editor (deferred — not Zapier)
- Budgeted agent steps behind approvals
