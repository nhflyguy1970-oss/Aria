# Adding an action to ARIA

Checklist for a new user-facing ability without editing five central files.

## 1. Handler (`jarvis/handlers/`)

Create or extend a handler module:

```python
from jarvis.handlers.registry import register_action
from jarvis.response import ok, err

@register_action("my_action", module="general", description="Short label for /api/actions")
def my_action(assistant, params: dict, message: str) -> dict:
    value = (params.get("key") or message).strip()
    if not value:
        return err("Need a value")
    return ok(f"Done: {value}", module="general")
```

Import side effects: add `from jarvis.handlers import my_module` in `jarvis/handlers/__init__.py` inside `ensure_handlers_loaded()` if you add a new file.

### Queued actions

GPU / long work — register queue metadata only (see `jarvis/handlers/queues.py`) or:

```python
@register_action("my_gpu_task", queue="media", module="image")
def _unused(assistant, params, message):
    raise RuntimeError("queued via media_jobs")
```

Background LLM tasks use `queue="background"`.

## 2. Router (`jarvis/router_table.py`)

Add a declarative rule (preferred for simple patterns):

```python
RouteRule(
    "my_action",
    30,
    "my action",
    lambda m, lower, _s: bool(re.search(r"\bmy trigger\b", lower)),
    params=lambda m: {"key": "parsed"},
),
```

Complex routing can stay in `jarvis/router.py` `_quick_route` or a domain helper (`home_assistant.quick_route_*`).

## 3. Tests

- `tests/test_phase3.py` or a focused `tests/test_my_action.py`
- Route: `route("my trigger phrase", SessionContext())["action"] == "my_action"`
- Handler: mock LLM if needed, `assistant.process("…")`

## 4. UI (optional)

- Chat chips: `/api/suggestions` or static chips in `index.html`
- Dedicated panel: follow `journal.js` or ES module under `gui/static/modules/`

## 5. MCP (optional)

Add tool in `scripts/jarvis-mcp-server.py` and route in `jarvis/jarvis_mcp.py` + `cursor_bridge._DOMAIN_MCP_TOOLS`.

## 6. Events (optional)

```python
from jarvis.events import emit, on

on("job_done", lambda **kw: ...)

emit("my_custom_event", detail="…")
```

Built-in: `job_done`, `memory_updated`, `ha_state_changed`.

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/registry/actions` | Registered handlers + queue metadata |
| `GET /api/registry/router/rules` | Declarative router table |
| `GET /api/actions` | Recent action audit log (unchanged) |
| `GET /api/jobs` | Unified job snapshot |

## Do not edit (unless unavoidable)

- `assistant.py` giant `handlers` dict — new actions use the registry
- Duplicate queue lists — use `register_queue` in `handlers/queues.py`
- `app.js` for job center / GPU strip — use `modules/jobs.mjs`, `modules/health.mjs`

## Version bump

After static changes: bump `jarvis-ui-version` meta, `app.js?v=`, and `JARVIS_UI_VERSION` default in `server.py`. **Reload UI** in the sidebar.
