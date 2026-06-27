"""ComfyUI API integration for local image generation."""

import copy
import json
import logging
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

from jarvis.config import DATA_DIR

COMFY_URL = os.getenv("JARVIS_COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
OUTPUT_DIR = DATA_DIR / "generated"
logger = logging.getLogger(__name__)
COMFY_ROOT = Path(os.getenv("JARVIS_COMFYUI_ROOT", Path.home() / "ComfyUI"))
DOWNLOAD_TIMEOUT = float(os.getenv("JARVIS_COMFYUI_DOWNLOAD_TIMEOUT", "120"))
DEFAULT_NEGATIVE = (
    "blurry, low quality, watermark, text, logo, deformed, bad anatomy, "
    "extra limbs, fused animals, wrong species"
)


def is_available() -> bool:
    try:
        with urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=3):
            return True
    except Exception:
        return False


def _fetch_system_stats() -> dict | None:
    try:
        with urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def comfyui_device_name() -> str:
    """Active ComfyUI torch device name, or empty if offline."""
    stats = _fetch_system_stats()
    if not stats:
        return ""
    devices = stats.get("devices") or []
    if not devices:
        return ""
    return str(devices[0].get("name") or "")


def nvidia_comfyui_required() -> bool:
    try:
        from jarvis.gpu_routing import gpu_preference, nvidia_available

        return gpu_preference() in ("nvidia", "both", "auto") and nvidia_available()
    except Exception:
        return False


def wait_until_ready(timeout: float = 90) -> bool:
    deadline = time.time() + timeout
    delay = 0.5
    while time.time() < deadline:
        if is_available():
            return True
        time.sleep(delay)
        delay = min(delay * 1.4, 4.0)
    return False


def _find_checkpoint(override: str | None = None) -> str:
    if override:
        path = COMFY_ROOT / "models" / "checkpoints" / Path(override).name
        if path.is_file():
            return path.name
    from jarvis.comfyui_settings import resolve_checkpoint_name

    return resolve_checkpoint_name()


def _is_flux_checkpoint(ckpt: str) -> bool:
    return "flux" in ckpt.lower()


def _sampler_settings(ckpt: str) -> tuple[int, float, str, str]:
    if _is_flux_checkpoint(ckpt):
        steps = int(os.getenv("JARVIS_COMFYUI_STEPS", "4"))
        cfg = float(os.getenv("JARVIS_COMFYUI_CFG", "1.0"))
        sampler = os.getenv("JARVIS_COMFYUI_SAMPLER", "euler")
        scheduler = os.getenv("JARVIS_COMFYUI_SCHEDULER", "simple")
        return steps, cfg, sampler, scheduler

    is_turbo = "turbo" in ckpt.lower()
    if is_turbo:
        return 4, 1.0, "euler", "normal"
    steps = int(os.getenv("JARVIS_COMFYUI_STEPS", "30"))
    cfg = float(os.getenv("JARVIS_COMFYUI_CFG", "7.5"))
    sampler = os.getenv("JARVIS_COMFYUI_SAMPLER", "dpmpp_2m")
    scheduler = os.getenv("JARVIS_COMFYUI_SCHEDULER", "karras")
    return steps, cfg, sampler, scheduler


def _random_seed() -> int:
    return secrets.randbelow(2**32)


def _patch_workflow_generation(
    wf: dict,
    *,
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
) -> dict:
    """Patch custom workflow prompts, latent size, and randomize all seeds."""
    wf = copy.deepcopy(wf)
    for node in wf.values():
        if not isinstance(node, dict):
            continue
        title = (node.get("_meta") or {}).get("title", "")
        class_type = node.get("class_type", "")
        inputs = node.get("inputs") or {}
        if class_type == "CLIPTextEncode" and title == "Positive":
            inputs["text"] = prompt
        if class_type == "CLIPTextEncode" and title == "Negative":
            inputs["text"] = negative_prompt or DEFAULT_NEGATIVE
        if class_type == "KSampler":
            inputs["seed"] = _random_seed()
        if class_type == "RandomNoise":
            inputs["noise_seed"] = _random_seed()
        if class_type == "EmptyLatentImage":
            inputs["width"] = width
            inputs["height"] = height
    return wf


def _workflow(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    negative_prompt: str = "",
    checkpoint: str | None = None,
) -> dict:
    from jarvis.comfyui_settings import effective_workflow_path

    wf_path = effective_workflow_path()
    if wf_path and Path(wf_path).exists():
        wf = json.loads(Path(wf_path).read_text(encoding="utf-8"))
        return _patch_workflow_generation(
            wf,
            prompt=prompt,
            negative_prompt=negative_prompt or DEFAULT_NEGATIVE,
            width=width,
            height=height,
        )

    ckpt = _find_checkpoint(checkpoint)
    steps, cfg, sampler_name, scheduler = _sampler_settings(ckpt)
    seed = _random_seed()
    if _is_flux_checkpoint(ckpt):
        negative = negative_prompt.strip()
    else:
        negative = negative_prompt.strip() or DEFAULT_NEGATIVE

    return {
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": steps, "cfg": cfg,
            "sampler_name": sampler_name, "scheduler": scheduler,
            "denoise": 1, "model": ["4", 0], "positive": ["6", 0],
            "negative": ["7", 0], "latent_image": ["5", 0],
        }},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}, "_meta": {"title": "Positive"}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["4", 1]}, "_meta": {"title": "Negative"}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "jarvis", "images": ["8", 0]}},
    }


def _is_gpu_failure(result: str) -> bool:
    if not result.startswith("ERROR:"):
        return False
    lower = result.lower()
    return (
        "hip error" in lower
        or "invalid device function" in lower
        or "gpu image generation failed" in lower
    )


def upload_image(path: str | Path) -> str:
    """Upload an image to ComfyUI input folder; returns the filename ComfyUI assigned."""
    file_path = Path(path).expanduser().resolve()
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    import mimetypes

    content = file_path.read_bytes()
    content_type = mimetypes.guess_type(file_path.name)[0] or "image/png"
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{file_path.name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{COMFY_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode())
    name = result.get("name")
    if not name:
        raise RuntimeError(f"ComfyUI upload failed: {result}")
    return str(name)


def _comfy_http_error_detail(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
        data = json.loads(body) if body else {}
    except Exception:
        return str(exc)
    parts: list[str] = [str(exc)]
    err = data.get("error") or {}
    if err.get("message"):
        parts.append(str(err["message"]))
    node_errors = data.get("node_errors") or {}
    for node_id, info in node_errors.items():
        for item in info.get("errors") or []:
            msg = item.get("message", "")
            detail = item.get("details", "")
            if msg or detail:
                parts.append(f"node {node_id}: {msg} {detail}".strip())
    return " — ".join(dict.fromkeys(p for p in parts if p))


def interrupt_running() -> None:
    """Ask ComfyUI to stop the current prompt (best-effort)."""
    try:
        req = urllib.request.Request(f"{COMFY_URL}/interrupt", data=b"", method="POST")
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


def _cancel_check_default():
    try:
        from jarvis.media_jobs import should_abort_job

        return should_abort_job()
    except Exception:
        return False


def _download_output(url: str, out_path: Path, timeout: float | None = None) -> None:
    t = timeout if timeout is not None else DOWNLOAD_TIMEOUT
    with urllib.request.urlopen(url, timeout=t) as resp:
        out_path.write_bytes(resp.read())


def run_workflow(
    workflow: dict,
    filename_prefix: str = "jarvis",
    *,
    timeout_sec: int = 300,
    cancel_check=None,
) -> str:
    """Queue a ComfyUI workflow and return the saved output path or ERROR: string."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client_id = str(uuid.uuid4())
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = _comfy_http_error_detail(e)
        return f"ERROR: ComfyUI request failed: {detail}"
    except Exception as e:
        return f"ERROR: ComfyUI request failed: {e}"

    prompt_id = result.get("prompt_id")
    if not prompt_id:
        return f"ERROR: ComfyUI rejected prompt: {result}"

    if cancel_check is None:
        cancel_check = _cancel_check_default

    deadline = time.time() + timeout_sec
    delay = 0.75
    poll_failures = 0
    while time.time() < deadline:
        if cancel_check():
            interrupt_running()
            try:
                from jarvis.media_jobs import job_timed_out

                if job_timed_out():
                    return f"ERROR: Timed out after {int(os.getenv('JARVIS_MEDIA_JOB_TIMEOUT_SEC', '900'))}s"
            except Exception:
                pass
            return "ERROR: Cancelled by user"
        time.sleep(delay)
        delay = min(delay * 1.15, 5.0)
        try:
            with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}", timeout=10) as resp:
                history = json.loads(resp.read().decode())
            poll_failures = 0
        except Exception as exc:
            poll_failures += 1
            if poll_failures == 1 or poll_failures % 20 == 0:
                logger.warning("ComfyUI history poll failed (%d): %s", poll_failures, exc)
            continue
        if prompt_id not in history:
            continue

        entry = history[prompt_id]
        outputs = entry.get("outputs", {})
        saved = _save_workflow_outputs(outputs, filename_prefix)
        if saved:
            return saved

        status = entry.get("status", {})
        if not status.get("completed"):
            continue

        for msg in status.get("messages", []):
            if not msg or msg[0] != "execution_error":
                continue
            detail = str(msg[1].get("exception_message", "unknown error"))
            if _is_gpu_failure(f"ERROR: {detail}"):
                return f"ERROR: GPU image generation failed: {detail[:200]}"
            return f"ERROR: ComfyUI: {detail[:240]}"

        saved = _save_workflow_outputs(outputs, filename_prefix)
        if saved:
            return saved
        return "ERROR: ComfyUI finished but produced no output — check data/logs/comfyui.log"

    return "ERROR: ComfyUI generation timed out — check data/logs/comfyui.log"


def _save_workflow_outputs(outputs: dict, filename_prefix: str) -> str | None:
    """Download first video/gif/image from ComfyUI workflow outputs (video preferred)."""
    for key in ("videos", "gifs", "animated", "images"):
        for node_out in outputs.values():
            for item in node_out.get(key, []):
                fname = item.get("filename", "")
                if not fname:
                    continue
                sub = item.get("subfolder", "")
                img_type = item.get("type", "output")
                params = urllib.parse.urlencode({"filename": fname, "subfolder": sub, "type": img_type})
                out_name = Path(fname).name
                if filename_prefix and not out_name.startswith(f"{filename_prefix}_"):
                    out_name = f"{filename_prefix}_{out_name}"
                out_path = OUTPUT_DIR / out_name
                _download_output(f"{COMFY_URL}/view?{params}", out_path)
                return str(out_path)
    return None


def _generate_once(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    negative_prompt: str = "",
    checkpoint: str | None = None,
) -> str:
    from jarvis.vram_guard import prepare_for_comfyui

    prepare_for_comfyui()
    from jarvis.services import ensure_comfyui_nvidia

    ensure_comfyui_nvidia(block=True, timeout=90)
    if not is_available():
        from jarvis.branding import assistant_name

        return (
            f"ERROR: ComfyUI is not running. Restart {assistant_name()} or run: "
            "~/ComfyUI/venv/bin/python ~/ComfyUI/main.py --listen 127.0.0.1 --port 8188"
        )

    return run_workflow(_workflow(prompt, width, height, negative_prompt, checkpoint=checkpoint))


def generate(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    negative_prompt: str = "",
    checkpoint: str | None = None,
) -> str:
    result = _generate_once(prompt, width, height, negative_prompt, checkpoint=checkpoint)
    if not _is_gpu_failure(result):
        return result

    from jarvis.comfyui_settings import auto_fallback_enabled, effective_cpu_mode
    from jarvis.services import fallback_comfyui_to_cpu

    if auto_fallback_enabled() and not effective_cpu_mode():
        if fallback_comfyui_to_cpu():
            retry = _generate_once(prompt, width, height, negative_prompt, checkpoint=checkpoint)
            if not retry.startswith("ERROR:"):
                return retry
            if _is_gpu_failure(retry):
                return (
                    "ERROR: GPU and CPU image generation both failed. "
                    "Check data/logs/comfyui.log or switch to CPU in the sidebar."
                )
            return retry

    if auto_fallback_enabled():
        return result + " (auto CPU fallback failed to restart ComfyUI)"

    return (
        result
        + " Switch ComfyUI to CPU or Auto (GPU → CPU) in the sidebar under Image engine."
    )
