"""ComfyUI API integration for local image generation."""

import contextvars
import copy
import json
import logging
import os
import secrets
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from contextlib import contextmanager
from pathlib import Path

from jarvis.config import DATA_DIR
from jarvis.image_safety import with_minor_negative

COMFY_URL = os.getenv("JARVIS_COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
_TARGET: contextvars.ContextVar[str] = contextvars.ContextVar("comfy_target", default="")


def _base() -> str:
    """ComfyUI instance for the current job (the Z-Image worker sets its own)."""
    return _TARGET.get() or COMFY_URL


@contextmanager
def target(url: str):
    token = _TARGET.set(url.rstrip("/"))
    try:
        yield
    finally:
        _TARGET.reset(token)
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
    if "lustify" in ckpt.lower():
        # Tested 2026-10-13: CFG 7.5 overcooks Lustify; 5.5 with SDE sampling looks natural.
        return (int(os.getenv("JARVIS_COMFYUI_STEPS", "30")), float(os.getenv("JARVIS_COMFYUI_CFG", "5.5")),
                os.getenv("JARVIS_COMFYUI_SAMPLER", "dpmpp_2m_sde"), os.getenv("JARVIS_COMFYUI_SCHEDULER", "karras"))
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
    seed: int | None = None,
    steps: int | None = None,
    cfg: float | None = None,
    sampler: str | None = None,
    scheduler: str | None = None,
) -> dict:
    """Patch custom workflow prompts, latent size, and seeds/sampler overrides."""
    wf = copy.deepcopy(wf)
    use_seed = int(seed) if seed is not None else _random_seed()
    _patch_workflow_generation.last_seed = use_seed  # type: ignore[attr-defined]
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
            inputs["seed"] = use_seed
            if steps is not None:
                inputs["steps"] = int(steps)
            if cfg is not None:
                inputs["cfg"] = float(cfg)
            if sampler:
                inputs["sampler_name"] = sampler
            if scheduler:
                inputs["scheduler"] = scheduler
        if class_type == "RandomNoise":
            inputs["noise_seed"] = use_seed
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
    *,
    seed: int | None = None,
    steps: int | None = None,
    cfg: float | None = None,
    sampler: str | None = None,
    scheduler: str | None = None,
    workflow: str | None = None,
) -> dict:
    from jarvis.comfyui_settings import effective_workflow_path

    wf_path = (workflow or "").strip() or effective_workflow_path()
    if wf_path and Path(wf_path).exists():
        wf = json.loads(Path(wf_path).read_text(encoding="utf-8"))
        patched = _patch_workflow_generation(
            wf,
            prompt=prompt,
            negative_prompt=with_minor_negative(negative_prompt or DEFAULT_NEGATIVE),
            width=width,
            height=height,
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler=sampler,
            scheduler=scheduler,
        )
        _workflow.last_seed = getattr(_patch_workflow_generation, "last_seed", seed)  # type: ignore[attr-defined]
        return patched

    ckpt = _find_checkpoint(checkpoint)
    d_steps, d_cfg, d_sampler, d_scheduler = _sampler_settings(ckpt)
    use_steps = int(steps) if steps is not None else d_steps
    use_cfg = float(cfg) if cfg is not None else d_cfg
    use_sampler = sampler or d_sampler
    use_scheduler = scheduler or d_scheduler
    use_seed = int(seed) if seed is not None else _random_seed()
    # Stash for callers that want last seed
    _workflow.last_seed = use_seed  # type: ignore[attr-defined]
    if _is_flux_checkpoint(ckpt):
        negative = negative_prompt.strip()
    else:
        negative = with_minor_negative(negative_prompt.strip() or DEFAULT_NEGATIVE)

    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": use_seed,
                "steps": use_steps,
                "cfg": use_cfg,
                "sampler_name": use_sampler,
                "scheduler": use_scheduler,
                "denoise": 1,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": prompt, "clip": ["4", 1]},
            "_meta": {"title": "Positive"},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["4", 1]},
            "_meta": {"title": "Negative"},
        },
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "jarvis", "images": ["8", 0]},
        },
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
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="image"; filename="{file_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
        + content
        + f"\r\n--{boundary}--\r\n".encode()
    )
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
        req = urllib.request.Request(f"{_base()}/interrupt", data=b"", method="POST")
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


def _report(pct: float, message: str, job_id: str | None) -> None:
    try:
        from jarvis.media_jobs import report_progress

        report_progress(pct, message, job_id=job_id)
    except Exception:
        pass


def _listen_progress(client_id: str, job_id: str | None, stop: threading.Event) -> None:
    """Relay ComfyUI's per-step websocket events for this client to the media job's progress bar.

    Sampling maps to 12–95%; model loading and decode/save sit either side. Best effort: no
    websocket (or an older ComfyUI) just leaves the coarse stage messages in place."""
    try:
        import websocket  # websocket-client
    except ImportError:
        return
    ws_url = _base().replace("http://", "ws://", 1).replace("https://", "wss://", 1)
    try:
        ws = websocket.create_connection(f"{ws_url}/ws?clientId={client_id}", timeout=5)
    except Exception:
        return
    ws.settimeout(1.0)
    try:
        while not stop.is_set():
            try:
                raw = ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            except Exception:
                return
            if not isinstance(raw, str):
                continue  # binary latent previews
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            data = msg.get("data") or {}
            if msg.get("type") == "progress" and data.get("max"):
                value, total = int(data.get("value") or 0), int(data["max"])
                if value >= total:
                    _report(95, "Decoding and saving…", job_id)
                else:
                    _report(12 + 83 * value / total, f"Generating — step {value}/{total}", job_id)
            elif msg.get("type") == "execution_start":
                _report(10, "Loading model…", job_id)
    finally:
        try:
            ws.close()
        except Exception:
            pass


_MODEL_INPUTS = {
    "ckpt_name": ("checkpoints",), "unet_name": ("diffusion_models", "unet"),
    "clip_name": ("text_encoders", "clip"), "clip_name1": ("text_encoders", "clip"),
    "clip_name2": ("text_encoders", "clip"), "vae_name": ("vae",), "lora_name": ("loras",),
    "model_name": ("animatediff_models", "upscale_models"),
}
RAM_OVERHEAD_MIB = 2048  # latents, decode buffers and Python/torch working set beside the weights


def workflow_ram_mib(workflow: dict) -> int | None:
    """Host RAM a workflow needs: its model files plus working memory, capped at the Flux-sized
    default. None when no model file can be found (the scheduler then uses its default)."""
    from jarvis.gpu_scheduler import IMAGE_PROFILE

    seen: set[Path] = set()
    for node in (workflow or {}).values():
        inputs = node.get("inputs", {}) if isinstance(node, dict) else {}
        for key, subdirs in _MODEL_INPUTS.items():
            name = inputs.get(key)
            if not isinstance(name, str) or not name:
                continue
            for sub in subdirs:
                path = COMFY_ROOT / "models" / sub / name
                if path.is_file():
                    seen.add(path)
                    break
    if not seen:
        return None
    weights_mib = sum(p.stat().st_size for p in seen) // 1048576
    return min(weights_mib + RAM_OVERHEAD_MIB, int(IMAGE_PROFILE["ram_mib"]))


def run_workflow(
    workflow: dict,
    filename_prefix: str = "jarvis",
    *,
    timeout_sec: int = 300,
    cancel_check=None,
    vram_mib: int | None = None,
    ram_mib: int | None = None,
) -> str:
    """Queue a ComfyUI workflow in the exclusive RTX 3060 slot; output path or ERROR: string.

    ``ram_mib`` overrides the file-size estimate for models that stream weights from host RAM."""
    from jarvis import gpu_scheduler

    base_cancel = cancel_check or _cancel_check_default
    _report(6, "Waiting for the GPU…", None)
    try:
        with gpu_scheduler.admit_image(label=filename_prefix, vram_mib=vram_mib,
                                       ram_mib=ram_mib or workflow_ram_mib(workflow)) as job:
            result = _run_workflow(workflow, filename_prefix, timeout_sec=timeout_sec,
                                   cancel_check=lambda: job.cut_off or base_cancel())
            if job.cut_off:
                return f"ERROR: Image job stopped to protect the system: {job.cutoff_reason}"
            return result
    except gpu_scheduler.GpuUnavailable as exc:
        return f"ERROR: Image job not started: {exc.reason}"


@contextmanager
def image_session(label: str, *, vram_mib: int | None = None, ram_mib: int | None = None,
                  timeout_sec: int = 300, cancel_check=None):
    """One exclusive RTX admission for several workflows in a row (e.g. a render and its retry):
    the models stay loaded between them, where separate ``run_workflow`` calls free ComfyUI
    after each. Yields ``run(workflow) -> path | "ERROR: ..."``; raises GpuUnavailable when
    the slot cannot be admitted."""
    from jarvis import gpu_scheduler

    base_cancel = cancel_check or _cancel_check_default
    _report(6, "Waiting for the GPU…", None)
    with gpu_scheduler.admit_image(label=label, vram_mib=vram_mib, ram_mib=ram_mib) as job:
        def run(workflow: dict, filename_prefix: str = label) -> str:
            if job.cut_off:
                return f"ERROR: Image job stopped to protect the system: {job.cutoff_reason}"
            result = _run_workflow(workflow, filename_prefix, timeout_sec=timeout_sec,
                                   cancel_check=lambda: job.cut_off or base_cancel())
            if job.cut_off:
                return f"ERROR: Image job stopped to protect the system: {job.cutoff_reason}"
            return result

        yield run


def _run_workflow(
    workflow: dict,
    filename_prefix: str = "jarvis",
    *,
    timeout_sec: int = 300,
    cancel_check=None,
) -> str:
    """Queue a ComfyUI workflow and return the saved output path or ERROR: string."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client_id = str(uuid.uuid4())
    try:
        from jarvis.media_jobs import current_job_id

        job_id = current_job_id()
    except Exception:
        job_id = None
    _report(8, "Starting ComfyUI job…", job_id)
    stop_progress = threading.Event()
    if job_id:  # connect before queueing so the first steps are not missed
        threading.Thread(target=_listen_progress, args=(client_id, job_id, stop_progress),
                         name="comfy-progress", daemon=True).start()
    try:
        return _run_workflow_queued(workflow, filename_prefix, client_id,
                                    timeout_sec=timeout_sec, cancel_check=cancel_check)
    finally:
        stop_progress.set()


def _run_workflow_queued(
    workflow: dict,
    filename_prefix: str,
    client_id: str,
    *,
    timeout_sec: int,
    cancel_check,
) -> str:
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(
        f"{_base()}/prompt",
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
            with urllib.request.urlopen(f"{_base()}/history/{prompt_id}", timeout=10) as resp:
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
                params = urllib.parse.urlencode(
                    {"filename": fname, "subfolder": sub, "type": img_type}
                )
                out_name = Path(fname).name
                if filename_prefix and not out_name.startswith(f"{filename_prefix}_"):
                    out_name = f"{filename_prefix}_{out_name}"
                out_path = OUTPUT_DIR / out_name
                _download_output(f"{_base()}/view?{params}", out_path)
                return str(out_path)
    return None


def _selected_zimage() -> bool:
    from jarvis.comfyui_settings import resolve_checkpoint_name
    from jarvis.zimage import CHECKPOINT

    return resolve_checkpoint_name() == CHECKPOINT


def _generate_once(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    negative_prompt: str = "",
    checkpoint: str | None = None,
    *,
    seed: int | None = None,
    steps: int | None = None,
    cfg: float | None = None,
    sampler: str | None = None,
    scheduler: str | None = None,
    workflow: str | None = None,
) -> str:
    from jarvis import zimage
    from jarvis.image_safety import refusal_for

    refused = refusal_for(prompt)
    if refused:
        return refused
    if checkpoint in ("zimage", zimage.CHECKPOINT) or (not checkpoint and _selected_zimage()):
        # Z-Image Turbo runs on its own on-demand worker (Phase 8 qualified INT8 runtime).
        return zimage.generate(prompt, width, height, seed=seed)
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

    return run_workflow(
        _workflow(
            prompt,
            width,
            height,
            negative_prompt,
            checkpoint=checkpoint,
            seed=seed,
            steps=steps,
            cfg=cfg,
            sampler=sampler,
            scheduler=scheduler,
            workflow=workflow,
        )
    )


def generate(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    negative_prompt: str = "",
    checkpoint: str | None = None,
    *,
    seed: int | None = None,
    steps: int | None = None,
    cfg: float | None = None,
    sampler: str | None = None,
    scheduler: str | None = None,
    workflow: str | None = None,
) -> str:
    result = _generate_once(
        prompt,
        width,
        height,
        negative_prompt,
        checkpoint=checkpoint,
        seed=seed,
        steps=steps,
        cfg=cfg,
        sampler=sampler,
        scheduler=scheduler,
        workflow=workflow,
    )
    # Expose last seed used (from workflow build)
    try:
        generate.last_seed = getattr(_workflow, "last_seed", seed)  # type: ignore[attr-defined]
    except Exception:
        generate.last_seed = seed  # type: ignore[attr-defined]

    if not _is_gpu_failure(result):
        return result

    from jarvis.comfyui_settings import auto_fallback_enabled, effective_cpu_mode

    if auto_fallback_enabled() and not effective_cpu_mode():
        try:
            from jarvis.services import fallback_comfyui_to_cpu
        except ImportError:
            fallback_comfyui_to_cpu = None  # type: ignore[assignment]
        ok = False
        try:
            ok = bool(fallback_comfyui_to_cpu and fallback_comfyui_to_cpu())
        except Exception as exc:
            return (
                f"{result} (CPU fallback error: {exc}). "
                "Open Mission Control or switch Image Engine to CPU."
            )
        if ok:
            retry = _generate_once(
                prompt,
                width,
                height,
                negative_prompt,
                checkpoint=checkpoint,
                seed=seed,
                steps=steps,
                cfg=cfg,
                sampler=sampler,
                scheduler=scheduler,
                workflow=workflow,
            )
            if not retry.startswith("ERROR:"):
                return retry
            if _is_gpu_failure(retry):
                return (
                    "ERROR: GPU and CPU image generation both failed. "
                    "Check data/logs/comfyui.log, free VRAM, or open Mission Control."
                )
            return retry
        return (
            f"{result} (auto CPU fallback failed to restart ComfyUI). "
            "Open Mission Control or switch Image Engine to CPU."
        )

    if auto_fallback_enabled():
        return result + " (already on CPU — check ComfyUI logs or Mission Control)"

    return (
        result
        + " Switch ComfyUI to CPU or Auto (GPU → CPU) in Image Engine, or open Mission Control."
    )
