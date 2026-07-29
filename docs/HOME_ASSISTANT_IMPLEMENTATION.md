# Home Assistant / Smart Home Implementation

Aria's dedicated **Smart Home** product — Home Assistant connectivity, device control, scenes, rooms, favorites, search, profiles, history, and orchestration.

## Product identity

Smart Home owns operator workflows around HA. **Home Assistant** owns devices, entities, automations, Lovelace, and integrations.

Censored and uncensored modes share **one Smart Home engine**. Differences are presentation / permission policy only.

## One pipeline

```
Chat → Voice → Mission Control → Planner → Calendar → Automation → Browser → MCP
  → Smart Home Engine → Permissions → Entity Resolution → Execution
  → Status Bus → Activity → Completion
```

## Architecture

| Layer | Module | Role |
|-------|--------|------|
| Core client | `jarvis.home_assistant` | REST, find/control, scenes, NL routes |
| Lights | `jarvis.ha_light_control` | Brightness, color, daylight |
| Product | `jarvis.home_assistant_product.*` | Home, recovery, rooms, favorites, profiles, bridges |
| HTTP | `/api/homeassistant/*` + `/api/smarthome/product/*` | Core + product APIs |
| UI | Smart Home sidebar + `smarthome_home.js` | Control-first Home |

## Permissions

Tool permission `ha_control` gates toggle/scene/control (ask / allow / never). Product APIs honor the same gate.

## Rooms & favorites

Stored under `DATA_DIR/home_assistant_product/`. Rooms can seed from HA area attributes. Favorites are pin/reorder lists of entity IDs.

## Profiles

Built-ins: Home, Away, Office, Workshop, Night, Vacation, Quiet Hours — favorite rooms/devices, scenes, brightness, confirmation policy.

## Mission Control

`enrich_snapshot` attaches `snap["smarthome"]` with connection, entity count, rooms, favorites, webhook, recovery, deep links.

## Voice / Vision

- Voice Home Mode → `voice_bridge.home_command` → engine (Voice only speaks)
- Vision camera → `vision_bridge.analyze_camera` → `vision_product.engine.analyze` (confirm-gated)

## Planner / Calendar / Automation

Candidate/preview bridges only. HA owns device automations; Aria orchestrates webhooks (`ha_scene`).

## Reliability

- `list_entities` for device_router
- Color NL wired through `parse_control` → `control_entity` / `set_light`
- Aliases + fuzzy + entity filter on find path
- `JARVIS_HA_AUTOSTART` default off (aligned with `service_policy`)
- Setup button uses `haSetupWizardBtn`
- Sunlight `tick_sunlight` on scheduler; `bootstrap_sunlight` on daemon start

## Testing

```bash
.venv/bin/pytest tests/test_home_assistant.py tests/test_ha_*.py tests/test_smarthome_product.py -q
```

## Roadmap

- Optional HA WebSocket (experimental)
- Richer climate UI
- Multi-HA (experimental only)

## Do not build

Second Home Assistant / Lovelace clone, cloud hub, marketplace, separate Home LLM, silent Memory ingestion, auto-buy, always-on cameras.
