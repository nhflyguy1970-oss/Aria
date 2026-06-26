#!/usr/bin/env python3
"""Save Hugging Face token to data/jarvis.env for pyannote diarization."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / "data" / "jarvis.env"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/set_hf_token.py hf_your_token_here", file=sys.stderr)
        print("  or:  ./venv/bin/python scripts/set_hf_token.py hf_...", file=sys.stderr)
        print("Token: https://huggingface.co/settings/tokens", file=sys.stderr)
        print("Terms: https://huggingface.co/pyannote/speaker-diarization-3.1", file=sys.stderr)
        return 1

    token = sys.argv[1].strip().strip('"').strip("'")
    if not token:
        print("ERROR: empty token", file=sys.stderr)
        return 1
    if not token.startswith("hf_"):
        print("Warning: Hugging Face tokens usually start with hf_", file=sys.stderr)

    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    lines = [ln for ln in lines if not re.match(r"^export HF_TOKEN=", ln.strip())]
    lines = [ln for ln in lines if not re.match(r"^export HUGGINGFACE_TOKEN=", ln.strip())]
    while lines and not lines[-1].strip():
        lines.pop()
    stamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    lines.extend(["", f"# Hugging Face — pyannote diarization (added {stamp})", f'export HF_TOKEN="{token}"'])
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cli = ROOT / "venv" / "bin" / "huggingface-cli"
    if cli.is_file():
        subprocess.run([str(cli), "login", "--token", token], check=False, capture_output=True)

    print(f"HF_TOKEN saved to {ENV_FILE}")
    print("Restart Jarvis, then Audio → Advanced → Diarize speakers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
