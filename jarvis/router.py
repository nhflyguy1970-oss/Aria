import json
import os
import re

from jarvis import llm
from jarvis.session import SessionContext

# Text transforms — must not trigger audio transform_genre ("convert … to uppercase").
_TEXT_CONVERT_TARGETS = (
    r"uppercase|lowercase|title case|camel case|snake case|kebab case|"
    r"binary|hex|ascii|markdown|html|json|yaml|csv|pdf|base64"
)
_AUDIO_TRANSFORM_RE = re.compile(
    rf"\b(transform|remix|convert)\s+.+\s+(?:into|as|to)\s+(?!{_TEXT_CONVERT_TARGETS}\b)",
    re.I | re.S,
)


def _vision_attachment_action(message: str) -> str:
    """Route image attach to describe, ocr, region, code, or analyze."""
    lower = message.lower().strip()
    if not lower or lower in ("please analyze the attached file.", "analyze", "(attachment)"):
        return "describe"
    if re.search(
        r"\b(html|css|react|vue|tailwind|image.?to.?code|screenshot.?to.?code|convert.*\b(code|html))\b",
        lower,
    ):
        return "image_to_code"
    if re.search(
        r"\b(structured|table|form|markdown|json)\b.*\b(ocr|text|extract)\b"
        r"|\b(ocr|extract).*\b(structured|table|form|markdown|json)\b",
        lower,
    ):
        return "ocr_structured"
    if re.search(
        r"\b(top.?left|top.?right|bottom.?left|bottom.?right|center|middle|region|corner|quadrant)\b",
        lower,
    ):
        return "region"
    if re.search(
        r"\b(read (all )?text|ocr|extract (all )?text|what text|transcribe (this )?(image|screenshot|photo)?)\b",
        lower,
    ):
        return "ocr"
    if re.search(
        r"\b(describe|what do you see|what is this|tell me about (this|the) (image|photo|screenshot|picture))\b",
        lower,
    ):
        return "describe"
    return "analyze"


def py_path_from_message(message: str) -> str:
    """Extract a .py path from natural language (in/at/to/called/named, or last .py token)."""
    if m := re.search(r"\b(?:in|at|to|called|named)\s+[`'\"]?([\w./-]+\.py)", message, re.I):
        return m.group(1)
    paths = re.findall(r"[`'\"]?([\w./-]+\.py)[`'\"]?", message)
    return paths[-1] if paths else ""


def _image_generation_route(message: str, lower: str | None = None) -> dict | None:
    from jarvis.modules.image import normalize_image_prompt

    text = (lower if lower is not None else message.lower()).strip()
    m = re.search(
        r"\b(?:generate|create|draw|make|paint)\s+(?:an?\s+)?"
        r"(?:[\w-]+\s+){0,4}"
        r"(?:image|picture|photo|pic|illustration|artwork|wallpaper|portrait)s?\b"
        r"(?:\s+(?:of|showing|with|depicting))?\s*(.*)",
        text,
    )
    if not m:
        return None
    prompt = normalize_image_prompt((m.group(1) or "").strip() or message.strip())
    return {"action": "generate_image", "params": {"prompt": prompt}}


def _image_edit_route(message: str, lower: str, session: SessionContext) -> dict | None:
    """Whole-image img2img edit when the user has a recent image in context."""
    path = session.last_image
    if not path:
        return None
    if re.search(r"\b(?:inpaint|in-?paint|mask)\b", lower):
        return None
    if re.search(
        r"\b(?:generate|create|draw|paint|make)\s+(?:an?\s+)?(?:new\s+)?"
        r"(?:[\w-]+\s+){0,4}(?:image|picture|photo|pic|illustration)s?\b",
        lower,
    ):
        return None
    if re.search(
        r"\bmake\s+(?:an?\s+)?(?:[\w-]+\s+){0,4}(?:image|picture|photo|pic|illustration)s?\s+of\b",
        lower,
    ):
        return None
    m = re.search(
        r"\b(?:edit|change|modify|adjust|alter|transform|make)\s+"
        r"(?:the\s+)?(?:image|picture|photo|it|this|that)?\s*[:\-]?\s*(.+)$",
        message.strip(),
        re.I,
    )
    if m:
        part = m.group(1).strip()
        if len(part) >= 3:
            return {"action": "edit_image", "params": {"path": path, "prompt": part}, "thinking": "image edit"}
    if re.search(r"\b(?:edit|change|modify)\s+(?:the\s+)?(?:image|picture|photo)\b", lower):
        return {"action": "edit_image", "params": {"path": path, "prompt": message.strip()}, "thinking": "image edit"}
    return None


def _document_path_in_message(message: str) -> str:
    """Extract a PDF/DOCX path from natural language."""
    if m := re.search(
        r"\b(?:file|document|pdf|warranty|attached|open|in)\s+[`'\"]?([\w./-]+\.(?:pdf|docx))[`'\"]?",
        message,
        re.I,
    ):
        return m.group(1)
    paths = re.findall(r"[`'\"]?([\w./-]+\.(?:pdf|docx))[`'\"]?", message, re.I)
    return paths[-1] if paths else ""


def infer_script_path(message: str) -> str:
    """Guess a sandbox script path when the user did not specify one."""
    path = py_path_from_message(message)
    if path:
        return path
    if m := re.search(r"\b(?:implement|add|build|create)\s+([a-zA-Z_]\w*)", message):
        return f"data/scripts/{m.group(1).lower()}.py"
    return "data/scripts/script.py"


def py_file_exists(path: str) -> bool:
    if not path:
        return False
    from jarvis import fs
    from jarvis.config import PROJECT_ROOT
    try:
        return fs.resolve_path(path, base=PROJECT_ROOT).exists()
    except (ValueError, OSError):
        return False


ACTIONS = """
Available actions (respond with JSON only):

- chat: general conversation. params: {}
- remember: store a fact. params: {"text": "..."}
- recall: list stored facts. params: {}
- memory_search: search memory. params: {"query": "..."}
- memory_forget: delete matching memories. params: {"query": "..."}
- memory_correct: replace a wrong fact. params: {"new_fact": "...", "search_hint": "..."}
- memory_summarize: extract facts from recent chat. params: {}
- memory_prune: drop stale auto memories. params: {}
- memory_namespace: set active namespace. params: {"namespace": "work"}
- apply_proposal: apply last code proposal. params: {}
- dismiss_proposal: dismiss last proposal. params: {}
- undo_apply: restore files from last apply backup. params: {}

- coding_read: read/load a file. params: {"path": "..."}
- coding_fix: fix errors in a Python file. params: {"path": "..."}
- coding_improve: improve a file. params: {"path": "..."}
- coding_find: find files by name. params: {"query": "..."}
- coding_search: search file contents. params: {"query": "..."}
- coding_run: run a Python file. params: {"path": "..."}
- coding_project: index a project folder. params: {"path": "..."}
- coding_review: architecture review. params: {}
- coding_show: show file. params: {"path": "..."}
- coding_create: write a NEW Python script (not fix an existing file). params: {"description": "...", "path": "optional/filename.py"}
- coding_agent: multi-step coding task (read, edit, test, retry). params: {"task": "...", "path": "optional", "max_steps": 5}
- coding_refactor: multi-file refactor. params: {"task": "...", "path": "optional"}
- coding_chat: ask about the codebase with semantic search. params: {"query": "..."}
- coding_diagnose: explain what's wrong without changing code. params: {"path": "...", "task": "..."}
- code_index: build semantic code search index. params: {"path": "optional project root"}
- code_search: semantic code search. params: {"query": "..."}
- syntax_check: full syntax/lint check (py_compile, ruff, pyright, mypy). params: {"path": "..."}
- coding_task: list/pause/resume long-running coding tasks. params: {"action": "list|pause|resume", "task_id": "..."}
- extract_function: AST extract lines into function. params: {"path": "...", "start_line": N, "end_line": N, "name": "..."}
- move_module: move Python file and update imports. params: {"from": "...", "to": "..."}
- git_commit: commit changes. params: {"message": "...", "files": ["optional paths"]}
- git_branch: create and switch git branch. params: {"name": "..."}
- git_summarize: summarize git diff in plain English. params: {"file": "optional"}

- data_load: load CSV, JSON, XLSX, or SQLite. params: {"path": "..."}
- data_query: ask about loaded data. params: {"question": "..."}
- data_summary: summarize loaded data. params: {}
- data_sql: run SELECT on loaded SQLite DB. params: {"query": "SELECT ..."}

- web_search: search the web (SearXNG/DuckDuckGo). params: {"query": "..."}
- weather_forecast: local weather forecast (Open-Meteo). params: {"day": "optional YYYY-MM-DD"}

- rename_symbol: rename identifier across project. params: {"symbol": "...", "new_name": "..."}
- coding_lsp: syntax/lint check on file (alias for syntax_check). params: {"path": "..."}
- lsp_definition: go to definition. params: {"path": "...", "line": 1, "column": 1}
- lsp_references: find references. params: {"path": "...", "line": 1}
- lsp_hover: hover docs at position. params: {"path": "...", "line": 1}
- lsp_format: format document via LSP. params: {"path": "...", "write": true}
- lsp_symbols: document outline. params: {"path": "..."}

- generate_music: create music from prompt (MusicGen). params: {"prompt": "...", "duration": 10}

- branch_create: fork chat conversation. params: {"name": "..."}
- branch_switch: switch active chat branch. params: {"branch_id": "..."}
- branch_list: list chat branches. params: {}
- branch_delete: delete chat branch(es). params: {"branch_ids": ["id1"]} or {"branch_id": "id"}

- transcribe: speech-to-text. params: {"path": "...", "model": "base"}
- analyze_audio: transcribe and summarize. params: {"path": "..."}
- record_transcribe: record from mic then transcribe. params: {"duration": 5}
- speak: text-to-speech (alias for generate_audio). params: {"text": "..."}
- generate_audio: create speech from text. params: {"text": "...", "voice": "", "speed": 175}
- edit_audio: edit audio file (trim, volume, speed, fade). params: {"path": "...", "instruction": "..."}
- play_audio: play audio file through Sound Blaster. params: {"path": "..."}
- generate_music: generate music (needs transformers+scipy or audiocraft). params: {"prompt": "...", "duration": 10}
- transform_genre: remix audio into new genre (MusicGen-Melody). params: {"path": "...", "genre": "jazz rock"}
- generate_song: AI lyrics + music. params: {"topic": "...", "genre": "pop", "mood": "uplifting"}
- voice_to_song: turn voice recording into sung track. params: {"path": "...", "lyrics": "", "style": "pop ballad"}

- describe_image: describe an image. params: {"path": "..."}
- analyze_image: ask about an image. params: {"path": "...", "question": "..."}
- generate_image: create image. params: {"prompt": "..."}
- generate_video: create short video clip (keyframe + motion). params: {"prompt": "..."}
- generate_meme: classic top/bottom meme with AI background. params: {"idea": "...", "top": "", "bottom": "", "use_ai_image": true}
- upscale_image: 2× upscale last/given image. params: {"path": "...", "scale": 2}
- inpaint_image: ComfyUI inpaint masked region. params: {"path": "...", "prompt": "...", "region": {"x":0.25,"y":0.25,"w":0.5,"h":0.5}}
- enhance_prompt: improve image prompt. params: {"prompt": "..."}
- process_audio_vst: apply AE-5 EQ/VST chain to audio file. params: {"path": "...", "chain": "voice|music|scout|gaming"}
- set_vst_live: route all playback through live PipeWire EQ sink. params: {"preset": "voice|music|scout|gaming|off"}

- journal_log: rapid log to today's bullet journal. params: {"text": "..."}
- journal_today: show today's daily log. params: {}
- journal_monthly: show current monthly log. params: {}
- journal_open_tasks: list open journal tasks. params: {}
- journal_reflect: AI reflection on journal. params: {}
- journal_migrate: migrate open tasks to next month. params: {}
- journal_search: search journal entries. params: {"query": "..."}
- journal_remember: save journal bullet or today to memory. params: {"bullet_id": "..."}
- journal_schedule: schedule open task to future month. params: {"month": "YYYY-MM", "task_query": "taxes", "bullet_id": "..."}
- journal_thread: thread/migrate task to daily log. params: {"day": "YYYY-MM-DD", "task_query": "report", "duplicate": false}
- journal_review: AI summary after month/week review checklist. params: {}

- git_status: show git status. params: {}
- git_diff: show git diff. params: {"file": "..."}
- data_chart: generate chart from loaded data. params: {"column": ""}

- clear: reset conversation. params: {}
- capabilities: list what Jarvis can do. params: {}
- models_info: recommend Ollama models for hardware. params: {}
- greeting: friendly hello. params: {}
- morning_briefing: daily summary — weather, open tasks, today's schedule. params: {}
- briefing_news_detail: expand a headline from the morning briefing with web research. params: {"query": "...", "title": "optional headline"}
- document_summarize: summarize attached or recent PDF/Word doc. params: {"path": "optional"}
- document_query: answer question about a document. params: {"path": "optional", "question": "..."}
- document_info: page count and preview of a document. params: {"path": "optional"}
- upgrade_wizard: propose a self-upgrade (jarvis/ + tests/ only). params: {"task": "..."}
- upgrade_verify: run isolated pytest/ruff on pending upgrade. params: {"proposal_id": "optional"}
- upgrade_apply: apply verified upgrade with snapshot. params: {"proposal_id": "optional", "force": false}
- upgrade_rollback: restore pre-upgrade snapshot. params: {"snapshot_id": "optional"}
- learn_about: research a topic via web search and save brief to data/knowledge/. params: {"topic": "..."}
- learn_remember: store key points from last learn-about brief into memory. params: {"slug": "optional"}
- ha_status: Home Assistant connection and house snapshot. params: {}
- ha_control: turn on/off/toggle a device. params: {"target": "...", "action": "on|off|toggle"}
- ha_scene: activate a Home Assistant scene. params: {"scene": "..."}
- ha_set_token: save Home Assistant long-lived token from chat. params: {"token": "..."}
"""

ROUTER_PROMPT = """You route user requests for Jarvis AI assistant.
Use session context for follow-ups ("fix it" = last file, "apply that" = apply_proposal).
If ambiguous between multiple files, set needs_clarification true with choices.
Use coding_create when the user wants a NEW script/file (e.g. "write a python script hello world") — NOT coding_fix.
Use coding_fix only when fixing an existing .py file that has errors.
Use coding_agent for multi-step tasks: implement features, debug until tests pass, cross-file changes.
Use coding_chat ONLY for questions about THIS Jarvis project / its source code
(e.g. "how does the router work in jarvis", "where is branch delete handled").
Use "chat" for general tech, hardware, AI products, and anything outside this repo
(e.g. Intel Movidius VPU, GPUs, LLMs, cloud APIs).
Use coding_diagnose before fixing when user wants explanation first.

{actions}

Session context: {session_context}

Respond with ONLY valid JSON:
{{"action": "<name>", "params": {{}}, "thinking": "<reason>",
  "needs_clarification": false, "clarification_question": "", "choices": []}}

User message: {message}
{attachment_context}
"""

_CODEBASE_HINTS = re.compile(
    r"\b("
    r"jarvis|this (project|repo|codebase)|our code|the code|source code|codebase|"
    r"\.py\b|\.js\b|\.ts\b|\.html\b|function\s+\w+|class\s+\w+|module\s+\w+|"
    r"import\s+|file\s+[`'\"]?\S+|in\s+jarvis|"
    r"where is .+ (defined|implemented)|how is .+ implemented|"
    r"explain (the )?code|search code|code search|extra_routes|assistant\.py"
    r")\b",
    re.I,
)

_GENERAL_TECH = re.compile(
    r"\b("
    r"intel|amd|nvidia|movidius|vpu|tpu|npu|gpu|cpu|asic|fpga|"
    r"openai|anthropic|google|microsoft|apple|qualcomm|"
    r"llama|gpt|transformer|neural network|machine learning|deep learning|"
    r"rocm|cuda|onnx|tensorrt|ollama|comfyui|accelerator|inference chip"
    r")\b",
    re.I,
)


def is_general_knowledge_question(message: str, session: SessionContext | None = None) -> bool:
    """General tech / hardware / AI product questions — not about this repo."""
    from jarvis.runtime_routing import is_runtime_routing_question

    if is_runtime_routing_question(message):
        return False
    if is_codebase_question(message, session):
        return False
    text = (message or "").strip()
    if not text:
        return False
    lower = text.lower()
    if _GENERAL_TECH.search(text):
        return True
    if re.search(r"\b(would|could|can|should) .+ work (?:for|with)\b", lower):
        return True
    if re.search(r"\bwhat is\b.+\b(vpu|tpu|npu|gpu|llm|transformer)\b", lower):
        return True
    return False


def is_codebase_question(message: str, session: SessionContext | None = None) -> bool:
    """True when the user is asking about this project's code, not general tech."""
    text = (message or "").strip()
    if not text:
        return False
    lower = text.lower()
    if _CODEBASE_HINTS.search(text):
        return True
    if _GENERAL_TECH.search(text):
        return False
    if re.search(r"\bhow (?:does|would|can|do)\b", lower) and not re.search(
        r"\b(code|file|function|class|module|jarvis|project|repo|implement)\b",
        lower,
    ):
        return False
    if session and session.last_file and re.search(r"\b(it|that|this)\b", lower):
        return True
    return False


def _maybe_downgrade_coding_chat(intent: dict, message: str, session: SessionContext) -> dict:
    if intent.get("action") != "coding_chat":
        return intent
    if is_codebase_question(message, session):
        return intent
    out = dict(intent)
    out["action"] = "chat"
    out["params"] = {}
    out["thinking"] = (out.get("thinking") or "routed") + "; general knowledge → chat"
    return out


def _follow_up_route(message: str, session: SessionContext) -> dict | None:
    lower = message.lower().strip()

    from jarvis.briefing_news import briefing_news_intent

    news_intent = briefing_news_intent(message, session)
    if news_intent:
        return news_intent

    if re.search(r"\b(apply (it|that|the changes?)|yes apply|go ahead|do it)\b", lower):
        return {"action": "apply_proposal", "params": {}, "thinking": "follow-up"}

    if re.match(r"^apply[\s!.?,]*$", lower):
        return {"action": "apply_proposal", "params": {}, "thinking": "follow-up"}

    if re.search(r"\bundo(\s+(last\s+)?apply|\s+(it|that|the changes?|last))\b", lower):
        return {"action": "undo_apply", "params": {}, "thinking": "follow-up"}

    if re.match(r"^undo[\s!.?,]*$", lower):
        return {"action": "undo_apply", "params": {}, "thinking": "follow-up"}

    if re.search(r"\b(dismiss|reject|cancel|don't apply|never mind)\b", lower) and session.last_proposal_id:
        return {"action": "dismiss_proposal", "params": {}, "thinking": "follow-up"}

    if re.search(r"\b(verify upgrade|test upgrade|run upgrade tests)\b", lower):
        return {"action": "upgrade_verify", "params": {}, "thinking": "upgrade verify"}

    if re.search(r"\b(apply upgrade|apply jarvis upgrade)\b", lower):
        return {"action": "upgrade_apply", "params": {}, "thinking": "upgrade apply"}

    if re.search(r"\b(rollback upgrade|undo upgrade|rollback jarvis)\b", lower):
        return {"action": "upgrade_rollback", "params": {}, "thinking": "upgrade rollback"}

    if re.search(
        r"\b(remember key points|remember what you learned|save key points from that)\b",
        lower,
    ) and session.last_knowledge_slug:
        return {
            "action": "learn_remember",
            "params": {"slug": session.last_knowledge_slug},
            "thinking": "learn remember",
        }

    if re.search(r"\b(fix (it|that)|repair (it|that)|debug (it|that))\b", lower) and session.last_file:
        return {"action": "coding_fix", "params": {"path": session.last_file}, "thinking": "follow-up"}

    if re.search(r"\b(refactor (it|that)|refactor across)\b", lower) and session.last_file:
        if session.last_coding_mode == "refactor" or re.search(r"\b(across|modules?|project|files?)\b", lower):
            return {
                "action": "coding_refactor",
                "params": {"task": message, "path": session.last_file},
                "thinking": "follow-up",
            }
        return {"action": "coding_improve", "params": {"path": session.last_file}, "thinking": "follow-up"}

    if re.search(r"\b(improve (it|that)|clean (it|that) up)\b", lower) and session.last_file:
        return {"action": "coding_improve", "params": {"path": session.last_file}, "thinking": "follow-up"}

    if re.search(r"\b(run (it|that)|execute (it|that))\b", lower) and session.last_file:
        return {"action": "coding_run", "params": {"path": session.last_file}, "thinking": "follow-up"}

    if re.search(r"\b(show (it|that)|open (it|that)|display (it|that))\b", lower) and session.last_file:
        return {"action": "coding_show", "params": {"path": session.last_file}, "thinking": "follow-up"}

    if re.search(r"\b(that file|the file|same file)\b", lower) and session.last_file:
        if "fix" in lower:
            return {"action": "coding_fix", "params": {"path": session.last_file}, "thinking": "follow-up"}
        if "run" in lower:
            return {"action": "coding_run", "params": {"path": session.last_file}, "thinking": "follow-up"}

    if re.search(r"\b(search (for )?that|same search)\b", lower) and session.last_search_query:
        return {"action": "coding_search", "params": {"query": session.last_search_query}, "thinking": "follow-up"}

    if re.search(r"\b(summarize (the )?data|data summary)\b", lower) and session.last_data_path:
        return {"action": "data_summary", "params": {}, "thinking": "follow-up"}

    if session.last_data_path and re.search(
        r"\b((?:export|save)\s+(?:to\s+)?(?:csv|json|pdf|results)|export\s+(?:the\s+)?(?:data|report))\b",
        lower,
    ):
        return {"action": "data_export", "params": {"instruction": message}, "thinking": "export data"}

    if session.last_data_path and re.search(
        r"\b(clean|fix null|fill null|drop duplicates?|remove duplicates?)\b",
        lower,
    ):
        return {"action": "data_clean", "params": {"instruction": message}, "thinking": "clean data"}

    if session.last_data_path and re.search(
        r"\b(chart|graph|plot)\b",
        lower,
    ):
        from jarvis.modules.data import parse_chart_request
        spec = parse_chart_request(message)
        return {"action": "data_chart", "params": spec, "thinking": "chart data"}

    if session.last_data_path and re.search(
        r"\b(how many|average|mean|sum|total|count|group by|median|min|max|what columns|describe)\b",
        lower,
    ):
        return {"action": "data_query", "params": {"question": message}, "thinking": "data follow-up"}

    if session.last_document_path and re.search(
        r"\b(summarize (the )?document|document summary|summarize (it|that|the pdf|the warranty))\b",
        lower,
    ):
        return {"action": "document_summarize", "params": {"path": session.last_document_path}, "thinking": "document follow-up"}

    if session.last_document_path and (
        session.last_module == "document"
        or re.search(r"\b(the document|this pdf|the warranty|that clause|the contract)\b", lower)
    ):
        if re.search(
            r"\b(what|which|when|where|who|how|does|is there|are there|find|clause|section|coverage|warranty|expire)\b",
            lower,
        ) or message.strip().endswith("?"):
            return {
                "action": "document_query",
                "params": {"path": session.last_document_path, "question": message},
                "thinking": "document follow-up",
            }

    if re.search(r"\b(describe (it|that|the image|this))\b", lower) and session.last_image:
        return {"action": "describe_image", "params": {"path": session.last_image}, "thinking": "follow-up"}

    if session.last_image and session.last_module == "vision":
        if not (
            _is_capabilities_question(lower)
            or _is_models_question(lower)
            or _is_greeting(lower)
            or re.match(r"^clear\b", lower)
            or re.search(r"\b(remember|recall|search the web|generate|create|implement|fix |debug )\b", lower)
        ):
            vision_follow_up = (
                re.search(
                    r"\b(in (the|this) (image|photo|picture|screenshot)|"
                    r"about (the|this) (image|photo|picture|screenshot)|"
                    r"the (image|photo|screenshot|picture))\b",
                    lower,
                )
                or re.match(
                    r"^(what color|what text|what does|what is|what are|what's|"
                    r"where is|where are|how many|how much|who is|"
                    r"is there|are there|can you see|can you read|"
                    r"does it|do you see)\b",
                    lower,
                )
                or (message.strip().endswith("?") and len(message.strip()) < 240)
            )
            if vision_follow_up:
                return {
                    "action": "analyze_image",
                    "params": {"path": session.last_image, "question": message},
                    "thinking": "vision follow-up",
                }

    if re.search(r"\b(edit (it|that)|trim (it|that)|cut (it|that)|make it louder|speed it up)\b", lower) and session.last_audio:
        return {"action": "edit_audio", "params": {"path": session.last_audio, "instruction": message}, "thinking": "follow-up"}

    return None


def _is_capabilities_question(lower: str) -> bool:
    from jarvis.runtime_routing import is_runtime_routing_question

    if is_runtime_routing_question(lower):
        return False
    patterns = [
        r"what (can you do|do you do|are you able|services|features|capabilities)",
        r"what(?:'s| is) (?:your|jarvis)",
        r"how can you help",
        r"what (?:are|is) (?:the |your )?(?:services|features|capabilities|functions)",
        r"list (?:your )?(?:services|capabilities|features|abilities)",
        r"what (?:things|stuff) can you",
        r"help me understand what you",
        r"^what can you\b",
    ]
    return any(re.search(p, lower) for p in patterns)


def _is_models_question(lower: str) -> bool:
    from jarvis.runtime_routing import is_runtime_routing_question

    if is_runtime_routing_question(lower):
        return False
    return bool(re.search(
        r"\b(what models|which models|model recommendations?|best models|recommended models|what ollama)\b",
        lower,
    ))


def _is_greeting(lower: str) -> bool:
    return bool(re.match(
        r"^(hi|hello|hey|greetings|good (morning|afternoon|evening)|yo)[\s!.?,]*$",
        lower,
    ))


_INPAINT_IMAGE_WORDS = (
    r"image|picture|photo|selfie|screenshot|pic|background|sky|face|"
    r"mask|region|area|foreground|subject"
)
_INPAINT_NOT_IMAGE = re.compile(
    r"\b(?:code|coding|bug|function|script|memory|task|journal|audio|video|meme|"
    r"data|csv|python|\.py|git|branch|model|ollama|settings|config|error|test|pytest|"
    r"proposal|commit|file|router|module|class|import|syntax|ollama|chat|upgrade|yourself)\b",
    re.I,
)
_META_SELF_QUESTION = re.compile(
    r"\b(?:how hard|how easy|would it be|could you|can you|are you able)\b.*"
    r"\b(?:fix|upgrade|improve|update|change|rewrite)\b.*"
    r"\b(?:yourself|you\b|jarvis|your (?:code|system|software))\b|"
    r"\b(?:fix|upgrade|improve|update)\b.*\b(?:yourself|jarvis|your (?:code|system|software))\b",
    re.I,
)


def _is_meta_self_question(message: str) -> bool:
    return bool(_META_SELF_QUESTION.search(message))


def is_meta_self_question(message: str) -> bool:
    return _is_meta_self_question(message)


def _extract_inpaint_prompt(message: str) -> str:
    for pat in (
        r"(?:inpaint(?:ing)?|in-?paint|edit|retouch|fix|replace|change|remove)\s+"
        r"(?:the\s+)?(?:(?:\w+\s+){0,4})?(?:to|with|into)\s+(.+)",
        r"(?:inpaint(?:ing)?|in-?paint|edit)\s*[:\-]\s*(.+)",
    ):
        if m := re.search(pat, message, re.I):
            text = m.group(1).strip()
            if len(text) > 2:
                return text
    return message.strip()


def _maybe_inpaint_route(message: str, lower: str, session: SessionContext) -> dict | None:
    """Route inpaint only when the user clearly means edit an existing image region."""
    if _is_meta_self_question(message):
        return None
    if _INPAINT_NOT_IMAGE.search(message):
        return None

    from jarvis.vision_media import parse_region

    image_words = _INPAINT_IMAGE_WORDS
    mentions_image = bool(re.search(rf"\b(?:{image_words})\b", lower))
    has_last_image = bool(session.last_image)

    if re.search(r"\b(?:inpaint(?:ing)?|in-?paint)\b", lower):
        if has_last_image or mentions_image:
            prompt = _extract_inpaint_prompt(message)
            if len(prompt) > 2:
                return {
                    "action": "inpaint_image",
                    "params": {"prompt": prompt, "region": parse_region(message, None)},
                }
        return None

    if not mentions_image and not has_last_image:
        return None

    if m := re.search(
        rf"\b(?:edit|retouch|fill in)\s+(?:the\s+)?(?:{image_words}|it|this|that)\b",
        lower,
    ):
        prompt = _extract_inpaint_prompt(message)
        if len(prompt) > 2:
            return {
                "action": "inpaint_image",
                "params": {"prompt": prompt, "region": parse_region(message, None)},
            }

    if m := re.search(
        rf"\b(?:fix|replace|change|remove)\s+(?:the\s+)?(?:{image_words})\b"
        rf"(?:\s+(?:to|with|into))?\s*(.*)",
        lower,
    ):
        prompt = (m.group(1) or "").strip() or _extract_inpaint_prompt(message)
        if len(prompt) > 2:
            return {
                "action": "inpaint_image",
                "params": {"prompt": prompt, "region": parse_region(message, None)},
            }

    if has_last_image and re.search(
        rf"\b(?:fix|replace|change|remove|edit)\s+(?:the\s+)?(?:it|this|that)\b", lower
    ) and re.search(
        rf"\b(?:{image_words}|region|area|mask|top|bottom|left|right|center|corner|half|quarter)\b",
        lower,
    ):
        prompt = _extract_inpaint_prompt(message)
        if len(prompt) > 2:
            return {
                "action": "inpaint_image",
                "params": {"prompt": prompt, "region": parse_region(message, None)},
            }

    region = parse_region(message, None)
    if has_last_image and region and re.search(
        r"\b(?:fix|replace|change|remove|edit|erase|delete|inpaint)\b", lower
    ):
        prompt = _extract_inpaint_prompt(message)
        if len(prompt) > 2:
            return {
                "action": "inpaint_image",
                "params": {"prompt": prompt, "region": region},
            }

    return None


def _finalize_intent(intent: dict, message: str, session: SessionContext) -> dict:
    """Last-line guards before executing the routed action."""
    from jarvis.runtime_routing import is_runtime_routing_question, route_runtime_priority
    from jarvis.runtime_routing_trace import log_route_decision

    action = intent.get("action")
    if action in ("documentation_search",) or str(action or "").startswith("documentation_"):
        return log_route_decision(
            message=message,
            intent=intent,
            stage="finalize",
            reason=intent.get("route_reason") or "documentation",
            confidence=intent.get("route_confidence"),
            handler=intent.get("route_handler") or "DocumentationEngine",
        )
    if action == "web_search" and is_runtime_routing_question(message):
        runtime = route_runtime_priority(message)
        if runtime:
            intent = runtime
            action = intent.get("action")

    if action != "inpaint_image":
        return log_route_decision(
            message=message,
            intent=intent,
            stage="finalize",
            reason=intent.get("route_reason"),
            confidence=intent.get("route_confidence"),
            handler=intent.get("route_handler"),
        )
    if _is_meta_self_question(message):
        intent = {"action": "chat", "params": {}, "thinking": "meta self-improvement"}
        return log_route_decision(message=message, intent=intent, stage="finalize_inpaint_guard")
    if _maybe_inpaint_route(message, message.lower(), session) is None:
        intent = {"action": "chat", "params": {}, "thinking": "not an image edit"}
        return log_route_decision(message=message, intent=intent, stage="finalize_inpaint_guard")
    return log_route_decision(message=message, intent=intent, stage="finalize")


def _quick_route(
    message: str,
    attachment: dict | None,
    session: SessionContext,
    *,
    skip_runtime_priority: bool = False,
) -> dict | None:
    follow = _follow_up_route(message, session)
    if follow:
        return follow

    # Runtime keyword fallback — only when NLU did not run.
    from jarvis.routing_inspector import is_routing_command
    from jarvis.runtime_routing import route_runtime_priority

    if routing_cmd := is_routing_command(message):
        return {
            "action": routing_cmd,
            "params": {},
            "thinking": "routing inspector",
            "route_handler": "RoutingInspector",
        }

    if not skip_runtime_priority:
        if runtime_hit := route_runtime_priority(message):
            return runtime_hit

    from jarvis.router_table import match_router_table

    table_hit = match_router_table(message, session)
    if table_hit:
        return table_hit

    lower = message.lower().strip()

    from jarvis.upgrade_wizard import is_upgrade_task, parse_upgrade_task

    if re.search(r"\b(rollback upgrade|undo upgrade|rollback jarvis upgrade)\b", lower):
        return {"action": "upgrade_rollback", "params": {}, "thinking": "upgrade rollback"}

    if re.search(r"\b(verify upgrade|test upgrade|run upgrade tests)\b", lower):
        return {"action": "upgrade_verify", "params": {}, "thinking": "upgrade verify"}

    if re.search(r"\b(apply upgrade|apply jarvis upgrade)\b", lower):
        return {"action": "upgrade_apply", "params": {}, "thinking": "upgrade apply"}

    if is_upgrade_task(message):
        return {
            "action": "upgrade_wizard",
            "params": {"task": parse_upgrade_task(message)},
            "thinking": "upgrade wizard",
        }

    from jarvis.knowledge import is_learn_command, parse_learn_topic

    if is_learn_command(message):
        return {
            "action": "learn_about",
            "params": {"topic": parse_learn_topic(message)},
            "thinking": "learn about topic",
        }

    from jarvis.home_assistant import parse_ha_token_message, quick_route_home_assistant

    if token := parse_ha_token_message(message):
        return {
            "action": "ha_set_token",
            "params": {"token": token},
            "thinking": "home assistant token",
        }

    if ha_intent := quick_route_home_assistant(message):
        return {**ha_intent, "thinking": "home assistant"}

    if _is_meta_self_question(message):
        return {"action": "chat", "params": {}, "thinking": "meta self-improvement"}

    if _is_models_question(lower):
        return {"action": "models_info", "params": {}, "thinking": "models question"}

    if _is_capabilities_question(lower) or (
        re.search(r"^(hi|hello|hey)\b", lower) and _is_capabilities_question(lower)
    ):
        return {"action": "capabilities", "params": {}, "thinking": "capabilities question"}

    if re.search(r"^good morning\b", lower) and os.getenv("JARVIS_BRIEFING", "1") != "0":
        return {"action": "morning_briefing", "params": {}, "thinking": "morning briefing"}

    if _is_greeting(lower):
        return {"action": "greeting", "params": {}, "thinking": "greeting"}

    if re.match(r"^clear[\s!.?,]*$", lower):
        return {"action": "clear", "params": {}, "thinking": "clear conversation"}

    compare_match = re.match(
        r"^compare\s+(\S+)\s+(?:and|with|vs\.?)\s+(\S+)\s*$",
        message.strip(),
        re.I,
    )
    if compare_match:
        return {
            "action": "compare_images",
            "params": {"path1": compare_match.group(1), "path2": compare_match.group(2)},
            "thinking": "compare images",
        }

    batch_match = re.search(
        r"analyze all (?:images?|pngs?|jpegs?|screenshots?|photos?) in [`'\"]?([^\s`'\"]+)",
        message,
        re.I,
    )
    if batch_match:
        return {
            "action": "batch_vision",
            "params": {"folder": batch_match.group(1)},
            "thinking": "batch vision folder",
        }

    if re.search(r"^(hi|hello|hey)\b", lower) and len(lower) < 120:
        if any(w in lower for w in ("help", "do", "can", "service", "capable", "able")):
            return {"action": "capabilities", "params": {}, "thinking": "hello + help"}

    if attachment:
        path = attachment.get("path", "")
        kind = attachment.get("kind", "")
        if kind == "image":
            if re.search(r"\b(remember|don't forget|note that|keep in mind)\b", lower):
                return {
                    "action": "remember_image",
                    "params": {"path": path, "hint": message},
                    "thinking": "remember image content",
                }
            action = _vision_attachment_action(message)
            if action == "describe":
                return {"action": "describe_image", "params": {"path": path}}
            if action == "ocr":
                return {"action": "ocr_image", "params": {"path": path}}
            if action == "ocr_structured":
                return {"action": "ocr_structured_image", "params": {"path": path}}
            if action == "image_to_code":
                return {"action": "image_to_code", "params": {"path": path}}
            if action == "region":
                from jarvis.vision_media import parse_region
                crop = parse_region(message, attachment.get("crop"))
                return {
                    "action": "analyze_region",
                    "params": {"path": path, "question": message, "crop": crop},
                }
            return {"action": "analyze_image", "params": {"path": path, "question": message}}
        if kind == "video_frame":
            return {"action": "analyze_video_frame", "params": {"path": path, "question": message or "Describe this video frame."}}
        if kind == "audio":
            if any(w in lower for w in ("genre", "remix", "transform", "make it sound like")) or (
                "convert to" in lower and _AUDIO_TRANSFORM_RE.search(message)
            ):
                return {"action": "transform_genre", "params": {"path": path, "genre": message}}
            if any(w in lower for w in ("sing", "singing", "voice to song", "make me sing")):
                return {"action": "voice_to_song", "params": {"path": path, "lyrics": message}}
            if any(w in lower for w in ("edit", "trim", "cut", "crop", "fade", "volume", "speed", "normalize", "louder", "quieter")):
                return {"action": "edit_audio", "params": {"path": path, "instruction": message}}
            if any(w in lower for w in ("diarize", "who spoke", "speakers", "speaker")):
                return {"action": "diarize_audio", "params": {"path": path}}
            if any(w in lower for w in ("summarize", "summary", "analyze", "about")):
                return {"action": "analyze_audio", "params": {"path": path}}
            return {"action": "transcribe", "params": {"path": path}}
        if kind == "data":
            if any(w in lower for w in ("query", "ask", "how many", "what", "average", "sum")):
                return {"action": "data_load", "params": {"path": path}}
            return {"action": "data_load", "params": {"path": path}}
        if kind == "document":
            from jarvis.document_pipeline import document_attachment_action

            act = document_attachment_action(message)
            if act == "info":
                return {"action": "document_info", "params": {"path": path}, "thinking": "document info"}
            if act == "query":
                return {
                    "action": "document_query",
                    "params": {"path": path, "question": message},
                    "thinking": "document question",
                }
            return {"action": "document_summarize", "params": {"path": path}, "thinking": "document summarize"}
        if kind == "file":
            return {"action": "chat", "params": {"file_path": path}, "thinking": "file attachment"}

    if re.search(r"\b(record and transcribe|record transcribe|transcribe (?:what )?i say)\b", lower):
        m = re.search(r"(\d+)\s*seconds?", lower)
        return {"action": "record_transcribe", "params": {"duration": int(m.group(1)) if m else 5}}

    if re.search(r"\b(record|listen for)\s+(\d+)\s*seconds?\b", lower):
        m = re.search(r"(\d+)\s*seconds?", lower)
        return {"action": "record_transcribe", "params": {"duration": int(m.group(1)) if m else 5}}

    if re.search(r"\b(play (?:the )?audio|play (?:that|it) aloud)\b", lower):
        return {"action": "play_audio", "params": {}}

    m = re.search(r"schedule\s+(.+?)\s+to\s+(\d{4}-\d{2})\b", message, re.I)
    if m:
        return {
            "action": "journal_schedule",
            "params": {"task_query": m.group(1).strip(), "month": m.group(2)},
        }

    m = re.search(r"thread\s+(.+?)\s+to\s+(today|\d{4}-\d{2}-\d{2})\b", message, re.I)
    if m:
        from jarvis.modules.journal import _today

        day = _today() if m.group(2).lower() == "today" else m.group(2)
        return {"action": "journal_thread", "params": {"task_query": m.group(1).strip(), "day": day}}

    if re.search(r"\b(thread tasks to today|pull tasks to today)\b", lower):
        return {"action": "journal_thread", "params": {}}

    if re.search(r"\b(thread .+ to today|thread to today)\b", lower):
        m = re.search(r"thread\s+(.+?)\s+to\s+today", message, re.I)
        params: dict = {}
        if m:
            params["task_query"] = m.group(1).strip()
        return {"action": "journal_thread", "params": params}

    if re.search(r"\b(month.?end review|weekly review|run journal review)\b", lower):
        return {"action": "journal_review", "params": {}}

    if re.search(r"\b(remember (this )?bullet|save journal to memory|remember journal entry)\b", lower):
        m = re.search(r"\b([a-f0-9]{8})\b", message)
        return {"action": "journal_remember", "params": {"bullet_id": m.group(1) if m else ""}}

    if re.search(r"\b(remember|don't forget|note that|keep in mind)\b", lower):
        text = re.sub(
            r"^(please\s+)?(remember|don't forget|note that|keep in mind)\s*(that\s+)?",
            "",
            message,
            flags=re.I,
        ).strip()
        text = re.sub(r"^(these|the following)\s+facts?\s*:?\s*", "", text, flags=re.I).strip()
        if text:
            return {"action": "remember", "params": {"text": text}}

    if re.search(r"\b(what do you remember|recall|my memories)\b", lower):
        return {"action": "recall", "params": {}}

    if re.search(
        r"\b("
        r"something i like|what do i like|things? i like|my hobbies|my interests|"
        r"what do i enjoy|tell me something about me|what do you know about me|"
        r"about me\b|who am i\b|tell me about myself"
        r")\b",
        lower,
    ):
        return {"action": "memory_about_user", "params": {"question": message}, "thinking": "user profile"}

    if re.search(r"\b(search my memory|search memory|find in memory|memory search)\b", lower):
        query = re.sub(
            r"^(please\s+)?(search my memory|search memory|find in memory|memory search)\s*(for\s+)?",
            "",
            message,
            flags=re.I,
        ).strip() or message
        return {"action": "memory_search", "params": {"query": query}, "thinking": "memory search"}

    if re.search(r"\b(forget|delete memory|remove memory)\b", lower):
        query = re.sub(
            r"^(please\s+)?(forget|delete memory|remove memory)\s*(about\s+)?",
            "",
            message,
            flags=re.I,
        ).strip() or message
        return {"action": "memory_forget", "params": {"query": query}, "thinking": "forget memory"}

    if re.search(
        r"\b(correct|update|fix)\s+(that|the fact|memory|my memory)\b",
        lower,
    ) or re.search(r"^(?:please\s+)?actually,?\s+", lower):
        from jarvis.trust_memory import parse_memory_correct

        parsed = parse_memory_correct(message)
        if parsed:
            hint, new_fact = parsed
            return {
                "action": "memory_correct",
                "params": {"new_fact": new_fact, "search_hint": hint},
                "thinking": "correct memory",
            }

    if re.search(
        r"\b(summarize (this )?conversation to memory|remember (this|our) conversation|save conversation to memory)\b",
        lower,
    ):
        return {"action": "memory_summarize", "params": {}, "thinking": "summarize to memory"}

    if re.search(r"\b(set memory namespace|memory namespace)\b", lower):
        m = re.search(r"\b(?:namespace|project)\s+[`'\"]?(\w[\w-]*)[`'\"]?", message, re.I)
        return {
            "action": "memory_namespace",
            "params": {"namespace": m.group(1) if m else ""},
            "thinking": "memory namespace",
        }

    if re.search(r"\bprune (stale )?memor", lower):
        return {"action": "memory_prune", "params": {}, "thinking": "prune memory"}

    if re.search(r"\b(list|show|what)\s+cheatsheets?\b", lower):
        return {"action": "cheatsheet_list", "params": {}, "thinking": "cheatsheet list"}

    if re.search(r"\b(reset|restore)\s+.*cheatsheets?\b", lower):
        from jarvis.cheatsheets import resolve_key_from_message

        key = resolve_key_from_message(message) or ""
        return {"action": "cheatsheet_reset", "params": {"key": key}, "thinking": "reset cheatsheet"}

    if re.search(r"\bcheat\s*sheets?\b", lower):
        from jarvis.cheatsheets import resolve_key_from_message

        key = resolve_key_from_message(message) or ""
        return {"action": "cheatsheet_show", "params": {"key": key}, "thinking": "cheatsheet"}

    if re.search(
        r"\b(save (where i left off|project checkpoint|my progress)|remember where i left off|checkpoint (my )?project)\b",
        lower,
    ):
        return {"action": "project_checkpoint", "params": {}, "thinking": "project checkpoint"}

    if re.search(
        r"\b(where did i leave off|what was i working on|resume (my )?project|catch me up on (the )?project)\b",
        lower,
    ):
        return {"action": "project_resume", "params": {}, "thinking": "project resume"}

    if re.search(r"\b(review (the )?project|architecture review)\b", lower):
        return {"action": "coding_review", "params": {}}

    if re.search(
        r"\b(write|create|make|generate)\s+(?:me\s+)?(?:a\s+)?(?:new\s+)?(?:python\s+)?(script|program)\b",
        lower,
    ) or (
        re.search(r"\b(write|create|make)\b", lower)
        and re.search(r"\b(python|script|hello world)\b", lower)
        and not re.search(r"\b(fix|repair|debug|improve|refactor)\b", lower)
    ):
        path = py_path_from_message(message)
        return {"action": "coding_create", "params": {"description": message, "path": path}}

    if re.search(r"\b(with tests?|and tests?|pytest)\b", lower) and re.search(r"\.py\b", message):
        path = py_path_from_message(message)
        if path and re.search(r"\b(implement|write|create|make|generate|add|build)\b", lower):
            if not re.search(r"\b(fix|repair|debug|refactor)\b", lower):
                return {"action": "coding_create", "params": {"description": message, "path": path}}

    if m := re.search(
        r"\b(?:fix|repair|debug)(?:\s+(?:any\s+)?(?:issues?|bugs?|errors?|problems?))?\s+in\s+[`'\"]?([^\s`'\"]+\.py)",
        lower,
    ):
        return {"action": "coding_fix", "params": {"path": m.group(1)}}

    if m := re.search(r"\b(?:fix|repair|debug)\s+(?:the\s+)?(?:file\s+)?[`'\"]?([^\s`'\"]+\.py)", lower):
        return {"action": "coding_fix", "params": {"path": m.group(1)}}

    if m := re.search(r"\b(?:improve|refactor|clean up)\s+(?:the\s+)?(?:file\s+)?[`'\"]?([^\s`'\"]+)", lower):
        return {"action": "coding_improve", "params": {"path": m.group(1)}}

    if m := re.search(r"\b(?:run|execute)\s+(?:the\s+)?(?:file\s+)?[`'\"]?([^\s`'\"]+\.py)", lower):
        return {"action": "coding_run", "params": {"path": m.group(1)}}

    if re.search(r"\b(morning briefing|daily briefing|today'?s briefing|brief me)\b", lower):
        return {"action": "morning_briefing", "params": {}, "thinking": "morning briefing"}

    from jarvis.briefing_news import briefing_news_intent

    news_intent = briefing_news_intent(message, session)
    if news_intent:
        return news_intent

    if img := _image_edit_route(message, lower, session):
        return img

    if img := _image_generation_route(message, lower):
        return {**img, "thinking": "image generation"}

    if re.search(
        r"\b(search|find in) (?:my )?(?:documents?|document library|files in library)\b",
        lower,
    ):
        return {"action": "document_search", "params": {"query": message}, "thinking": "document library search"}

    doc_path = _document_path_in_message(message)
    if doc_path and re.search(
        r"\b(summarize|summary|overview|what does|warranty|coverage|explain)\b",
        lower,
    ):
        if re.search(r"\b(summarize|summary|overview|explain)\b", lower):
            return {"action": "document_summarize", "params": {"path": doc_path}, "thinking": "document path summarize"}
        return {"action": "document_query", "params": {"path": doc_path, "question": message}, "thinking": "document path query"}

    if re.search(r"\b(what did i write|journal today|today'?s journal|daily log)\b", lower):
        return {"action": "journal_today", "params": {}, "thinking": "journal today"}

    if re.search(r"\b(monthly log|journal this month|month'?s journal)\b", lower):
        return {"action": "journal_monthly", "params": {}, "thinking": "journal monthly"}

    if re.search(
        r"\b(open tasks|journal tasks|what('s| is) on my (plate|list)|my todos?|to-?do list)\b",
        lower,
    ):
        return {"action": "journal_open_tasks", "params": {}, "thinking": "journal tasks"}

    if re.search(r"\b(journal reflect|reflect on my journal|monthly review|weekly review)\b", lower):
        return {"action": "journal_reflect", "params": {}}

    if re.search(r"\b(migrate journal|monthly migration)\b", lower):
        return {"action": "journal_migrate", "params": {}}

    if m := re.search(r"\b(?:log|journal)[:\s]+(.+)", lower):
        return {"action": "journal_log", "params": {"text": m.group(1).strip()}}

    if re.search(r"\bsearch journal\b", lower):
        return {"action": "journal_search", "params": {"query": message}}

    if re.search(r"\b(git status|what changed in git)\b", lower):
        return {"action": "git_status", "params": {}}

    if re.search(r"\b(git diff|show diff)\b", lower):
        return {"action": "git_diff", "params": {}}

    if re.search(r"\b(summarize (the )?diff|what did i change)\b", lower):
        return {"action": "git_summarize", "params": {}}

    if m := re.search(r"\bcommit(?:\s+with\s+message)?[:\s]+(.+)", message, re.I):
        return {"action": "git_commit", "params": {"message": m.group(1).strip()}}

    if m := re.search(r"\bcreate\s+(?:git\s+)?branch\s+[`'\"]?([\w./-]+)", message, re.I):
        return {"action": "git_branch", "params": {"name": m.group(1)}}

    if re.search(r"\bcreate (?:a )?pull request\b", lower):
        title = re.sub(r"^.*create (?:a )?pull request[:\s]+", "", message, flags=re.I).strip()
        return {"action": "git_pr", "params": {"title": title or "Jarvis changes"}}

    if m := re.search(r"\b(?:find references|who uses|references for)\s+(\w+)", message, re.I):
        return {"action": "find_references", "params": {"symbol": m.group(1)}}

    if re.search(r"\brun tests?\s+for\b", lower):
        path = py_path_from_message(message) or session.last_file or ""
        return {"action": "coding_run_tests", "params": {"path": path}}

    if m := re.search(r"\brun command[:\s]+(.+)", message, re.I):
        return {"action": "coding_run_command", "params": {"command": m.group(1).strip()}}

    if re.search(r"\b(index code|build code index|reindex code)\b", lower):
        return {"action": "code_index", "params": {}}

    if m := re.search(r"\b(?:search code for|find in code|where is)\s+(.+)", message, re.I):
        return {"action": "code_search", "params": {"query": m.group(1).strip()}}

    if m := re.search(r"\bfind files?(?: named| matching| called| like)?\s+(.+)", message, re.I):
        return {"action": "coding_find", "params": {"query": m.group(1).strip()}}

    if m := re.search(
        r"\b(?:read|load)\s+(?:file\s+)?[`'\"]?([^\s`'\"]+\.\w+)",
        message,
        re.I,
    ):
        return {"action": "coding_read", "params": {"path": m.group(1)}}

    if re.search(r"\bindex (?:this )?(?:project|folder|directory|codebase)\b", lower):
        path = py_path_from_message(message) or "."
        return {"action": "coding_project", "params": {"path": path}}

    if re.search(r"\b(diagnose|explain what's wrong|what's wrong with)\b", lower) and (
        session.last_file or re.search(r"\.(?:py|js|ts)\b", message)
    ):
        path = session.last_file or ""
        if m := re.search(r"[`'\"]?([^\s`'\"]+\.(?:py|js|ts|sh))", message):
            path = m.group(1)
        return {"action": "coding_diagnose", "params": {"path": path, "task": message}}

    if re.search(r"\b(fix|improve)\b.*\b(selection|selected)\b", lower) or re.match(r"^fix selection\s*$", lower):
        return {"action": "coding_fix", "params": {"use_selection": True}, "thinking": "editor selection"}

    if re.search(r"\bexplain\b.*\b(selection|selected|this code)\b", lower) or re.match(r"^explain selection\s*$", lower):
        return {"action": "coding_explain_selection", "params": {}, "thinking": "editor selection"}

    if re.search(r"\b(editor context|what'?s in (my )?editor|cursor (file|selection))\b", lower):
        return {"action": "coding_editor_status", "params": {}, "thinking": "editor bridge"}

    if re.search(r"\bdebug until\b", lower) and re.search(r"\btests?\s+pass\b", lower):
        path = session.last_file or ""
        if m := re.search(r"[`'\"]?([^\s`'\"]+\.py)", message):
            path = m.group(1)
        if path:
            return {"action": "coding_fix_tests", "params": {"path": path}, "thinking": "pattern match"}

    if re.search(
        r"\b(implement|build|add feature)\b",
        lower,
    ) and not re.search(r"\b(image|audio|music|journal)\b", lower):
        path = py_path_from_message(message) or session.last_file or ""
        with_tests = re.search(r"\b(with tests?|and tests?|pytest)\b", lower)
        if with_tests or not path or not py_file_exists(path):
            if not path or not py_file_exists(path):
                path = path if path and not py_file_exists(path) else infer_script_path(message)
            return {"action": "coding_create", "params": {"description": message, "path": path}}

    if re.search(
        r"\b(implement|build|add feature|debug until|fix across|refactor)\b",
        lower,
    ) and not re.search(r"\b(image|audio|music|journal)\b", lower):
        path = session.last_file or ""
        if m := re.search(r"[`'\"]?([^\s`'\"]+\.py)", message):
            path = m.group(1)
        max_steps = 2 if re.search(r"\bdebug until\b", lower) else 5
        return {"action": "coding_agent", "params": {"task": message, "path": path, "max_steps": max_steps}}

    if re.search(r"\brefactor\b", lower) and re.search(r"\b(files?|modules?|project)\b", lower):
        return {"action": "coding_refactor", "params": {"task": message, "path": session.last_file or ""}}

    if re.search(
        r"\b(how does|where is|explain (the )?code|what does .+ do|how is .+ implemented)\b",
        lower,
    ) and is_codebase_question(message, session):
        return {"action": "coding_chat", "params": {"query": message}}

    if re.search(r"\b(keep going|continue coding|run tests again)\b", lower):
        return {"action": "coding_agent", "params": {"task": message, "path": session.last_file or ""}}

    if re.search(r"\b(chart|graph|plot)\b", lower) and re.search(r"\b(data|csv|column)\b", lower):
        from jarvis.modules.data import parse_chart_request
        return {"action": "data_chart", "params": parse_chart_request(message)}

    if re.search(r"\b(search (the )?web|web search|look up online|google)\b", lower):
        q = re.sub(r"^(please\s+)?(search (the )?web for|web search|look up online|google)\s*[:\-]?\s*", "", message, flags=re.I).strip()
        return {"action": "web_search", "params": {"query": q or message}}

    from jarvis.runtime_routing import route_runtime_priority

    if runtime_hit := route_runtime_priority(message):
        return runtime_hit

    if is_general_knowledge_question(message, session):
        return {"action": "web_search", "params": {"query": message}, "thinking": "general knowledge"}

    if re.search(
        r"\b(weather|forecast|temperature|rain|snow|sunny|cloudy|humid|wind)\b",
        lower,
    ) and re.search(
        r"\b(what|how|will|going to|like|expect|tomorrow|today|tonight|this week|next week)\b",
        lower,
    ):
        return {"action": "weather_forecast", "params": {}, "thinking": "pattern match"}

    if m := re.search(r"\brename\s+(\w+)\s+(?:to|as)\s+(\w+)\b", lower):
        return {"action": "rename_symbol", "params": {"symbol": m.group(1), "new_name": m.group(2)}}

    if re.search(r"\b(go to definition|jump to definition|definition of)\b", lower):
        path = session.last_file or ""
        if m := re.search(r"[`'\"]?([^\s`'\"]+\.\w+)", message):
            path = m.group(1)
        line = 1
        if m := re.search(r"\bline\s+(\d+)\b", lower):
            line = int(m.group(1))
        return {"action": "lsp_definition", "params": {"path": path, "line": line}}

    if re.search(r"\b(find references|show references|who calls)\b", lower):
        path = session.last_file or ""
        if m := re.search(r"[`'\"]?([^\s`'\"]+\.\w+)", message):
            path = m.group(1)
        line = 1
        if m := re.search(r"\bline\s+(\d+)\b", lower):
            line = int(m.group(1))
        return {"action": "lsp_references", "params": {"path": path, "line": line}}

    if re.search(r"\b(hover|type info|what is this symbol)\b", lower) and session.last_file:
        line = 1
        if m := re.search(r"\bline\s+(\d+)\b", lower):
            line = int(m.group(1))
        return {"action": "lsp_hover", "params": {"path": session.last_file, "line": line}}

    if re.search(r"\b(format (this )?file|lsp format)\b", lower):
        path = session.last_file or ""
        if m := re.search(r"[`'\"]?([^\s`'\"]+\.\w+)", message):
            path = m.group(1)
        return {"action": "lsp_format", "params": {"path": path, "write": True}}

    if re.search(r"\b(document symbols|outline|list symbols)\b", lower):
        path = session.last_file or ""
        if m := re.search(r"[`'\"]?([^\s`'\"]+\.\w+)", message):
            path = m.group(1)
        return {"action": "lsp_symbols", "params": {"path": path}}

    if re.search(r"\b(check (syntax|types)|syntax check|lint|pyright|ruff|mypy|lsp)\b", lower):
        path = session.last_file or ""
        if m := re.search(r"[`'\"]?([^\s`'\"]+\.\w+)", message):
            path = m.group(1)
        return {"action": "syntax_check", "params": {"path": path}}

    if re.search(r"\b(list|show)\b.*\bcoding tasks?\b", lower):
        return {"action": "coding_task", "params": {"action": "list"}}

    if re.search(r"\bpause\b.*\bcoding task\b", lower):
        return {"action": "coding_task", "params": {"action": "pause"}}

    if re.search(r"\bresume\b.*\bcoding task\b", lower):
        return {"action": "coding_task", "params": {"action": "resume"}}

    if m := re.search(r"\bextract\s+lines?\s+(\d+)\s*[-–]\s*(\d+)\s+(?:as|into)\s+(\w+)", message, re.I):
        return {
            "action": "extract_function",
            "params": {"start_line": int(m.group(1)), "end_line": int(m.group(2)), "name": m.group(3), "path": session.last_file or ""},
        }

    if m := re.search(r"\bmove\s+(?:module\s+)?(\S+\.py)\s+to\s+(\S+)", message, re.I):
        return {"action": "move_module", "params": {"from": m.group(1), "to": m.group(2)}}

    if re.search(r"\b(generate|create|make)\s+(?:some\s+)?music\b", lower):
        return {"action": "generate_music", "params": {"prompt": message}}

    if re.search(r"\b(write|compose|create)\s+(?:a\s+)?song\b", lower):
        return {"action": "generate_song", "params": {"topic": message}}

    if _AUDIO_TRANSFORM_RE.search(message) and (
        session.last_audio
        or re.search(
            r"\b(music|audio|track|song|genre|jazz|rock|pop|ballad|remix|beat|melody|mp3|wav|flac|recording)\b",
            lower,
        )
    ):
        return {"action": "transform_genre", "params": {"genre": message, "path": session.last_audio or ""}}

    if re.search(r"\b(sing|turn my voice|voice to song|make me sing)\b", lower):
        return {"action": "voice_to_song", "params": {"path": session.last_audio or "", "lyrics": message}}

    if re.search(r"\b(new branch|fork (this )?chat|branch (this )?conversation)\b", lower):
        name = re.sub(r".*branch\s*", "", message, flags=re.I).strip() or "Branch"
        return {"action": "branch_create", "params": {"name": name}}

    if re.search(r"\b(list branches|show branches|chat branches)\b", lower):
        return {"action": "branch_list", "params": {}}

    if m := re.search(r"\b(?:switch|use) branch\s+(\S+)", lower):
        return {"action": "branch_switch", "params": {"branch_id": m.group(1)}}

    if re.search(r"\b(delete|remove|trim)\s+branch(?:es)?\b", lower):
        ids = re.findall(r"`([^`]+)`|\b(branch_[a-z0-9_]+)\b", message, flags=re.I)
        flat = [g for pair in ids for g in pair if g]
        if flat:
            return {"action": "branch_delete", "params": {"branch_ids": flat}}
        if m := re.search(r"\b(?:delete|remove|trim)\s+branch(?:es)?\s+(\S+)", lower):
            return {"action": "branch_delete", "params": {"branch_id": m.group(1)}}
        return {"action": "branch_delete", "params": {}}

    if re.search(r"\bselect\s+.+\bfrom\b", lower):
        return {"action": "data_sql", "params": {"query": message}}

    audio_gen = (
        r"\b(?:generate|create|make)\s+(?:an?\s+)?(?:audio|voice|speech|recording)\s+"
        r"(?:that\s+)?(?:says?|reading?|of)?\s*[:\-]?\s*(.+)"
    )
    if m := re.search(audio_gen, lower):
        return {"action": "generate_audio", "params": {"text": m.group(1).strip()}}

    if img := _image_generation_route(message, lower):
        return img

    if m := re.search(
        r"\b(?:generate|create|make)\s+(?:an?\s+)?(?:video|clip|animation|movie)\s+(?:of\s+)?(.+)",
        lower,
    ):
        return {"action": "generate_video", "params": {"prompt": m.group(1).strip()}}

    if m := re.search(
        r'\b(?:make|create|generate)\s+(?:an?\s+)?meme\s+(?:with\s+)?'
        r'(?:top\s+["\']?(.+?)["\']?\s+)?(?:and\s+)?(?:bottom\s+["\']?(.+?)["\']?)?$',
        message,
        re.I,
    ):
        top = (m.group(1) or "").strip()
        bottom = (m.group(2) or "").strip()
        if top or bottom:
            return {"action": "generate_meme", "params": {"top": top, "bottom": bottom}}

    if m := re.search(r"\b(?:make|create|generate)\s+(?:an?\s+)?meme\s+(?:about\s+)?(.+)", lower):
        return {"action": "generate_meme", "params": {"idea": m.group(1).strip()}}

    if re.search(r"\bmeme\s+(?:generator|time|ify)\b", lower):
        return {"action": "generate_meme", "params": {"idea": message}}

    if re.search(r"\b(upscale|enlarge)\s+(the\s+)?(image|picture|photo|it)\b", lower):
        scale = 2
        if m := re.search(r"\b(\d)\s*x\b", lower):
            scale = int(m.group(1))
        return {"action": "upscale_image", "params": {"scale": scale}}

    if inpaint := _maybe_inpaint_route(message, lower, session):
        return inpaint

    if re.search(r"\b(live\s+)?(ae-5|sound blaster)\s+(eq|vst)\b", lower) or re.search(
        r"\b(enable|disable|turn off)\s+live\s+(eq|vst)\b", lower
    ):
        preset = "off" if re.search(r"\b(off|disable|direct)\b", lower) else "voice"
        for key in ("scout", "gaming", "music", "voice"):
            if key in lower:
                preset = key
                break
        return {"action": "set_vst_live", "params": {"preset": preset}}

    if m := re.search(
        r"\b(?:apply|run|use)\s+(voice|music|scout|gaming|flat)\s+(?:eq|vst|chain)\b",
        lower,
    ):
        return {"action": "process_audio_vst", "params": {"chain": m.group(1), "path": session.last_audio}}

    if re.search(r"\b(eq|vst|process)\s+(the\s+)?(audio|recording|clip)\b", lower) and session.last_audio:
        chain = "voice"
        for key in ("scout", "gaming", "music", "voice"):
            if key in lower:
                chain = key
                break
        return {"action": "process_audio_vst", "params": {"chain": chain, "path": session.last_audio}}

    if re.search(r"\b(edit (the )?audio|trim (the )?audio|cut (the )?audio)\b", lower):
        return {"action": "edit_audio", "params": {"path": session.last_audio, "instruction": message}}

    if re.search(r"\b(read (it|aloud|this)|speak|say that)\b", lower):
        text = re.sub(r"^(please\s+)?(read (it|aloud|this)|speak|say that)\s*[:\-]?\s*", "", message, flags=re.I).strip()
        return {"action": "generate_audio", "params": {"text": text or message}}

    return None


def normalize_route_intent(intent: dict) -> dict:
    """Ensure tool-router output has string action + dict params."""
    action = intent.get("action", "chat")
    if isinstance(action, dict):
        intent["action"] = str(action.get("name") or action.get("action") or "chat")
    elif not isinstance(action, str) or not action.strip():
        intent["action"] = "chat"
    params = intent.get("params")
    if not isinstance(params, dict):
        intent["params"] = {}
    return intent


def _resolve_ambiguous_path(path: str, session) -> dict | None:
    if path:
        return None
    if session.last_file:
        return None
    if len(session.recent_files) > 1:
        return {
            "action": "clarify",
            "params": {},
            "needs_clarification": True,
            "clarification_question": "Which file did you mean?",
            "choices": session.recent_files[:5],
            "thinking": "ambiguous path",
        }
    return None


def route(message: str, session: SessionContext, attachment: dict | None = None) -> dict:
    if session.pending_clarification:
        choice = message.strip()
        pending = session.pending_clarification
        session.pending_clarification = None
        if choice.isdigit():
            idx = int(choice) - 1
            choices = pending.get("choices", [])
            if 0 <= idx < len(choices):
                choice = choices[idx]
        action = pending.get("action", "coding_fix")
        return {
            "action": action,
            "params": {"path": choice},
            "thinking": "clarification resolved",
        }

    follow = _follow_up_route(message, session)
    if follow:
        follow.setdefault("thinking", "follow-up")
        return _finalize_intent(normalize_route_intent(follow), message, session)

    from jarvis.routing_inspector import is_routing_command
    from jarvis.timeline_commands import is_timeline_command

    if routing_cmd := is_routing_command(message):
        intent = {
            "action": routing_cmd,
            "params": {},
            "thinking": "routing inspector",
            "route_handler": "RoutingInspector",
        }
        return _finalize_intent(intent, message, session)

    if timeline_cmd := is_timeline_command(message):
        intent = {
            "action": timeline_cmd,
            "params": {},
            "thinking": "timeline",
            "route_handler": "Timeline",
        }
        return _finalize_intent(intent, message, session)

    nlu_used = False
    from jarvis.nlu.pipeline import nlu_enabled, route_via_nlu

    if nlu_enabled():
        nlu_intent = route_via_nlu(message, session, attachment)
        if nlu_intent:
            nlu_used = True
            nlu_intent.setdefault("thinking", "nlu")
            nlu_intent = normalize_route_intent(nlu_intent)
            nlu_intent = _maybe_downgrade_coding_chat(nlu_intent, message, session)
            return _finalize_intent(nlu_intent, message, session)

    quick = _quick_route(message, attachment, session, skip_runtime_priority=nlu_used)
    if quick:
        quick.setdefault("thinking", "pattern match")
        quick = normalize_route_intent(quick)
        quick = _maybe_downgrade_coding_chat(quick, message, session)
        if quick["action"] in ("coding_fix", "coding_improve", "coding_run", "coding_show", "coding_read"):
            path = quick.get("params", {}).get("path") or session.resolve_path(None)
            if not path:
                amb = _resolve_ambiguous_path(path, session)
                if amb:
                    session.pending_clarification = {
                        "action": quick["action"],
                        "choices": amb["choices"],
                    }
                    return amb
            elif not quick.get("params", {}).get("path"):
                quick["params"]["path"] = path
        return _finalize_intent(quick, message, session)

    attachment_context = json.dumps(attachment) if attachment else ""
    tool_result = llm.route_with_tools(message, session.context_summary(), attachment)
    if tool_result:
        tool_result = normalize_route_intent(tool_result)
        tool_result = _maybe_downgrade_coding_chat(tool_result, message, session)
        if tool_result.get("needs_clarification"):
            session.pending_clarification = {
                "action": tool_result.get("action"),
                "choices": tool_result.get("choices", []),
            }
        return _finalize_intent(tool_result, message, session)

    prompt = ROUTER_PROMPT.format(
        actions=ACTIONS,
        message=message,
        session_context=session.context_summary(),
        attachment_context=attachment_context or "none",
    )

    try:
        raw = llm.ask(llm.general_model(), [{"role": "user", "content": prompt}])
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        parsed = json.loads(raw)
        if "action" in parsed:
            parsed.setdefault("params", {})
            parsed = normalize_route_intent(parsed)
            parsed = _maybe_downgrade_coding_chat(parsed, message, session)
            if parsed.get("needs_clarification"):
                session.pending_clarification = {
                    "action": parsed.get("action"),
                    "choices": parsed.get("choices", []),
                }
            return _finalize_intent(parsed, message, session)
    except (json.JSONDecodeError, KeyError):
        pass

    from jarvis.runtime_routing import route_runtime_priority

    if runtime_hit := route_runtime_priority(message):
        return _finalize_intent(runtime_hit, message, session)

    return _finalize_intent(
        {"action": "chat", "params": {}, "thinking": "fallback"},
        message,
        session,
    )
