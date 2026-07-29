# Capabilities Implementation

**Product:** Capabilities  
**Package:** `jarvis/capabilities_product/`  
**Operator term:** Capabilities (not “Plugins”)  
**Date:** 2026-07-29

---

## Executive summary

Capabilities is Aria’s **unified management system** for everything that extends Aria. It does **not** replace Voice, Vision, Browser, Fly Tying, Smart Home, Planner, Calendar, Gallery, Coding, Models, Automation, Mission Control, or Knowledge Graph — those remain first-class products. Capabilities **extends** them.

Internally, multiple extension layers remain:

| Layer | Location | Role |
|-------|----------|------|
| Host extensions | `jarvis/extensions/*` + `jarvis/extensibility` | First-party domain packs (chat routes + HTTP) |
| Intelligence SDK | `jarvis/intelligence/plugin_sdk.py` + `data/plugins/` | Local third-party / trusted-local capabilities |
| ACM plugins | `aria_acm/acm/plugins/` | Cognitive in-process hooks |
| AI Platform plugins | `aiplatform/plugins/` (optional) | Platform module lifecycle |

Capabilities is a **facade + policy + UX + contribution wiring** layer. It does **not** merge these systems into one runtime.

---

## Architecture

```
Discovery (all layers)
    → Registry projection
    → Trust evaluation
    → Permission review
    → Validation
    → Enable/Disable policy (persistent)
    → Load (respecting quarantine / lazy)
    → Contribution registration (chat / voice / tools / workflows / automation)
    → Mission Control + Capabilities Home
    → Status / Health / Diagnostics / Activity / Recovery
```

**One engine** for censored and uncensored modes. Differences may only be presentation/policy enforcement — never a duplicated plugin system.

---

## Security model (honest)

- **No OS sandbox** for Capabilities today.
- Manifest `sandbox: true` is **compatibility metadata only** and does **not** isolate code.
- Local capabilities run **in-process** with Aria privileges.
- Safety communication uses **trust levels** + **permission previews** + **default-off for third-party**.

### Trust levels

Built-in · First-party · Trusted Local · Experimental · Untrusted · Disabled · Quarantined · Unknown

### Permissions (human-readable)

Examples: Read memory, Write memory, RAG search, Graph read/write, Filesystem, Network, Voice, Vision, Browser, Home Assistant, Models, Automation, Microphone, Camera.

---

## Lifecycle

- **Built-in / first-party host:** default **enabled**.
- **Third-party / SDK:** default **disabled**.
- **Enable / Disable:** persisted under `DATA_DIR/capabilities_product/policy.json`.
- **Host disable:** skipped on load; may require restart for full unload.
- **SDK disable:** contributions unregistered; load skipped.
- **Quarantine:** repeated failures auto-quarantine until acknowledged.
- **Hot reload:** trusted local SDK only.
- **Lazy load:** policy `lazy` defers heavy host/SDK load.

---

## Contributions

Trusted manifests may declare:

```json
"contributions": {
  "actions": [{"name": "…", "patterns": ["…"], "reply": "…"}],
  "tools": [{"name": "…", "description": "…"}],
  "voice_intents": [{"phrase": "…", "action": "…"}],
  "workflow_steps": [],
  "automation_actions": []
}
```

Registration wires chat actions + router rules and exposes tool/voice/workflow/automation lists to bridges.

---

## Operator guide

1. Open **Capabilities** (System sidebar, view tab, Mission Control card, or command palette `Open Capabilities Home`).
2. Search / filter by layer, category, trust.
3. Select a capability → review **risk**, **permissions**, **isolation note**.
4. Enable only if you accept in-process execution.
5. Use Recovery / Diagnostics when loads fail or items quarantine.

Scaffold:

```bash
python main.py capability new my_helper --description "Local helper"
# or: aria capability new my_helper   (via main.py passthrough)
```

Created capabilities are **disabled** until reviewed.

---

## Developer guide

### Host extension (first-party)

Keep using `jarvis/extensions/<name>/extension.py` exporting `EXTENSION`. Do not rewrite into the SDK solely for cosmetics. Register actions with `extension=` when applicable.

### Local capability (SDK)

Place under `data/plugins/<id>/`:

- `aria_plugin.json`
- entry module (`plugin.py`)
- optional `README.md`, `tests/`

Use `PluginContext.require(...)` before privileged helpers.

### Registry API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/registry/extensions` | Host extensions (compat + policy) |
| GET | `/api/capabilities/product` | Product status |
| GET | `/api/capabilities/product/home` | Capabilities Home payload |
| GET | `/api/capabilities/product/registry` | Unified registry |
| POST | `/api/capabilities/product/enable` | Enable + optional load |
| POST | `/api/capabilities/product/disable` | Disable |
| POST | `/api/capabilities/product/load` | Load one or all enabled |
| POST | `/api/capabilities/product/hot-reload` | Trusted local hot reload |
| GET | `/api/capabilities/product/diagnostics` | Diagnostics |
| GET | `/api/capabilities/product/recovery` | Recovery |
| GET | `/api/capabilities/product/mission` | Mission Control panel |

---

## Mission Control

Snapshot key: `capabilities` — counts, failed, disabled, trust summary, recovery, diagnostics links.

---

## Experimental

Research/prototype only (Capabilities Home → Experimental):

- Process isolation / WASM / seccomp — **not available**
- Signed local bundles — research
- MCP export descriptors — available (export only)
- NL stub generator — writes **disabled** experimental stubs only (never auto-installs)

**Do not build:** public marketplace, cloud store, auto AI install, duplicate product engines.

---

## Testing

```bash
venv/bin/pytest tests/test_capabilities_product.py tests/test_extensions.py tests/test_intelligence_platform.py -q
```

---

## Roadmap

1. Stronger isolation (process/WASM) when research completes  
2. Signed local bundles (still no public marketplace)  
3. Deeper MCP bidirectional bridge under explicit trust  
4. Lazy-load graphs for heavy first-party packs  

---

## Package map

`jarvis/capabilities_product/` — terminology, policy, settings, models, adapters, registry, loader, contributions, status_bus, health, history, engine, api, mission_bridge, bridges, scaffold, experimental.
