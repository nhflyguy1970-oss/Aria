import json
import os
import re
from typing import Iterator

from ollama import chat, embed, generate

from jarvis.config import SYSTEM_PROMPT
from jarvis.model_store import model_for

# Ollama Python client expects sampling params inside `options`, not top-level kwargs.
_CHAT_OPTION_KEYS = frozenset(
    {
        "temperature",
        "num_predict",
        "top_k",
        "top_p",
        "repeat_penalty",
        "seed",
        "num_ctx",
        "stop",
        "min_p",
        "tfs_z",
        "typical_p",
        "presence_penalty",
        "frequency_penalty",
        "mirostat",
        "mirostat_tau",
        "mirostat_eta",
    }
)


def _normalize_chat_kwargs(kwargs: dict) -> dict:
    """Move Ollama sampling params from top-level kwargs into `options`."""
    out = dict(kwargs)
    options = dict(out.pop("options", None) or {})
    for key in list(out.keys()):
        if key in _CHAT_OPTION_KEYS:
            options[key] = out.pop(key)
    if options:
        out["options"] = options
    return out


def _with_system(messages: list[dict]) -> list[dict]:
    if messages and messages[0].get("role") == "system":
        return messages
    return [{"role": "system", "content": SYSTEM_PROMPT}, *messages]


def usage_from_response(response: dict) -> dict:
    """Token/timing stats from an Ollama chat/generate response."""
    out: dict = {}
    if response.get("prompt_eval_count") is not None:
        out["prompt_tokens"] = int(response["prompt_eval_count"])
    if response.get("eval_count") is not None:
        out["completion_tokens"] = int(response["eval_count"])
    total_ns = response.get("total_duration")
    if total_ns:
        out["total_duration_ms"] = int(total_ns) // 1_000_000
    return out


def ask(model: str, messages: list[dict], **kwargs) -> str:
    text, _ = ask_with_usage(model, messages, **kwargs)
    return text


def ask_with_usage(model: str, messages: list[dict], **kwargs) -> tuple[str, dict]:
    from jarvis.inference.gateway import chat_with_usage

    role = kwargs.pop("role", "general")
    return chat_with_usage(model, messages, role=role, **kwargs)


def ask_with_system(model: str, system: str, user: str, **kwargs) -> str:
    """LLM call with a custom system prompt (no Jarvis chat persona)."""
    try:
        response = chat(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            **_normalize_chat_kwargs(kwargs),
        )
        return response["message"]["content"]
    except Exception as e:
        raise RuntimeError(
            f"Ollama error with model '{model}': {e}. "
            "Is Ollama running? Try: ollama serve"
        ) from e


def ask_stream(
    model: str,
    messages: list[dict],
    *,
    cancel_key: str = "",
    usage: dict | None = None,
    **kwargs,
) -> Iterator[str]:
    try:
        from jarvis.chat_cancel import is_cancelled
        from jarvis.inference.gateway import stream_chat
        from jarvis.inference.policy import select_route

        role = kwargs.pop("role", "general")
        route = select_route(model, role=role, messages=messages)
        if route.backend == "litellm":
            for content in stream_chat(model, messages, role=role, route=route, **kwargs):
                if cancel_key and is_cancelled(cancel_key):
                    break
                if content:
                    yield content
            return

        stream = chat(
            model=route.model,
            messages=_with_system(messages),
            stream=True,
            **_normalize_chat_kwargs(kwargs),
        )
        for chunk in stream:
            if cancel_key and is_cancelled(cancel_key):
                break
            if usage is not None:
                usage.update(usage_from_response(chunk))
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
    except Exception as e:
        raise RuntimeError(
            f"Ollama error with model '{model}': {e}. "
            "Is Ollama running? Try: ollama serve"
        ) from e


def generate_text(model: str, prompt: str, **kwargs) -> str:
    response = generate(model=model, prompt=prompt, **kwargs)
    return response["response"]


def embed_available() -> bool:
    """True if the embed model returns a non-empty vector."""
    return bool(embed_text("ping"))


_embed_warned = False


def embed_text(text: str) -> list[float]:
    global _embed_warned
    try:
        response = embed(model=model_for("embed"), input=text)
        return response["embeddings"][0]
    except Exception as exc:
        if not _embed_warned:
            import logging

            logging.getLogger("jarvis").warning(
                "Embedding model unavailable (%s) — memory search may be degraded",
                exc,
            )
            _embed_warned = True
        return []


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


ROUTER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "route_request",
            "description": "Route user request to the correct Jarvis action",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action name e.g. chat, coding_fix, remember, describe_image",
                    },
                    "params": {
                        "type": "object",
                        "description": "Action parameters",
                    },
                    "needs_clarification": {
                        "type": "boolean",
                        "description": "True if user must pick between options",
                    },
                    "clarification_question": {"type": "string"},
                    "choices": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["action", "params"],
            },
        },
    }
]


def route_with_tools(message: str, context: str, attachment: dict | None) -> dict | None:
    """Use Ollama tool calling for routing when supported."""
    attachment_context = json.dumps(attachment) if attachment else "none"
    prompt = (
        "Route this request. Use coding_chat only for questions about the Jarvis project's "
        "source code — not general hardware/AI topics (VPUs, GPUs, LLMs, etc.). "
        "Use chat for general knowledge.\n"
        f"Session context: {context}\n"
        f"Attachment: {attachment_context}\n"
        f"User: {message}"
    )
    try:
        response = chat(
            model=general_model(),
            messages=[{"role": "user", "content": prompt}],
            tools=ROUTER_TOOLS,
        )
        tool_calls = response.get("message", {}).get("tool_calls") or []
        if tool_calls:
            args = tool_calls[0].get("function", {}).get("arguments", "{}")
            if isinstance(args, str):
                args = json.loads(args)
            elif not isinstance(args, dict):
                args = {}
            action = args.get("action", "chat")
            if isinstance(action, dict):
                args["action"] = str(action.get("name") or action.get("action") or "chat")
            elif not isinstance(action, str) or not action.strip():
                args["action"] = "chat"
            if not isinstance(args.get("params"), dict):
                args["params"] = {}
            args.setdefault("params", {})
            args["thinking"] = "tool_call"
            return args
    except Exception as exc:
        import logging

        logging.getLogger("jarvis").warning("Tool router failed, falling back: %s", exc)
    return None


def extract_memories(text: str) -> list[str]:
    """Auto-extract memorable facts from conversation."""
    prompt = (
        "Extract durable facts about the USER only — name, preferences, tools, habits, projects. "
        "Skip generic chat summaries, questions, assistant replies, and one-off tasks. "
        "Each fact must be a complete sentence starting with 'User' or 'The user'. "
        "Max 2 facts. "
        'Return JSON only: {"facts": ["fact1"]}. '
        "Empty array if nothing personal and durable.\n\n"
        f"Text: {text}"
    )
    try:
        raw = ask(general_model(), [{"role": "user", "content": prompt}])
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        data = json.loads(raw)
        return [f for f in data.get("facts", []) if isinstance(f, str) and len(f) > 3]
    except Exception:
        return []


def is_valid_python(code: str) -> bool:
    if not code or not code.strip():
        return False
    try:
        compile(code, "<generated>", "exec")
        return True
    except SyntaxError:
        return False


def sanitize_python_code(text: str) -> str:
    """Strip markdown fences and prose; return executable Python only."""
    text = text.strip()
    if "CODE:" in text:
        text = text.split("CODE:", 1)[1].strip()

    fence = re.search(r"```(?:python)?\s*\n([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    else:
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text.strip())

    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue
        if re.match(
            r"^(#|import |from |def |class |@|if __name__|\"\"\"|'''|[\w.]+\s*=)",
            s,
        ):
            start = i
            break
    code = "\n".join(lines[start:]).strip()
    return code if is_valid_python(code) else ""


def parse_code_response(response_text: str) -> tuple[str, str]:
    text = response_text.strip()

    if "CODE:" in text:
        parts = text.split("CODE:", 1)
        explanation = parts[0].replace("EXPLANATION:", "").strip()
        explanation = re.sub(r"^[-*]\s*", "", explanation, flags=re.M).strip()
        code = sanitize_python_code(parts[1])
        if explanation and explanation.lower() not in ("no explanation provided.", "- what the script does"):
            return explanation, code
        return "Script ready to apply.", code

    code = sanitize_python_code(text)
    return "Script ready to apply.", code


CODER_SYSTEM = (
    "You write Python. Output ONLY valid Python source code — "
    "no markdown, no code fences, no prose before or after code."
)

CODER_FIX_SYSTEM = (
    "You fix Python files so tests pass. Output the COMPLETE corrected file only.\n"
    "No markdown fences, no SEARCH/REPLACE blocks, no English prose in the output.\n"
    "Change only what is needed to fix the errors."
)

CODER_MULTI_SYSTEM = (
    "You write Python scripts and pytest tests. Use exactly this format:\n\n"
    "FILE: relative/path.py\n"
    "CODE:\n"
    "<python only>\n\n"
    "FILE: relative/path/test_file.py\n"
    "CODE:\n"
    "<pytest tests only>\n\n"
    "No markdown fences. Tests must use pytest.\n"
    "When script and test share a folder, import by module filename only "
    "(e.g. `from fizzbuzz import run`, never `from scripts.fizzbuzz import`). "
    "Do not import unused modules."
)

CODER_PATCH_SYSTEM = (
    "You edit code with minimal changes. Prefer SEARCH/REPLACE hunks over full rewrites.\n"
    "CRITICAL: EXPLANATION is the only place for English prose. "
    "SEARCH, REPLACE, and CODE blocks must contain ONLY valid source code — "
    "never markdown, Docker/shell instructions, or documentation.\n"
    "Format:\n\n"
    "EXPLANATION: brief summary\n\n"
    "FILE: relative/path.py\n"
    "SEARCH:\n"
    "<exact lines to find>\n"
    "REPLACE:\n"
    "<replacement lines>\n\n"
    "Use multiple SEARCH/REPLACE blocks per file if needed. "
    "SEARCH text must match the file exactly. "
    "If a full rewrite is simpler, use FILE/CODE instead.\n\n"
    "FILE: path.py\n"
    "CODE:\n"
    "<complete valid file contents>"
)

CODER_MULTI_EDIT_SYSTEM = (
    "You edit multiple files in a project. Use FILE/SEARCH/REPLACE or FILE/CODE blocks.\n"
    "Keep changes minimal. Update imports and tests when needed.\n"
    "Same format as patch edits but multiple FILE blocks."
)

CODER_DIAGNOSE_SYSTEM = (
    "You are a senior engineer. Diagnose the code — do NOT write fixed code.\n"
    "Explain: what is wrong, where, why, and concrete steps to fix.\n"
    "Use bullet points. Reference line numbers when possible."
)

CODING_CHAT_SYSTEM = (
    "You are Jarvis coding assistant with access to project context.\n"
    "Answer questions about the codebase clearly. Cite file paths.\n"
    "If the user wants changes, describe what you would change but say they can ask you to fix/implement it.\n"
    "Do not invent files that are not in the context."
)

CODE_EXTENSIONS_LANG = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/React",
    ".jsx": "JavaScript/React",
    ".sh": "Shell",
    ".rs": "Rust",
    ".go": "Go",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
}


def generate_python_code(
    task: str,
    *,
    existing: str | None = None,
    errors: str | None = None,
) -> tuple[str, str]:
    """Generate or edit a single Python file. Returns (explanation, code)."""
    if existing:
        user = f"Task: {task}\n\nCurrent file:\n{existing}"
        if errors:
            user += f"\n\nRuntime errors:\n{errors}"
    else:
        user = f"Write a Python script: {task}"
    raw = ask_with_system(coder_model(), CODER_SYSTEM, user)
    explanation, code = parse_code_response(raw)
    return explanation, sanitize_python_code(code)


def generate_python_fix(
    task: str,
    *,
    existing: str,
    errors: str | None = None,
    context: str = "",
) -> tuple[str, str]:
    """Full-file rewrite optimized for making pytest pass."""
    user = f"Task: {task}\n\nCurrent file:\n{existing}"
    if context:
        user += f"\n\nRelated context:\n{context}"
    if errors:
        user += f"\n\nErrors (must fix all):\n{errors}"
    raw = ask_with_system(coder_model(), CODER_FIX_SYSTEM, user)
    explanation, code = parse_code_response(raw)
    return explanation, sanitize_python_code(code)


def _lang_for_path(path: str) -> str:
    from pathlib import Path
    return CODE_EXTENSIONS_LANG.get(Path(path).suffix.lower(), "code")


def generate_patched_edit(
    task: str,
    *,
    path: str,
    content: str,
    context: str = "",
    errors: str | None = None,
) -> tuple[str, list[dict]]:
    """Generate patch-style or full-file edit. Returns (explanation, file_items)."""
    lang = _lang_for_path(path)
    user = f"Task: {task}\nLanguage: {lang}\n\nPrimary file ({path}):\n{content}"
    if context:
        user += f"\n\nRelated context:\n{context}"
    if errors:
        user += f"\n\nErrors to fix:\n{errors}"
    raw = ask_with_system(coder_model(), CODER_PATCH_SYSTEM, user)
    return _parse_patch_or_code_response(raw, default_path=path)


def generate_multi_file_edit(
    task: str,
    *,
    context: str = "",
    errors: str | None = None,
) -> tuple[str, list[dict]]:
    """Generate multi-file edits. Returns (explanation, file_items)."""
    user = f"Task: {task}"
    if context:
        user += f"\n\nProject context:\n{context}"
    if errors:
        user += f"\n\nErrors from last attempt:\n{errors}"
    raw = ask_with_system(coder_model(), CODER_MULTI_EDIT_SYSTEM, user)
    return _parse_patch_or_code_response(raw)


def _parse_patch_or_code_response(raw: str, default_path: str = "") -> tuple[str, list[dict]]:
    """Parse patch hunks or FILE/CODE blocks."""
    from jarvis.patch_util import parse_search_replace_blocks

    text = raw.strip()
    explanation = ""
    if "EXPLANATION:" in text:
        parts = text.split("EXPLANATION:", 1)[1]
        if "FILE:" in parts:
            explanation, rest = parts.split("FILE:", 1)
            explanation = explanation.strip()
            text = "FILE:" + rest
        else:
            explanation = parts.strip()

    patch_files = parse_search_replace_blocks(text)
    if patch_files:
        items = [{"path": f["path"], "hunks": f["hunks"]} for f in patch_files]
        return explanation or "Patch edits ready.", items

    exp, files = parse_multi_code_response(text)
    if files:
        for f in files:
            if not f.get("path") and default_path:
                f["path"] = default_path
            if f.get("code") and f["path"].endswith(".py"):
                f["code"] = sanitize_python_code(f["code"])
        return exp or explanation or "Changes ready.", files

    exp, code = parse_code_response(raw)
    if code:
        path = default_path or "data/scripts/script.py"
        return exp or explanation, [{"path": path, "code": sanitize_python_code(code) if path.endswith(".py") else code}]
    return explanation or "No changes generated.", []


def diagnose_code(
    task: str,
    *,
    path: str,
    content: str,
    context: str = "",
    errors: str | None = None,
) -> str:
    """Explain issues without generating fixed code."""
    user = f"Task: {task}\n\nFile: {path}\n\n{content}"
    if context:
        user += f"\n\nContext:\n{context}"
    if errors:
        user += f"\n\nErrors:\n{errors}"
    return ask_with_system(coder_model(), CODER_DIAGNOSE_SYSTEM, user)


def coding_chat_answer(message: str, *, context: str = "") -> str:
    """Answer coding questions with project context."""
    user = message
    if context:
        user = f"Project context:\n{context}\n\nQuestion: {message}"
    return ask_with_system(coder_model(), CODING_CHAT_SYSTEM, user)


def generate_script_with_test(task: str, script_path: str) -> tuple[str, list[dict]]:
    """Generate script + matching pytest file. Returns (explanation, files)."""
    from pathlib import Path

    parent = Path(script_path).parent
    stem = Path(script_path).stem
    test_path = str(parent / f"test_{stem}.py")
    user = (
        f"Create:\n"
        f"1) Script at FILE: {script_path}\n"
        f"2) Pytest at FILE: {test_path}\n\n"
        f"Requirement: {task}"
    )
    raw = ask_with_system(coder_model(), CODER_MULTI_SYSTEM, user)
    explanation, files = parse_multi_code_response(raw)
    cleaned: list[dict] = []
    for item in files:
        path = item.get("path") or script_path
        code = sanitize_python_code(item.get("code", ""))
        if code:
            cleaned.append({"path": path, "code": code})
    if not cleaned:
        _, code = generate_python_code(task)
        cleaned = [{"path": script_path, "code": code}]
    elif len(cleaned) == 1:
        cleaned[0]["path"] = script_path
    return explanation or "Script and test ready to apply.", cleaned


def parse_multi_code_response(response_text: str) -> tuple[str, list[dict]]:
    """Parse multi-file response with FILE: path / CODE: blocks."""
    text = response_text.strip()
    explanation = ""
    files: list[dict] = []

    if "FILE:" in text:
        header, rest = text.split("FILE:", 1)
        explanation = header.replace("EXPLANATION:", "").strip()
        chunks = re.split(r"\nFILE:\s*", rest)
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            if "CODE:" in chunk:
                path_part, code_part = chunk.split("CODE:", 1)
                path = path_part.strip().splitlines()[0].strip()
                code = sanitize_python_code(code_part.strip())
                if path and code:
                    files.append({"path": path, "code": code})
        if files:
            return explanation or "Multi-file changes.", files

    exp, code = parse_code_response(text)
    return exp, [{"path": "", "code": code}] if code else []


def coder_model() -> str:
    return model_for("coder")


def general_model() -> str:
    return model_for("general")


def review_model() -> str:
    return model_for("review")


def vision_model() -> str:
    return model_for("vision")


# describe/batch → fast; ocr/compare/region/code/pdf/identify → quality model when enabled
_VISION_TASK_TIER: dict[str, str] = {
    "describe": "light",
    "batch": "light",
    "ocr": "heavy",
    "ocr_structured": "heavy",
    "compare": "heavy",
    "region": "heavy",
    "image_to_code": "heavy",
    "pdf": "heavy",
    "identify": "heavy",
}


def _is_light_vision_model(name: str) -> bool:
    return "moondream" in (name or "").lower()


def _heavy_vision_order(*, low_vram: bool) -> tuple[str, ...]:
    from jarvis.ollama_health import supports_mllama

    if low_vram:
        order = ("llama3.2-vision:11b", "llama3.2-vision", "llava:13b", "llava")
    else:
        order = ("llava:13b", "llama3.2-vision:11b", "llama3.2-vision", "llava")
    if not supports_mllama():
        order = tuple(c for c in order if "llama3.2-vision" not in c)
    return order


def vision_model_for_task(task: str = "describe") -> str:
    """Pick vision model by task and vision mode (custom uses Vision dropdown for all tasks)."""
    from jarvis.config import load_vision_quality
    from jarvis.gpu import is_low_vram
    from jarvis.model_store import _installed, _match_installed

    quality = load_vision_quality()
    tier = _VISION_TASK_TIER.get(task, "light")
    if quality == "custom":
        chosen = model_for("vision")
        if tier != "light" and _is_light_vision_model(chosen):
            installed = _installed()
            for candidate in _heavy_vision_order(low_vram=is_low_vram()):
                match = _match_installed(candidate, installed)
                if match:
                    return match
        return chosen

    installed = _installed()
    light = (
        _match_installed("moondream:latest", installed)
        or _match_installed("moondream", installed)
        or model_for("vision")
    )
    if quality == "fast" or tier == "light":
        return light

    order = _heavy_vision_order(low_vram=is_low_vram())
    if not order:
        order = ("moondream:latest", "moondream", "llava:13b", "llava")
    for candidate in order:
        match = _match_installed(candidate, installed)
        if match:
            return match
    return model_for("vision")


def image_model() -> str:
    return model_for("image")


def embed_model() -> str:
    return model_for("embed")

