"""Local capability SDK — manifests, permissions, load hooks (operator term: Capabilities).

Honest security note: code loads in-process with Aria. The historical ``sandbox`` manifest
field is retained for compatibility but does **not** enable OS isolation.
"""

from __future__ import annotations

import importlib
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR, PROJECT_ROOT

log = logging.getLogger("jarvis.intelligence.plugins")

PLUGIN_DIR = DATA_DIR / "plugins"
MANIFEST_NAME = "aria_plugin.json"

ALLOWED_PERMISSIONS = frozenset(
    {
        "memory.read",
        "memory.write",
        "rag.search",
        "graph.read",
        "graph.write",
        "automation.manage",
        "workflow.run",
        "http.egress",
        "fs.read",
        "fs.write",
        "tools.execute",
        "voice.use",
        "vision.use",
        "browser.use",
        "ha.control",
        "models.use",
        "microphone",
        "camera",
    }
)


@dataclass
class PluginManifest:
    id: str
    name: str
    version: str = "0.1.0"
    description: str = ""
    entry: str = ""  # module:attr
    permissions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    sandbox: bool = False  # compatibility only — does NOT isolate
    category: str = "Utilities"
    author: str = ""
    tags: list[str] = field(default_factory=list)
    experimental: bool = False
    contributions: dict[str, Any] = field(default_factory=dict)
    settings_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadedPlugin:
    manifest: PluginManifest
    path: Path
    module: Any | None = None
    error: str = ""


_loaded: dict[str, LoadedPlugin] = {}


def discover_plugin_dirs() -> list[Path]:
    roots = [PLUGIN_DIR, PROJECT_ROOT / "plugins"]
    found: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / MANIFEST_NAME).is_file():
                found.append(child)
    return found


def read_manifest(path: Path) -> PluginManifest:
    data = json.loads((path / MANIFEST_NAME).read_text(encoding="utf-8"))
    perms = [p for p in (data.get("permissions") or []) if p in ALLOWED_PERMISSIONS]
    return PluginManifest(
        id=str(data.get("id") or path.name),
        name=str(data.get("name") or path.name),
        version=str(data.get("version") or "0.1.0"),
        description=str(data.get("description") or ""),
        entry=str(data.get("entry") or ""),
        permissions=perms,
        dependencies=list(data.get("dependencies") or []),
        sandbox=bool(data.get("sandbox", False)),
        category=str(data.get("category") or "Utilities"),
        author=str(data.get("author") or ""),
        tags=list(data.get("tags") or []),
        experimental=bool(data.get("experimental", False)),
        contributions=dict(data.get("contributions") or {}) if isinstance(data.get("contributions"), dict) else {},
        settings_schema=dict(data.get("settings_schema") or {}) if isinstance(data.get("settings_schema"), dict) else {},
    )


def validate_manifest(manifest: PluginManifest) -> list[str]:
    errors: list[str] = []
    if not manifest.id:
        errors.append("missing id")
    if not manifest.entry or ":" not in manifest.entry:
        errors.append("entry must be module:attr")
    bad = [p for p in manifest.permissions if p not in ALLOWED_PERMISSIONS]
    if bad:
        errors.append(f"unknown permissions: {bad}")
    return errors


class PluginPermissionError(PermissionError):
    pass


class PluginContext:
    """Capability-gated context passed to local capabilities (SDK plugins)."""

    def __init__(self, manifest: PluginManifest) -> None:
        self.manifest = manifest
        self.permissions = set(manifest.permissions)
        self.isolation = "none"
        self.sandbox_enforced = False

    def require(self, perm: str) -> None:
        if perm not in self.permissions:
            raise PluginPermissionError(f"capability {self.manifest.id} lacks permission {perm}")

    def rag_search(self, query: str, limit: int = 5) -> dict[str, Any]:
        self.require("rag.search")
        from jarvis.intelligence.hybrid_rag import hybrid_search

        return hybrid_search(query, limit=limit)

    def memory_search(self, query: str, limit: int = 5) -> dict[str, Any]:
        self.require("memory.read")
        from jarvis.intelligence.memory_platform import search_memories

        return search_memories(query, limit=limit)

    def memory_write(self, content: str, **kwargs: Any) -> dict[str, Any]:
        self.require("memory.write")
        # Prefer ACM/primary remember when available
        try:
            from jarvis import acm_bridge

            return {"ok": True, "result": acm_bridge.primary_remember(content, **kwargs)}
        except Exception as exc:
            return {"ok": False, "message": str(exc), "hint": "memory.write requires ACM remember path"}

    def graph_search(self, query: str, limit: int = 5) -> dict[str, Any]:
        self.require("graph.read")
        from jarvis.intelligence.knowledge_graph import search_graph

        return search_graph(query, limit=limit)

    def graph_ingest(self, payload: dict[str, Any] | str) -> dict[str, Any]:
        self.require("graph.write")
        from jarvis.intelligence.knowledge_graph import ingest_text

        if isinstance(payload, dict):
            text = str(payload.get("text") or payload.get("content") or "")
            return ingest_text(text, **{k: v for k, v in payload.items() if k not in ("text", "content")})
        return ingest_text(str(payload))

    def run_workflow(self, workflow_id: str, **kwargs: Any) -> dict[str, Any]:
        self.require("workflow.run")
        from jarvis.intelligence.workflow_engine import run_workflow

        return run_workflow(workflow_id, **kwargs)

    def manage_automation(self, action: str, **kwargs: Any) -> dict[str, Any]:
        self.require("automation.manage")
        from jarvis.intelligence import automation_engine

        allowed = {
            "list_rules": automation_engine.list_rules,
            "status": automation_engine.status,
            "set_paused": automation_engine.set_paused,
            "start_engine": automation_engine.start_engine,
            "stop_engine": automation_engine.stop_engine,
            "run_rule": automation_engine.run_rule,
            "delete_rule": automation_engine.delete_rule,
        }
        fn = allowed.get(action)
        if not callable(fn):
            raise PluginPermissionError(f"unknown automation action: {action}")
        return fn(**kwargs)

    def http_get(self, url: str, timeout: float = 10.0) -> dict[str, Any]:
        self.require("http.egress")
        import urllib.request

        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(64_000)
            return {"ok": True, "status": getattr(resp, "status", 200), "body": body.decode("utf-8", errors="replace")}

    def fs_read(self, path: str, max_bytes: int = 1_000_000) -> dict[str, Any]:
        self.require("fs.read")
        p = Path(path)
        data = p.read_bytes()[:max_bytes]
        return {"ok": True, "path": str(p), "bytes": len(data), "text": data.decode("utf-8", errors="replace")}

    def fs_write(self, path: str, content: str) -> dict[str, Any]:
        self.require("fs.write")
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(p)}

    def execute_tool(self, name: str, **kwargs: Any) -> dict[str, Any]:
        self.require("tools.execute")
        from jarvis.handlers.registry import call_action, has_action

        if not has_action(name):
            return {"ok": False, "message": f"unknown tool/action: {name}"}
        # assistant may be None in bootstrap — callers should prefer chat path
        return {"ok": False, "message": "execute_tool requires chat/assistant context", "action": name, "params": kwargs}

    def use_voice(self, **kwargs: Any) -> dict[str, Any]:
        self.require("voice.use")
        return {"ok": True, "bridge": "voice", "params": kwargs, "note": "Voice product owns synthesis/ASR."}

    def use_vision(self, **kwargs: Any) -> dict[str, Any]:
        self.require("vision.use")
        return {"ok": True, "bridge": "vision", "params": kwargs, "note": "Vision product owns analysis."}

    def use_browser(self, **kwargs: Any) -> dict[str, Any]:
        self.require("browser.use")
        return {"ok": True, "bridge": "browser", "params": kwargs, "note": "Browser product owns the agent."}

    def ha_control(self, **kwargs: Any) -> dict[str, Any]:
        self.require("ha.control")
        return {"ok": True, "bridge": "smarthome", "params": kwargs, "note": "Smart Home product owns HA control."}

    def use_models(self, **kwargs: Any) -> dict[str, Any]:
        self.require("models.use")
        return {"ok": True, "bridge": "models", "params": kwargs, "note": "Models product owns providers."}


def load_plugin(path: Path) -> LoadedPlugin:
    manifest = read_manifest(path)
    errors = validate_manifest(manifest)
    if errors:
        return LoadedPlugin(manifest=manifest, path=path, error="; ".join(errors))

    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    mod_name, attr = manifest.entry.split(":", 1)
    try:
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
        module = importlib.import_module(mod_name)
        handler = getattr(module, attr, None)
        ctx = PluginContext(manifest)
        if callable(handler):
            handler(ctx)
        loaded = LoadedPlugin(manifest=manifest, path=path, module=module)
        _loaded[manifest.id] = loaded
        log.info(
            "loaded capability %s v%s (in-process; isolation=none; sandbox_flag=%s)",
            manifest.id,
            manifest.version,
            manifest.sandbox,
        )
        return loaded
    except Exception as exc:
        log.exception("capability load failed: %s", path)
        return LoadedPlugin(manifest=manifest, path=path, error=str(exc))


def load_all() -> dict[str, Any]:
    summary = []
    for d in discover_plugin_dirs():
        try:
            from jarvis.capabilities_product import policy as cap_policy

            m = read_manifest(d)
            cap_id = f"sdk:{m.id}"
            if cap_policy.is_quarantined(cap_id) or not cap_policy.is_enabled(cap_id, trust="trusted_local"):
                summary.append(
                    {
                        "id": m.id,
                        "name": m.name,
                        "version": m.version,
                        "ok": False,
                        "error": "disabled_or_quarantined",
                        "permissions": m.permissions,
                        "path": str(d),
                    }
                )
                continue
        except Exception:
            pass
        lp = load_plugin(d)
        if not lp.error:
            try:
                from jarvis.capabilities_product.contributions import register_contributions
                from jarvis.router_table import invalidate_router_table

                register_contributions(f"sdk:{lp.manifest.id}", lp.manifest)
                invalidate_router_table()
            except Exception:
                log.exception("contribution registration failed for %s", lp.manifest.id)
        summary.append(
            {
                "id": lp.manifest.id,
                "name": lp.manifest.name,
                "version": lp.manifest.version,
                "ok": not lp.error,
                "error": lp.error,
                "permissions": lp.manifest.permissions,
                "path": str(lp.path),
            }
        )
    return {"ok": True, "capabilities": summary, "plugins": summary}  # plugins alias for compat


def list_plugins() -> list[dict[str, Any]]:
    out = []
    for d in discover_plugin_dirs():
        try:
            m = read_manifest(d)
            data = {**asdict(m), "path": str(d), "loaded": m.id in _loaded, "isolation": "none"}
            out.append(data)
        except Exception as exc:
            out.append({"path": str(d), "error": str(exc)})
    return out


def create_example_plugin() -> Path:
    """Write a sample capability under data/plugins for discovery demos."""
    root = PLUGIN_DIR / "hello_aria"
    root.mkdir(parents=True, exist_ok=True)
    (root / MANIFEST_NAME).write_text(
        json.dumps(
            {
                "id": "hello_aria",
                "name": "Hello Aria",
                "version": "1.0.0",
                "description": "Example local capability with a chat contribution",
                "entry": "plugin:register",
                "permissions": ["rag.search"],
                "sandbox": False,
                "category": "Utilities",
                "contributions": {
                    "actions": [
                        {
                            "name": "hello_aria",
                            "description": "Hello from Capabilities example",
                            "patterns": ["hello aria capability", "say hello capability"],
                            "reply": "Hello from the Hello Aria capability.",
                            "info": True,
                        }
                    ],
                    "tools": [{"name": "hello_aria_tool", "description": "Example agent tool"}],
                    "voice_intents": [{"phrase": "hello capability", "action": "hello_aria"}],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (root / "plugin.py").write_text(
        "def register(ctx):\n"
        "    assert 'rag.search' in ctx.permissions\n"
        "    assert ctx.isolation == 'none'\n"
        "    return {'ok': True}\n",
        encoding="utf-8",
    )
    return root
