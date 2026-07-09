import asyncio
import json
import os
import subprocess
import threading
import time
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from jarvis.env_loader import load_jarvis_env

load_jarvis_env()

import uvicorn
from fastapi import Body, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from jarvis.assistant import JarvisAssistant
from jarvis.audio_device import apply_system_default, detect_devices
from jarvis.config import DATA_DIR, PROJECT_ROOT, is_uncensored
from jarvis.gpu import detect_gpu
from jarvis.ollama_health import check_ollama

STATIC_DIR = Path(__file__).parent / "static"
ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
APP_VERSION = "3.1.0"
UI_VERSION = os.getenv("JARVIS_UI_VERSION", "5.16.73")
assistant = JarvisAssistant(uncensored=is_uncensored())

from jarvis.assistant_instance import set_assistant

set_assistant(assistant)
os.environ.setdefault("JARVIS_APP_VERSION", APP_VERSION)
os.environ.setdefault("JARVIS_UI_VERSION", UI_VERSION)
apply_system_default()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from jarvis import audio_wakeword
    from jarvis.media_jobs import recover_stale_jobs

    recover_stale_jobs()
    audio_wakeword.configure(chat_processor=assistant.process)

    def _warm_flytying_index() -> None:
        try:
            from jarvis.flytying.config import blackfly_data_available
            from jarvis.flytying import index as recipe_index

            if blackfly_data_available():
                recipe_index.recipes()
        except Exception:
            pass

    threading.Thread(target=_warm_flytying_index, daemon=True, name="flytying-warm").start()

    yield
    try:
        assistant.branches.persist(session=assistant.session)
        assistant.auto_checkpoint(reason="shutdown")
    except Exception:
        pass


from jarvis.branding import assistant_name

app = FastAPI(title=assistant_name(), version=APP_VERSION, lifespan=lifespan)

try:
    from jarvis.extensibility.loader import register_extension_api

    register_extension_api(app, assistant)
except Exception:
    import logging

    logging.getLogger("jarvis.gui.server").exception("Extension API registration failed")

from jarvis.auth import APIKeyMiddleware
from jarvis.network_guard import NetworkGuardMiddleware
from jarvis.rate_limit import RateLimitMiddleware

app.add_middleware(NetworkGuardMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(APIKeyMiddleware)

from jarvis.gui.extra_routes import register_routes

register_routes(app, assistant)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "message": f"Server error: {exc}",
                "detail": traceback.format_exc()[-500:] if app.debug else None,
            },
        )
    raise exc


_health_full_cache: dict = {"at": 0.0, "data": None}
_HEALTH_TTL = float(os.getenv("JARVIS_HEALTH_CACHE_SEC", "8"))
_HEALTH_FULL_TTL = float(os.getenv("JARVIS_HEALTH_FULL_CACHE_SEC", "45"))
_health_refresh_lock = threading.Lock()


def _build_health_lite() -> dict:
    from jarvis.media_jobs import busy_state
    from jarvis.services import _http_ok

    ollama_ok = False
    try:
        ollama_ok = _http_ok("http://127.0.0.1:11434/api/tags", timeout=1.5)
    except Exception:
        pass
    busy = busy_state()
    return {
        "status": "ok",
        "version": APP_VERSION,
        "jarvis_running": True,
        "ready": ollama_ok,
        "uncensored": is_uncensored(),
        "busy": busy["busy"] or busy["pending"] > 0,
        "busy_job": busy.get("label") or "",
        "media_queue": busy,
    }


def _refresh_health_full_cache() -> None:
    try:
        payload = _build_health_payload()
        _health_full_cache["data"] = payload
        _health_full_cache["at"] = time.time()
    except Exception:
        pass


def _live_payload() -> dict:
    """Fast liveness probe — never blocks on ComfyUI/GPU probes."""
    from jarvis.auth import api_key_enabled

    ollama_ok = False
    try:
        from jarvis.services import _http_ok

        ollama_ok = _http_ok("http://127.0.0.1:11434/api/tags", timeout=1.5)
    except Exception:
        pass
    from jarvis.auth import api_key_enabled, localhost_key_exempt
    from jarvis.branding import branding_dict

    return {
        "ok": True,
        "version": APP_VERSION,
        "ui_version": UI_VERSION,
        "ready": ollama_ok,
        "uncensored": is_uncensored(),
        "api_key_required": api_key_enabled(),
        "api_key_localhost_exempt": localhost_key_exempt(),
        **branding_dict(),
    }


@app.get("/api/ping")
def ping():
    """Instant liveness — used by tray watchdog; must never call Ollama/GPU."""
    return {"ok": True}


@app.get("/api/live")
def live():
    return _live_payload()


def _build_health_payload() -> dict:
    from jarvis.auth import api_key_enabled
    from jarvis.sandbox import firejail_available, sandbox_enabled
    from jarvis.services import get_status

    svc = get_status(force=True)
    gpu = detect_gpu()
    from jarvis.vram_guard import recommendations, status as vram_status

    gpu["low_vram"] = vram_status()["low_vram"]
    gpu["vram_guard"] = vram_status()
    gpu["tips"] = recommendations()
    from jarvis.resource_router import snapshot as resource_snapshot, status_line as resource_status_line

    resources = resource_snapshot()
    audio = detect_devices()
    status = assistant.get_status()
    return {
        "status": "ok" if svc.get("ready") else "starting",
        "version": APP_VERSION,
        "jarvis_running": True,
        "ready": svc.get("ready", False),
        "services": svc.get("services", []),
        "comfyui_settings": svc.get("comfyui_settings", {}),
        "ollama": svc.get("ollama", check_ollama()),
        "gpu": gpu,
        "resources": resources,
        "resource_status_line": resource_status_line(),
        "audio": audio,
        "integrations": {
            "comfyui": next((s["running"] for s in svc.get("services", []) if s["name"] == "comfyui"), False),
            "web_search": next((s["running"] for s in svc.get("services", []) if s["name"] == "web_search"), True),
            "firejail": firejail_available() if sandbox_enabled() else False,
            "api_key_required": api_key_enabled(),
        },
        **status,
    }


@app.get("/api/health")
def health(force: bool = False):
    lite = _build_health_lite()
    full = _health_full_cache.get("data")
    full_age = time.time() - _health_full_cache.get("at", 0)

    if force:
        from jarvis.concurrent_pool import background_executor

        background_executor().submit(_refresh_health_full_cache)
    elif full is None or full_age > _HEALTH_FULL_TTL:
        from jarvis.concurrent_pool import background_executor

        if _health_refresh_lock.acquire(blocking=False):
            try:
                background_executor().submit(_refresh_health_full_cache)
            finally:
                _health_refresh_lock.release()

    if full:
        merged = dict(full)
        merged.update(lite)
        return merged
    return lite


@app.get("/api/health/full")
def health_full():
    """Heavy health payload — same as legacy /api/health before diet."""
    payload = _build_health_payload()
    _health_full_cache["data"] = payload
    _health_full_cache["at"] = time.time()
    return payload


@app.get("/api/services")
def services_status():
    from jarvis.services import get_status

    return get_status(force=False)


@app.get("/api/workstation")
def workstation_status():
    from jarvis.workstation.lifecycle import status as ws_status

    return ws_status(force=False)


@app.get("/api/workstation/diagnose")
def workstation_diagnose():
    from jarvis.workstation.operations import diagnose, format_report

    report = diagnose(force=True)
    report["message"] = format_report(force=True)
    return report


@app.post("/api/workstation/up")
def workstation_up(body: dict | None = None):
    from jarvis.workstation.lifecycle import up as ws_up

    body = body or {}
    return ws_up(
        (body.get("component") or body.get("target") or "").strip() or None,
        profile=(body.get("profile") or "").strip() or None,
    )


@app.post("/api/workstation/down")
def workstation_down(body: dict | None = None):
    from jarvis.workstation.lifecycle import down as ws_down

    body = body or {}
    return ws_down(
        (body.get("component") or body.get("target") or "").strip() or None,
        profile=(body.get("profile") or "").strip() or None,
    )


@app.post("/api/workstation/restart")
def workstation_restart(body: dict):
    from jarvis.workstation.lifecycle import restart as ws_restart

    target = (body.get("component") or body.get("target") or "").strip()
    if not target:
        return {"ok": False, "error": "component required"}
    return ws_restart(target)


@app.post("/api/workstation/recover")
def workstation_recover():
    from jarvis.workstation.operations import format_report, recover_safe

    result = recover_safe()
    result["message"] = format_report(force=True)
    return result


@app.get("/api/workstation/inference")
def workstation_inference():
    from jarvis.inference.gateway import gateway_status

    return gateway_status()


@app.get("/api/knowledge/registry")
def knowledge_registry(refresh: bool = False):
    from jarvis.knowledge.registry import format_registry_markdown, registry_snapshot

    snap = registry_snapshot(refresh=refresh)
    snap["message"] = format_registry_markdown(refresh=refresh)
    return snap


@app.post("/api/knowledge/sync")
def knowledge_sync():
    from jarvis.knowledge.registry import sync_registry

    return sync_registry()


@app.get("/api/knowledge/search")
def knowledge_unified_search(q: str = "", limit: int = 12):
    from jarvis.knowledge.search import format_unified_results, unified_search

    if not q.strip():
        return {"ok": False, "error": "q parameter required"}
    result = unified_search(q.strip(), limit=min(limit, 30))
    result["message"] = format_unified_results(result)
    return result


@app.post("/api/knowledge/ingest")
def knowledge_ingest(force: bool = False):
    from jarvis.knowledge.ingestion import ingest_all

    return ingest_all(force=force)


@app.post("/api/knowledge/git-sync")
def knowledge_git_sync(force: bool = False):
    from jarvis.knowledge.git_sync import sync_all

    return sync_all(force=force)


@app.get("/api/knowledge/git-sync")
def knowledge_git_sync_status():
    from jarvis.knowledge.git_sync import list_repo_states, repo_summary_markdown

    states = [s.to_dict() for s in list_repo_states()]
    return {"ok": True, "repos": states, "message": repo_summary_markdown()}


@app.get("/api/tools")
def tools_list():
    from jarvis.tools.executor import tool_status

    return tool_status()


@app.post("/api/tools/execute")
def tools_execute(body: dict):
    from jarvis.tools.executor import execute_tool

    tool_id = (body.get("tool") or body.get("tool_id") or "").strip()
    if not tool_id:
        return {"ok": False, "error": "tool required"}
    return execute_tool(tool_id, body)


@app.post("/api/agents/chain")
def agents_chain(body: dict):
    from jarvis.agents.coordinator import run_agent_chain
    from jarvis.assistant_instance import get_assistant

    goal = (body.get("goal") or "").strip()
    if not goal:
        return {"ok": False, "error": "goal required"}
    roles = body.get("roles")
    return run_agent_chain(get_assistant(), goal, roles=roles)


@app.post("/api/services/ensure")
def services_ensure():
    from jarvis.services import ensure_services
    return ensure_services(pull_models=False)


@app.get("/api/metrics")
def metrics():
    from jarvis.metrics import snapshot

    return snapshot()


@app.get("/api/metrics/prometheus")
def metrics_prometheus():
    from fastapi.responses import PlainTextResponse

    from jarvis.observability.prometheus import prometheus_text

    return PlainTextResponse(prometheus_text(), media_type="text/plain; version=0.0.4")


@app.post("/api/automation/maintenance")
def automation_maintenance(smoke_tests: bool = False):
    from jarvis.automation.ops import run_maintenance

    return run_maintenance(smoke_tests=smoke_tests)


@app.get("/api/automation/maintenance")
def automation_maintenance_status():
    from jarvis.automation.ops import last_maintenance

    return last_maintenance()


@app.get("/api/interfaces/openwebui")
def openwebui_status():
    from jarvis.interfaces.openwebui import inference_url, status

    payload = status()
    payload["inference_url"] = inference_url()
    return payload


@app.get("/api/training/status")
def training_status_api():
    from jarvis.training.workspace import training_status

    return training_status()


@app.get("/api/jobs")
def jobs_center():
    from jarvis.jobs_center import snapshot

    return snapshot()


@app.get("/api/registry/actions")
def actions_registry():
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    return {"ok": True, "actions": all_actions()}


@app.get("/api/registry/router/rules")
def router_rules():
    from jarvis.router_table import list_rules

    return {"ok": True, "rules": list_rules()}


@app.get("/api/debug/bundle")
def debug_bundle():
    from jarvis.debug_bundle import collect

    return collect()


@app.get("/api/vram/preflight")
def vram_preflight(action: str = "video"):
    from jarvis.resource_router import preflight

    return preflight(action)


@app.get("/api/resources")
def resources_status():
    from jarvis.resource_router import snapshot, status_line

    snap = snapshot()
    return {"ok": True, "status_line": status_line(), **snap}


@app.get("/api/comfyui/settings")
def comfyui_settings_get():
    from jarvis.comfyui_settings import get_settings_dict
    from jarvis.services import _comfy_healthy

    data = get_settings_dict()
    data["running"] = _comfy_healthy()
    return data


@app.post("/api/comfyui/settings")
async def comfyui_settings_set(
    mode: str = Form(""),
    checkpoint: str = Form(""),
    checkpoint_file: str = Form(""),
    workflow_file: str = Form(""),
    async_apply: str = Form("1"),
):
    from jarvis.async_util import run_sync
    from jarvis.comfyui_settings_jobs import get_job, submit

    def apply_settings() -> dict:
        from jarvis.comfyui_settings import get_settings_dict, save_workflow_file
        from jarvis.services import set_comfyui_checkpoint, set_comfyui_checkpoint_file, set_comfyui_mode

        result = {}
        try:
            if checkpoint.strip():
                result.update(set_comfyui_checkpoint(checkpoint.strip().lower()))
            elif checkpoint_file.strip():
                result.update(set_comfyui_checkpoint_file(checkpoint_file.strip()))
            if workflow_file.strip():
                save_workflow_file(workflow_file.strip())
            if mode.strip():
                result.update(set_comfyui_mode(mode.strip().lower()))
        except ValueError as exc:
            return {"ok": False, "message": str(exc)}
        if not result:
            return get_settings_dict()
        return result

    use_async = _form_bool(async_apply, default=True)
    if not use_async:
        try:
            return await run_sync(apply_settings)
        except ValueError as e:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(e)})

    job_id = submit("ComfyUI settings", apply_settings)
    return {"ok": True, "pending": True, "job_id": job_id, "message": "Applying ComfyUI settings in background…"}


@app.get("/api/comfyui/settings/job/{job_id}")
def comfyui_settings_job(job_id: str):
    from jarvis.comfyui_settings_jobs import get_job

    job = get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"ok": False, "message": "Job not found"})
    out = {"ok": True, **job}
    if job.get("done") and job.get("result"):
        out.update(job["result"])
    return out


_nsfw_install_proc: subprocess.Popen | None = None
_animatediff_install_proc: subprocess.Popen | None = None


@app.get("/api/comfyui/install-nsfw/status")
def comfyui_install_nsfw_status():
    global _nsfw_install_proc
    log_path = DATA_DIR / "logs" / "nsfw-checkpoints-install.log"
    running = _nsfw_install_proc is not None and _nsfw_install_proc.poll() is None
    tail = ""
    if log_path.is_file():
        try:
            text = log_path.read_text(encoding="utf-8", errors="replace")
            tail = "\n".join(text.splitlines()[-8:])
        except OSError:
            pass
    return {"ok": True, "running": running, "log_tail": tail, "log_path": str(log_path)}


@app.post("/api/comfyui/install-nsfw")
def comfyui_install_nsfw():
    global _nsfw_install_proc
    if _nsfw_install_proc is not None and _nsfw_install_proc.poll() is None:
        return {"ok": True, "message": "Install already running", "running": True}
    script = PROJECT_ROOT / "scripts" / "install-nsfw-checkpoints.sh"
    if not script.is_file():
        return JSONResponse(status_code=404, content={"ok": False, "message": "install script not found"})
    log_dir = DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "nsfw-checkpoints-install.log"
    with open(log_path, "a", encoding="utf-8") as logf:
        logf.write(f"\n--- started {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        _nsfw_install_proc = subprocess.Popen(
            [str(script)],
            cwd=str(PROJECT_ROOT),
            stdout=logf,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    return {"ok": True, "message": "NSFW checkpoint download started (~44 GB)", "running": True}


@app.get("/api/comfyui/install-animatediff/status")
def comfyui_install_animatediff_status():
    global _animatediff_install_proc
    log_path = DATA_DIR / "logs" / "animatediff-install.log"
    running = _animatediff_install_proc is not None and _animatediff_install_proc.poll() is None
    tail = ""
    if log_path.is_file():
        try:
            text = log_path.read_text(encoding="utf-8", errors="replace")
            tail = "\n".join(text.splitlines()[-8:])
        except OSError:
            pass
    from jarvis.comfyui_animatediff import readiness

    return {
        "ok": True,
        "running": running,
        "log_tail": tail,
        "log_path": str(log_path),
        "readiness": readiness(),
    }


@app.post("/api/comfyui/install-animatediff")
def comfyui_install_animatediff():
    global _animatediff_install_proc
    if _animatediff_install_proc is not None and _animatediff_install_proc.poll() is None:
        return {"ok": True, "message": "Install already running", "running": True}
    script = PROJECT_ROOT / "scripts" / "install-animatediff.sh"
    if not script.is_file():
        return JSONResponse(status_code=404, content={"ok": False, "message": "install script not found"})
    log_dir = DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "animatediff-install.log"
    with open(log_path, "a", encoding="utf-8") as logf:
        logf.write(f"\n--- started {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        env = os.environ.copy()
        try:
            from jarvis.gpu_routing import gpu_env_for_subprocess

            for key, value in gpu_env_for_subprocess().items():
                if value == "":
                    env.pop(key, None)
                else:
                    env[key] = value
        except Exception:
            pass
        _animatediff_install_proc = subprocess.Popen(
            [str(script)],
            cwd=str(PROJECT_ROOT),
            stdout=logf,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
    return {"ok": True, "message": "AnimateDiff install started (~2 GB motion module + custom nodes)", "running": True}


@app.get("/api/video/settings")
def video_settings_get():
    from jarvis.video_settings import get_settings_dict

    return get_settings_dict()


@app.post("/api/video/settings")
def video_settings_set(
    duration_sec: str = Form(""),
    fps: str = Form(""),
    width: str = Form(""),
    height: str = Form(""),
    engine: str = Form(""),
    animatediff_frames: str = Form(""),
    keyframe_preset: str = Form(""),
    keyframe_checkpoint: str = Form(""),
):
    from jarvis.video_settings import (
        clear_keyframe_checkpoint,
        get_settings_dict,
        save_keyframe_checkpoint,
        save_keyframe_preset,
        save_settings,
    )

    try:
        if keyframe_preset.strip():
            save_keyframe_preset(keyframe_preset.strip().lower())
        elif keyframe_checkpoint.strip():
            if keyframe_checkpoint.strip() == "__preset__":
                clear_keyframe_checkpoint()
            else:
                save_keyframe_checkpoint(keyframe_checkpoint.strip())
        kwargs = {}
        if duration_sec.strip():
            kwargs["duration_sec"] = float(duration_sec)
        if fps.strip():
            kwargs["fps"] = int(fps)
        if width.strip():
            kwargs["width"] = int(width)
        if height.strip():
            kwargs["height"] = int(height)
        if engine.strip():
            kwargs["engine"] = engine.strip().lower()
        if animatediff_frames.strip():
            kwargs["animatediff_frames"] = int(animatediff_frames)
        if kwargs:
            save_settings(**kwargs)
        return get_settings_dict()
    except ValueError as e:
        return JSONResponse(status_code=400, content={"ok": False, "message": str(e)})


@app.post("/api/video/upload")
async def video_upload(file: UploadFile = File(...)):
    from jarvis.cache_state import invalidate_video_gallery
    from jarvis.video_ops import VIDEO_UPLOAD_DIR, ensure_dirs, safe_video_name

    ensure_dirs()
    name = safe_video_name(file.filename or "upload.mp4")
    dest = VIDEO_UPLOAD_DIR / name
    content = await file.read()
    dest.write_bytes(content)
    invalidate_video_gallery()
    return {"ok": True, "name": name, "path": str(dest)}


@app.get("/api/video/probe")
def video_probe(path: str):
    from jarvis.video_ops import probe

    return probe(path)


@app.post("/api/video/trim")
async def video_trim(
    path: str = Form(...),
    start: str = Form("0"),
    end: str = Form(""),
    duration: str = Form(""),
):
    from jarvis.cache_state import invalidate_video_gallery
    from jarvis.video_ops import trim

    end_f = float(end) if end.strip() else None
    dur_f = float(duration) if duration.strip() else None
    result = trim(path, float(start or 0), end=end_f, duration=dur_f)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    invalidate_video_gallery()
    return {"ok": True, "path": result, "name": Path(result).name}


@app.post("/api/video/analyze-frame")
async def video_analyze_frame(
    path: str = Form(...),
    second: str = Form("0"),
    question: str = Form("Describe this video frame."),
):
    from jarvis.vision_media import build_vision_prompt, extract_video_frame, vision_task_for_question

    p = Path(path).expanduser().resolve()
    if not p.is_file():
        return JSONResponse(status_code=404, content={"ok": False, "message": "File not found"})
    try:
        frame_bytes, frame_name = extract_video_frame(p.read_bytes(), p.name, float(second or 0))
    except ValueError as e:
        return JSONResponse(status_code=400, content={"ok": False, "message": str(e)})
    frame_path = DATA_DIR / "uploads" / frame_name
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    frame_path.write_bytes(frame_bytes)
    task = vision_task_for_question(question)
    prompt = build_vision_prompt(question, task)
    answer = assistant.vision.analyze(prompt, str(frame_path), task=task)
    if answer.startswith("ERROR:"):
        return JSONResponse(status_code=500, content={"ok": False, "message": answer})
    return {"ok": True, "message": answer, "frame_path": str(frame_path)}


@app.get("/api/gpu")
def gpu_status():
    from jarvis.resource_router import snapshot as resource_snapshot, status_line as resource_status_line
    from jarvis.vram_guard import recommendations, status as vram_status

    gpu = detect_gpu()
    gpu["low_vram"] = vram_status()["low_vram"]
    gpu["vram_guard"] = vram_status()
    gpu["tips"] = recommendations()
    gpu["resources"] = resource_snapshot()
    gpu["resource_status_line"] = resource_status_line()
    return gpu


@app.post("/api/gpu/free-vram")
def gpu_free_vram():
    from jarvis.vram_guard import free_vram

    return free_vram()


@app.get("/api/audio/devices")
def audio_devices():
    return detect_devices()


@app.get("/api/audio/status")
def audio_status():
    return {"ok": True, **assistant.audio.status()}


@app.post("/api/audio/detect-language")
async def audio_detect_language(path: str = Form(...), model: str = Form("")):
    from jarvis.audio_whisper import detect_language

    out = detect_language(path, model=model or None)
    if not out.get("ok"):
        return JSONResponse(status_code=400, content={"ok": False, **out})
    return {"ok": True, **out}


@app.post("/api/audio/creative-eq")
async def audio_creative_eq(preset: str = Form("status")):
    import subprocess

    script = PROJECT_ROOT / "scripts" / "apply-creative-eq.sh"
    if not script.is_file():
        return JSONResponse(status_code=404, content={"ok": False, "message": "EQ script not found"})
    try:
        proc = subprocess.run(
            [str(script), preset.strip() or "status"],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=str(PROJECT_ROOT),
        )
        return {
            "ok": proc.returncode == 0,
            "preset": preset,
            "output": (proc.stdout or proc.stderr or "").strip(),
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "message": str(e)})


@app.get("/api/audio/vst/status")
def audio_vst_status():
    from jarvis.audio_vst import status as vst_status
    from jarvis.audio_vst_live import live_status

    return {"ok": True, **vst_status(), "live": live_status()}


@app.post("/api/audio/vst/playback-chain")
async def audio_vst_playback_chain(chain: str = Form("flat")):
    from jarvis.audio_settings import VST_PLAYBACK_CHAINS, save_settings

    chain_id = (chain or "flat").strip().lower()
    if chain_id not in VST_PLAYBACK_CHAINS:
        return JSONResponse(status_code=400, content={"ok": False, "message": f"Unknown chain: {chain_id}"})
    save_settings({"vst_playback_chain": chain_id})
    return {"ok": True, "playback_chain": chain_id}


@app.post("/api/audio/vst/process")
async def audio_vst_process(path: str = Form(...), chain: str = Form("voice")):
    from jarvis.audio_vst import process_file

    result = process_file(path, chain)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    return {"ok": True, "audio_path": result, "path": result, "chain": chain}


@app.post("/api/audio/vst/live")
async def audio_vst_live(preset: str = Form("off"), install: str = Form("0")):
    from jarvis.audio_vst_live import activate_live, deactivate_live, install_filter_configs

    if install.strip().lower() in ("1", "true", "yes"):
        ok, msg = install_filter_configs()
        if not ok:
            return JSONResponse(status_code=400, content={"ok": False, "message": msg})
    preset = (preset or "off").strip().lower()
    if preset in ("off", "none", "direct"):
        ok, msg = deactivate_live()
    else:
        ok, msg = activate_live(preset)
    if not ok:
        return JSONResponse(status_code=400, content={"ok": False, "message": msg})
    from jarvis.audio_vst_live import live_status

    return {"ok": True, "message": msg, "live": live_status()}


@app.post("/api/audio/vst/register-plugin")
async def audio_vst_register_plugin(name: str = Form(...), path: str = Form(...)):
    from jarvis.audio_vst import register_vst_plugin

    try:
        entry = register_vst_plugin(name, path)
    except (FileNotFoundError, RuntimeError) as e:
        return JSONResponse(status_code=400, content={"ok": False, "message": str(e)})
    return {"ok": True, "plugin": entry}


@app.post("/api/image/upscale")
async def image_upscale(path: str = Form(...), scale: int = Form(2)):
    job_id = assistant._enqueue_media(
        "upscale_image",
        {"path": path, "scale": scale},
        f"upscale {scale}x",
    )
    return {"ok": True, "job_id": job_id["job_id"], "pending": True, "message": job_id["message"]}


@app.get("/api/media/status")
def media_status():
    from jarvis.media_jobs import busy_state, list_recent

    return {"ok": True, **busy_state(), "recent": list_recent(5)}


@app.get("/api/media/job/{job_id}")
def media_job_status(job_id: str):
    from jarvis.media_jobs import get_job

    job = get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"ok": False, "message": "Job not found"})
    out = {"ok": True, **job}
    if job.get("done") and job.get("result"):
        out["result"] = job["result"]
    return out


@app.post("/api/media/job/{job_id}/cancel")
def media_job_cancel(job_id: str):
    from jarvis.media_jobs import cancel_job

    if not cancel_job(job_id):
        return JSONResponse(status_code=400, content={"ok": False, "message": "Cannot cancel"})
    return {"ok": True}


@app.get("/api/coding/status")
def coding_status():
    from jarvis.coding_jobs import job_stats, list_recent

    return {"ok": True, **job_stats(), "recent": list_recent(5)}


@app.post("/api/coding/job/{job_id}/cancel")
def coding_job_cancel(job_id: str):
    from jarvis.coding_jobs import cancel_job

    if not cancel_job(job_id):
        return JSONResponse(status_code=400, content={"ok": False, "message": "Cannot cancel"})
    return {"ok": True}


@app.get("/api/coding/job/{job_id}")
def coding_job_status(job_id: str):
    from jarvis.coding_jobs import get_job

    job = get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"ok": False, "message": "Job not found"})
    out = {"ok": True, **job}
    if job.get("done") and job.get("result"):
        out["result"] = job["result"]
    return out


@app.post("/api/meme/generate")
async def meme_generate(payload: dict = Body(...)):
    top = str(payload.get("top") or "").strip()
    bottom = str(payload.get("bottom") or "").strip()
    idea = str(payload.get("idea") or payload.get("prompt") or "").strip()
    image_prompt = str(payload.get("image_prompt") or "").strip()
    use_ai = payload.get("use_ai_image", True)
    preview_only = payload.get("preview_only", False)
    if isinstance(use_ai, str):
        use_ai = use_ai.lower() not in ("0", "false", "no")
    if isinstance(preview_only, str):
        preview_only = preview_only.lower() in ("1", "true", "yes")

    if preview_only:
        from jarvis.modules.meme import MemeEngine

        if not top and not bottom:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "message": "Need top or bottom text for preview"},
            )
        engine = MemeEngine()
        path = engine.preview_text_only(top, bottom)
        if path.startswith("ERROR:"):
            return JSONResponse(status_code=400, content={"ok": False, "message": path})
        return {
            "ok": True,
            "path": path,
            "image_path": path,
            "image_name": Path(path).name,
        }

    queued = assistant._enqueue_media(
        "generate_meme",
        {
            "top": top,
            "bottom": bottom,
            "idea": idea,
            "image_prompt": image_prompt,
            "use_ai_image": use_ai,
            "background_path": payload.get("background_path"),
        },
        idea or f"{top} {bottom}".strip(),
    )
    return {"ok": True, "job_id": queued["job_id"], "pending": True, "message": queued["message"]}


def _resolve_image_path(path: str) -> Path | None:
    from jarvis.config import DATA_DIR

    for sub in ("generated", "uploads", "inpaint_masks"):
        root = (DATA_DIR / sub).resolve()
        candidate = Path(path).expanduser().resolve()
        if root in candidate.parents and candidate.is_file():
            return candidate
    return None


@app.post("/api/image/inpaint")
async def image_inpaint(
    path: str = Form(...),
    prompt: str = Form(...),
    region: str = Form(""),
    denoise: float = Form(0.85),
    mask: UploadFile | None = File(None),
):
    import json as _json

    from jarvis.cache_state import invalidate_gallery
    from jarvis.image_post import inpaint_region

    src = _resolve_image_path(path)
    if not src:
        return JSONResponse(status_code=400, content={"ok": False, "message": "Image path not allowed or not found"})

    region_dict = None
    if region.strip():
        try:
            region_dict = _json.loads(region)
        except _json.JSONDecodeError:
            return JSONResponse(status_code=400, content={"ok": False, "message": "Invalid region JSON"})

    mask_path = None
    if mask and mask.filename:
        upload_dir = DATA_DIR / "inpaint_masks"
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest = upload_dir / f"upload_{Path(mask.filename).name}"
        dest.write_bytes(await mask.read())
        mask_path = str(dest)

    queued = assistant._enqueue_media(
        "inpaint_image",
        {
            "path": str(src),
            "mask_path": mask_path,
            "prompt": prompt.strip(),
            "region": region_dict,
            "denoise": denoise,
        },
        prompt.strip(),
    )
    return {"ok": True, "job_id": queued["job_id"], "pending": True, "message": queued["message"]}


@app.post("/api/image/edit")
async def image_edit(
    path: str = Form(...),
    prompt: str = Form(...),
    denoise: float = Form(0.58),
):
    src = _resolve_image_path(path)
    if not src:
        return JSONResponse(status_code=400, content={"ok": False, "message": "Image path not allowed or not found"})

    queued = assistant._enqueue_media(
        "edit_image",
        {
            "path": str(src),
            "prompt": prompt.strip(),
            "denoise": denoise,
        },
        prompt.strip(),
    )
    return {"ok": True, "job_id": queued["job_id"], "pending": True, "message": queued["message"]}


@app.post("/api/audio/record")
async def audio_record(duration: float = Form(5.0), source: str = Form("")):
    from jarvis.async_util import run_sync

    result = await run_sync(assistant.audio.record, duration, source=source or None)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    assistant.session.note_audio(result)
    from jarvis.audio_device import measure_peak_db
    peak = measure_peak_db(Path(result))
    return {"ok": True, "audio_path": result, "peak_db": peak, "message": "Recording saved"}


@app.post("/api/audio/record-transcribe")
async def audio_record_transcribe(
    duration: float = Form(5.0), model: str = Form(""), source: str = Form(""), language: str = Form(""),
):
    path, text = assistant.audio.record_and_transcribe(
        duration, model=model or None, source=source or None, language=language or None,
    )
    if path.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": path})
    from jarvis.audio_device import measure_peak_db
    peak = measure_peak_db(Path(path)) if not path.startswith("ERROR:") else None
    if text.startswith("ERROR:"):
        return JSONResponse(
            status_code=400,
            content={"ok": False, "message": text, "audio_path": path, "peak_db": peak},
        )
    assistant.session.note_audio(path)
    return {"ok": True, "audio_path": path, "transcript": text, "peak_db": peak}


@app.post("/api/audio/probe-capture")
async def audio_probe_capture(duration: float = Form(2.0), source: str = Form("")):
    from jarvis.audio_device import probe_capture

    return probe_capture(source=source or None, duration_sec=duration)


@app.post("/api/audio/mic-profile")
async def audio_set_mic_profile(profile: str = Form("rear")):
    from jarvis.audio_device import capture_volume_for, effective_input_source, mic_routing_status
    from jarvis.audio_settings import MIC_PROFILES, mic_profile_info, save_settings

    key = profile.strip().lower()
    if key not in MIC_PROFILES:
        return JSONResponse(status_code=400, content={"ok": False, "message": f"Unknown profile: {profile}"})
    info = mic_profile_info(key)
    save_settings({
        "mic_profile": key,
        "creative_capture_volume": info.get("default_capture_volume", "100%"),
    })
    assistant.audio.get_devices()
    routing = mic_routing_status()
    return {
        "ok": True,
        "profile": key,
        "label": info["label"],
        "hint": info["hint"],
        "capture_volume": capture_volume_for(effective_input_source()),
        "mic_routing": routing,
    }


@app.post("/api/audio/capture-volume")
async def audio_set_capture_volume(volume: str = Form(""), source: str = Form("")):
    from jarvis.audio_device import capture_volume_for, effective_input_source, prepare_input_source
    from jarvis.audio_settings import save_settings

    src = (source or effective_input_source()).strip()
    vol = volume.strip() or capture_volume_for(src)
    if _is_creative_input_api(src):
        save_settings({"creative_capture_volume": vol})
    else:
        save_settings({"capture_volume": vol})
    prepare_input_source(src)
    return {"ok": True, "source": src, "capture_volume": capture_volume_for(src)}


def _is_creative_input_api(source: str) -> bool:
    from jarvis.audio_device import _is_creative_input
    return _is_creative_input(source)


@app.post("/api/audio/input-source")
async def audio_set_input_source(source: str = Form("")):
    from jarvis.audio_device import effective_input_source, list_input_sources
    from jarvis.audio_settings import save_settings

    name = source.strip()
    if name:
        valid = {s["name"] for s in list_input_sources()}
        if valid and name not in valid:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "message": f"Unknown input source: {name}"},
            )
        save_settings({"input_source": name})
    else:
        save_settings({"input_source": ""})
    assistant.audio.get_devices()
    return {"ok": True, "input_source": effective_input_source()}


@app.post("/api/audio/transcribe")
async def audio_transcribe(path: str = Form(...), model: str = Form(""), language: str = Form("")):
    result = assistant.audio.transcribe(path, model=model or None, language=language or None)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    return {"ok": True, "transcript": result, "path": path}


@app.post("/api/audio/transcribe-upload")
async def audio_transcribe_upload(file: UploadFile = File(...), model: str = Form("")):
    upload_dir = DATA_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe = Path(file.filename or "audio.wav").name
    dest = upload_dir / safe
    content = await file.read()
    if not content:
        return JSONResponse(status_code=400, content={"ok": False, "message": "Empty file"})
    dest.write_bytes(content)
    result = assistant.audio.transcribe(str(dest), model=model or None)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    assistant.session.note_audio(str(dest))
    return {"ok": True, "transcript": result, "path": str(dest)}


@app.post("/api/audio/generate")
async def audio_generate(text: str = Form(...), auto_play: str = Form("1")):
    play = auto_play.lower() not in ("0", "false", "no")
    result = assistant.audio.generate(text.strip(), auto_play=play)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    assistant.session.note_audio(result)
    return {"ok": True, "audio_path": result, "message": "Speech generated"}


@app.get("/api/audio/recent")
def audio_recent():
    from jarvis.modules.audio import EDITED_DIR, GENERATED_DIR, RECORDINGS_DIR
    from jarvis.music_gen import MUSIC_DIR
    from jarvis.song_studio import SONGS_DIR

    def _list(folder: Path, limit: int = 8) -> list[dict]:
        if not folder.exists():
            return []
        files = sorted(
            (f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return [{"name": f.name, "path": str(f)} for f in files[:limit]]

    return {
        "recordings": _list(RECORDINGS_DIR),
        "generated": _list(GENERATED_DIR),
        "edited": _list(EDITED_DIR),
        "music": _list(MUSIC_DIR),
        "songs": _list(SONGS_DIR),
    }


@app.delete("/api/audio/file")
def audio_delete_file(path: str, category: str = ""):
    result = assistant.audio.delete_file(path, category=category or None)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    return {"ok": True, "deleted": result, "message": "File deleted"}


@app.post("/api/audio/delete")
async def audio_delete_post(path: str = Form(...), category: str = Form("")):
    result = assistant.audio.delete_file(path, category=category or None)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    return {"ok": True, "deleted": result, "message": "File deleted"}


@app.post("/api/audio/speak")
async def audio_speak(text: str = Form(...)):
    """Generate TTS and play through Creative Sound Blaster."""
    result = assistant.audio.generate(text.strip())
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    return {
        "ok": True,
        "message": f"Playing on {assistant.audio.devices.get('name', 'Creative')}",
        "audio_path": result,
        "devices": assistant.audio.get_devices(),
    }


@app.post("/api/audio/play")
async def audio_play(path: str = Form("")):
    target = path.strip() or assistant.audio.last_output
    if not target:
        return JSONResponse(status_code=400, content={"ok": False, "message": "No audio file specified"})
    result = assistant.audio.play(target)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    return {"ok": True, "message": "Playing", "audio_path": result}


@app.post("/api/audio/whisper-model")
async def audio_set_whisper_model(model: str = Form("base")):
    from jarvis.audio_settings import WHISPER_MODELS, save_settings

    key = model.strip().lower()
    if key not in WHISPER_MODELS:
        return JSONResponse(status_code=400, content={"ok": False, "message": f"Unknown model: {model}"})
    save_settings({"whisper_model": key})
    return {"ok": True, "whisper_model": key}


@app.post("/api/audio/edit")
async def audio_edit(
    path: str = Form(...),
    instruction: str = Form(""),
    start_sec: float = Form(-1),
    end_sec: float = Form(-1),
    normalize: str = Form("0"),
):
    result = assistant.audio.edit(
        path,
        instruction=instruction.strip(),
        start_sec=start_sec if start_sec >= 0 else None,
        end_sec=end_sec if end_sec >= 0 else None,
        normalize=normalize.lower() in ("1", "true", "yes"),
    )
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    assistant.session.note_audio(result)
    return {"ok": True, "audio_path": result, "message": "Edited audio saved"}


@app.post("/api/audio/analyze")
async def audio_analyze(path: str = Form(...), model: str = Form("")):
    result = assistant.audio.analyze(path, model=model or None)
    if not result.get("ok"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result.get("error", "Analyze failed")})
    return {"ok": True, **result}


@app.post("/api/audio/convert")
async def audio_convert(path: str = Form(...), output: str = Form(...)):
    result = assistant.audio.convert(path, output)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    assistant.session.note_audio(result)
    return {"ok": True, "audio_path": result, "message": "Converted"}


@app.get("/api/audio/waveform")
def audio_waveform(path: str, samples: int = 200):
    result = assistant.audio.waveform(path, samples=samples)
    if not result.get("ok"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result.get("error", "Waveform failed")})
    return result


@app.post("/api/audio/record-vad")
async def audio_record_vad(
    max_duration: float = Form(30.0),
    threshold_db: float = Form(-40.0),
    min_silence: float = Form(0.8),
    source: str = Form(""),
    transcribe: str = Form("0"),
    model: str = Form(""),
):
    result = assistant.audio.record_vad(
        max_duration,
        threshold_db=threshold_db,
        min_silence_sec=min_silence,
        source=source or None,
    )
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    from jarvis.audio_device import measure_peak_db
    peak = measure_peak_db(Path(result))
    assistant.session.note_audio(result)
    payload = {"ok": True, "audio_path": result, "peak_db": peak, "message": "VAD recording saved"}
    if transcribe.lower() in ("1", "true", "yes"):
        text = assistant.audio.transcribe(result, model=model or None)
        if text.startswith("ERROR:"):
            payload["transcript_error"] = text
        else:
            payload["transcript"] = text
    return payload


@app.post("/api/audio/record/ptt/start")
async def audio_ptt_start(source: str = Form("")):
    session_id, path_or_err = assistant.audio.record_ptt_start(source=source or None)
    if not session_id:
        return JSONResponse(status_code=400, content={"ok": False, "message": path_or_err})
    return {"ok": True, "session_id": session_id, "expected_path": path_or_err}


@app.post("/api/audio/record/ptt/stop")
async def audio_ptt_stop(session_id: str = Form(...), transcribe: str = Form("0"), model: str = Form("")):
    result = assistant.audio.record_ptt_stop(session_id.strip())
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    from jarvis.audio_device import measure_peak_db
    peak = measure_peak_db(Path(result))
    assistant.session.note_audio(result)
    payload = {"ok": True, "audio_path": result, "peak_db": peak, "message": "Push-to-talk recording saved"}
    if transcribe.lower() in ("1", "true", "yes"):
        text = assistant.audio.transcribe(result, model=model or None)
        if text.startswith("ERROR:"):
            payload["transcript_error"] = text
        else:
            payload["transcript"] = text
    return payload


@app.post("/api/audio/journal-from-transcript")
async def audio_journal_from_transcript(text: str = Form(...), bullet_type: str = Form("note")):
    bullet = assistant.journal.daily_add(text.strip(), bullet_type or "note")
    return {"ok": True, "bullet": bullet}


@app.get("/api/audio/music/status")
def audio_music_status():
    from jarvis.music_gen import install_hint, musicgen_available, musicgen_backend

    installed = musicgen_available()
    backend = musicgen_backend()
    return {
        "ok": True,
        "installed": installed,
        "backend": backend,
        "model": os.getenv("JARVIS_MUSICGEN_MODEL", "facebook/musicgen-small"),
        "hint": "" if installed else install_hint(),
    }


@app.post("/api/audio/music")
async def audio_music(prompt: str = Form(...), duration: int = Form(10)):
    from jarvis import music_gen

    result = music_gen.generate_music(prompt.strip(), duration=min(max(duration, 5), 30))
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    assistant.session.note_audio(result)
    return {"ok": True, "audio_path": result, "message": "Music generated"}


@app.post("/api/audio/whisper-language")
async def audio_set_whisper_language(language: str = Form("en")):
    from jarvis.audio_settings import WHISPER_LANGUAGES, save_settings
    key = language.strip().lower()
    if key not in WHISPER_LANGUAGES:
        return JSONResponse(status_code=400, content={"ok": False, "message": f"Unknown language: {language}"})
    save_settings({"whisper_language": key})
    return {"ok": True, "whisper_language": key}


@app.post("/api/audio/piper-speed")
async def audio_set_piper_speed(speed: float = Form(1.0)):
    from jarvis.audio_settings import save_settings
    speed = max(0.5, min(2.0, float(speed)))
    save_settings({"piper_speed": speed})
    return {"ok": True, "piper_speed": speed}


@app.get("/api/audio/session")
def audio_get_session():
    from jarvis.audio_session import load_session
    return {"ok": True, "session": load_session()}


@app.post("/api/audio/session")
async def audio_save_session(
    audio_path: str = Form(""),
    transcript: str = Form(""),
    summary: str = Form(""),
):
    from jarvis.audio_session import save_session
    patch = {}
    if audio_path:
        patch["audio_path"] = audio_path
    if transcript:
        patch["transcript"] = transcript
    if summary:
        patch["summary"] = summary
    return {"ok": True, "session": save_session(patch)}


@app.get("/api/audio/search")
def audio_search(q: str = "", limit: int = 20):
    from jarvis.audio_search import search
    return {"ok": True, "results": search(q, limit=limit)}


@app.post("/api/audio/batch-transcribe")
async def audio_batch_transcribe(paths: str = Form(...), model: str = Form(""), language: str = Form("")):
    path_list = [p.strip() for p in paths.splitlines() if p.strip()]
    if not path_list:
        return JSONResponse(status_code=400, content={"ok": False, "message": "No paths provided"})
    results = assistant.audio.batch_transcribe(path_list, model=model or None, language=language or None)
    return {"ok": True, "results": results}


@app.get("/api/audio/job/{job_id}")
def audio_job_status(job_id: str):
    from jarvis.audio_progress import get_job
    job = get_job(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"ok": False, "message": "Unknown job"})
    return {"ok": True, **job}


@app.post("/api/audio/job/{job_id}/cancel")
def audio_job_cancel(job_id: str):
    from jarvis.audio_progress import cancel_job, finish_job

    if not cancel_job(job_id):
        return JSONResponse(status_code=404, content={"ok": False, "message": "Job not found or already finished"})
    finish_job(job_id, error="Cancelled by user")
    return {"ok": True, "cancelled": True}


def _run_audio_job(fn):
    from jarvis.concurrent_pool import background_executor
    background_executor().submit(fn)


@app.post("/api/audio/song/genre")
async def audio_song_genre(
    path: str = Form(...),
    genre: str = Form(...),
    duration: int = Form(30),
    async_job: str = Form("1"),
):
    from jarvis.audio_progress import finish_job, start_job

    if async_job.lower() in ("1", "true", "yes"):
        job_id = start_job("Genre transform")
        def run():
            try:
                result = assistant.audio.transform_genre(path, genre, duration=duration, job_id=job_id)
                if result.startswith("ERROR:"):
                    finish_job(job_id, error=result)
                else:
                    assistant.session.note_audio(result)
                    finish_job(job_id, result={"audio_path": result})
            except Exception as e:
                from jarvis.audio_progress import JobCancelled
                finish_job(job_id, error="Cancelled by user" if isinstance(e, JobCancelled) else str(e))
        _run_audio_job(run)
        return {"ok": True, "job_id": job_id, "message": "Genre transform started"}
    result = assistant.audio.transform_genre(path, genre, duration=duration)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    assistant.session.note_audio(result)
    return {"ok": True, "audio_path": result}


@app.get("/api/audio/song/limits")
def audio_song_limits(duration: int = 30):
    from jarvis.ml_memory import song_generation_plan

    return {"ok": True, **song_generation_plan(duration)}


@app.post("/api/audio/song/full")
async def audio_song_full(
    topic: str = Form(...),
    genre: str = Form("pop"),
    mood: str = Form("uplifting"),
    duration: int = Form(30),
    async_job: str = Form("1"),
):
    from jarvis.audio_progress import start_job

    if async_job.lower() in ("1", "true", "yes"):
        job_id = start_job("Full song")
        def run():
            from jarvis.audio_progress import finish_job
            try:
                result = assistant.audio.generate_full_song(
                    topic.strip(), genre=genre, mood=mood, duration=duration, job_id=job_id,
                )
                if result.get("ok") and result.get("audio_path"):
                    assistant.session.note_audio(result["audio_path"])
                elif not result.get("ok"):
                    finish_job(job_id, error=result.get("error", "Song generation failed"))
            except Exception as e:
                from jarvis.audio_progress import JobCancelled
                finish_job(job_id, error="Cancelled by user" if isinstance(e, JobCancelled) else str(e))
        _run_audio_job(run)
        return {"ok": True, "job_id": job_id, "message": "Song generation started"}
    result = assistant.audio.generate_full_song(topic.strip(), genre=genre, mood=mood, duration=duration)
    if not result.get("ok"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result.get("error", "Failed")})
    assistant.session.note_audio(result.get("audio_path", ""))
    return {"ok": True, **result}


@app.post("/api/audio/podcast/mix")
async def audio_podcast_mix(
    backing_path: str = Form(...),
    vocal_path: str = Form(""),
    vocal_gain_db: float = Form(2.0),
    title: str = Form("podcast_mix"),
):
    from jarvis.song_studio import mix_podcast_tracks

    vocal = vocal_path.strip() or assistant.session.last_audio or assistant.audio.last_output
    if not vocal:
        return JSONResponse(status_code=400, content={"ok": False, "message": "No vocal track — record audio or pass vocal_path"})
    result = mix_podcast_tracks(backing_path, vocal, vocal_gain_db=vocal_gain_db, title=title)
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    assistant.session.note_audio(result)
    return {"ok": True, "audio_path": result, "message": f"Mixed podcast track saved to `{result}`"}


@app.post("/api/audio/song/voice")
async def audio_song_voice(
    path: str = Form(""),
    lyrics: str = Form(""),
    title: str = Form(""),
    style: str = Form("pop ballad"),
    genre: str = Form("pop"),
    duration: int = Form(30),
    async_job: str = Form("1"),
):
    from jarvis.audio_progress import finish_job, start_job

    voice_path = path.strip() or assistant.audio.last_output
    if not voice_path:
        return JSONResponse(status_code=400, content={"ok": False, "message": "No voice recording specified"})
    if async_job.lower() in ("1", "true", "yes"):
        job_id = start_job("Voice to song")
        def run():
            try:
                result = assistant.audio.voice_to_song(
                    voice_path, lyrics=lyrics, title=title, style=style,
                    genre=genre, duration=duration, job_id=job_id,
                )
                if result.get("ok") and result.get("audio_path"):
                    assistant.session.note_audio(result["audio_path"])
                elif not result.get("ok"):
                    finish_job(job_id, error=result.get("error", "Failed"))
            except Exception as e:
                from jarvis.audio_progress import JobCancelled
                finish_job(job_id, error="Cancelled by user" if isinstance(e, JobCancelled) else str(e))
        _run_audio_job(run)
        return {"ok": True, "job_id": job_id, "message": "Voice-to-song started"}
    result = assistant.audio.voice_to_song(
        voice_path, lyrics=lyrics, title=title, style=style, genre=genre, duration=duration,
    )
    if not result.get("ok"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result.get("error", "Failed")})
    assistant.session.note_audio(result.get("audio_path", ""))
    return {"ok": True, **result}


@app.post("/api/audio/journal-with-audio")
async def audio_journal_with_audio(
    text: str = Form(...),
    audio_path: str = Form(""),
    bullet_type: str = Form("note"),
):
    note = text.strip()
    if audio_path.strip():
        note = f"{note}\n\n🎧 `{audio_path.strip()}`"
    bullet = assistant.journal.daily_add(note, bullet_type or "note")
    return {"ok": True, "bullet": bullet}


@app.get("/api/audio/torch-device")
def audio_torch_device():
    from jarvis.torch_device import device_info
    return {"ok": True, **device_info()}


@app.get("/api/audio/vocals/status")
def audio_vocals_status():
    from jarvis.audio_vocals import bark_available, install_hint, xtts_available
    return {
        "ok": True,
        "bark": bark_available(),
        "xtts": xtts_available(),
        "hint": install_hint(),
    }


@app.post("/api/audio/vocals/generate")
async def audio_vocals_generate(
    text: str = Form(...),
    engine: str = Form("auto"),
    speaker_wav: str = Form(""),
):
    from datetime import datetime

    from jarvis.audio_vocals import VOCALS_DIR, generate_vocals_for_song

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = VOCALS_DIR / f"vocal_{stamp}.wav"
    result = generate_vocals_for_song(
        text, out, engine=engine, speaker_wav=speaker_wav or None,
    )
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    assistant.session.note_audio(result)
    return {"ok": True, "audio_path": result}


@app.get("/api/audio/diarize/status")
def audio_diarize_status():
    from jarvis.audio_diarize import diarize_status
    return {"ok": True, **diarize_status()}


@app.post("/api/audio/diarize")
async def audio_diarize(path: str = Form(...), num_speakers: int = Form(0)):
    result = assistant.audio.diarize(path, num_speakers=num_speakers or None)
    if not result.get("ok"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result.get("error", "Failed")})
    return {"ok": True, **result}


@app.get("/api/audio/transcribe-stream")
def audio_transcribe_stream(path: str, model: str = "", language: str = ""):
    import json as _json

    from jarvis.audio_whisper import transcribe_stream_events

    def gen():
        for ev in transcribe_stream_events(path, model=model or None, language=language or None):
            yield f"data: {_json.dumps(ev)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/api/audio/record/live/start")
async def audio_live_start(source: str = Form("")):
    from jarvis.audio_live import start_live_record
    sid, path_or_err = start_live_record(source=source or None)
    if not sid:
        return JSONResponse(status_code=400, content={"ok": False, "message": path_or_err})
    return {"ok": True, "session_id": sid, "expected_path": path_or_err}


@app.get("/api/audio/record/live/level")
def audio_live_level(session_id: str):
    from jarvis.audio_live import live_level
    return live_level(session_id)


@app.post("/api/audio/record/live/stop")
async def audio_live_stop(
    session_id: str = Form(...),
    transcribe: str = Form("1"),
    model: str = Form(""),
    language: str = Form(""),
):
    from jarvis.audio_device import measure_peak_db
    from jarvis.audio_live import live_level, stop_live_record

    partial = live_level(session_id).get("partial_text", "")
    result = stop_live_record(session_id.strip())
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    peak = measure_peak_db(Path(result))
    assistant.session.note_audio(result)
    payload = {"ok": True, "audio_path": result, "peak_db": peak, "partial_transcript": partial}
    if transcribe.lower() in ("1", "true", "yes"):
        text = assistant.audio.transcribe(result, model=model or None, language=language or None)
        if text.startswith("ERROR:"):
            payload["transcript_error"] = text
        else:
            payload["transcript"] = text
    return payload


@app.get("/api/audio/wakeword/status")
def audio_wakeword_status():
    from jarvis.audio_wakeword import status as ww_status
    return {"ok": True, **ww_status()}


@app.post("/api/audio/wakeword/start")
async def audio_wakeword_start():
    from jarvis.audio_wakeword import start_listener

    result = start_listener()  # default handler sends desktop notification
    if result.startswith("ERROR:"):
        return JSONResponse(status_code=400, content={"ok": False, "message": result})
    return {"ok": True, "message": result}


@app.post("/api/audio/wakeword/stop")
async def audio_wakeword_stop():
    from jarvis.audio_wakeword import stop_listener
    stop_listener()
    return {"ok": True}


@app.get("/api/suggestions")
def suggestions():
    return {
        "suggestions": [
            "What can you do?",
            "Describe this screenshot",
            "Read all text in this image",
            "Implement fizzbuzz in data/scripts/fizzbuzz.py with tests",
            "fix selection",
            "debug until tests pass for data/scripts/foo.py",
        ],
        "memory_chips": [
            "List cheatsheets",
            "Memory cheatsheet",
            "What do you remember about me?",
            "Correct that …",
            "Forget about …",
            "Remember strategy: keep answers concise",
            "Tell me something I like to do",
            "Search my memory for preferences",
            "Summarize this conversation to memory",
            "Save where I left off",
            "Where did I leave off?",
            "Set memory namespace work",
            "Prune stale memories",
        ],
        "journal_chips": [
            "Morning briefing",
            "Journal today",
            "What are my open tasks?",
            "Log: • finish taxes",
            "Reflect on my week",
            "Search journal for meeting",
            "Journal cheatsheet",
        ],
        "data_chips": [
            "Summarize this warranty PDF",
            "Learn about: edge AI accelerators",
            "House status",
            "Turn off the living room lights",
            "I'm heading out",
            "What does the warranty say about coverage?",
            "How many rows are there?",
            "Describe this data",
            "Chart the first numeric column",
            "Export results to CSV",
            "Export report to PDF",
            "Clean duplicates and nulls",
        ],
        "vision_chips": [
            "Describe this screenshot",
            "Read all text in this image",
            "Structured OCR (tables/forms)",
            "What's in the top-left region?",
            "Convert this UI to HTML",
            "Remember what this image says",
        ],
    }


@app.get("/api/vision/settings")
def vision_settings_get():
    from jarvis.config import load_vision_quality
    from jarvis.gpu import detect_gpu, is_low_vram
    gpu = detect_gpu()
    return {
        "ok": True,
        "quality_mode": load_vision_quality(),
        "model": assistant.get_status().get("models", {}).get("vision"),
        "low_vram": is_low_vram(),
        "vram_gb": round((gpu.get("vram_mb") or 0) / 1024, 1),
    }


@app.post("/api/vision/settings")
async def vision_settings_post(quality_mode: str = Form("fast")):
    from jarvis.config import save_vision_quality
    save_vision_quality(quality_mode)
    return {"ok": True, "quality_mode": quality_mode, "model": assistant.get_status().get("models", {}).get("vision")}


@app.get("/api/models")
def models_info():
    from jarvis.capabilities import models_guide
    from jarvis.model_store import get_all_settings
    status = assistant.get_status()
    return {
        "guide": models_guide(),
        "active": status.get("models", {}),
        "missing": status.get("models_missing", []),
        "ollama_running": status.get("ollama", {}).get("running", False),
        "settings": get_all_settings(),
    }


@app.get("/api/models/settings")
def get_model_settings():
    from jarvis.model_store import get_all_settings
    return get_all_settings()


@app.post("/api/models/settings")
async def save_model_settings(
    mode: str = Form("standard"),
    general: str = Form(""),
    coder: str = Form(""),
    review: str = Form(""),
    vision: str = Form(""),
    image: str = Form(""),
    embed: str = Form(""),
):
    from jarvis.model_store import update_models
    models = {k: v for k, v in {
        "general": general, "coder": coder, "review": review,
        "vision": vision, "image": image, "embed": embed,
    }.items() if v}
    if vision.strip():
        from jarvis.config import save_vision_quality
        save_vision_quality("custom")
    return {"ok": True, "settings": update_models(mode, models)}


@app.post("/api/models/preset")
async def apply_preset_endpoint(preset: str = Form(...), mode: str = Form("")):
    from jarvis.model_store import apply_preset
    m = mode if mode in ("standard", "uncensored") else None
    return {"ok": True, "settings": apply_preset(preset, m)}


@app.post("/api/models/reset")
async def reset_models(mode: str = Form("")):
    from jarvis.model_store import reset_to_optimized
    m = mode if mode in ("standard", "uncensored") else None
    return {"ok": True, "settings": reset_to_optimized(m)}


@app.post("/api/models/refresh")
def refresh_models():
    from jarvis.model_store import get_all_settings
    return {"ok": True, "settings": get_all_settings()}


@app.post("/api/models/pull")
async def pull_model_endpoint(model: str = Form(...)):
    from jarvis.async_util import stream_sync_iter
    from jarvis.model_pull import pull_model

    async def event_stream():
        async for event in stream_sync_iter(lambda: pull_model(model), thread_name="jarvis-model-pull"):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/models/pull-missing")
async def pull_missing():
    from jarvis.async_util import stream_sync_iter
    from jarvis.model_pull import pull_model
    from jarvis.model_store import get_missing_models

    missing = get_missing_models()
    if not missing:
        return {"ok": True, "message": "All active models are installed.", "pulled": []}

    def produce():
        for model in missing:
            yield {"type": "model_start", "model": model}
            yield from pull_model(model)
        yield {"type": "all_done", "ok": True}

    async def event_stream():
        async for event in stream_sync_iter(produce, thread_name="jarvis-model-pull"):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/uncensored/auth")
def uncensored_auth_status(request: Request, session_token: str = ""):
    from jarvis.uncensored_auth import auth_status

    client_id = request.client.host if request.client else "local"
    return auth_status(session_token, client_id=client_id)


@app.post("/api/uncensored/reset")
def uncensored_reset_password():
    """Clear uncensored password so a new one can be set (standard mode only)."""
    if is_uncensored():
        return JSONResponse(
            status_code=400,
            content={"ok": False, "message": "Turn off uncensored mode before resetting the password."},
        )
    from jarvis.uncensored_auth import clear_password

    clear_password()
    return {"ok": True, "message": "Uncensored password cleared. Toggle uncensored to set a new one."}


@app.post("/api/mode")
async def set_mode(
    request: Request,
    uncensored: str = Form("false"),
    password: str = Form(""),
    confirm_password: str = Form(""),
    session_token: str = Form(""),
):
    enabling = uncensored.lower() in ("true", "1", "yes")
    new_session = session_token
    client_id = request.client.host if request.client else "local"

    if enabling:
        from jarvis.uncensored_auth import try_enable

        token, err = try_enable(password, session_token, confirm_password, client_id=client_id)
        if err:
            return JSONResponse(
                status_code=403,
                content={
                    "ok": False,
                    "message": err,
                    "auth_required": True,
                    "uncensored": is_uncensored(),
                },
            )
        new_session = token
    else:
        from jarvis.uncensored_auth import invalidate_all_sessions, invalidate_session

        if session_token:
            invalidate_session(session_token)
        invalidate_all_sessions()

    assistant.set_uncensored(enabling)
    from jarvis.comfyui_settings import get_settings_dict

    status = assistant.get_status()
    status["comfyui_settings"] = get_settings_dict()
    status["session_token"] = new_session if enabling else ""
    return {"ok": True, **status}


def _form_bool(value: str, *, default: bool = False) -> bool:
    if value is None or str(value).strip() == "":
        return default
    return str(value).lower() in ("true", "1", "yes", "on")


@app.get("/api/chat/model")
def chat_model_get():
    from jarvis import llm
    return {
        "chat_model": assistant.session.chat_model or "",
        "default": llm.general_model(),
    }


@app.post("/api/chat/model")
async def chat_model_set(model: str = Form("")):
    name = model.strip()
    assistant.session.note_chat_model(name)
    assistant.branches.save_session(assistant.branches.active_id, assistant.session)
    from jarvis import llm
    return {
        "ok": True,
        "chat_model": name,
        "effective": name or llm.general_model(),
    }


@app.post("/api/chat/cancel")
async def chat_cancel(request_id: str = Form(...)):
    from jarvis.chat_cancel import cancel

    cancel(request_id.strip())
    return {"ok": True}


@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    file: UploadFile | None = File(None),
    file2: UploadFile | None = File(None),
    stream: str = Form("false"),
    branch_id: str = Form(""),
    crop: str = Form(""),
    video_second: str = Form(""),
    pdf_page: str = Form(""),
    request_id: str = Form(""),
    lite_ui: str = Form("false"),
):
    import json as _json

    crop_dict = None
    if crop.strip():
        try:
            crop_dict = _json.loads(crop)
        except _json.JSONDecodeError:
            crop_dict = None

    vsec = None
    if video_second.strip():
        try:
            vsec = float(video_second.strip())
        except ValueError:
            vsec = None
    ppage = None
    if pdf_page.strip():
        try:
            ppage = max(1, int(pdf_page.strip()))
        except ValueError:
            ppage = None

    attachment = None
    attachment2 = None
    if file and file.filename:
        content = await file.read()
        attachment = assistant.save_upload(
            file.filename, content, crop=crop_dict,
            video_second=vsec, pdf_page=ppage, message=message,
        )
        if attachment and ppage and attachment.get("kind") == "document":
            attachment["pdf_page"] = ppage
    if file2 and file2.filename:
        content2 = await file2.read()
        attachment2 = assistant.save_upload(
            file2.filename, content2, message=message,
            video_second=vsec, pdf_page=ppage,
        )

    use_stream = _form_bool(stream)
    use_lite_ui = _form_bool(lite_ui)
    bid = branch_id.strip() or None

    if use_stream:
        rid = request_id.strip()
        from jarvis.async_util import stream_sync_iter

        def _sse_payload(event: dict) -> str:
            try:
                return _json.dumps(event, default=str)
            except Exception as exc:
                return _json.dumps({
                    "type": "done",
                    "ok": False,
                    "message": f"Could not encode response: {exc}",
                })

        async def event_stream():
            from jarvis.chat_cancel import begin

            if rid:
                begin(rid)
            yield f"data: {_sse_payload({'type': 'status', 'message': 'Processing…'})}\n\n"
            try:
                async for event in stream_sync_iter(
                    lambda: assistant.process_stream(
                        message,
                        attachment,
                        branch_id=bid,
                        attachment2=attachment2,
                        request_id=rid,
                        lite_ui=use_lite_ui,
                    ),
                    thread_name="jarvis-chat-stream",
                ):
                    yield f"data: {_sse_payload(event)}\n\n"
            except Exception as e:
                yield f"data: {_sse_payload({'type': 'done', 'ok': False, 'message': str(e)})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    try:
        return await asyncio.to_thread(
            assistant.process, message, attachment, bid, attachment2,
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "message": str(e)})


@app.post("/api/apply")
async def apply_proposal(proposal_id: str = Form(""), force: str = Form("false")):
    from jarvis.async_util import run_sync

    return await run_sync(
        assistant.apply_proposal,
        proposal_id or None,
        force=force.lower() in ("1", "true", "yes"),
    )


@app.get("/api/proposals/{proposal_id}")
async def get_proposal(proposal_id: str):
    from jarvis.async_util import run_sync

    return await run_sync(assistant.proposal_diff, proposal_id)


@app.get("/favicon.ico")
async def favicon():
    for path in (STATIC_DIR / "favicon.svg", ASSETS_DIR / "jarvis-icon.svg"):
        if path.exists():
            return FileResponse(path, media_type="image/svg+xml")
    return JSONResponse(status_code=404, content={"detail": "not found"})


@app.get("/")
async def index():
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def serve(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True):
    """Run server only (used by daemon/tray)."""
    from jarvis.lan import client_base_url, is_lan_bind, lan_status

    host = os.getenv("JARVIS_HOST", host)
    port = int(os.getenv("JARVIS_PORT", port))
    ollama = check_ollama()
    gpu = detect_gpu()
    mode = "UNCENSORED" if is_uncensored() else "Standard"
    url = client_base_url(host, port)

    from jarvis.branding import assistant_name

    print(f"\n  {assistant_name()} GUI v{APP_VERSION} ({mode})")
    print(f"  → {url}")
    if is_lan_bind(host):
        status = lan_status()
        for connect in status.get("connect_urls") or []:
            print(f"  LAN → {connect}")
        if status.get("api_key_required"):
            print("  API key required for /api/* (enter once in the browser)")
        else:
            print("  WARNING: set JARVIS_API_KEY before using LAN URLs")
    print()
    if ollama["running"]:
        print(f"  Ollama: OK ({len(ollama['models'])} models)")
    else:
        print("  Ollama: starting automatically…")
    if gpu.get("ollama_using_gpu"):
        print(f"  GPU: active ({gpu.get('name', '')})")
    elif gpu.get("vendor") == "amd":
        print(f"  GPU: {gpu.get('name', 'AMD')} — {gpu.get('recommendation', '')}")

    if open_browser and os.getenv("JARVIS_NO_BROWSER") != "1" and client_base_url(host, port).startswith("http://127.0.0.1"):
        from jarvis.gui_launcher import open_gui

        open_gui(url)
    uvicorn.run(app, host=host, port=port, log_level="info")


def main(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True):
    serve(host=host, port=port, open_browser=open_browser)
