# Mission Control Implementation

## Philosophy

**Mission Control** is the Infrastructure Health Console for the Aria AI Operating System.

It answers: *Is the platform healthy enough to operate?*

It does **not** answer: *What work is running?* (Job Center) or *What durable events need attention?* (Activity Center).

| Owns | Does not own |
|------|----------------|
| Infrastructure health | Execution |
| Provider health | Scheduling |
| Runtime status | Durable events |
| Hardware | Chat |
| Recovery (approved) | Automation orchestration |
| Routing / performance | Workflow editing |
| Connection diagnostics | Autonomous repairs |
| Operational guidance | Job / Activity product UX |

**Never auto-remediate.** Every repair or inference mutation requires operator confirmation and is audited.

## Architecture

```
AI Platform Mission Control aggregator  ← source of truth for snapshots
        ↑
jarvis/mission_control.py               ← thin collect + enrich
        ↑
jarvis/mission_control_ops/             ← Aria operator surfaces
  health_brief.py
  predictive.py
  activity_bridge.py
  automation_gate.py
  inference_actions.py
  verification.py
  enrich.py
        ↑
GUI: mission_control.js + mission_control_ux.js
APIs: /api/mission-control*
```

Compatibility aliases: view id `workstation` remains; `mission` aliases to it. APIs `/api/workstation*` remain for lifecycle.

## Health lifecycle

1. Collect Platform snapshot  
2. Enrich with health brief, advisor action cards, predictive warnings, platform link, sparkline series  
3. Correlate critical issues → Activity-shaped events (deduped)  
4. Overview displays Health Brief + primary CTA  
5. Operator may approve an action (confirm required)  
6. Optional post-repair verification publishes to Activity  

## Advisor → approved actions

Recommendations become action cards:

- Warm Model / Recover Runtime / Reconnect Platform (confirm + execute)
- Open Inference / Recovery / Job Center / Activity (navigate)
- Create Activity Alert (confirm)

## Queue Snapshot & Operations Event Log

| Tab id | UI label | Product boundary |
|--------|----------|------------------|
| `jobs` | Queue Snapshot | Read-only queue health — deep link **Open Job Center** |
| `activity` | Operations Event Log | MC ops stream — deep link **Open Activity Center** |

These tabs never replace Job Center or Activity Center.

## Progressive disclosure

- **Primary:** Overview, Routing, Performance, Recovery, Connection  
- **Advanced:** Hardware, Inference, Memory, Knowledge, Databases, Settings, Timeline, Release, Applications, Queue Snapshot, Operations Event Log, Intent Analytics  
- **Experimental:** Sessions / Diagnostics / Endurance (Platform cognitive, read-only, with Platform MC link)

Groups collapse; state persists in `AriaUiPrefs.missionControl`.

## Accessibility

- `role="tablist"` / `role="tab"` / `role="tabpanel"`
- `aria-selected`, `aria-controls`, roving `tabindex`
- Arrow keys / Home / End
- Live region for tab and health announcements
- Severity classes for contrast hierarchy

## Shortcut

**Ctrl+Shift+M** opens Mission Control. Mini chat moved to **Ctrl+Shift+K**.

Shown in palette, shortcuts modal, toolbar, and help.

## Persistence

Remembered across sessions: selected tab, advanced/experimental group expansion, routing filter/search (via prefs).

## Safe inference actions

`POST /api/mission-control/inference/action` with `confirmed: true`:

- warm_model, switch_model, reload_provider, unload_model, reconnect  

Audit log: `DATA_DIR/mission_control/inference_audit.jsonl`.

## Performance mini-charts

Overview and Performance tabs render sparklines from rolling series under `DATA_DIR/mission_control/series/`.

## Automation health gate

Rules may set `params.health_gate`:

| Mode | Behavior when MC unhealthy |
|------|----------------------------|
| `off` | Allow |
| `warn` | Allow + warning |
| `delay` / `skip` | Skip run |
| `pause` | Cancel |
| `auto` (default) | warn if degraded; skip if critical |

Wired in `jarvis.intelligence.automation_engine.run_rule`.

## Platform Mission Control link

When advanced labs exist only on Platform, Aria shows **Open Platform Mission Control** with an honest explanation — never silently hide capabilities.

## Activity correlation

Critical health → deduped events with severity, subsystem, suggested fix, and `fix: mc:<tab>` deep links into Mission Control.

## SSE

`GET /api/mission-control/stream` emits `event: health` every ~8s. Polling remains the primary refresh path.

## Testing

- `tests/test_mission_control.py` — aggregator shim  
- `tests/test_mission_control_ops.py` — brief, predictive, gate, inference confirm, correlation, enrich, verify  
- `tests/test_mission_control_integration.py` — wiring  

## Migration

| Old UI term | New |
|-------------|-----|
| Console / Workstation (product name) | Mission Control |
| Jobs tab | Queue Snapshot |
| Activity tab | Operations Event Log |
| Ctrl+Shift+M mini chat | Ctrl+Shift+K |
| view `mission` | alias → `workstation` |

Internal ids (`workstation`, `jobs`, `activity`) kept for compatibility.

## Roadmap

- Richer incremental tab refresh (per-tab ETags)
- Deeper Platform cognitive read models when aggregator exposes them
- Optional operator policy packs for inference permissions

## Design checklist

Every change must reinforce Mission Control as the health console, avoid Job/Activity overlap, improve operator efficiency and safe remediation, and strengthen trust in the AI Operating System.
