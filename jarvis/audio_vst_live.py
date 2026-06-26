"""Live AE-5 EQ via PipeWire filter-chain virtual sinks."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from jarvis.audio_device import _detect_pipewire_sink, _run

FILTER_DIR = Path.home() / ".config/pipewire/filter-chain.conf.d"
JARVIS_FILTER_PREFIX = "jarvis-ae5-"

# 6-band EQ: (freq, bq_label, Q, gain_db)
LIVE_EQ_BANDS: dict[str, list[tuple[float, str, float, float]]] = {
    "voice": [
        (100, "bq_lowshelf", 1.0, -3.0),
        (250, "bq_peaking", 1.0, -2.0),
        (1000, "bq_peaking", 1.0, 1.0),
        (3000, "bq_peaking", 1.0, 4.0),
        (5000, "bq_peaking", 1.0, 2.0),
        (8000, "bq_highshelf", 1.0, 1.0),
    ],
    "music": [
        (80, "bq_lowshelf", 1.0, 2.0),
        (200, "bq_peaking", 1.0, 0.5),
        (500, "bq_peaking", 1.0, 0.0),
        (2000, "bq_peaking", 1.0, 0.5),
        (6000, "bq_peaking", 1.0, 1.5),
        (10000, "bq_highshelf", 1.0, 1.5),
    ],
    "scout": [
        (120, "bq_lowshelf", 1.0, 1.0),
        (400, "bq_peaking", 1.0, -1.0),
        (2000, "bq_peaking", 1.0, 0.5),
        (5000, "bq_peaking", 1.0, 2.0),
        (8000, "bq_peaking", 1.0, 3.0),
        (12000, "bq_highshelf", 1.0, 2.5),
    ],
    "gaming": [
        (100, "bq_lowshelf", 1.0, -2.0),
        (250, "bq_peaking", 1.0, -1.0),
        (2500, "bq_peaking", 1.0, 3.0),
        (5000, "bq_peaking", 1.0, 2.0),
        (7000, "bq_peaking", 1.0, 1.5),
        (10000, "bq_highshelf", 1.0, 1.0),
    ],
    "flat": [
        (100, "bq_lowshelf", 1.0, 0.0),
        (250, "bq_peaking", 1.0, 0.0),
        (1000, "bq_peaking", 1.0, 0.0),
        (3000, "bq_peaking", 1.0, 0.0),
        (6000, "bq_peaking", 1.0, 0.0),
        (10000, "bq_highshelf", 1.0, 0.0),
    ],
}

LIVE_SINK_NODE: dict[str, str] = {
    preset: f"effect_input.jarvis_ae5_{preset}" for preset in LIVE_EQ_BANDS
}


def _band_nodes(bands: list[tuple[float, str, float, float]]) -> str:
    lines = []
    for i, (freq, label, q, gain) in enumerate(bands, start=1):
        lines.append(
            f"""                    {{
                        type  = builtin
                        name  = eq_band_{i}
                        label = {label}
                        control = {{ "Freq" = {freq:.1f} "Q" = {q:.1f} "Gain" = {gain:.1f} }}
                    }}"""
        )
    return "\n".join(lines)


def _band_links(count: int = 6) -> str:
    links = []
    for i in range(1, count):
        links.append(f'                    {{ output = "eq_band_{i}:Out" input = "eq_band_{i + 1}:In" }}')
    return "\n".join(links)


def generate_filter_conf(preset: str) -> str:
    bands = LIVE_EQ_BANDS.get(preset, LIVE_EQ_BANDS["flat"])
    node_name = LIVE_SINK_NODE[preset]
    title = preset.replace("_", " ").title()
    return f"""# Jarvis AE-5 live EQ — {title} (auto-generated)
context.modules = [
    {{ name = libpipewire-module-filter-chain
        flags = [ nofail ]
        args = {{
            node.description = "Jarvis AE-5 {title}"
            media.name       = "Jarvis AE-5 {title}"
            filter.graph = {{
                nodes = [
{_band_nodes(bands)}
                ]
                links = [
{_band_links(len(bands))}
                ]
            }}
            audio.channels = 2
            audio.position = [ FL FR ]
            capture.props = {{
                node.name   = "{node_name}"
                media.class = Audio/Sink
            }}
            playback.props = {{
                node.name    = "effect_output.jarvis_ae5_{preset}"
                node.passive = true
            }}
        }}
    }}
]
"""


def install_filter_configs() -> tuple[bool, str]:
    """Write PipeWire filter-chain configs to ~/.config/pipewire/filter-chain.conf.d/."""
    if not shutil.which("pactl"):
        return False, "PipeWire/PulseAudio not found (pactl missing)"

    FILTER_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for preset in LIVE_EQ_BANDS:
        dest = FILTER_DIR / f"{JARVIS_FILTER_PREFIX}{preset}.conf"
        dest.write_text(generate_filter_conf(preset), encoding="utf-8")
        written.append(dest.name)

    for old in FILTER_DIR.glob(f"{JARVIS_FILTER_PREFIX}*.conf"):
        if old.stem.replace(JARVIS_FILTER_PREFIX, "") not in LIVE_EQ_BANDS:
            old.unlink(missing_ok=True)

    return True, (
        f"Installed {len(written)} filter configs to {FILTER_DIR}. "
        "Restart PipeWire (or log out/in) once, then pick a live chain in the Audio tab."
    )


def _list_sinks() -> list[str]:
    code, out = _run(["pactl", "list", "short", "sinks"])
    if code != 0:
        return []
    return [line.split("\t")[1] for line in out.splitlines() if "\t" in line]


def live_sink_available(preset: str) -> bool:
    node = LIVE_SINK_NODE.get(preset, "")
    return any(node in s for s in _list_sinks())


def live_status() -> dict:
    from jarvis.audio_settings import saved_vst_live_chain

    default = ""
    code, out = _run(["pactl", "get-default-sink"])
    if code == 0:
        default = out.strip()

    presets = {}
    for preset, node in LIVE_SINK_NODE.items():
        presets[preset] = {
            "sink_node": node,
            "available": live_sink_available(preset),
            "active": node in default,
        }
    creative = _detect_pipewire_sink()
    return {
        "default_sink": default,
        "creative_sink": creative,
        "selected": saved_vst_live_chain() or "off",
        "filter_dir": str(FILTER_DIR),
        "presets": presets,
    }


def activate_live(preset: str) -> tuple[bool, str]:
    """Route system default playback through a Jarvis virtual EQ sink."""
    preset = (preset or "off").strip().lower()
    if preset in ("off", "none", "direct", ""):
        return deactivate_live()

    if preset not in LIVE_SINK_NODE:
        return False, f"Unknown live preset '{preset}'"

    node = LIVE_SINK_NODE[preset]
    if not live_sink_available(preset):
        ok, msg = install_filter_configs()
        if not ok:
            return False, msg
        return False, (
            f"Live sink '{node}' not loaded yet. {msg}"
        )

    code, out = _run(["pactl", "set-default-sink", node])
    if code != 0:
        return False, f"Could not set default sink to {node}: {out.strip()}"

    from jarvis.audio_settings import save_settings

    save_settings({"vst_live_chain": preset})
    return True, f"Live AE-5 EQ → {preset} (sink {node})"


def deactivate_live() -> tuple[bool, str]:
    """Restore default sink to the Creative Sound Blaster."""
    creative = _detect_pipewire_sink() or os.getenv("JARVIS_AUDIO_SINK", "").strip()
    if not creative:
        return False, "Creative sink not detected"

    code, out = _run(["pactl", "set-default-sink", creative])
    if code != 0:
        return False, f"Could not restore Creative sink: {out.strip()}"

    from jarvis.audio_settings import save_settings

    save_settings({"vst_live_chain": "off"})
    return True, f"Live EQ off — default sink → {creative}"
