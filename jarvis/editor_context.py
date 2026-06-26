"""Editor context from Cursor/VS Code extension bridge."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from jarvis.config import DATA_DIR

CONTEXT_FILE = DATA_DIR / "editor_context.json"
DEFAULT_MAX_AGE_S = 120


@dataclass
class EditorContext:
    workspace: str = ""
    active_file: str = ""
    relative_file: str = ""
    language: str = ""
    selection: str = ""
    selection_start: dict[str, int] = field(default_factory=dict)
    selection_end: dict[str, int] = field(default_factory=dict)
    cursor_line: int = 0
    open_files: list[str] = field(default_factory=list)
    updated_at: float = 0.0

    def is_fresh(self, *, max_age_s: float = DEFAULT_MAX_AGE_S) -> bool:
        if not self.updated_at or not self.relative_file:
            return False
        return (time.time() - self.updated_at) <= max_age_s

    def has_selection(self) -> bool:
        return bool(self.selection.strip())

    def selection_line_count(self) -> int:
        if not self.has_selection():
            return 0
        return max(1, self.selection.count("\n") + 1)

    def format_for_prompt(self, *, max_selection: int = 4000) -> str:
        if not self.relative_file:
            return ""
        parts = [f"Active editor file: {self.relative_file}"]
        if self.language:
            parts.append(f"Language: {self.language}")
        if self.cursor_line:
            parts.append(f"Cursor line: {self.cursor_line}")
        if self.open_files:
            parts.append("Open tabs: " + ", ".join(self.open_files[:12]))
        if self.has_selection():
            sel = self.selection[:max_selection]
            if len(self.selection) > max_selection:
                sel += "…"
            start = self.selection_start
            end = self.selection_end
            loc = ""
            if start and end:
                loc = f" (lines {start.get('line', '?')}-{end.get('line', '?')})"
            parts.append(f"Selected text{loc}:\n```\n{sel}\n```")
        return "\n".join(parts)


def _from_dict(data: dict[str, Any]) -> EditorContext:
    return EditorContext(
        workspace=str(data.get("workspace", "")),
        active_file=str(data.get("active_file", "")),
        relative_file=str(data.get("relative_file", "")),
        language=str(data.get("language", "")),
        selection=str(data.get("selection", "")),
        selection_start=dict(data.get("selection_start") or {}),
        selection_end=dict(data.get("selection_end") or {}),
        cursor_line=int(data.get("cursor_line") or data.get("line") or 0),
        open_files=list(data.get("open_files") or []),
        updated_at=float(data.get("updated_at") or 0),
    )


def save_context(payload: dict[str, Any]) -> EditorContext:
    payload = dict(payload)
    payload["updated_at"] = time.time()
    ctx = _from_dict(payload)
    CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONTEXT_FILE.write_text(json.dumps(asdict(ctx), indent=2), encoding="utf-8")
    return ctx


def load_context() -> EditorContext:
    if not CONTEXT_FILE.exists():
        return EditorContext()
    try:
        data = json.loads(CONTEXT_FILE.read_text(encoding="utf-8"))
        return _from_dict(data if isinstance(data, dict) else {})
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return EditorContext()


def get_context(*, max_age_s: float = DEFAULT_MAX_AGE_S) -> EditorContext | None:
    ctx = load_context()
    return ctx if ctx.is_fresh(max_age_s=max_age_s) else None


def context_summary() -> str:
    ctx = get_context()
    if not ctx:
        return ""
    sel = " + selection" if ctx.has_selection() else ""
    return f"{ctx.relative_file}{sel}"
