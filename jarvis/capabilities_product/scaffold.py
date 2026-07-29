"""Scaffold a new local capability under data/plugins."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jarvis.config import DATA_DIR, PROJECT_ROOT


def scaffold_capability(
    name: str,
    *,
    description: str = "",
    category: str = "Utilities",
    permissions: list[str] | None = None,
    under_project: bool = False,
) -> dict[str, Any]:
    slug = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name.strip().lower()).strip("_")
    if not slug:
        raise ValueError("name required")
    root_base = (PROJECT_ROOT / "plugins") if under_project else (DATA_DIR / "plugins")
    root = root_base / slug
    if root.exists():
        raise FileExistsError(f"already exists: {root}")
    root.mkdir(parents=True, exist_ok=True)
    perms = list(permissions or [])
    manifest = {
        "id": slug,
        "name": name.strip() or slug,
        "version": "0.1.0",
        "description": description or f"{name} capability",
        "entry": "plugin:register",
        "permissions": perms,
        "sandbox": False,
        "category": category,
        "author": "",
        "tags": ["local", "scaffolded"],
        "settings_schema": {
            "type": "object",
            "properties": {
                "enabled_note": {"type": "string", "title": "Operator note", "default": ""}
            },
        },
        "contributions": {
            "actions": [
                {
                    "name": f"{slug}_status",
                    "description": f"{name} status",
                    "patterns": [f"{slug} status", f"{name.lower()} status"],
                    "reply": f"{name} capability is installed. Open Capabilities Home to manage it.",
                    "info": True,
                }
            ],
            "tools": [{"name": f"{slug}_tool", "description": f"Tool surface for {name}"}],
            "voice_intents": [{"phrase": f"{name} status", "action": f"{slug}_status"}],
            "workflow_steps": [],
            "automation_actions": [],
        },
    }
    (root / "aria_plugin.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (root / "plugin.py").write_text(
        '"""Capability entrypoint."""\n\n'
        "def register(ctx):\n"
        "    # Use ctx.require('perm') before privileged helpers.\n"
        "    return {'ok': True, 'id': ctx.manifest.id}\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        f"# {name}\n\n"
        f"{description or 'Local Aria capability.'}\n\n"
        "## Operator\n\n"
        "1. Open **Capabilities Home**\n"
        "2. Review permissions and trust\n"
        "3. Enable only if you accept in-process execution\n\n"
        "## Developer\n\n"
        "Entry: `plugin:register`\n"
        "Manifest: `aria_plugin.json`\n",
        encoding="utf-8",
    )
    tests_dir = root / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_smoke.py").write_text(
        "def test_manifest_exists():\n"
        "    from pathlib import Path\n"
        f"    assert (Path(__file__).resolve().parents[1] / 'aria_plugin.json').is_file()\n",
        encoding="utf-8",
    )
    from jarvis.capabilities_product import policy as cap_policy

    cap_id = f"sdk:{slug}"
    cap_policy.set_enabled(cap_id, False)
    cap_policy.set_trust_override(cap_id, "trusted_local")
    return {"ok": True, "id": cap_id, "path": str(root), "enabled": False, "manifest": manifest}


def scaffold_cli(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="aria capability new", description="Scaffold a local Aria capability")
    parser.add_argument("name", help="Capability name")
    parser.add_argument("--description", default="", help="Short description")
    parser.add_argument("--category", default="Utilities")
    parser.add_argument("--permission", action="append", default=[], help="Permission id (repeatable)")
    parser.add_argument("--project", action="store_true", help="Create under PROJECT_ROOT/plugins")
    args = parser.parse_args(argv)
    try:
        result = scaffold_capability(
            args.name,
            description=args.description,
            category=args.category,
            permissions=args.permission,
            under_project=bool(args.project),
        )
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    print("Created DISABLED trusted-local capability. Review in Capabilities Home before enabling.")
    return 0
