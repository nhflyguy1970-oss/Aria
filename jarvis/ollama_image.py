"""Generate images via Ollama HTTP API (no separate ComfyUI server required)."""

import base64
import json
import urllib.request
from datetime import datetime

from jarvis import llm
from jarvis.config import DATA_DIR
from jarvis.ollama_health import ollama_host

OUTPUT_DIR = DATA_DIR / "generated"


def generate(prompt: str, width: int = 1024, height: int = 1024) -> str | None:
    """Return path to PNG or None if model/API unavailable."""
    model = llm.image_model()
    host = ollama_host()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"ollama_{stamp}.png"

    payloads = [
        {"model": model, "prompt": prompt, "stream": False, "width": width, "height": height},
        {"model": model, "prompt": prompt, "stream": False},
    ]
    for payload in payloads:
        try:
            req = urllib.request.Request(
                f"{host}/api/generate",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode())
            for key in ("image", "images"):
                val = data.get(key)
                if isinstance(val, str) and val:
                    out_path.write_bytes(base64.b64decode(val))
                    return str(out_path)
                if isinstance(val, list) and val:
                    out_path.write_bytes(base64.b64decode(val[0]))
                    return str(out_path)
            if data.get("response"):
                text = data["response"]
                if text.startswith("data:image") or len(text) > 500:
                    b64 = text.split(",", 1)[-1] if "," in text else text
                    out_path.write_bytes(base64.b64decode(b64))
                    return str(out_path)
        except Exception:
            continue
    return None
