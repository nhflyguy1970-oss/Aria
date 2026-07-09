# Architecture Boundaries

Aria is an **application**. AI Platform is the **host**. They are separate repositories and separate releases.

## Standalone (default capability)

Aria must always work without AI Platform:

```bash
./aria install
./aria start
./aria doctor
./aria acceptance
```

- Desktop icon: **Aria** → `./scripts/launch-jarvis.sh`
- Configuration: `data/jarvis.env`
- Workstation implementation: `jarvis/application/standalone/workstation_impl/`

## Platform attached (optional)

When `aiplatform` is installed on the same machine:

- `./workstation` (or `scripts/workstation.sh`) runs the **platform** CLI
- `jarvis.workstation` shims delegate to `aiplatform.workstation`
- `jarvis/application/host.py` implements `ApplicationHost` and registers Aria extensions
- Desktop icon: **AI Workstation** when platform is detected (`install-desktop-shortcuts.sh`)

## What stays in Aria

Application behavior only: conversation, memory, GUI, tray, voice, engineering, briefing, smart home, journal, and Aria-specific acceptance probes.

## What moved to AI Platform

Generic workstation lifecycle, infrastructure registry, integration probes, inventory, hardware, repair framework, and platform acceptance catalog.

## Compatibility shims

`jarvis/workstation/*.py` re-export standalone (or platform) implementations so existing imports and tests keep working. New code should use:

- `jarvis.application.*` for Aria application layer
- `aiplatform.workstation.*` for platform mode

See AI Platform [ADR-0020](https://github.com/nhflyguy1970-oss/AI-Platform/blob/main/docs/adr/ADR-0020-workstation-ownership.md).
