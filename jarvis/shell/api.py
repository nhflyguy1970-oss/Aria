"""Shell HTTP API — hotkeys, design tokens, product-home checklist, JS bundle."""

from __future__ import annotations

from pathlib import Path

# Shell chrome scripts — single HTTP round-trip for cold start.
SHELL_BUNDLE_SCRIPTS: tuple[str, ...] = (
    "ui_prefs.js",
    "hotkey_registry.js",
    "breadcrumbs.js",
    "discoverability.js",
    "quick_dock.js",
    "status_bar.js",
    "collapsible_panels.js",
    "global_history.js",
    "split_view.js",
)

_STATIC = Path(__file__).resolve().parent.parent / "gui" / "static"


def register_product_routes(app, assistant) -> None:  # noqa: ARG001
    from fastapi.responses import Response

    @app.get("/api/shell/product")
    def shell_product():
        from jarvis.shell.engine import product_status

        return product_status()

    @app.get("/api/shell/hotkeys")
    def shell_hotkeys(group: str = ""):
        from jarvis.shell.hotkeys import list_hotkeys, shortcuts_modal_items

        return {
            "ok": True,
            "hotkeys": list_hotkeys(group=group),
            "shortcuts": shortcuts_modal_items(),
        }

    @app.get("/api/shell/design")
    def shell_design():
        from jarvis.shell.design_tokens import DESIGN_TOKENS, token_css_variables

        return {"ok": True, "tokens": DESIGN_TOKENS, "css_variables": token_css_variables()}

    @app.get("/api/shell/product-home")
    def shell_product_home():
        from jarvis.shell.product_home import checklist_payload

        return checklist_payload()

    @app.get("/api/shell/mental-model")
    def shell_mental_model():
        from jarvis.shell.terminology import MENTAL_MODEL

        return {"ok": True, "mental_model": MENTAL_MODEL}

    @app.get("/api/shell/bundle.js")
    def shell_bundle_js():
        parts: list[str] = [
            "/* Aria shell bundle — navigation/chrome only; products load separately. */\n"
        ]
        for name in SHELL_BUNDLE_SCRIPTS:
            path = _STATIC / name
            if not path.is_file():
                parts.append(f"/* missing: {name} */\n")
                continue
            parts.append(f"\n/* === {name} === */\n")
            parts.append(path.read_text(encoding="utf-8"))
            parts.append("\n")
        return Response(
            content="".join(parts),
            media_type="application/javascript; charset=utf-8",
            headers={"Cache-Control": "public, max-age=60"},
        )
