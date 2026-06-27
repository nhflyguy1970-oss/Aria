"""FunctionGemma intent router — HF tool-calling to ARIA actions (~50ms on CPU)."""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any

from jarvis.p1_flags import local_router_enabled
from jarvis.session import SessionContext

log = logging.getLogger("jarvis.functiongemma")

_DEVELOPER_PROMPT = (
    "You are a model that can do function calling with the following functions"
)

# Core fast-route actions (same set as local_router).
_ROUTER_ACTIONS = (
    "system_info",
    "morning_briefing",
    "planner_add_task",
    "planner_set_timer",
    "planner_set_alarm",
    "planner_today",
    "curated_briefing",
    "audio_stop",
    "audio_pause",
    "ha_control",
    "ha_status",
    "web_search",
    "weather_forecast",
    "generate_cad",
    "iterate_cad",
    "chat",
    "thinking",
    "nonthinking",
)

_ACTION_DESCRIPTIONS: dict[str, str] = {
    "system_info": "System status, GPU, Ollama, services",
    "morning_briefing": "Morning briefing with weather and calendar",
    "planner_add_task": "Add a task to the planner",
    "planner_set_timer": "Start a countdown timer",
    "planner_set_alarm": "Set an alarm for a time",
    "planner_today": "Show today's planner items",
    "curated_briefing": "Curated news briefing",
    "audio_stop": "Stop audio playback",
    "audio_pause": "Pause audio playback",
    "ha_control": "Control a smart home device or room",
    "ha_status": "Smart home status",
    "web_search": "Search the web",
    "weather_forecast": "Weather forecast for a location",
    "generate_cad": "Generate a new 3D CAD part or STL from a description",
    "iterate_cad": "Modify or iterate the current CAD design (taller, thicker, holes, etc.)",
    "chat": "General conversation when no tool fits",
    "thinking": "Route to deep reasoning chat",
    "nonthinking": "Route to fast chat",
}

_ACTION_PROPERTIES: dict[str, dict[str, dict[str, str]]] = {
    "planner_add_task": {
        "text": {"type": "string", "description": "Task text"},
    },
    "planner_set_timer": {
        "duration": {"type": "string", "description": "e.g. 10 minutes"},
        "label": {"type": "string", "description": "Optional timer label"},
    },
    "planner_set_alarm": {
        "time": {"type": "string", "description": "e.g. 7am tomorrow"},
        "label": {"type": "string", "description": "Optional alarm label"},
    },
    "ha_control": {
        "target": {"type": "string", "description": "Device or room name"},
        "action": {"type": "string", "description": "on, off, or toggle"},
    },
    "web_search": {
        "query": {"type": "string", "description": "Search query"},
    },
    "weather_forecast": {
        "location": {"type": "string", "description": "City or place"},
    },
    "generate_cad": {
        "prompt": {"type": "string", "description": "Part or object to design"},
        "backend": {"type": "string", "description": "auto, build123d, openscad, or meshy"},
    },
    "iterate_cad": {
        "prompt": {"type": "string", "description": "Change to apply to the current design"},
        "model_id": {"type": "string", "description": "Optional existing model id"},
    },
}

_CALL_RE = re.compile(
    r"<start_function_call>\s*call:(?P<name>[\w]+)\s*\{(?P<args>[^}]*)\}\s*<end_function_call>",
    re.DOTALL,
)
_JSON_CALL_RE = re.compile(r"call:(?P<name>[\w]+)\s*\{(?P<args>[^}]*)\}")

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 120.0

_BASE_FG_MODEL = "google/functiongemma-270m-it"
_PROBE_UTTERANCE = "what's on my planner today"

_HF_MODEL: Any = None
_HF_PROCESSOR: Any = None
_HF_MODEL_ID: str | None = None
_HF_LOAD_FAILED = False
_USING_FALLBACK = False
_PARSE_PROBE_DONE = False
_PARSE_PROBE_OK: bool | None = None
_LOAD_LOCK = threading.Lock()


def router_backend() -> str:
    """auto | functiongemma | ollama"""
    return (os.getenv("JARVIS_ROUTER_BACKEND") or "auto").strip().lower()


def functiongemma_model_id() -> str:
    return (os.getenv("JARVIS_FUNCTIONGEMMA_MODEL") or _BASE_FG_MODEL).strip()


def active_model_id() -> str:
    """Model actually loaded (may differ from env when fallback is active)."""
    if _HF_MODEL_ID:
        return _HF_MODEL_ID
    if _USING_FALLBACK:
        return _BASE_FG_MODEL
    return functiongemma_model_id()


def _resolve_device() -> str:
    device = (os.getenv("JARVIS_FUNCTIONGEMMA_DEVICE") or "auto").strip().lower()
    if device == "auto":
        import torch

        if getattr(torch.version, "hip", None):
            return "cpu"
        device = "cuda" if torch.cuda.is_available() else "cpu"
    return device


def hf_available() -> bool:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401

        return True
    except ImportError:
        return False


def model_cached() -> bool:
    model_id = functiongemma_model_id()
    if Path(model_id).is_dir():
        return True
    try:
        from huggingface_hub import try_to_load_from_cache

        return try_to_load_from_cache(model_id, "config.json") is not None
    except Exception:
        return False


def functiongemma_ready() -> bool:
    if not hf_available():
        return False
    if _HF_MODEL is not None and _PARSE_PROBE_OK:
        return True
    if _HF_LOAD_FAILED:
        return False
    if Path(functiongemma_model_id()).is_dir():
        return True
    return model_cached()


def build_tool_schema(action: str, *, description: str | None = None) -> dict[str, Any]:
    props = dict(_ACTION_PROPERTIES.get(action, {}))
    desc = description or _ACTION_DESCRIPTIONS.get(action) or action.replace("_", " ")
    return {
        "type": "function",
        "function": {
            "name": action,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": list(props.keys()) if props else [],
            },
        },
    }


def build_router_tool_schemas() -> list[dict[str, Any]]:
    """Core fast-route tools only (smaller prompt → better base-model accuracy)."""
    return [build_tool_schema(action) for action in _ROUTER_ACTIONS]


def build_tool_schemas(*, limit: int = 32) -> list[dict[str, Any]]:
    """Tool list for FunctionGemma from core router actions + registered handlers."""
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    schemas: list[dict[str, Any]] = []
    seen: set[str] = set()

    for action in _ROUTER_ACTIONS:
        if action in seen:
            continue
        seen.add(action)
        schemas.append(build_tool_schema(action))

    for row in all_actions():
        name = row.get("action") or ""
        if not name or name in seen or row.get("info"):
            continue
        if not row.get("registered") and not row.get("queue"):
            continue
        seen.add(name)
        schemas.append(
            build_tool_schema(
                name,
                description=(row.get("description") or name.replace("_", " ")).strip(),
            )
        )
        if len(schemas) >= limit:
            break
    return schemas


def _parse_call_args(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    text = re.sub(r"<escape>(.*?)</escape>", r"\1", text, flags=re.DOTALL)
    text = text.replace("<escape>", "").replace("</escape>", "")
    if not text:
        return {}
    if text.startswith("{"):
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            pass
    params: dict[str, Any] = {}
    for part in re.split(r",\s*(?=\w+:)", text):
        if ":" not in part:
            continue
        key, _, val = part.partition(":")
        key = key.strip().strip('"').strip("'")
        val = val.strip().strip('"').strip("'")
        if key:
            params[key] = val
    return params


def parse_function_call(raw: str) -> dict[str, Any] | None:
    """Parse FunctionGemma tool output to {action, params, thinking}."""
    text = (raw or "").strip()
    if not text:
        return None

    m = _CALL_RE.search(text) or _JSON_CALL_RE.search(text)
    if not m:
        parsed = _parse_json_intent(text)
        return parsed

    action = m.group("name")
    params = _parse_call_args(m.group("args"))
    return _normalize_intent(action, params, thinking=f"functiongemma:{action}")


def _parse_json_intent(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(text[start:end])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or "action" not in data:
        return None
    return _normalize_intent(
        str(data.get("action") or "chat"),
        data.get("params") if isinstance(data.get("params"), dict) else {},
        thinking=str(data.get("thinking") or "json"),
    )


def _normalize_intent(action: str, params: dict[str, Any], *, thinking: str) -> dict[str, Any]:
    action = (action or "chat").strip()
    if action == "thinking":
        return {
            "action": "chat",
            "params": {"thinking_mode": "deep"},
            "thinking": "deep chat",
        }
    if action == "nonthinking":
        return {
            "action": "chat",
            "params": {"thinking_mode": "fast"},
            "thinking": "fast chat",
        }
    if action == "iterate_cad":
        params = dict(params or {})
        params.setdefault("edit", True)
        if not params.get("prompt"):
            return {
                "action": "chat",
                "params": {},
                "thinking": "iterate_cad missing prompt",
            }
        return {
            "action": "iterate_cad",
            "params": params,
            "thinking": thinking,
        }
    if action not in _ROUTER_ACTIONS and action != "chat":
        from jarvis.handlers.registry import has_action

        if not has_action(action):
            return {
                "action": "chat",
                "params": {},
                "thinking": f"unknown tool {action}",
            }
    return {
        "action": action,
        "params": dict(params or {}),
        "thinking": thinking,
    }


def _apply_voice_tuning(parsed: dict[str, Any], message: str, session: SessionContext) -> dict[str, Any]:
    if not getattr(session, "voice_mode", False):
        return parsed
    from jarvis.brain_routing import needs_deep_thinking

    params = parsed.setdefault("params", {})
    if params.get("thinking_mode") != "deep" and not needs_deep_thinking(message):
        params["thinking_mode"] = "fast"
        params["voice"] = True
        parsed["thinking"] = parsed.get("thinking") or "voice fast"
    return parsed


def _unload_hf() -> None:
    global _HF_MODEL, _HF_PROCESSOR, _HF_MODEL_ID
    _HF_MODEL = None
    _HF_PROCESSOR = None
    _HF_MODEL_ID = None


def _load_hf_weights(model_id: str) -> bool:
    global _HF_MODEL, _HF_PROCESSOR, _HF_MODEL_ID, _HF_LOAD_FAILED
    if not hf_available():
        _HF_LOAD_FAILED = True
        return False
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor

        device = _resolve_device()
        # ROCm half-precision can emit pad-only garbage on small models — prefer fp32.
        use_fp16 = device == "cuda" and not getattr(torch.version, "hip", None)
        dtype = torch.float16 if use_fp16 else torch.float32

        log.info("Loading FunctionGemma %s on %s", model_id, device)
        processor = AutoProcessor.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id, dtype=dtype)
        model.to(device)
        model.eval()

        _HF_PROCESSOR = processor
        _HF_MODEL = model
        _HF_MODEL_ID = model_id
        _HF_LOAD_FAILED = False
        return True
    except Exception as exc:
        log.warning("FunctionGemma load failed (%s): %s", model_id, exc)
        _unload_hf()
        return False


def _probe_parseable() -> bool:
    if _HF_MODEL is None or _HF_PROCESSOR is None:
        return False
    try:
        tools = build_router_tool_schemas()
        raw = _generate_hf(_PROBE_UTTERANCE, tools)
        return parse_function_call(raw) is not None
    except Exception as exc:
        log.debug("FunctionGemma parse probe failed: %s", exc)
        return False


def _load_hf() -> bool:
    global _HF_LOAD_FAILED, _USING_FALLBACK, _PARSE_PROBE_DONE, _PARSE_PROBE_OK
    if _HF_LOAD_FAILED:
        return False
    if _HF_MODEL is not None and _HF_PROCESSOR is not None:
        return True

    with _LOAD_LOCK:
        if _HF_LOAD_FAILED:
            return False
        if _HF_MODEL is not None and _HF_PROCESSOR is not None:
            return True

        configured = functiongemma_model_id()
        candidates = [configured]
        if configured != _BASE_FG_MODEL:
            candidates.append(_BASE_FG_MODEL)

        for idx, model_id in enumerate(candidates):
            if idx > 0:
                _unload_hf()
                _USING_FALLBACK = True
                log.warning(
                    "FunctionGemma %s failed — falling back to %s",
                    configured,
                    model_id,
                )
            if not _load_hf_weights(model_id):
                continue
            if _probe_parseable():
                _PARSE_PROBE_DONE = True
                _PARSE_PROBE_OK = True
                _HF_LOAD_FAILED = False
                return True
            log.warning("FunctionGemma %s failed parse probe", model_id)

        _unload_hf()
        _PARSE_PROBE_DONE = True
        _PARSE_PROBE_OK = False
        _HF_LOAD_FAILED = True
        return False


def _generate_hf(message: str, tools: list[dict[str, Any]]) -> str:
    import torch

    if not _load_hf():
        raise RuntimeError("FunctionGemma model not loaded")

    msgs = [
        {"role": "developer", "content": _DEVELOPER_PROMPT},
        {"role": "user", "content": message},
    ]
    inputs = _HF_PROCESSOR.apply_chat_template(
        msgs,
        tools=tools,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )
    device = _HF_MODEL.device
    inputs = {k: v.to(device) if hasattr(v, "to") else v for k, v in inputs.items()}

    max_tokens = int(os.getenv("JARVIS_FUNCTIONGEMMA_MAX_TOKENS", "96"))
    with torch.inference_mode():
        out = _HF_MODEL.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
        )
    in_len = inputs["input_ids"].shape[-1]
    # Keep special tokens — FunctionGemma function calls use <start_function_call> etc.
    return _HF_PROCESSOR.decode(out[0][in_len:], skip_special_tokens=False).strip()


def try_functiongemma_route(message: str, session: SessionContext) -> dict[str, Any] | None:
    """Route via FunctionGemma tool calling. Returns None on miss or error."""
    if not local_router_enabled():
        return None
    text = (message or "").strip()
    if not text or len(text) > 280 or text.count("\n") > 2:
        return None

    cache_key = text.lower()
    cached = _CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < _CACHE_TTL:
        return dict(cached[1])

    if not _load_hf():
        return None

    try:
        tools = build_router_tool_schemas()
        t0 = time.perf_counter()
        raw = _generate_hf(text, tools)
        ms = int((time.perf_counter() - t0) * 1000)
        parsed = parse_function_call(raw)
        if not parsed:
            return None
        from jarvis.router_hints import contradicts_hint, try_hint_route

        if contradicts_hint(text, str(parsed.get("action") or "")):
            override = try_hint_route(text)
            if override:
                parsed = override
                parsed["router"] = "functiongemma+hint"
        parsed = _apply_voice_tuning(parsed, text, session)
        parsed["router_ms"] = ms
        parsed["router"] = "functiongemma"
        _CACHE[cache_key] = (time.time(), parsed)
        return parsed
    except Exception as exc:
        log.debug("FunctionGemma route skipped: %s", exc)
        return None


def warm_model() -> dict[str, Any]:
    """Pre-load HF weights (first-run / health)."""
    global _HF_LOAD_FAILED, _PARSE_PROBE_DONE, _PARSE_PROBE_OK
    if _HF_MODEL is None:
        _HF_LOAD_FAILED = False
        _PARSE_PROBE_DONE = False
        _PARSE_PROBE_OK = None
    ok = _load_hf()
    parse_ok = bool(_PARSE_PROBE_OK) if _PARSE_PROBE_DONE else False
    return {
        "ok": ok and parse_ok,
        "model": functiongemma_model_id(),
        "active_model": active_model_id(),
        "fallback": _USING_FALLBACK,
        "parse_probe": parse_ok,
        "hf": hf_available(),
        "cached": model_cached(),
        "device": _resolve_device() if hf_available() else None,
    }


def router_status() -> dict[str, Any]:
    return {
        "backend": router_backend(),
        "model": functiongemma_model_id(),
        "active_model": active_model_id(),
        "fallback": _USING_FALLBACK,
        "hf_available": hf_available(),
        "ready": functiongemma_ready(),
        "loaded": _HF_MODEL is not None,
        "parse_probe": _PARSE_PROBE_OK,
        "device": _resolve_device() if hf_available() else None,
        "tools": len(build_tool_schemas()),
        "cache_entries": len(_CACHE),
    }
