import shutil
import subprocess
from typing import Iterator


def pull_model(model: str) -> Iterator[dict]:
    """Stream ollama pull progress as event dicts."""
    from jarvis.model_store import is_ollama_pullable

    ollama = shutil.which("ollama")
    if not ollama:
        yield {"type": "error", "message": "ollama not found in PATH"}
        return

    if not model or not model.strip():
        yield {"type": "error", "message": "No model name provided"}
        return

    if not is_ollama_pullable(model):
        yield {
            "type": "error",
            "message": f"{model.strip()} is not an Ollama model (local backend — nothing to pull)",
        }
        return

    model = model.strip()
    yield {"type": "start", "model": model, "message": f"Pulling {model}…"}

    try:
        proc = subprocess.Popen(
            [ollama, "pull", model],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in proc.stdout or []:
            line = line.strip()
            if line:
                yield {"type": "progress", "message": line}
        proc.wait()
        if proc.returncode == 0:
            yield {"type": "done", "ok": True, "message": f"Successfully pulled {model}"}
        else:
            yield {"type": "done", "ok": False, "message": f"Pull failed (exit {proc.returncode})"}
    except Exception as e:
        yield {"type": "done", "ok": False, "message": str(e)}
