"""Single hotkey registry — documentation, shortcuts modal, discoverability, palette."""

from __future__ import annotations

from typing import Any

# Canonical chords. Clients and docs must use this list.
HOTKEYS: list[dict[str, Any]] = [
    {"id": "palette", "chord": "Ctrl+K", "action": "command_palette", "label": "Command palette", "group": "core"},
    {"id": "sidebar_search", "chord": "Ctrl+Shift+F", "action": "sidebar_search", "label": "Sidebar search", "group": "core"},
    {"id": "shortcuts", "chord": "Ctrl+/", "action": "shortcuts_modal", "label": "Keyboard shortcuts", "group": "core"},
    {"id": "settings", "chord": "Ctrl+,", "action": "open_settings", "label": "Settings Home", "group": "core"},
    {"id": "home", "chord": "Ctrl+Home", "action": "open_home", "label": "Home", "group": "core"},
    {"id": "favorites", "chord": "Ctrl+1…9", "action": "jump_favorite", "label": "Jump Favorites / primary views", "group": "nav"},
    {"id": "cycle", "chord": "Ctrl+Tab", "action": "cycle_views", "label": "Cycle views", "group": "nav"},
    {"id": "back", "chord": "Alt+←", "action": "view_back", "label": "Back in view history", "group": "nav"},
    {"id": "forward", "chord": "Alt+→", "action": "view_forward", "label": "Forward in view history", "group": "nav"},
    {"id": "notifications", "chord": "Ctrl+Shift+A", "action": "open_notifications", "label": "Notifications (Activity Center inbox)", "group": "products"},
    {"id": "layouts", "chord": "Ctrl+Shift+L", "action": "open_layouts", "label": "Layouts", "group": "products", "aliases": ["Ctrl+Shift+P"]},
    {"id": "layout_presets", "chord": "Ctrl+Alt+1…8", "action": "apply_layout_preset", "label": "Apply starter layout by index", "group": "products"},
    {"id": "mission", "chord": "Ctrl+Shift+M", "action": "open_mission_control", "label": "Mission Control", "group": "products"},
    {"id": "mini_chat", "chord": "Ctrl+Shift+K", "action": "toggle_mini_chat", "label": "Floating mini chat", "group": "products"},
    {"id": "split", "chord": "Ctrl+\\", "action": "toggle_split", "label": "Split view", "group": "products"},
    {"id": "automation", "chord": "Ctrl+Shift+O", "action": "open_automation", "label": "Automation Home", "group": "products"},
    {"id": "view_paths", "chord": "Ctrl+Shift+V", "action": "open_view_paths", "label": "View Paths", "group": "products"},
    {"id": "models", "chord": "Ctrl+Shift+.", "action": "open_models", "label": "Models Home", "group": "products"},
    {"id": "coding", "chord": "Ctrl+Shift+C", "action": "open_coding", "label": "Coding Home", "group": "products"},
    {"id": "gallery", "chord": "Ctrl+Shift+G", "action": "open_gallery", "label": "Gallery Home", "group": "products"},
    {"id": "browser", "chord": "Ctrl+Shift+B", "action": "open_browser", "label": "Browser Home", "group": "products"},
    {"id": "vision", "chord": "Ctrl+Shift+I", "action": "open_vision", "label": "Vision Home", "group": "products"},
    {"id": "reload", "chord": "Ctrl+Shift+R", "action": "reload_ui", "label": "Reload UI", "group": "system"},
]


def list_hotkeys(*, group: str = "") -> list[dict[str, Any]]:
    if not group:
        return [dict(h) for h in HOTKEYS]
    return [dict(h) for h in HOTKEYS if h.get("group") == group]


def hotkey_by_id(hotkey_id: str) -> dict[str, Any] | None:
    for h in HOTKEYS:
        if h["id"] == hotkey_id:
            return dict(h)
    return None


def chord_for(action: str) -> str:
    for h in HOTKEYS:
        if h.get("action") == action or h.get("id") == action:
            return str(h.get("chord") or "")
    return ""


def shortcuts_modal_items() -> list[dict[str, str]]:
    return [{"chord": h["chord"], "label": h["label"], "id": h["id"]} for h in HOTKEYS]


def validate_registry() -> list[str]:
    """Detect duplicate primary chords (aliases allowed)."""
    errors: list[str] = []
    seen: dict[str, str] = {}
    for h in HOTKEYS:
        chord = str(h.get("chord") or "").lower()
        if not chord:
            errors.append(f"missing_chord:{h.get('id')}")
            continue
        if chord in seen:
            errors.append(f"duplicate_chord:{chord}:{seen[chord]}:{h.get('id')}")
        else:
            seen[chord] = str(h.get("id"))
    return errors
