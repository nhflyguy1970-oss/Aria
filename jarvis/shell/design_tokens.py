"""Design tokens — professional dark shell (source of truth for docs/tests)."""

from __future__ import annotations

from typing import Any

DESIGN_TOKENS: dict[str, Any] = {
    "version": "2.0.0",
    "theme_default": "professional_dark",
    "themes": ["professional_dark", "professional_light"],
    "colors": {
        "bg_deep": "#0e1116",
        "bg_panel": "#151a21",
        "bg_elevated": "#1b222c",
        "bg_hover": "#232b36",
        "border": "#2c3542",
        "text": "#e6e9ef",
        "text_muted": "#8b949e",
        "accent": "#4f7cac",
        "accent_dim": "#3d6287",
        "accent_subtle": "rgba(79, 124, 172, 0.12)",
        "status_ok": "#3d9a6a",
        "status_warn": "#c9a227",
        "status_err": "#c45c5c",
        "status_info": "#4f7cac",
    },
    "typography": {
        "font": '"IBM Plex Sans", "DM Sans", system-ui, sans-serif',
        "mono": '"IBM Plex Mono", "JetBrains Mono", monospace',
        "text_xs": "0.72rem",
        "text_sm": "0.8125rem",
        "text_md": "0.9375rem",
        "text_lg": "1.125rem",
        "text_xl": "1.35rem",
    },
    "spacing": {
        "1": "0.25rem",
        "2": "0.5rem",
        "3": "0.75rem",
        "4": "1rem",
        "5": "1.5rem",
        "6": "2rem",
    },
    "radius": {"sm": "6px", "md": "8px", "lg": "10px"},
    "elevation": {
        "1": "0 1px 2px rgba(0,0,0,0.35)",
        "2": "0 4px 16px rgba(0,0,0,0.4)",
    },
    "motion": {
        "fast": "0.12s ease",
        "med": "0.18s ease",
        "policy": "state_only",
    },
    "density": ["comfortable", "standard", "compact", "operator"],
    "forbidden": [
        "neon_glow",
        "movie_hud",
        "cyberpunk",
        "rgb_theme",
        "decorative_pulse",
        "hologram",
    ],
}


def token_css_variables() -> dict[str, str]:
    c = DESIGN_TOKENS["colors"]
    t = DESIGN_TOKENS["typography"]
    s = DESIGN_TOKENS["spacing"]
    r = DESIGN_TOKENS["radius"]
    e = DESIGN_TOKENS["elevation"]
    m = DESIGN_TOKENS["motion"]
    return {
        "--bg-deep": c["bg_deep"],
        "--bg-panel": c["bg_panel"],
        "--bg-elevated": c["bg_elevated"],
        "--bg-hover": c["bg_hover"],
        "--border": c["border"],
        "--text": c["text"],
        "--text-muted": c["text_muted"],
        "--accent": c["accent"],
        "--accent-dim": c["accent_dim"],
        "--accent-glow": c["accent_subtle"],
        "--status-ok": c["status_ok"],
        "--status-warn": c["status_warn"],
        "--status-err": c["status_err"],
        "--status-info": c["status_info"],
        "--font": t["font"],
        "--mono": t["mono"],
        "--text-xs": t["text_xs"],
        "--text-sm": t["text_sm"],
        "--text-md": t["text_md"],
        "--text-lg": t["text_lg"],
        "--text-xl": t["text_xl"],
        "--space-1": s["1"],
        "--space-2": s["2"],
        "--space-3": s["3"],
        "--space-4": s["4"],
        "--space-5": s["5"],
        "--space-6": s["6"],
        "--radius-sm": r["sm"],
        "--radius-md": r["md"],
        "--radius-lg": r["lg"],
        "--elev-1": e["1"],
        "--elev-2": e["2"],
        "--transition-fast": m["fast"],
        "--transition-med": m["med"],
    }
