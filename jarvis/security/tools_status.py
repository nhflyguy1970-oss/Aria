"""Agent tools status for sidebar and Security tab."""

from __future__ import annotations

from typing import Any


def tools_status() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "", module: str = "") -> None:
        rows.append({"name": name, "ok": ok, "detail": detail, "module": module})

    try:
        from jarvis.ollama_health import check_ollama

        ollama = check_ollama()
        running = bool(ollama.get("running"))
        models = len(ollama.get("models") or [])
        add("Ollama", running, f"{models} models" if running else "not running", "brain")
    except Exception as exc:
        add("Ollama", False, str(exc)[:80], "brain")

    try:
        from jarvis.sandbox import firejail_available, sandbox_enabled

        avail = firejail_available()
        enabled = sandbox_enabled()
        add("Firejail sandbox", avail and enabled, "enabled" if enabled else "available" if avail else "missing", "coding")
    except Exception as exc:
        add("Firejail sandbox", False, str(exc)[:80], "coding")

    try:
        from jarvis.lsp import tools_status as lsp_tools
        from jarvis.syntax_check import available_tools

        tools = {**available_tools(), **lsp_tools()}
        linters = [k for k, v in tools.items() if v and k not in ("py_compile", "bash", "node")]
        add("Coding linters", bool(linters), ", ".join(linters[:4]) or "none", "coding")
        if tools.get("lsp"):
            add("LSP", True, "language servers", "coding")
    except Exception:
        add("Coding linters", False, "not loaded", "coding")

    try:
        from jarvis.browser_playwright import browser_stack_ready
        from jarvis.p2_flags import browser_agent_enabled

        stack = browser_stack_ready()
        pw_ok = bool(stack.get("playwright") and stack.get("chromium"))
        agent_on = browser_agent_enabled()
        add("Browser agent", agent_on and pw_ok, "Playwright" if pw_ok else "Playwright missing", "web")
    except Exception:
        add("Browser agent", False, "not loaded", "web")

    try:
        from jarvis.engineering.cad_deps import cad_status
        from jarvis.p3_flags import cad_enabled, printer_enabled

        c = cad_status()
        cad_ok = cad_enabled() and c.get("ready", False)
        add("CAD lab", cad_ok, "OpenSCAD/build123d" if cad_ok else "deps missing", "engineering")
        if printer_enabled():
            add("3D printer", True, "Bambu/USB", "engineering")
    except Exception:
        add("CAD lab", False, "not loaded", "engineering")

    try:
        from jarvis.home_assistant import ha_enabled
        from jarvis.p2_flags import kasa_enabled

        add("Home Assistant", ha_enabled(), "", "smarthome")
        add("Kasa", kasa_enabled(), "TP-Link", "smarthome")
    except Exception:
        pass

    try:
        from jarvis.extensibility.loader import list_extensions

        exts = list_extensions()
        add("Extensions", bool(exts), f"{len(exts)} loaded" if exts else "none", "core")
        for ext in exts[:6]:
            add(ext.get("name", "?"), True, (ext.get("description") or "")[:50], "extension")
    except Exception:
        add("Extensions", False, "not loaded", "core")

    try:
        from jarvis.p4_flags import cloud_live_voice_enabled, face_auth_enabled, gestures_enabled, pin_lock_enabled

        add("PIN lock", pin_lock_enabled(), "GUI", "security")
        add("Face auth", face_auth_enabled(), "", "security")
        add("Cloud Live voice", cloud_live_voice_enabled(), "Gemini", "voice")
        add("Gestures", gestures_enabled(), "MediaPipe", "presence")
    except Exception:
        pass

    try:
        from jarvis.native_window import is_available

        add("Native shell", is_available(), "GTK window", "shell")
    except Exception:
        add("Native shell", False, "", "shell")

    return rows
