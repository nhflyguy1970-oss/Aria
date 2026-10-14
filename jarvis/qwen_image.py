"""Qwen-Image 2512 (FP8 + Lightning 8-step LoRA): ARIA's high-accuracy Regular-mode image model.

Chosen 2026-10-14 for complex scenes (exact counts, left/right/behind relations, in-image
text). It is a 20B MMDiT that runs on the stock ComfyUI (native ``qwen_image`` support) with
ComfyUI's weight streaming on the 12 GB RTX 3060, so it is slower than Flux Schnell (minutes
rather than seconds) and is used only when ``image_quality`` picks the quality tier. It is
never used in Uncensored mode (not NSFW-trained; Lustify stays the Uncensored model). Every
job goes through ``comfyui.run_workflow``: the exclusive RTX slot, 82 C cutoff and RAM floor.
"""
from __future__ import annotations

import secrets

from jarvis.comfyui_settings import COMFY_ROOT

LABEL = "Qwen-Image 2512 (high quality)"
FILES = {
    "diffusion_models": "qwen_image_2512_fp8_e4m3fn.safetensors",
    "text_encoders": "qwen_2.5_vl_7b_fp8_scaled.safetensors",
    "vae": "qwen_image_vae.safetensors",
    "loras": "Qwen-Image-2512-Lightning-8steps-V1.0-bf16.safetensors",
}
STEPS = 8  # Lightning distillation: 8 steps at CFG 1
SHIFT = 3.1
# Weights are streamed from host RAM (20 GB UNet + 9 GB encoder).
RAM_MIB = 32768  # ComfyUI RSS peaked at 29.7 GiB (31.1 GB) during a Qwen-Image job, 2026-10-14
VRAM_MIB = 9800
TIMEOUT_S = 900
ETA = "typically 1½–3½ minutes"  # 2026-10-14 RTX 3060: ~95 s warm, ~190 s when weights reload
MAX_PIXELS = 1344 * 768  # ~1 MP keeps a 1344x768 render near 1 minute of sampling


def installed() -> bool:
    return all((COMFY_ROOT / "models" / sub / name).is_file() for sub, name in FILES.items())


def fit_size(width: int, height: int) -> tuple[int, int]:
    """Keep the aspect ratio within ~1 MP, multiples of 16."""
    w, h = max(256, int(width)), max(256, int(height))
    scale = min(1.0, (MAX_PIXELS / (w * h)) ** 0.5)
    return max(256, int(w * scale) // 16 * 16), max(256, int(h * scale) // 16 * 16)


GPU_TE_NODE = "ARIATextEncoderLoaderGPU"  # comfy_nodes/aria_nodes


def gpu_text_encoder_available() -> bool:
    """ARIA's GPU text-encoder node is loaded in the running ComfyUI. Without it the stock
    loader encodes on the CPU under --lowvram (~58 s per Qwen job instead of a few seconds)."""
    import json
    import urllib.request

    from jarvis import comfyui

    try:
        with urllib.request.urlopen(f"{comfyui._base()}/object_info/{GPU_TE_NODE}", timeout=5) as r:
            return GPU_TE_NODE in json.loads(r.read() or b"{}")
    except Exception:  # noqa: BLE001
        return False


def build_workflow(prompt: str, width: int, height: int, seed: int | None = None,
                   filename_prefix: str = "jarvis_qwen", gpu_text_encoder: bool = False) -> dict:
    seed = secrets.randbelow(2**32) if seed is None else int(seed)
    te = ({"class_type": GPU_TE_NODE, "inputs": {"clip_name": FILES["text_encoders"], "type": "qwen_image"}}
          if gpu_text_encoder else
          {"class_type": "CLIPLoader", "inputs": {"clip_name": FILES["text_encoders"], "type": "qwen_image", "device": "default"}})
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": FILES["diffusion_models"], "weight_dtype": "default"}},
        "2": te,
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": FILES["vae"]}},
        "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": FILES["loras"], "strength_model": 1.0}},
        "5": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["4", 0], "shift": SHIFT}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": prompt}, "_meta": {"title": "Positive"}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": " "}, "_meta": {"title": "Negative"}},
        "8": {"class_type": "EmptySD3LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "9": {"class_type": "KSampler", "inputs": {"model": ["5", 0], "positive": ["6", 0], "negative": ["7", 0],
                                                   "latent_image": ["8", 0], "seed": seed, "steps": STEPS, "cfg": 1.0,
                                                   "sampler_name": "euler", "scheduler": "simple", "denoise": 1}},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["3", 0]}},
        "11": {"class_type": "SaveImage", "inputs": {"images": ["10", 0], "filename_prefix": filename_prefix}},
    }


def generate(prompt: str, width: int = 1344, height: int = 768, *, seed: int | None = None,
             count_prompt: str | None = None) -> str:
    """Render one image; returns the saved path or an ERROR: string.

    With ``count_prompt`` (and no fixed seed) the objects it asks for are counted on the RX 7600
    helper; a miscount renders again with a new seed in the same RTX admission (weights stay
    loaded: ~70 s instead of a ~230 s reload) and the closer attempt is kept. The outcome is
    left in ``generate.last_check``; the seed used in ``generate.last_seed``."""
    from jarvis import comfyui, gpu_scheduler, image_verify
    from jarvis.image_safety import refusal_for
    from jarvis.media_jobs import report_progress

    generate.last_check = {}  # type: ignore[attr-defined]
    if refused := refusal_for(prompt):
        return refused
    if not installed():
        return "ERROR: Qwen-Image is not installed (model files missing under ComfyUI/models)"
    from jarvis.services import ensure_comfyui_nvidia
    from jarvis.vram_guard import prepare_for_comfyui

    prepare_for_comfyui()
    ensure_comfyui_nvidia(block=True, timeout=90)
    if not comfyui.is_available():
        return "ERROR: ComfyUI is not running, so the high-quality image model could not start."
    width, height = fit_size(width, height)
    gpu_te = gpu_text_encoder_available()
    check_counts = bool(count_prompt and seed is None and image_verify.expected_counts(count_prompt))
    seed = secrets.randbelow(2**32) if seed is None else int(seed)
    generate.last_seed = seed  # type: ignore[attr-defined]
    try:
        with comfyui.image_session("jarvis_qwen", vram_mib=VRAM_MIB, ram_mib=RAM_MIB, timeout_sec=TIMEOUT_S) as run:
            result = run(build_workflow(prompt, width, height, seed, gpu_text_encoder=gpu_te))
            if result.startswith("ERROR:") or not check_counts:
                return result
            report_progress(93, "Checking object counts…")
            best = image_verify.check(result, count_prompt)
            attempts = 1

            def off(chk: dict) -> tuple[int, int]:
                return chk["misses"], sum(abs(r["got"] - r["want"]) for r in chk["checked"])

            while best["ran"] and best["misses"] and attempts <= image_verify.retries():
                miss = next(r for r in best["checked"] if r["got"] != r["want"])
                report_progress(50, f"Counted {miss['got']} {miss['noun']}, not {miss['want']} — rendering again…")
                new_seed = secrets.randbelow(2**32)
                again = run(build_workflow(prompt, width, height, new_seed, gpu_text_encoder=gpu_te))
                if again.startswith("ERROR:"):
                    break
                attempts += 1
                chk = image_verify.check(again, count_prompt)
                if chk["ran"] and off(chk) < off(best):
                    image_verify.set_aside(result)
                    result, best = again, chk
                    generate.last_seed = new_seed  # type: ignore[attr-defined]
                else:
                    image_verify.set_aside(again)
            generate.last_check = {**best, "attempts": attempts}  # type: ignore[attr-defined]
            return result
    except gpu_scheduler.GpuUnavailable as exc:
        return f"ERROR: Image job not started: {exc.reason}"


def release_memory() -> None:
    """After a Qwen-Image job (and any count-check retry): stop ComfyUI if idle — the only way
    to get Qwen-Image's ~30 GB of host memory back (see services.release_comfyui)."""
    try:
        from jarvis.services import release_comfyui

        release_comfyui("a Qwen-Image job")
    except Exception:  # noqa: BLE001
        pass
