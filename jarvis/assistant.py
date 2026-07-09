import logging
import re
import subprocess
import threading
import uuid
from pathlib import Path
from typing import Any, Iterator

from jarvis import fs, llm, proposal_store, rag
from jarvis.action_log import log_action
from jarvis.branches import BranchManager
from jarvis.capabilities import capabilities_message, greeting_message, models_guide
from jarvis.code_context import format_context, gather_context
from jarvis.coding_agent import CodingAgent
from jarvis.coding_tasks import TaskManager
from jarvis.coding_test_impact import format_test_impact
from jarvis.coding_verify import verify_python_files
from jarvis.config import (
    DATA_DIR,
    PROJECT_ROOT,
    build_system_prompt,
    is_uncensored,
    load_personality_preset,
    set_uncensored,
)
from jarvis.diff_util import make_diff
from jarvis.model_store import get_models
from jarvis.modules.audio import SUPPORTED_AUDIO, AudioEngine
from jarvis.modules.coding import CodingEngine
from jarvis.modules.data import DataEngine
from jarvis.modules.general import GeneralEngine
from jarvis.modules.image import ImageEngine
from jarvis.modules.journal import BulletJournal
from jarvis.modules.memory import MemoryStore
from jarvis.modules.vision import IMAGE_EXTENSIONS, VisionEngine
from jarvis.ollama_health import check_ollama, models_missing
from jarvis.router import infer_script_path, py_path_from_message, route
from jarvis.sandbox import run_sandboxed
from jarvis.syntax_check import available_tools, check_files, diagnostics_to_dicts, format_diagnostics
from jarvis.vision_media import (
    PDF_EXTENSIONS,
    VIDEO_EXTENSIONS,
    apply_crop_bytes,
    extract_pdf_page,
    extract_video_frame,
    parse_region,
    parse_video_second,
)

from jarvis.response import err as _err, ok as _ok, stream_done as _stream_done
from jarvis.session import SessionContext
from jarvis.handlers.media import MediaHandler

UPLOAD_DIR = DATA_DIR / "uploads"


def display_chat_user_content(content: str) -> str:
    """Strip injected memory/RAG prefix from legacy stored user turns."""
    if "\n\nUser: " in content:
        return content.rsplit("\n\nUser: ", 1)[-1]
    return content


def perform_undo_apply(assistant) -> dict:
    """Shared undo logic for chat and GUI API."""
    backups = getattr(assistant, "last_apply_backups", None) or []
    if not backups and getattr(assistant, "last_apply_backup", None):
        backups = [{"path": assistant.last_apply_path, "backup": assistant.last_apply_backup}]
    if not backups:
        return _err("Nothing to undo.")
    restored = []
    deleted = []
    for item in backups:
        path = item.get("path")
        backup = item.get("backup")
        is_new = item.get("is_new") or backup == "(new file)"
        was_deleted = item.get("was_deleted")
        if not path:
            continue
        if is_new:
            resolved = fs.resolve_path(path, base=assistant.coding._base())
            if resolved.exists():
                resolved.unlink()
                deleted.append(path)
            continue
        if was_deleted:
            if not backup or not Path(backup).exists():
                continue
            content = Path(backup).read_text(encoding="utf-8")
            fs.write_file(path, content, base=assistant.coding._base())
            restored.append(path)
            continue
        if not backup or not Path(backup).exists():
            continue
        content = Path(backup).read_text(encoding="utf-8")
        fs.write_file(path, content, base=assistant.coding._base())
        restored.append(path)
    assistant.last_apply_backups = []
    assistant.last_apply_backup = None
    assistant.last_apply_path = None
    if not restored and not deleted:
        return _err("Could not restore — backup files missing.")
    parts = []
    if restored:
        parts.append("Restored:\n" + "\n".join(f"- `{p}`" for p in restored))
    if deleted:
        parts.append("Deleted new files:\n" + "\n".join(f"- `{p}`" for p in deleted))
    return _ok("\n\n".join(parts), module="coding")


logger = logging.getLogger("jarvis.assistant")


class JarvisAssistant:
    """Unified natural-language interface to all Jarvis modules."""

    def __init__(self, uncensored: bool | None = None):
        if uncensored is not None:
            set_uncensored(uncensored)
        self.coding = CodingEngine()
        self.memory = MemoryStore()
        self.general = GeneralEngine(memory=self.memory)
        self.audio = AudioEngine()
        self._vision_engines: dict[str, VisionEngine] = {}
        self._vision_llava_warned = False
        self.image = ImageEngine()
        from jarvis.modules.video import VideoEngine
        from jarvis.modules.meme import MemeEngine

        self.video = VideoEngine()
        self.meme = MemeEngine()
        self._media = MediaHandler(self)
        self.data = DataEngine()
        self.journal = BulletJournal()
        self.branches = BranchManager()
        self.session = self.branches.load_session(self.branches.active_id)
        self.pending_proposals: dict[str, dict] = proposal_store.load()
        self.pending_diagnoses: dict[str, dict] = {}
        self.task_manager = TaskManager()
        self._active_task_id: str = ""
        self.last_apply_backup: str | None = None
        self.last_apply_path: str | None = None
        self.last_apply_backups: list[dict] = []
        self._request_lock = threading.Lock()
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        from jarvis.cheatsheets import seed_cheatsheets

        seed_cheatsheets(self.memory)
        from jarvis.trust_memory import scrub_store

        scrubbed = scrub_store(self.memory)
        self._trust_last_scrub = scrubbed.get("removed", 0)
        self.sync_project_namespace()
        self.refresh_system_prompt()

    def _build_prompt(self) -> str:
        return build_system_prompt(load_personality_preset(), self.memory)

    def refresh_system_prompt(self) -> None:
        prompt = self._build_prompt()
        self.branches.update_system_prompt(self.branches.active_id, prompt)
        self.conversation = self.branches.get_conversation(self.branches.active_id, prompt)

    def sync_project_namespace(self) -> str | None:
        from jarvis.behaviors.memory.context import MemoryContext
        from jarvis.behaviors.memory.engine import MemoryEngine

        return MemoryEngine.sync_project_namespace(MemoryContext.from_orchestrator(self))

    def auto_checkpoint(self, *, reason: str = "exit") -> dict:
        from jarvis.behaviors.memory.context import MemoryContext
        from jarvis.behaviors.memory.engine import MemoryEngine

        return MemoryEngine.auto_checkpoint(MemoryContext.from_orchestrator(self), reason=reason)

    @property
    def vision(self) -> VisionEngine:
        bid = self.branches.active_id or "main"
        if bid not in self._vision_engines:
            self._vision_engines[bid] = VisionEngine()
        return self._vision_engines[bid]

    def set_uncensored(self, enabled: bool) -> None:
        set_uncensored(enabled)
        self.refresh_system_prompt()

    def switch_branch(self, branch_id: str) -> bool:
        self.branches.save_session(self.branches.active_id, self.session)
        if not self.branches.switch(branch_id):
            return False
        self.session = self.branches.load_session(branch_id)
        self.conversation = self.branches.get_conversation(branch_id, self._build_prompt())
        return True

    def delete_branch(self, branch_id: str) -> bool:
        self.branches.save_session(self.branches.active_id, self.session)
        was_active = self.branches.active_id == branch_id
        if not self.branches.delete_branch(branch_id):
            return False
        if was_active:
            self.session = self.branches.load_session("main")
            self.conversation = self.branches.get_conversation("main", self._build_prompt())
        return True

    def delete_branches(self, branch_ids: list[str]) -> dict:
        deleted: list[str] = []
        for bid in branch_ids:
            if self.delete_branch(bid):
                deleted.append(bid)
        return {"deleted": deleted, "active": self.branches.active_id}

    def clear_branch_messages(self, branch_id: str) -> dict:
        bid = (branch_id or "").strip() or "main"
        prompt = self._build_prompt()
        if not self.branches.clear_messages(bid, prompt):
            return _err(f"Unknown branch: {bid}", module="general")
        if self.branches.active_id == bid:
            self.session = SessionContext()
            self.conversation = self.branches.get_conversation(bid, prompt)
            self.coding.conversation.clear()
            self.general.conversation.clear()
            self.vision.current_image = None
            self.vision._session_image = None
            self.vision.conversation.clear()
            self.vision._image_cache.clear()
            self._vision_engines.clear()
            self._vision_llava_warned = False
        else:
            self.branches.persist(branch_id=bid, session=SessionContext())
        return _ok(
            "Main chat cleared." if bid == "main" else f"Branch **{bid}** cleared.",
            module="general",
            branch_id=bid,
        )

    def create_branch(self, name: str, from_index: int | None = None) -> str:
        self.branches.save_session(self.branches.active_id, self.session)
        bid = self.branches.create_branch(name, self.branches.active_id, from_index)
        self.session = self.branches.load_session(bid)
        self.conversation = self.branches.get_conversation(bid, self._build_prompt())
        return bid

    def fork_branch(self, name: str, display_index: int) -> str:
        self.branches.save_session(self.branches.active_id, self.session)
        bid = self.branches.fork_at_display_index(name, display_index, self.branches.active_id)
        self.session = self.branches.load_session(bid)
        self.conversation = self.branches.get_conversation(bid, self._build_prompt())
        return bid

    def get_status(self) -> dict:
        ollama = check_ollama()
        active = get_models()
        required = [active["general"], active["coder"], active["embed"]]
        missing = models_missing(required, ollama.get("models", [])) if ollama["running"] else required
        from jarvis import rag
        from jarvis.config import load_vision_quality
        from jarvis.gpu import detect_gpu, is_low_vram

        embed_ok = llm.embed_available()
        embed_warn = rag.embed_warning()
        vision_name = llm.vision_model()
        installed = ollama.get("models", []) if ollama.get("running") else []
        vision_installed = any(
            vision_name.lower() in m.lower() or m.lower().startswith(vision_name.split(":")[0].lower())
            for m in installed
        )
        gpu = detect_gpu()
        vram_gb = round((gpu.get("vram_mb") or 0) / 1024, 1)
        vision_note = ""
        if not vision_installed and ollama.get("running"):
            vision_note = f"Vision model `{vision_name}` not installed — run Pull missing models."
        elif load_vision_quality() == "fast":
            vision_note = "Vision mode: Fast (moondream preset). Switch to Use selected model to keep your Vision dropdown."
        elif load_vision_quality() == "quality":
            vision_note = "Vision mode: Quality preset (heavy model for OCR/compare)."
        elif is_low_vram() and "llava" in vision_name.lower() and "13" in vision_name:
            vision_note = "8GB GPU: llava:13b is heavy — consider llama3.2-vision:11b or moondream."
        else:
            from jarvis.model_store import _saved_vision_model, _load_raw
            from jarvis.ollama_health import ollama_version, requires_mllama, supports_mllama

            saved = _saved_vision_model(_load_raw(), "uncensored" if is_uncensored() else "standard", installed)
            if saved and requires_mllama(saved) and not supports_mllama() and vision_name != saved:
                vision_note = (
                    f"Ollama {'.'.join(str(x) for x in (ollama_version() or (0, 0, 0)))} "
                    f"does not support `{saved}` (mllama removed in 0.30.x). "
                    f"Using `{vision_name}` — or run ./scripts/install-ollama-0.24.sh for llama3.2-vision."
                )

        data_note = ""
        pandas_ok = False
        try:
            import pandas  # noqa: F401
            pandas_ok = True
        except ImportError:
            data_note = "Install pandas for stats/charts: pip install pandas"
        ds = self.data.dataset
        data_loaded = bool(ds)
        if data_loaded and ds:
            data_note = (
                f"Loaded: {Path(self.data.dataset_path or self.session.last_data_path).name} "
                f"({ds.get('row_count', 0)} rows)"
            )
        elif self.session.last_data_path:
            data_note = f"Last file: {Path(self.session.last_data_path).name} — attach or ask to reload."

        from jarvis.config import (
            load_auto_checkpoint,
            load_auto_memory,
            load_auto_memory_mode,
            load_auto_namespace,
            load_memory_in_system_prompt,
            load_memory_namespace,
        )
        mem_stats = self.memory.stats()
        mem_note = f"{mem_stats['total']} memories"
        if mem_stats.get("by_type"):
            mem_note += " · " + ", ".join(f"{k}:{v}" for k, v in sorted(mem_stats["by_type"].items()))
        from jarvis.memory_context import detect_project_namespace

        return {
            "uncensored": is_uncensored(),
            "embed_ok": embed_ok,
            "embed_warning": embed_warn,
            "models": {
                "general": llm.general_model(),
                "coder": llm.coder_model(),
                "vision": vision_name,
                "review": llm.review_model(),
                "embed": llm.embed_model(),
            },
            "vision": {
                "model": vision_name,
                "installed": vision_installed,
                "quality_mode": load_vision_quality(),
                "vram_gb": vram_gb,
                "note": vision_note,
            },
            "data": {
                "loaded": data_loaded,
                "pandas": pandas_ok,
                "streaming": bool(ds.get("streaming")) if ds else False,
                "path": str(self.data.dataset_path or self.session.last_data_path or ""),
                "row_count": ds.get("row_count", 0) if ds else 0,
                "columns": (ds.get("columns") or [])[:12] if ds else [],
                "note": data_note,
            },
            "memory": {
                "total": mem_stats.get("total", 0),
                "namespaces": mem_stats.get("namespaces", []),
                "namespace": self.session.memory_namespace or load_memory_namespace(),
                "project_namespace": detect_project_namespace(),
                "auto_memory": load_auto_memory(),
                "auto_memory_mode": load_auto_memory_mode(),
                "auto_checkpoint": load_auto_checkpoint(),
                "auto_namespace": load_auto_namespace(),
                "memory_in_system_prompt": load_memory_in_system_prompt(),
                "embed_ok": embed_ok,
                "note": mem_note,
            },
            "ollama": ollama,
            "models_missing": missing,
            "session": self.session.context_summary(),
        }

    def save_upload(
        self,
        filename: str,
        content: bytes,
        *,
        crop: dict | None = None,
        video_second: float | None = None,
        pdf_page: int | None = None,
        message: str = "",
    ) -> dict:
        safe_name = Path(filename).name
        suffix = Path(safe_name).suffix.lower()

        if suffix in VIDEO_EXTENSIONS:
            try:
                second = parse_video_second(message, video_second)
                frame_bytes, frame_name = extract_video_frame(content, safe_name, second)
                return self.save_upload(frame_name, frame_bytes, crop=crop)
            except Exception as e:
                return {"path": "", "kind": "error", "name": safe_name, "error": str(e)}

        if crop and suffix in IMAGE_EXTENSIONS:
            try:
                content = apply_crop_bytes(content, crop)
                stem = Path(safe_name).stem
                safe_name = f"{stem}_crop.jpg"
            except Exception as e:
                return {"path": "", "kind": "error", "name": safe_name, "error": str(e)}

        dest = UPLOAD_DIR / safe_name
        if dest.exists():
            stem = Path(safe_name).stem
            ext = Path(safe_name).suffix
            for n in range(2, 1000):
                candidate = UPLOAD_DIR / f"{stem}_{n}{ext}"
                if not candidate.exists():
                    dest = candidate
                    safe_name = candidate.name
                    break

        dest.write_bytes(content)
        suffix = dest.suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            kind = "image"
            self.session.note_image(str(dest))
        elif suffix in PDF_EXTENSIONS or suffix == ".docx":
            kind = "document"
            self.session.note_document(str(dest))
        elif suffix in SUPPORTED_AUDIO:
            kind = "audio"
            self.session.note_audio(str(dest))
        elif suffix in {".csv", ".json", ".xlsx", ".xlsm", ".db", ".sqlite", ".sqlite3"}:
            kind = "data"
            self.session.note_data(str(dest))
        else:
            kind = "file"
            self.session.note_file(str(dest))
        return {"path": str(dest), "kind": kind, "name": safe_name}

    def process(
        self,
        message: str,
        attachment: dict | None = None,
        branch_id: str | None = None,
        attachment2: dict | None = None,
    ) -> dict:
        from jarvis.env_loader import load_jarvis_env
        from jarvis.request_activity import begin, end

        load_jarvis_env()
        begin()
        try:
            with self._request_lock:
                return self._process_unlocked(message, attachment, branch_id, attachment2)
        finally:
            end()

    def _process_unlocked(
        self,
        message: str,
        attachment: dict | None = None,
        branch_id: str | None = None,
        attachment2: dict | None = None,
    ) -> dict:
        if branch_id:
            self.switch_branch(branch_id)

        if (
            attachment
            and attachment2
            and attachment.get("kind") == "image"
            and attachment2.get("kind") == "image"
            and attachment.get("path")
            and attachment2.get("path")
        ):
            return self._compare_images(
                {"path1": attachment["path"], "path2": attachment2["path"]},
                message or "Compare these two images.",
            )

        if attachment2 and attachment2.get("kind") == "error":
            return _err(attachment2.get("error") or "Could not read the second attachment.")

        if attachment and attachment2 and attachment.get("kind") == "image":
            return _err("Compare needs two images. Attach a second image and try again.")

        if attachment and attachment.get("kind") == "error":
            return _err(attachment.get("error") or "Could not read attachment.")

        if attachment and attachment.get("kind") == "document":
            from jarvis.document_pipeline import document_attachment_action

            if document_attachment_action(message) == "vision":
                if Path(attachment.get("path", "")).suffix.lower() != ".pdf":
                    return _err(
                        "Vision OCR works on PDF pages only. For Word files, ask to **summarize this document**.",
                        module="document",
                    )
                try:
                    page = max(1, int(attachment.get("pdf_page") or 1))
                    attachment = self._pdf_to_image_attachment(attachment, page)
                except Exception as e:
                    return _err(str(e), module="document")

        if attachment:
            path = attachment.get("path", "")
            kind = attachment.get("kind", "")
            if path and kind == "image":
                self.session.note_image(path)
            elif path and kind == "audio":
                self.session.note_audio(path)
            elif path and kind == "data":
                self.session.note_data(path)
            elif path and kind == "document":
                self.session.note_document(path)
        intent = route(message, self.session, attachment)
        if intent.get("action") == "clarify" or intent.get("needs_clarification"):
            choices = intent.get("choices", [])
            question = intent.get("clarification_question", "Which one?")
            lines = "\n".join(f"{i+1}. {c}" for i, c in enumerate(choices))
            return _ok(
                f"{question}\n\n{lines}\n\nReply with a number or name.",
                module="general",
                type="clarification",
                choices=choices,
            )

        action = intent.get("action", "chat")
        if isinstance(action, dict):
            action = str(action.get("name") or action.get("action") or "chat")
        elif not isinstance(action, str) or not action.strip():
            action = "chat"
        params = intent.get("params", {})
        if not isinstance(params, dict):
            params = {}
        if action.startswith("coding_") or action in ("find_references", "extract_function", "move_module", "rename_symbol"):
            self._apply_editor_params(params, message, action)

        handlers = {
            "chat": self._chat,
            "apply_proposal": self._apply_proposal_nl,
            "dismiss_proposal": self._dismiss_proposal,
            "undo_apply": self._undo_apply,
            "coding_read": self._coding_read,
            "coding_fix": self._coding_fix,
            "coding_fix_tests": self._coding_fix_tests,
            "coding_improve": self._coding_improve,
            "coding_find": self._coding_find,
            "coding_search": self._coding_search,
            "coding_run": self._coding_run,
            "coding_project": self._coding_project,
            "coding_review": self._coding_review,
            "coding_show": self._coding_show,
            "coding_create": self._coding_create,
            "coding_agent": self._coding_agent,
            "coding_chat": self._coding_chat,
            "coding_diagnose": self._coding_diagnose,
            "coding_refactor": self._coding_refactor,
            "code_index": self._code_index,
            "code_search": self._code_search,
            "syntax_check": self._syntax_check,
            "coding_task": self._coding_task,
            "extract_function": self._extract_function,
            "move_module": self._move_module,
            "git_commit": self._git_commit,
            "git_branch": self._git_branch,
            "git_summarize": self._git_summarize,
            "data_load": self._data_load,
            "data_query": self._data_query,
            "data_summary": self._data_summary,
            "data_clean": self._data_clean,
            "data_export": self._data_export,
            "record_transcribe": self._record_transcribe,
            "transcribe": self._transcribe,
            "analyze_audio": self._analyze_audio,
            "speak": self._generate_audio,
            "generate_audio": self._generate_audio,
            "edit_audio": self._edit_audio,
            "play_audio": self._play_audio,
            "process_audio_vst": self._process_audio_vst,
            "set_vst_live": self._set_vst_live,
            "describe_image": self._describe_image,
            "analyze_image": self._analyze_image,
            "ocr_image": self._ocr_image,
            "ocr_structured_image": self._ocr_structured_image,
            "image_to_code": self._image_to_code,
            "analyze_region": self._analyze_region,
            "batch_vision": self._batch_vision,
            "analyze_video_frame": self._analyze_image,
            "compare_images": self._compare_images,
            "generate_image": self._generate_image,
            "generate_video": self._generate_video,
            "generate_meme": self._generate_meme,
            "upscale_image": self._upscale_image,
            "inpaint_image": self._inpaint_image,
            "edit_image": self._edit_image,
            "enhance_prompt": self._enhance_prompt,
            "journal_log": self._journal_log,
            "journal_reflect": self._journal_reflect,
            "journal_migrate": self._journal_migrate,
            "journal_search": self._journal_search,
            "journal_review": self._journal_review,
            "data_chart": self._data_chart,
            "data_sql": self._data_sql,
            "web_search": self._web_search,
            "rename_symbol": self._rename_symbol,
            "find_references": self._find_references,
            "coding_run_tests": self._coding_run_tests,
            "coding_run_command": self._coding_run_command,
            "git_pr": self._git_pr,
            "coding_editor_status": self._coding_editor_status,
            "coding_explain_selection": self._coding_explain_selection,
            "coding_lsp": self._coding_lsp,
            "lsp_definition": self._lsp_definition,
            "lsp_references": self._lsp_references,
            "lsp_hover": self._lsp_hover,
            "lsp_format": self._lsp_format,
            "lsp_symbols": self._lsp_symbols,
            "generate_music": self._generate_music,
            "transform_genre": self._transform_genre,
            "generate_song": self._generate_song,
            "voice_to_song": self._voice_to_song,
            "diarize_audio": self._diarize_audio,
            "branch_create": self._branch_create,
            "branch_switch": self._branch_switch,
            "branch_list": self._branch_list,
            "branch_delete": self._branch_delete,
            "morning_briefing": self._morning_briefing,
            "briefing_news_detail": self._briefing_news_detail,
            "document_summarize": self._document_summarize,
            "document_query": self._document_query,
            "document_search": self._document_search,
            "document_info": self._document_info,
            "upgrade_wizard": self._upgrade_wizard,
            "upgrade_verify": self._upgrade_verify,
            "upgrade_apply": self._upgrade_apply,
            "upgrade_rollback": self._upgrade_rollback,
            "learn_about": self._learn_about,
            "learn_remember": self._learn_remember,
            "ha_status": self._ha_status,
            "ha_control": self._ha_control,
            "ha_scene": self._ha_scene,
            "ha_query": self._ha_query,
            "ha_set_token": self._ha_set_token,
        }

        handler = handlers.get(action, self._chat)
        try:
            from jarvis.background_jobs import BACKGROUND_ACTIONS
            from jarvis.handlers import ensure_handlers_loaded
            from jarvis.handlers.registry import call_action, get_queue, has_action, is_info_action
            from jarvis.media_jobs import QUEUED_ACTIONS

            ensure_handlers_loaded()

            queue = get_queue(action)
            if queue == "media" or action in QUEUED_ACTIONS:
                result = self._enqueue_media(action, params, message)
            elif queue == "background" or action in BACKGROUND_ACTIONS:
                result = self._enqueue_background(action, params, message)
            elif queue == "coding" or action == "coding_agent":
                result = self._enqueue_coding(params, message)
            elif queue == "fix_tests" or action == "coding_fix_tests":
                result = self._enqueue_fix_tests(params, message)
            elif has_action(action):
                result = call_action(self, action, params, message)
            else:
                result = handler(params, message)
            result["action"] = action
            result["thinking"] = intent.get("thinking", "")
            result["uncensored"] = is_uncensored()
            if is_info_action(action) or action in ("capabilities", "models_info", "greeting"):
                result["type"] = "info"
            if result.get("module"):
                self.session.note_module(result["module"])
            if result.get("module") in ("coding", "data"):
                self.sync_project_namespace()
            if action in (
                "coding_agent", "coding_refactor", "coding_fix", "coding_improve",
                "coding_create", "coding_fix_tests",
            ):
                mode = params.get("mode") or action.replace("coding_", "")
                self.session.note_coding_mode(mode)
            log_action(action, result.get("module", ""), message[:120], result.get("ok", True))
            if result.get("ok") and action not in ("chat", "capabilities", "greeting", "models_info"):
                from jarvis.trust_memory import record_tool_outcome

                record_tool_outcome(self.memory, action=action, detail=message[:120], ok=True)
            if action == "chat":
                self.branches.persist(session=self.session)
            return result
        except Exception as e:
            return _err(f"Something went wrong: {e}")

    def process_stream(
        self,
        message: str,
        attachment: dict | None = None,
        branch_id: str | None = None,
        attachment2: dict | None = None,
        request_id: str = "",
        lite_ui: bool = False,
    ) -> Iterator[dict]:
        """Stream chat responses; non-chat actions return single chunk."""
        from jarvis.request_activity import begin, end

        begin()
        self._request_lock.acquire()
        self._stream_lite_ui = lite_ui
        try:
            try:
                yield from self._process_stream_unlocked(
                    message, attachment, branch_id, attachment2, request_id,
                    lite_ui=lite_ui,
                )
            except Exception as e:
                logger.exception("process_stream failed")
                yield _stream_done(_err(f"Something went wrong: {e}"), lite_ui=lite_ui)
        finally:
            self._stream_lite_ui = False
            self._request_lock.release()
            end()

    def _process_stream_unlocked(
        self,
        message: str,
        attachment: dict | None = None,
        branch_id: str | None = None,
        attachment2: dict | None = None,
        request_id: str = "",
        lite_ui: bool = False,
    ) -> Iterator[dict]:
        if branch_id:
            self.switch_branch(branch_id)
        if (
            attachment
            and attachment2
            and attachment.get("kind") == "image"
            and attachment2.get("kind") == "image"
        ):
            result = None
            for kind, payload in self.vision.compare_events(
                attachment["path"],
                attachment2["path"],
                message or "Compare these two images.",
                uploads_dir=UPLOAD_DIR,
            ):
                if kind == "status":
                    yield {"type": "status", "message": payload}
                elif kind == "error":
                    yield _stream_done(_err(payload))
                    return
                elif kind == "result":
                    result = self._compare_from_result(payload)
            if result:
                yield _stream_done(result)
            return
        if attachment2 and attachment2.get("kind") == "error":
            yield _stream_done(_err(attachment2.get("error") or "Could not read the second attachment."))
            return
        if attachment and attachment.get("kind") == "error":
            yield _stream_done(_err(attachment.get("error") or "Could not read attachment."))
            return
        if attachment and attachment.get("kind") == "document":
            from jarvis.document_pipeline import document_attachment_action

            if document_attachment_action(message) == "vision":
                if Path(attachment.get("path", "")).suffix.lower() != ".pdf":
                    yield _stream_done(_err(
                        "Vision OCR works on PDF pages only. For Word files, ask to **summarize this document**.",
                        module="document",
                    ))
                    return
                try:
                    page = max(1, int(attachment.get("pdf_page") or 1))
                    attachment = self._pdf_to_image_attachment(attachment, page)
                except Exception as e:
                    yield _stream_done(_err(str(e), module="document"))
                    return
        if attachment:
            path = attachment.get("path", "")
            kind = attachment.get("kind", "")
            if path and kind == "image":
                self.session.note_image(path)
            elif path and kind == "audio":
                self.session.note_audio(path)
            elif path and kind == "data":
                self.session.note_data(path)
            elif path and kind == "document":
                self.session.note_document(path)
        intent = route(message, self.session, attachment)
        action = intent.get("action", "chat")
        if isinstance(action, dict):
            action = str(action.get("name") or action.get("action") or "chat")
        elif not isinstance(action, str) or not action.strip():
            action = "chat"
        params = intent.get("params", {})
        if not isinstance(params, dict):
            params = {}
        if action.startswith("coding_") or action in ("find_references", "extract_function", "move_module", "rename_symbol"):
            self._apply_editor_params(params, message, action)

        instant = {
            "capabilities", "models_info", "greeting", "morning_briefing", "recall", "remember",
            "memory_about_user", "memory_search", "memory_forget", "memory_correct", "memory_prune",
            "memory_summarize", "memory_namespace", "cheatsheet_list", "cheatsheet_show",
            "cheatsheet_reset", "project_checkpoint", "project_resume",
            "undo_apply", "apply_proposal", "dismiss_proposal",
        }
        if action in ("coding_agent", "coding_refactor"):
            params = intent.get("params", {})
            if lite_ui:
                yield _stream_done(self._enqueue_coding(params, message), lite_ui=True)
                return
            for event in self._coding_agent_stream(
                params, message,
                mode="refactor" if action == "coding_refactor" else params.get("mode", "agent"),
            ):
                yield event
            return

        if action == "coding_fix_tests":
            yield _stream_done(self._enqueue_fix_tests(intent.get("params", {}), message), lite_ui=lite_ui)
            return

        if action in ("coding_fix", "coding_improve"):
            params = intent.get("params", {})
            path = self._resolve_coding_path(params.get("path", ""))
            mode = "fix" if action == "coding_fix" else "improve"
            task = None
            if mode == "fix":
                diagnosis = self._diagnosis_for_path(path) if path else ""
                task = f"Fix based on diagnosis:\n{diagnosis}" if diagnosis else None
                if params.get("use_selection"):
                    task = (task or "Fix the selected code.") + "\n\nSee Editor context for the selection."
            editor_prompt = self._editor_task_suffix(params)
            if lite_ui:
                from jarvis.coding_jobs import submit_coding_propose

                job_id = submit_coding_propose(
                    self, path, mode, task=task, editor_prompt=editor_prompt,
                )
                yield _stream_done(self._coding_job_result(
                    f"**Coding** queued — `{path or 'file'}` ({mode})\n\n"
                    "Working in the background — result appears here when ready.",
                    job_id,
                    action,
                ), lite_ui=True)
                return
            for event in self._coding_propose_stream(
                path, mode, task=task, message=message, editor_prompt=editor_prompt,
            ):
                yield event
            return

        if action == "coding_create":
            if lite_ui:
                from jarvis.coding_jobs import submit_coding_create

                job_id = submit_coding_create(self, intent.get("params", {}), message)
                yield _stream_done(self._coding_job_result(
                    "**Coding** queued — new script\n\n"
                    "Working in the background — result appears here when ready.",
                    job_id,
                    "coding_create",
                ), lite_ui=True)
                return
            for event in self._coding_create_stream(intent.get("params", {}), message):
                yield event
            return

        if action == "coding_task" and re.search(r"\bresume\b", message, re.I):
            coding_task = self.task_manager.get(intent.get("params", {}).get("task_id", "")) or self.task_manager.active()
            if coding_task:
                self.task_manager.resume(coding_task.id)
                agent_params = {
                    "task": coding_task.checkpoint.get("task") or coding_task.title,
                    "path": coding_task.path,
                    "mode": coding_task.mode,
                    "task_id": coding_task.id,
                    "max_steps": 5,
                }
                if lite_ui:
                    yield _stream_done(self._enqueue_coding(agent_params, message), lite_ui=True)
                    return
                for event in self._coding_agent_stream(
                    agent_params,
                    message,
                    mode=coding_task.mode,
                ):
                    yield event
                return

        if action == "coding_chat":
            yield {"type": "status", "message": "Searching codebase…"}
            result = self._coding_chat(intent.get("params", {}), message)
            yield _stream_done(result)
            return

        from jarvis.media_jobs import QUEUED_ACTIONS
        from jarvis.background_jobs import BACKGROUND_ACTIONS

        if action in QUEUED_ACTIONS:
            for event in self._yield_media_job(action, params, message):
                yield event
            return

        if action in BACKGROUND_ACTIONS:
            yield _stream_done(self._enqueue_background(action, params, message))
            return

        if intent.get("action") == "clarify" or intent.get("needs_clarification"):
            choices = intent.get("choices", [])
            question = intent.get("clarification_question", "Which one?")
            lines = "\n".join(f"{i+1}. {c}" for i, c in enumerate(choices))
            result = _ok(
                f"{question}\n\n{lines}\n\nReply with a number or name.",
                module="general",
                type="clarification",
                choices=choices,
            )
            yield _stream_done(result)
            return

        if action == "briefing_news_detail":
            from jarvis import web_search
            from jarvis.briefing_news import (
                expand_headline_detail_stream,
                load_recent_headlines,
                match_headline,
            )
            from jarvis.profiles import web_search_disabled

            if web_search_disabled():
                yield _stream_done(_err(
                    "Web search is disabled (offline profile). Switch profile in the sidebar.",
                    module="briefing",
                ))
                return

            headlines = self.session.last_briefing_headlines or load_recent_headlines()
            if not headlines:
                yield _stream_done(_err(
                    "No briefing headlines saved yet. Say **morning briefing** first.",
                    module="briefing",
                ))
                return

            query = (params.get("query") or message or "").strip()
            title_hint = (params.get("title") or "").strip()
            headline = match_headline(title_hint or query, headlines)
            if not headline and title_hint:
                headline = match_headline(title_hint, headlines)
            if not headline:
                nat = [h for h in headlines if h.get("category") == "national"]
                loc = [h for h in headlines if h.get("category") == "local"]
                parts: list[str] = []
                for i, h in enumerate(nat[:6], 1):
                    parts.append(f"National {i}. {h.get('title', 'Headline')}")
                for i, h in enumerate(loc[:6], 1):
                    parts.append(f"Local {i}. {h.get('title', 'Headline')}")
                listing = "\n".join(parts) or "\n".join(
                    f"{i}. {h.get('title', 'Headline')}" for i, h in enumerate(headlines[:8], 1)
                )
                yield _stream_done(_ok(
                    "Which briefing story should I expand?\n\n"
                    f"{listing}\n\n"
                    "Reply with **local headline 2**, **national headline 1**, or words from the title.",
                    module="briefing",
                    type="clarification",
                ))
                return

            yield {"type": "status", "message": f"Researching: {headline.get('title', 'story')}…"}
            search_terms = headline.get("title", "")
            if headline.get("source"):
                search_terms += f" {headline['source']}"
            results = web_search.search(search_terms, limit=6)
            full: list[str] = []
            for chunk in expand_headline_detail_stream(headline, user_query=query, results=results):
                full.append(chunk)
                yield {"type": "token", "content": chunk}
            answer = "".join(full).strip()
            result = _ok(answer, module="briefing", type="news_detail", headline=headline)
            self.session.note_briefing_headlines(headlines)
            yield _stream_done(result)
            return

        if action == "web_search":
            from jarvis import web_search
            from jarvis.profiles import web_search_disabled

            if web_search_disabled():
                yield _stream_done(_err(
                    "Web search is disabled (offline profile). Switch profile in the sidebar.",
                    module="general",
                ))
                return
            query = params.get("query") or re.sub(
                r"^(search (the )?web for|web search)[:\s]+", "", message, flags=re.I,
            ).strip() or message
            yield {"type": "status", "message": "Searching the web…"}
            results = web_search.search(query)
            if not results:
                yield _stream_done(_err(
                    f"No web results for that query ({web_search.backend_name()}). "
                    "Try again or run: `./venv/bin/pip install ddgs`",
                    module="general",
                ))
                return
            yield {"type": "status", "message": f"Summarizing {len(results)} results…"}
            full: list[str] = []
            for chunk in web_search.synthesize_answer_stream(query, results):
                full.append(chunk)
                yield {"type": "token", "content": chunk}
            answer = "".join(full).strip() or web_search.format_results(results)
            result = _ok(answer, module="general", type="web_search", results=results)
            yield _stream_done(result)
            return

        if action in (
            "describe_image", "analyze_image", "ocr_image", "ocr_structured_image",
            "image_to_code", "analyze_region", "analyze_video_frame", "compare_images",
        ):
            from jarvis.vision_media import build_vision_prompt, vision_task_for_question

            path = params.get("path") or self.session.last_image
            question = params.get("question") or message
            task = "describe"
            if action == "describe_image":
                question = "Describe this image in detail."
            elif action == "ocr_image":
                from jarvis.vision_media import OCR_PROMPT
                question = OCR_PROMPT
                task = "ocr"
            elif action == "ocr_structured_image":
                from jarvis.vision_media import OCR_STRUCTURED_PROMPT
                question = OCR_STRUCTURED_PROMPT
                task = "ocr_structured"
            elif action == "image_to_code":
                from jarvis.vision_media import IMAGE_TO_CODE_PROMPT
                question = IMAGE_TO_CODE_PROMPT
                task = "image_to_code"
            elif action == "analyze_region":
                result = self._analyze_region(params, message)
                yield _stream_done(result)
                return
            elif action == "compare_images":
                result = self._compare_images(params, message)
                yield _stream_done(result)
                return
            elif action in ("analyze_image", "analyze_video_frame"):
                task = vision_task_for_question(question)
                question = build_vision_prompt(question, task)

            yield {
                "type": "status",
                "message": f"Analyzing image ({llm.vision_model_for_task(task)})…",
            }

            full = []
            for token in self.vision.analyze_stream(question, path, task=task):
                if token.startswith("ERROR:"):
                    yield _stream_done(_err(token))
                    return
                full.append(token)
                yield {"type": "token", "content": token}
            answer = "".join(full)
            result = self._vision_ok(answer, image_path=path)
            result["action"] = action
            result["thinking"] = intent.get("thinking", "")
            result["uncensored"] = is_uncensored()
            self.session.note_module("vision")
            yield _stream_done(result)
            return

        if action != "chat" or action in instant:
            result = self._process_unlocked(message, attachment, branch_id, attachment2)
            yield _stream_done(result)
            return

        from jarvis.behaviors.conversation import ensure_conversation_engine

        yield from ensure_conversation_engine(self).execute_stream(
            message,
            params,
            request_id=request_id,
        )

    def _auto_remember(self, user_msg: str, assistant_msg: str) -> None:
        from jarvis.behaviors.memory import get_memory_behavior

        behavior = get_memory_behavior()
        if behavior is not None:
            behavior.auto_remember(self, user_msg, assistant_msg)

    @staticmethod
    def _stream_text_chunks(text: str, width: int = 24) -> Iterator[str]:
        words = text.split(" ")
        buf = ""
        for word in words:
            buf += word + " "
            if len(buf) >= width:
                yield buf
                buf = ""
        if buf:
            yield buf

    @staticmethod
    def _memory_citation(entry: dict) -> dict:
        from jarvis.behaviors.conversation import ConversationEngine

        return ConversationEngine.memory_citation(entry)

    def _chat_context_prefix(self, message: str) -> tuple[str, list[str], list[dict]]:
        from jarvis.behaviors.conversation import ensure_conversation_engine

        return ensure_conversation_engine(self).build_context_prefix(message)

    def _messages_for_llm(self, messages: list[dict], context_prefix: str) -> list[dict]:
        from jarvis.behaviors.conversation import ensure_conversation_engine

        return ensure_conversation_engine(self).messages_for_llm(messages, context_prefix)

    def _prepare_chat_user_message(self, message: str, params: dict) -> str:
        from jarvis.behaviors.conversation import ensure_conversation_engine

        return ensure_conversation_engine(self).prepare_user_message(message, params)

    def _read_upload_snippet(self, path: str, limit: int = 12000) -> str:
        from jarvis.behaviors.conversation import ensure_conversation_engine

        return ensure_conversation_engine(self)._read_upload_snippet(path, limit)

    def apply_proposal(self, proposal_id: str | None = None, *, force: bool = False) -> dict:
        pid = proposal_id or self.session.last_proposal_id
        proposal = self.pending_proposals.get(pid) if pid else None
        if not proposal:
            return _err("No pending proposal to apply.")

        if proposal.get("syntax_ok") is False and not force:
            return _err(
                "Proposal has syntax errors. Fix and try again, or apply with force from the GUI.",
                module="coding",
            )

        files = proposal.get("files")
        if not files:
            files = [{"path": proposal["path"], "code": proposal["code"]}]

        if proposal.get("mode") == "upgrade_wizard":
            from jarvis.upgrade_wizard import validate_proposal_paths

            ok_paths, path_errors = validate_proposal_paths(files)
            if not ok_paths:
                return _err(
                    "Upgrade blocked — live data paths not allowed:\n"
                    + "\n".join(f"- {e}" for e in path_errors),
                    module="coding",
                )
            if not proposal.get("verified") and not force:
                return _err(
                    "Run **verify upgrade** (or use the wizard **Verify tests** button) before applying.",
                    module="coding",
                )

        proposal = self.pending_proposals.pop(pid, None)

        applied = []
        self.last_apply_backups = []
        for item in files:
            path = item["path"]
            if not path:
                continue
            resolved = fs.resolve_path(path, base=self.coding._base())
            if item.get("delete"):
                if resolved.exists():
                    backup = fs.backup_file(path, base=self.coding._base())
                    resolved.unlink()
                    self.last_apply_backups.append({
                        "path": path, "backup": backup, "was_deleted": True,
                    })
                    applied.append(f"{path} (deleted)")
                continue
            code = item["code"]
            backup = fs.backup_file(path, base=self.coding._base()) if resolved.exists() else "(new file)"
            fs.write_file(path, code, base=self.coding._base())
            self.last_apply_backups.append({"path": path, "backup": backup, "is_new": backup == "(new file)"})
            applied.append(path)

        if not applied:
            return _err("Proposal had no valid files.")

        self._persist_proposals()
        self.last_apply_backup = self.last_apply_backups[-1]["backup"]
        self.last_apply_path = self.last_apply_backups[-1]["path"]
        self.session.last_proposal_id = ""
        is_create = proposal.get("mode") == "create"
        msg = "Done — applied changes to:\n" + "\n".join(f"- **{p}**" for p in applied)
        if len(self.last_apply_backups) == 1 and self.last_apply_backups[0]["backup"] != "(new file)":
            msg += f"\n\nBackup: `{self.last_apply_backup}`"

        py_files = []
        try:
            py_files = [
                fs.resolve_path(p, base=self.coding._base())
                for p in applied
                if fs.resolve_path(p, base=self.coding._base()).suffix == ".py"
                and not Path(p).name.startswith("test_")
            ]
            verify = verify_python_files(
                py_files,
                self.coding._base(),
                run_scripts=is_create,
            )
            if verify:
                msg += f"\n\n{verify}"
        except Exception as e:
            msg += f"\n\n**Verify warning:** {e}"

        import os
        if os.getenv("JARVIS_AUTO_COMMIT", "").lower() in ("1", "true", "yes"):
            from jarvis import git_util
            commit_msg = proposal.get("explanation", "Jarvis coding apply")[:200]
            cr = git_util.commit(commit_msg, path=self.coding._base(), files=applied)
            if not cr.startswith("ERROR"):
                msg += f"\n\n**Git:** {cr}"

        from jarvis.trust_memory import record_fix_success

        if py_files and verify and "**pytest:** failed" not in verify and "Syntax check failed" not in verify:
            record_fix_success(
                self.memory,
                paths=[str(p.relative_to(self.coding._base())) if p.is_relative_to(self.coding._base()) else p.name for p in py_files],
                note=proposal.get("explanation", "")[:120],
            )

        return _ok(msg, module="coding", type="applied", show_undo=True)

    def _apply_proposal_nl(self, params: dict, message: str) -> dict:
        return self.apply_proposal(params.get("proposal_id"))

    def _dismiss_proposal(self, params: dict, message: str) -> dict:
        pid = self.session.last_proposal_id
        if pid and pid in self.pending_proposals:
            self.pending_proposals.pop(pid, None)
            self._persist_proposals()
        self.session.last_proposal_id = ""
        return _ok("Okay, I won't apply those changes.", module="coding")

    def _undo_apply(self, params: dict, message: str) -> dict:
        return perform_undo_apply(self)

    def _store_refactor_proposal(
        self,
        files: list[dict],
        *,
        explanation: str,
        mode: str = "refactor",
    ) -> dict:
        if not files:
            return _err("No changes to propose.")
        proposal_id, payload = self._store_agent_proposal(
            files, mode=mode, explanation=explanation,
        )
        combined_diff = ""
        for f in files:
            if f.get("delete"):
                combined_diff += f"--- delete {f['path']}\n"
                continue
            orig = fs.read_file(f["path"], base=self.coding._base())
            if orig.startswith("ERROR:"):
                orig = ""
            combined_diff += make_diff(orig, f.get("code", "")) + "\n"
        files_note = "\n".join(
            f"- `{f['path']}`" + (" (delete)" if f.get("delete") else "")
            for f in files
        )
        syntax_note = ""
        if payload.get("_diag_summary"):
            syntax_note = f"\n\n**Syntax check:**\n{payload['_diag_summary']}"
        intro = (
            f"**Refactor proposal** ({len(files)} change(s)):\n{files_note}\n\n"
            f"{explanation}{syntax_note}\n\n"
            "Review the diff and hit **Apply changes** or say `apply it`."
        )
        extra = self._proposal_response_extra([f for f in files if not f.get("delete")])
        if extra.get("test_impact"):
            intro += f"\n\n{extra['test_impact']}"
        return _ok(
            intro,
            module="coding",
            type="proposal",
            proposal_id=proposal_id,
            diff=combined_diff.strip(),
            explanation=explanation,
            diagnostics=payload.get("diagnostics", []),
            syntax_ok=payload.get("syntax_ok", True),
            **extra,
        )

    def _capabilities(self, params: dict, message: str) -> dict:
        return _ok(capabilities_message(), module=None, type="info")

    def _models_info(self, params: dict, message: str) -> dict:
        msg = models_guide()
        status = self.get_status()
        if status.get("models_missing"):
            msg += "\n\n**Missing on your system:** " + ", ".join(f"`{m}`" for m in status["models_missing"])
            msg += "\n\nRun `./scripts/pull-models.sh` to install recommended models."
        return _ok(msg, module=None, type="info")

    def _greeting(self, params: dict, message: str) -> dict:
        lower = (message or "").lower().strip()
        if re.search(r"good (morning|afternoon|evening)\b", lower):
            return self._morning_briefing(params, message)
        return _ok(greeting_message(), module=None, type="info")

    def _morning_briefing(self, params: dict, message: str) -> dict:
        from jarvis.briefing_news import persist_briefing_headlines
        from jarvis.morning_briefing import build_briefing, mark_briefing_shown

        briefing = build_briefing(journal=self.journal, memory_store=self.memory)
        mark_briefing_shown(briefing["day"])
        headlines = briefing.get("briefing_headlines") or persist_briefing_headlines(briefing.get("news") or {})
        if headlines:
            self.session.note_briefing_headlines(headlines)
        return _ok(
            briefing["markdown"],
            module="briefing",
            type="briefing",
            open_task_count=briefing["open_task_count"],
            weather_line=briefing["weather_line"],
        )

    def _briefing_news_detail(self, params: dict, message: str) -> dict:
        from jarvis.briefing_news import (
            expand_headline_detail,
            load_recent_headlines,
            match_headline,
        )
        from jarvis.profiles import web_search_disabled

        headlines = self.session.last_briefing_headlines or load_recent_headlines()
        if not headlines:
            return _err(
                "No briefing headlines saved yet. Say **morning briefing** first.",
                module="briefing",
            )

        query = (params.get("query") or message or "").strip()
        title_hint = (params.get("title") or "").strip()
        headline = match_headline(title_hint or query, headlines)
        if not headline and title_hint:
            headline = match_headline(title_hint, headlines)
        if not headline:
            nat = [h for h in headlines if h.get("category") == "national"]
            loc = [h for h in headlines if h.get("category") == "local"]
            parts: list[str] = []
            for i, h in enumerate(nat[:6], 1):
                parts.append(f"National {i}. {h.get('title', 'Headline')}")
            for i, h in enumerate(loc[:6], 1):
                parts.append(f"Local {i}. {h.get('title', 'Headline')}")
            listing = "\n".join(parts) or "\n".join(
                f"{i}. {h.get('title', 'Headline')}" for i, h in enumerate(headlines[:8], 1)
            )
            return _ok(
                "Which briefing story should I expand?\n\n"
                f"{listing}\n\n"
                "Reply with **local headline 2**, **national headline 1**, or words from the title.",
                module="briefing",
                type="clarification",
            )

        if web_search_disabled():
            return _err(
                "Web search is disabled (offline profile). Switch profile to expand briefing stories.",
                module="briefing",
            )

        answer = expand_headline_detail(headline, user_query=query)
        self.session.note_briefing_headlines(headlines)
        return _ok(
            answer,
            module="briefing",
            type="news_detail",
            headline=headline,
        )

    def _resolve_document_path(self, params: dict) -> str:
        from jarvis.document_pipeline import documents_dir

        raw = (params.get("path") or "").strip()
        if not raw:
            return self.session.resolve_document("")
        p = Path(raw)
        if p.is_absolute() and p.exists():
            return str(p)
        for base in (PROJECT_ROOT, DATA_DIR, UPLOAD_DIR, documents_dir()):
            candidate = (base / raw).resolve()
            if candidate.exists():
                return str(candidate)
        resolved = p.expanduser()
        return str(resolved) if resolved.exists() else raw

    def _load_document(self, params: dict, message: str) -> tuple[dict | None, Any]:
        from jarvis.document_pipeline import parse_document

        path = self._resolve_document_path(params)
        if not path:
            return _err(
                "No document loaded. Attach a PDF or Word file, or put warranty docs in `data/documents/`.",
                module="document",
            ), None
        try:
            return None, parse_document(path)
        except Exception as e:
            return _err(str(e), module="document"), None

    def _document_info(self, params: dict, message: str) -> dict:
        from jarvis.document_pipeline import format_document_info

        err, doc = self._load_document(params, message)
        if err:
            return err
        self.session.note_module("document")
        return _ok(format_document_info(doc), module="document", document=doc.to_dict())

    def _document_summarize(self, params: dict, message: str) -> dict:
        from jarvis.document_pipeline import summarize_document

        err, doc = self._load_document(params, message)
        if err:
            return err
        self.session.note_module("document")
        try:
            summary = summarize_document(doc)
        except Exception as e:
            return _err(str(e), module="document")
        header = f"**{doc.title}** · {doc.page_count} page(s)\n\n"
        return _ok(header + summary, module="document", document=doc.to_dict())

    def _document_query(self, params: dict, message: str) -> dict:
        from jarvis.document_pipeline import answer_document

        err, doc = self._load_document(params, message)
        if err:
            return err
        question = (params.get("question") or message or "").strip()
        if not question:
            return _err("Ask a question about the loaded document.", module="document")
        self.session.note_module("document")
        try:
            answer = answer_document(doc, question)
        except Exception as e:
            return _err(str(e), module="document")
        return _ok(answer, module="document", document=doc.to_dict())

    def _document_search(self, params: dict, message: str) -> dict:
        from jarvis.documents_rag import format_hits_markdown, search

        query = (params.get("query") or message or "").strip()
        for prefix in (
            r"^search (?:my )?(?:documents?|document library|files in library)[:\s]*",
            r"^find in (?:my )?(?:documents?|document library)[:\s]*",
        ):
            query = re.sub(prefix, "", query, flags=re.I).strip()
        if not query:
            return _err("Say what to search for, e.g. **search documents warranty coverage**.", module="document")
        hits = search(query, limit=5)
        self.session.note_module("document")
        return _ok(format_hits_markdown(query, hits), module="document", type="document_search", hits=hits)

    def _upgrade_wizard(self, params: dict, message: str) -> dict:
        from jarvis.upgrade_wizard import (
            GUARDRAIL_PROMPT,
            parse_upgrade_task,
            save_session,
            validate_proposal_paths,
        )

        task = (params.get("task") or parse_upgrade_task(message) or message or "").strip()
        if not task:
            return _err(
                "Describe what to upgrade — e.g. `upgrade jarvis: add a /api/health route`.",
                module="coding",
            )

        agent = CodingAgent(self.coding._base(), max_steps=int(params.get("max_steps") or 4))
        full_task = f"{GUARDRAIL_PROMPT}\n\nUpgrade task: {task}"
        result = agent.run(full_task, path="jarvis/router.py", mode="refactor")
        if not result.ok or not result.files:
            return _err(result.message or "Could not produce an upgrade proposal.", module="coding")

        ok_paths, path_errors = validate_proposal_paths(result.files)
        if not ok_paths:
            return _err(
                "Proposal blocked by upgrade guardrails:\n" + "\n".join(f"- {e}" for e in path_errors),
                module="coding",
            )

        proposal_id, payload = self._store_agent_proposal(
            result.files,
            mode="upgrade_wizard",
            explanation=result.explanation or task,
        )
        payload["upgrade_task"] = task
        payload["verified"] = False
        self.pending_proposals[proposal_id] = payload
        self._persist_proposals()

        save_session({
            "step": "proposed",
            "task": task,
            "proposal_id": proposal_id,
            "verified": False,
            "snapshot_id": "",
        })

        combined_diff = ""
        for f in result.files:
            if f.get("delete"):
                combined_diff += f"--- delete {f['path']}\n"
                continue
            orig = fs.read_file(f["path"], base=self.coding._base())
            if orig.startswith("ERROR:"):
                orig = ""
            combined_diff += make_diff(orig, f.get("code", "")) + "\n"

        files_note = "\n".join(f"- `{f['path']}`" for f in result.files)
        intro = (
            f"**Upgrade proposal** ({len(result.files)} file(s)) — `jarvis/` + `tests/` only:\n"
            f"{files_note}\n\n"
            f"{result.explanation or task}\n\n"
            "Your journal and live memory are **not** in this diff. "
            "Next: **Verify tests**, then **Apply upgrade** (snapshot taken automatically)."
        )
        extra = self._proposal_response_extra(result.files)
        if extra.get("test_impact"):
            intro += f"\n\n{extra['test_impact']}"
        if payload.get("_diag_summary"):
            intro += f"\n\n**Syntax check:**\n{payload['_diag_summary']}"

        return _ok(
            intro,
            module="coding",
            type="upgrade_proposal",
            proposal_id=proposal_id,
            diff=combined_diff.strip(),
            explanation=result.explanation or task,
            diagnostics=payload.get("diagnostics", []),
            syntax_ok=payload.get("syntax_ok", True),
            upgrade_wizard=True,
            verified=False,
            agent_steps=[s.__dict__ for s in result.steps],
            **extra,
        )

    def _upgrade_proposal(self, proposal_id: str | None = None) -> dict | None:
        pid = (proposal_id or self.session.last_proposal_id or "").strip()
        if not pid:
            from jarvis.upgrade_wizard import get_session

            session = get_session() or {}
            pid = session.get("proposal_id") or ""
        if not pid or pid not in self.pending_proposals:
            return None
        return self.pending_proposals[pid]

    def _upgrade_verify(self, params: dict, message: str) -> dict:
        from jarvis.upgrade_wizard import get_session, save_session, verify_proposal

        proposal = self._upgrade_proposal(params.get("proposal_id"))
        if not proposal:
            return _err("No upgrade proposal to verify. Say `upgrade jarvis: …` first.", module="coding")

        pid = params.get("proposal_id") or self.session.last_proposal_id
        session = get_session() or {}
        if not pid:
            pid = session.get("proposal_id") or ""

        ok, detail = verify_proposal(proposal, base=self.coding._base())
        proposal["verified"] = ok
        if pid:
            self.pending_proposals[pid] = proposal
            self._persist_proposals()

        session["verified"] = ok
        session["verify_log"] = detail[:4000]
        session["step"] = "verified" if ok else "verify_failed"
        save_session(session)

        if ok:
            return _ok(
                f"**Upgrade verification passed.** Safe to apply — live journal untouched.\n\n{detail}",
                module="coding",
                type="upgrade_verified",
                proposal_id=pid,
                upgrade_wizard=True,
                verified=True,
            )
        return _err(
            f"**Upgrade verification failed.** Fix the proposal or dismiss and try again.\n\n{detail}",
            module="coding",
            type="upgrade_verify_failed",
            proposal_id=pid,
            upgrade_wizard=True,
            verified=False,
        )

    def _upgrade_apply(self, params: dict, message: str) -> dict:
        from jarvis.upgrade_wizard import create_snapshot, get_session, save_session

        proposal = self._upgrade_proposal(params.get("proposal_id"))
        if not proposal:
            return _err("No upgrade proposal to apply.", module="coding")

        pid = params.get("proposal_id") or self.session.last_proposal_id
        session = get_session() or {}
        if not pid:
            pid = session.get("proposal_id") or ""

        force = str(params.get("force", "")).lower() in ("1", "true", "yes")
        if not proposal.get("verified") and not force:
            verify_result = self._upgrade_verify({"proposal_id": pid}, message)
            if not verify_result.get("ok"):
                return verify_result

        files = proposal.get("files") or []
        snap = create_snapshot(files, task=session.get("task", ""), proposal_id=pid or "")
        session["snapshot_id"] = snap.get("id", "")
        session["step"] = "applying"
        save_session(session)

        result = self.apply_proposal(pid, force=force)
        if not result.get("ok"):
            session["step"] = "apply_failed"
            save_session(session)
            return result

        session["step"] = "applied"
        session["applied"] = True
        save_session(session)
        msg = result.get("message") or "Applied."
        msg += f"\n\n**Snapshot:** `{snap.get('id')}` — say **rollback upgrade** to undo."
        from jarvis.upgrade_wizard import requires_jarvis_restart

        if requires_jarvis_restart(files):
            from jarvis.branding import assistant_name

            msg += f"\n\n**Restart {assistant_name()}** (tray Quit → launch) to load GUI/server changes."
            result["requires_restart"] = True
        result["message"] = msg
        result["type"] = "upgrade_applied"
        result["upgrade_wizard"] = True
        result["snapshot_id"] = snap.get("id", "")
        return result

    def _upgrade_rollback(self, params: dict, message: str) -> dict:
        from jarvis.upgrade_wizard import get_session, rollback_snapshot, save_session

        session = get_session() or {}
        snapshot_id = params.get("snapshot_id") or session.get("snapshot_id") or ""
        ok, msg, restored = rollback_snapshot(snapshot_id)
        if not ok:
            return _err(msg, module="coding")
        session["step"] = "rolled_back"
        save_session(session)
        return _ok(
            msg + "\n\nLive journal and memory were not touched.",
            module="coding",
            type="upgrade_rollback",
            upgrade_wizard=True,
            restored=restored,
        )

    def _learn_about(self, params: dict, message: str) -> dict:
        from jarvis.knowledge import learn_topic, parse_learn_topic
        from jarvis.profiles import web_search_disabled

        if web_search_disabled():
            return _err(
                "Web search is disabled (offline profile). Switch profile to learn new topics.",
                module="general",
            )

        topic = (params.get("topic") or parse_learn_topic(message) or "").strip()
        result = learn_topic(topic)
        if not result.get("ok"):
            return _err(result.get("message", "Could not learn that topic."), module="general")

        self.session.note_knowledge(result["slug"])
        self.session.note_module("general")

        header = (
            f"**Learned about:** {result['topic']}\n"
            f"Saved to `{result['relative_path']}` "
            f"({result['result_count']} web source(s)).\n\n"
            "I'll use this brief in future chats when the topic comes up. "
            "Say **remember key points** to store bullets in memory.\n\n---\n\n"
        )
        return _ok(
            header + result["body"],
            module="general",
            type="knowledge_learned",
            topic=result["topic"],
            slug=result["slug"],
            knowledge_path=result["relative_path"],
            key_points=result.get("key_points") or [],
            show_remember_key_points=True,
        )

    def _learn_remember(self, params: dict, message: str) -> dict:
        from jarvis.knowledge import load_brief, remember_key_points

        slug = (params.get("slug") or self.session.last_knowledge_slug or "").strip()
        if not slug:
            return _err("Nothing to remember yet — run `learn about: …` first.", module="memory")

        brief = load_brief(slug)
        if not brief:
            return _err(f"No saved brief for `{slug}`.", module="memory")

        stored = remember_key_points(self.memory, brief["topic"], slug=slug)
        if not stored:
            return _err("No key points found in that brief.", module="memory")

        self.refresh_system_prompt()
        lines = "\n".join(f"- {p}" for p in stored)
        return _ok(
            f"Stored **{len(stored)}** key point(s) about **{brief['topic']}** in memory:\n\n{lines}",
            module="memory",
            type="remembered",
            remembered_count=len(stored),
        )

    def _ha_not_configured(self) -> dict:
        return _err(
            "**Home Assistant isn’t connected yet.**\n\n"
            "1. In HA (`http://127.0.0.1:8123`): **Profile → Security → Long-lived access tokens → Create token**\n"
            "2. In ARIA sidebar → **Smart home** → paste token → **Test connection** → **Save**\n"
            "3. Or run: `./scripts/set-ha-token.sh`\n\n"
            "Then ask **house status** again.",
            module="automation",
            type="ha_setup",
        )

    def _ha_status(self, params: dict, message: str) -> dict:
        from jarvis.home_assistant import ha_enabled, home_summary, status_payload

        if not ha_enabled():
            return self._ha_not_configured()
        payload = status_payload()
        conn = payload.get("connection") or {}
        if not conn.get("ok"):
            return _err(conn.get("message", "Home Assistant unreachable."), module="automation")
        ok, summary = home_summary()
        if not ok:
            return _err(summary, module="automation")
        header = f"**Home Assistant** connected"
        if conn.get("version"):
            header += f" (v{conn['version']})"
        header += ".\n\n"
        self.session.note_module("automation")
        return _ok(
            header + summary,
            module="automation",
            type="ha_status",
            homeassistant=payload,
        )

    def _ha_control(self, params: dict, message: str) -> dict:
        from jarvis.home_assistant import control_entity, ha_enabled, parse_control

        if not ha_enabled():
            return self._ha_not_configured()
        spec = parse_control(message) or params
        target = (spec.get("target") or "").strip()
        action = (spec.get("action") or "on").strip().lower()
        ok, msg = control_entity(target, action)
        self.session.note_module("automation")
        if not ok:
            return _err(msg, module="automation")
        return _ok(msg, module="automation", type="ha_control")

    def _ha_scene(self, params: dict, message: str) -> dict:
        from jarvis.home_assistant import activate_scene, ha_enabled, parse_scene

        if not ha_enabled():
            return self._ha_not_configured()
        scene = (params.get("scene") or parse_scene(message) or "").strip()
        ok, msg = activate_scene(scene)
        self.session.note_module("automation")
        if not ok:
            return _err(msg, module="automation")
        return _ok(msg, module="automation", type="ha_scene")

    def _ha_query(self, params: dict, message: str) -> dict:
        from jarvis.home_assistant import ha_enabled, query_entity

        if not ha_enabled():
            return self._ha_not_configured()
        query = (params.get("query") or message or "").strip()
        ok, msg = query_entity(query)
        self.session.note_module("automation")
        if not ok:
            return _err(msg, module="automation")
        return _ok(msg, module="automation", type="ha_query")

    def _ha_set_token(self, params: dict, message: str) -> dict:
        from jarvis.home_assistant import parse_ha_token_message, save_config, status_payload

        token = (params.get("token") or parse_ha_token_message(message) or "").strip()
        if not token:
            return _err(
                "Paste your Home Assistant token here, or say "
                "`set home assistant token: …` · Sidebar → **Smart home** also has a paste box.",
                module="automation",
            )
        result = save_config(token=token, ensure_automation_secret=True)
        conn = result.get("connection") or {}
        if not conn.get("ok"):
            return _err(
                conn.get("message", "Token saved but connection failed — check URL in Smart home panel."),
                module="automation",
            )
        self.session.note_module("automation")
        ver = f" (v{conn['version']})" if conn.get("version") else ""
        return _ok(
            f"Home Assistant connected{ver}. "
            "Try **house status** or **turn off the living room lights**.",
            module="automation",
            type="ha_connected",
            homeassistant=status_payload(),
        )

    def _pdf_to_image_attachment(self, attachment: dict, page: int = 1) -> dict:
        path = attachment.get("path", "")
        name = attachment.get("name") or Path(path).name
        content = Path(path).read_bytes()
        frame_bytes, frame_name = extract_pdf_page(content, name, page)
        dest = UPLOAD_DIR / frame_name
        if dest.exists():
            stem = Path(frame_name).stem
            ext = Path(frame_name).suffix
            for n in range(2, 1000):
                candidate = UPLOAD_DIR / f"{stem}_{n}{ext}"
                if not candidate.exists():
                    dest = candidate
                    frame_name = candidate.name
                    break
        dest.write_bytes(frame_bytes)
        return {"path": str(dest), "kind": "image", "name": frame_name}

    def _ask_instruction_sentence(self, topic: str, n_words: int) -> str:
        from jarvis.behaviors.conversation import ensure_conversation_engine

        return ensure_conversation_engine(self).ask_instruction_sentence(topic, n_words)

    def _try_strict_instructions(self, message: str) -> str | None:
        from jarvis.behaviors.conversation import ensure_conversation_engine

        return ensure_conversation_engine(self).try_strict_instructions(message)

    def _chat(self, params: dict, message: str) -> dict:
        from jarvis.behaviors.conversation import ensure_conversation_engine

        return ensure_conversation_engine(self).execute(params, message)

    def _apply_editor_params(self, params: dict, message: str, action: str) -> None:
        from jarvis.editor_context import get_context
        ctx = get_context()
        if not ctx:
            return
        if not params.get("path") and ctx.relative_file:
            params["path"] = ctx.relative_file
        lower = message.lower()
        if ctx.has_selection() and (
            params.get("use_selection")
            or re.search(r"\b(selection|selected|this code)\b", lower)
        ):
            params["use_selection"] = True
            params["_editor_prompt"] = ctx.format_for_prompt()
        elif action.startswith("coding_") and ctx.relative_file:
            params.setdefault("_editor_prompt", ctx.format_for_prompt(max_selection=800))

    def _resolve_coding_path(self, path: str) -> str:
        return self.session.resolve_path(path or None) or ""

    def _editor_task_suffix(self, params: dict) -> str:
        return params.get("_editor_prompt", "") or ""

    def _coding_read(self, params: dict, message: str) -> dict:
        path = self._resolve_coding_path(params.get("path", ""))
        if not path:
            return _err("Which file should I read?")
        content = fs.read_file(path, base=self.coding._base())
        if content.startswith("ERROR:"):
            return _err(content)
        self.session.note_file(path)
        self.coding.conversation.add_system(f"Loaded file: {path}\n\n{content}")
        preview = content[:3000] + ("…" if len(content) > 3000 else "")
        return _ok(f"Here's **{path}** ({len(content)} chars):\n\n```\n{preview}\n```", module="coding")

    def _persist_proposals(self) -> None:
        proposal_store.sync(self.pending_proposals)

    def _diagnosis_for_path(self, path: str) -> str:
        for diag in self.pending_diagnoses.values():
            if diag.get("path") == path:
                return diag.get("explanation", "")
        return ""

    def _check_proposal_syntax(self, files: list[dict]) -> tuple[list[dict], str]:
        """Run syntax/lint on proposed files; return (diagnostics dicts, summary text)."""
        checkable = [f for f in files if not f.get("delete") and f.get("code")]
        diags = check_files(checkable, self.coding._base(), deep=True, skip_typecheck=True)
        summary = format_diagnostics(diags)
        return diagnostics_to_dicts(diags), summary

    def _store_agent_proposal(
        self,
        files: list[dict],
        *,
        mode: str = "agent",
        explanation: str = "",
        task_id: str = "",
    ) -> tuple[str, dict]:
        proposal_id = str(uuid.uuid4())[:8]
        diag_dicts, diag_summary = self._check_proposal_syntax(files)
        payload: dict = {
            "mode": mode,
            "files": files,
            "explanation": explanation,
            "diagnostics": diag_dicts,
            "syntax_ok": not any(d.get("severity") == "error" for d in diag_dicts),
        }
        if len(files) == 1:
            payload["path"] = files[0]["path"]
            payload["code"] = files[0]["code"]
        self.pending_proposals[proposal_id] = payload
        self._persist_proposals()
        self.session.note_proposal(proposal_id)
        for f in files:
            self.session.note_file(f["path"])
        if task_id:
            self.task_manager.set_proposal(task_id, proposal_id)
        payload["_diag_summary"] = diag_summary
        return proposal_id, payload

    def _proposal_response_extra(self, files: list[dict]) -> dict:
        py_files = [
            fs.resolve_path(f["path"], base=self.coding._base())
            for f in files
            if f.get("path", "").endswith(".py")
        ]
        impact = format_test_impact(py_files, self.coding._base())
        return {"test_impact": impact} if impact else {}

    def proposal_diff(self, proposal_id: str) -> dict:
        pid = (proposal_id or "").strip()
        prop = self.pending_proposals.get(pid)
        if not prop:
            return _err("Proposal not found or already applied.", module="coding")
        combined = ""
        files = prop.get("files") or []
        if not files and prop.get("path"):
            files = [{"path": prop["path"], "code": prop.get("code", "")}]
        for f in files:
            path = f.get("path") or ""
            code = f.get("code", "")
            if not path:
                continue
            orig = fs.read_file(path, base=self.coding._base())
            if orig.startswith("ERROR:"):
                orig = ""
            combined += make_diff(orig, code) + "\n"
        if not combined.strip():
            return _err("No diff available for that proposal.", module="coding")
        return _ok(
            "",
            module="coding",
            proposal_id=pid,
            diff=combined.strip(),
            diff_total_lines=len(combined.splitlines()),
        )

    def _coding_agent_stream(self, params: dict, message: str, *, mode: str = "agent"):
        """Shared streaming agent path with TaskManager + max_steps."""
        try:
            yield from self._coding_agent_stream_inner(params, message, mode=mode)
        except Exception as e:
            logger.exception("coding agent stream failed")
            yield _stream_done(_err(f"Coding agent failed: {e}", module="coding"))

    def _coding_agent_stream_inner(self, params: dict, message: str, *, mode: str = "agent"):
        task_text = params.get("task") or message
        path = params.get("path") or self.session.resolve_path(None) or None
        max_steps = int(params.get("max_steps") or 5)
        task_id = params.get("task_id") or ""
        ct = None

        if not task_id:
            ct = self.task_manager.create(task_text[:120], path=path or "", mode=mode)
            task_id = ct.id
        else:
            ct = self.task_manager.get(task_id)
            if ct:
                self.task_manager.resume(task_id)
                path = path or ct.path or None
                task_text = ct.checkpoint.get("task") or task_text
                mode = ct.checkpoint.get("mode") or mode

        initial_errors = ""
        if ct:
            initial_errors = ct.checkpoint.get("last_errors") or ""

        self._active_task_id = task_id
        agent = CodingAgent(self.coding._base(), max_steps=max_steps)

        yield {"type": "status", "message": "Planning coding task…"}
        yield {"type": "status", "message": "Gathering project context…"}

        result = agent.run(
            task_text,
            path=path,
            mode=mode,
            diagnose_first=bool(params.get("diagnose_first")),
            initial_errors=initial_errors,
        )

        for step in result.steps:
            self.task_manager.add_step(task_id, step.action, step.detail, ok=step.ok)
            yield {
                "type": "agent_step",
                "step": step.step,
                "action": step.action,
                "detail": step.detail,
                "ok": step.ok,
            }

        if not result.ok:
            from jarvis.trust_memory import record_failure

            self.task_manager.save_state(task_id, last_errors=result.message)
            self.task_manager.complete(task_id, ok=False)
            record_failure(
                self.memory,
                path=path or "",
                error=result.message[:600],
                task=task_text[:160],
            )
            yield {"type": "done", "ok": False, "message": result.message, "module": "coding", "task_id": task_id}
            return

        if result.diagnose_only:
            self.task_manager.complete(task_id, ok=True)
            yield {
                "type": "done", "ok": True, "message": result.message,
                "module": "coding", "result_type": "diagnose", "task_id": task_id,
            }
            return

        proposal_id, payload = self._store_agent_proposal(
            result.files, mode=result.mode, explanation=result.explanation, task_id=task_id,
        )
        self.task_manager.save_state(
            task_id,
            task_text=task_text,
            path=path or "",
            mode=mode,
            files=[f["path"] for f in result.files],
            proposal_id=proposal_id,
        )
        self.task_manager.complete(task_id, ok=True)

        extra = self._proposal_response_extra(result.files)
        msg = result.message
        if payload.get("_diag_summary"):
            msg += f"\n\n**Syntax check:**\n{payload['_diag_summary']}"
        if extra.get("test_impact"):
            msg += f"\n\n{extra['test_impact']}"

        yield {"type": "status", "message": f"Proposal ready — {len(result.files)} file(s)"}
        yield _stream_done({
            "ok": True,
            "message": msg,
            "module": "coding",
            "result_type": "proposal",
            "proposal_id": proposal_id,
            "path": result.files[0]["path"] if result.files else "",
            "diff": result.diff,
            "explanation": result.explanation,
            "diagnostics": payload.get("diagnostics", []),
            "syntax_ok": payload.get("syntax_ok", True),
            "agent_steps": [
                {"step": s.step, "action": s.action, "detail": s.detail, "ok": s.ok}
                for s in result.steps
            ],
            "task_id": task_id,
            **extra,
        })

    def _code_unchanged(self, original: str, candidate: str) -> bool:
        return original.strip() == (candidate or "").strip()

    def _llm_edit_file(
        self,
        task: str,
        *,
        path: str,
        content: str,
        context: str = "",
        errors: str | None = None,
        require_test_pass: bool = False,
    ) -> tuple[str, str]:
        """Generate edited file content; retry until syntax/tests pass or attempts exhausted."""
        from jarvis.coding_verify import verify_candidate_pytest
        from jarvis.patch_util import apply_hunks_to_content

        base = self.coding._base()
        last_errors = errors or ""
        explanation = ""
        small_file = len(content.splitlines()) <= 150
        test_driven = require_test_pass or bool(last_errors and "pytest" in last_errors.lower())
        max_attempts = 3 if test_driven else 2

        for attempt in range(max_attempts):
            candidate = ""
            # Full-file rewrite first for small/test-driven fixes (patches often fail silently)
            if small_file and (test_driven or attempt == 0):
                explanation, candidate = llm.generate_python_fix(
                    task, existing=content, errors=last_errors or None, context=context,
                )
            if not candidate:
                explanation, file_items = llm.generate_patched_edit(
                    task, path=path, content=content, context=context, errors=last_errors or None,
                )
                candidate = file_items[0]["code"] if file_items and file_items[0].get("code") else ""
                if file_items and file_items[0].get("hunks"):
                    patched, hunk_errs = apply_hunks_to_content(content, file_items[0]["hunks"])
                    if hunk_errs:
                        last_errors = (last_errors + "\n" + "\n".join(hunk_errs)).strip()
                    if patched.strip() != content.strip():
                        candidate = patched
                    elif not candidate:
                        candidate = ""
                if not candidate:
                    explanation, candidate = llm.generate_python_fix(
                        task, existing=content, errors=last_errors or None, context=context,
                    )

            if not candidate or self._code_unchanged(content, candidate):
                last_errors = (
                    last_errors
                    + "\n\nYour last edit did not change the file. You MUST modify the code to fix the tests."
                ).strip()
                continue

            diags, summary = self._check_proposal_syntax([{"path": path, "code": candidate}])
            if any(d.get("severity") == "error" for d in diags):
                last_errors = (last_errors + "\n" + summary).strip() if summary else last_errors
                continue

            if test_driven:
                ok, pytest_out = verify_candidate_pytest(path, candidate, base)
                if ok:
                    return explanation, candidate
                last_errors = (
                    f"pytest still failing after your edit:\n{pytest_out}\n\n"
                    "Fix ALL failing tests. Return the complete corrected file."
                )
                continue

            return explanation, candidate

        return explanation or "Could not generate a valid fix.", content

    def _coding_propose(
        self,
        path: str,
        mode: str,
        *,
        task: str | None = None,
        editor_prompt: str = "",
    ) -> dict:
        content = fs.read_file(path, base=self.coding._base())
        if content.startswith("ERROR:"):
            return _err(content)

        ctx = gather_context(path, self.coding._base(), task=task or mode)
        context_text = format_context(ctx)
        from jarvis.code_context import _find_test_files, _is_sandbox_script
        if _is_sandbox_script(path):
            slim = [f"FILE: {path}\n{content}"]
            for rel_test in _find_test_files(path, self.coding._base()):
                t = fs.read_file(rel_test, base=self.coding._base())
                if not t.startswith("ERROR:"):
                    slim.append(f"--- {rel_test} (test) ---\n{t[:4000]}")
            context_text = "\n".join(slim)

        if editor_prompt:
            context_text = f"{context_text}\n\n--- Editor (Cursor) ---\n{editor_prompt}"

        stderr = ""
        resolved = fs.resolve_path(path, base=self.coding._base())
        if mode == "fix":
            try:
                compile_check = subprocess.run(
                    ["python3", "-m", "py_compile", str(resolved)],
                    capture_output=True, text=True, timeout=15,
                )
                if compile_check.returncode == 0:
                    result = run_sandboxed(
                        ["python3", str(resolved)],
                        cwd=str(self.coding._base()),
                        timeout=30,
                    )
                    stderr = result.stderr or (result.stdout if result.returncode != 0 else "")
                else:
                    stderr = compile_check.stderr or compile_check.stdout
            except Exception as e:
                return _err(str(e))
            if not stderr:
                from jarvis.coding_verify import collect_test_failures
                stderr = collect_test_failures(resolved, self.coding._base())
            if not stderr:
                from jarvis import lsp
                diag = lsp.check_python(resolved)
                if diag:
                    stderr = "\n".join(diag)
            if not stderr and not task:
                return _ok("Syntax, run, and tests look clean — no errors to fix.", module="coding")
            fix_task = task or "Fix all errors with minimal changes."
            if editor_prompt and "Selected text" in editor_prompt:
                fix_task += "\n\nFocus on the selected code in the Editor (Cursor) context."
            llm_errors = stderr or task or ""
            explanation, new_code = self._llm_edit_file(
                fix_task,
                path=path,
                content=content,
                context=context_text,
                errors=llm_errors,
                require_test_pass=bool(llm_errors and "pytest" in llm_errors.lower()),
            )
        else:
            improve_task = task or "Improve readability, structure, and robustness with minimal changes."
            explanation, new_code = self._llm_edit_file(
                improve_task, path=path, content=content, context=context_text,
            )

        diff = make_diff(content, new_code)
        files = [{"path": path, "code": new_code}]
        diag_dicts, diag_summary = self._check_proposal_syntax(files)
        proposal_id = str(uuid.uuid4())[:8]
        syntax_ok = not any(d.get("severity") == "error" for d in diag_dicts)
        self.pending_proposals[proposal_id] = {
            "path": path, "code": new_code, "mode": mode,
            "files": files, "diagnostics": diag_dicts,
            "syntax_ok": syntax_ok, "explanation": explanation,
        }
        self._persist_proposals()
        self.session.note_proposal(proposal_id)
        self.session.note_file(path)

        extra = self._proposal_response_extra(files)
        verb = "fixes" if mode == "fix" else "improvements"
        syntax_note = f"\n\n**Syntax check:**\n{diag_summary}" if diag_summary else ""
        intro = (
            f"I found {verb} for **{path}** (used {len(ctx.get('related', []))} related files for context).\n\n"
            f"{explanation}{syntax_note}\n\n"
            "Want me to apply these changes? Hit **Apply** or just say \"apply it\"."
        )
        if extra.get("test_impact"):
            intro += f"\n\n{extra['test_impact']}"
        return _ok(
            intro,
            module="coding",
            type="proposal",
            proposal_id=proposal_id,
            path=path,
            diff=diff,
            explanation=explanation,
            diagnostics=diag_dicts,
            syntax_ok=syntax_ok,
            **extra,
        )

    def _coding_propose_stream(
        self,
        path: str,
        mode: str,
        *,
        task: str | None = None,
        message: str = "",
        editor_prompt: str = "",
    ) -> Iterator[dict]:
        try:
            if not path:
                yield _stream_done(_err(
                    "Which file? Say e.g. `fix data/scripts/your_file.py`",
                ))
                return
            yield {"type": "status", "message": f"Loading **{path}**…"}
            yield {"type": "agent_step", "step": 1, "action": "read", "detail": path, "ok": True}
            content = fs.read_file(path, base=self.coding._base())
            if content.startswith("ERROR:"):
                yield _stream_done(_err(content))
                return
            yield {"type": "status", "message": "Running diagnostics…"}
            if mode == "fix":
                yield {"type": "agent_step", "step": 2, "action": "diagnose", "detail": "errors/tests", "ok": True}
            yield {"type": "status", "message": "Generating changes…"}
            yield {"type": "agent_step", "step": 3, "action": "edit", "detail": path, "ok": True}
            result = self._coding_propose(path, mode, task=task, editor_prompt=editor_prompt)
            if result.get("ok"):
                yield {"type": "agent_step", "step": 4, "action": "propose", "detail": path, "ok": True}
            yield _stream_done(result)
        except Exception as e:
            logger.exception("coding propose stream failed for %s", path)
            yield _stream_done(_err(f"Coding failed: {e}", module="coding"))

    def _coding_create_stream(self, params: dict, message: str) -> Iterator[dict]:
        try:
            yield {"type": "status", "message": "Planning new script + tests…"}
            yield {"type": "agent_step", "step": 1, "action": "plan", "detail": "create", "ok": True}
            yield {"type": "status", "message": "Generating code…"}
            yield {"type": "agent_step", "step": 2, "action": "generate", "detail": "script + pytest", "ok": True}
            result = self._coding_create(params, message)
            if result.get("ok"):
                yield {"type": "agent_step", "step": 3, "action": "propose", "detail": "ready", "ok": True}
            yield _stream_done(result)
        except Exception as e:
            logger.exception("coding create stream failed")
            yield _stream_done(_err(f"Could not create script: {e}", module="coding"))

    def _coding_create(self, params: dict, message: str) -> dict:
        description = (params.get("description") or message).strip()
        path = (params.get("path") or "").strip()
        if not path:
            path = py_path_from_message(message)
            if not path and re.search(r"hello\s*world", description, re.I):
                path = "data/scripts/hello_world.py"
            elif not path:
                path = infer_script_path(message)

        Path(path).parent  # ensure path shape valid
        scripts_dir = fs.resolve_path("data/scripts", base=self.coding._base())
        scripts_dir.mkdir(parents=True, exist_ok=True)

        explanation, file_items = llm.generate_script_with_test(description, path)
        if not file_items or not file_items[0].get("code", "").strip():
            return _err("I couldn't generate a script from that request. Try being more specific.")

        from jarvis.coding_verify import verify_proposed_files
        ok, verify_detail = verify_proposed_files(file_items, self.coding._base())
        verify_note = ""
        if verify_detail:
            verify_note = f"\n\n**Pre-apply verify:** {verify_detail}" + ("" if ok else " (failed — review before apply)")

        main = file_items[0]
        new_code = main["code"]
        path = main.get("path") or path
        proposal_id, payload = self._store_agent_proposal(
            file_items, mode="create", explanation=explanation,
        )
        combined_diff = ""
        for f in file_items:
            orig = fs.read_file(f["path"], base=self.coding._base())
            if orig.startswith("ERROR:"):
                orig = ""
            combined_diff += make_diff(orig, f["code"]) + "\n"

        files_note = "\n".join(f"- `{f['path']}`" for f in file_items)
        syntax_note = ""
        if payload.get("_diag_summary"):
            syntax_note = f"\n\n**Syntax check:**\n{payload['_diag_summary']}"
        extra = self._proposal_response_extra(file_items)
        intro = (
            f"I wrote:\n{files_note}\n\n"
            f"{explanation}{syntax_note}{verify_note}\n\n"
            "```python\n"
            f"{new_code[:2000]}{'…' if len(new_code) > 2000 else ''}\n"
            "```\n\n"
            "Say **apply it** to save — I'll run the script and pytest."
        )
        if extra.get("test_impact"):
            intro += f"\n\n{extra['test_impact']}"
        return _ok(
            intro,
            module="coding",
            type="proposal",
            proposal_id=proposal_id,
            path=path,
            diff=combined_diff.strip() or make_diff("", new_code),
            explanation=explanation,
            diagnostics=payload.get("diagnostics", []),
            syntax_ok=payload.get("syntax_ok", True),
            verify_ok=ok,
            **extra,
        )

    def _tests_verify_ok(self, verify: str) -> bool:
        if not verify.strip():
            return False
        lower = verify.lower()
        if "syntax check failed" in lower:
            return False
        if "pytest:** failed" in lower:
            return False
        return "pytest:** passed" in lower

    def _coding_fix_tests_stream(self, params: dict, message: str) -> Iterator[dict]:
        """Fast path: pytest → fix → verify (max 2 LLM calls)."""
        path = self._resolve_coding_path(params.get("path", ""))
        if not path:
            yield _stream_done(_err(
                "Which file? Open it in Cursor or say e.g. "
                "`debug until tests pass for data/scripts/your_file.py`",
            ))
            return

        self.session.note_file(path)
        content = fs.read_file(path, base=self.coding._base())
        if content.startswith("ERROR:"):
            yield _stream_done(_err(content))
            return

        from jarvis.code_context import _find_test_files
        from jarvis.coding_verify import collect_test_failures

        resolved = fs.resolve_path(path, base=self.coding._base())
        yield {"type": "status", "message": "Running pytest…"}
        errors = collect_test_failures(resolved, self.coding._base())
        if not errors:
            yield _stream_done(_ok(
                f"**Tests already pass** for `{path}`. Nothing to fix.",
                module="coding",
            ))
            return

        yield {"type": "agent_step", "step": 1, "action": "pytest", "detail": "failures loaded", "ok": False}

        slim = [f"FILE: {path}\n{content}"]
        for rel_test in _find_test_files(path, self.coding._base()):
            t = fs.read_file(rel_test, base=self.coding._base())
            if not t.startswith("ERROR:"):
                slim.append(f"--- {rel_test} (test) ---\n{t[:4000]}")
        ctx_text = "\n".join(slim)
        task = f"Fix `{path}` so all tests pass. Minimal changes only."

        explanation = ""
        new_code = content
        verify = ""
        for attempt in range(1, 3):
            yield {"type": "status", "message": f"Generating fix (attempt {attempt}/2)…"}
            yield {"type": "agent_step", "step": attempt + 1, "action": "edit", "detail": path, "ok": True}
            explanation, new_code = self._llm_edit_file(
                task, path=path, content=content, context=ctx_text, errors=errors,
                require_test_pass=True,
            )
            if self._code_unchanged(content, new_code):
                errors = (errors + "\n\nNo effective code change.").strip()
                continue
            verify = verify_python_files([resolved], self.coding._base(), run_scripts=False)
            if self._tests_verify_ok(verify):
                yield {"type": "agent_step", "step": attempt + 1, "action": "verify", "detail": "tests passed", "ok": True}
                break
            errors = verify or errors
            yield {"type": "agent_step", "step": attempt + 1, "action": "verify", "detail": "tests still failing", "ok": False}

        if self._code_unchanged(content, new_code):
            from jarvis.trust_memory import record_failure

            record_failure(
                self.memory,
                path=path,
                error=errors[:500],
                task=message[:160],
            )
            yield _stream_done(_err(
                f"Could not produce a fix for `{path}` after 2 attempts.\n\n"
                "The model returned the same broken code (often failed SEARCH/REPLACE patches).\n"
                "Try: `fix data/scripts/your_file.py` or check **Settings → coder model**.",
                module="coding",
            ))
            return

        diff = make_diff(content, new_code)
        files = [{"path": path, "code": new_code}]
        diag_dicts, diag_summary = self._check_proposal_syntax(files)
        syntax_ok = not any(d.get("severity") == "error" for d in diag_dicts)
        tests_ok = self._tests_verify_ok(verify)

        proposal_id = str(uuid.uuid4())[:8]
        self.pending_proposals[proposal_id] = {
            "path": path, "code": new_code, "mode": "fix",
            "files": files, "diagnostics": diag_dicts,
            "syntax_ok": syntax_ok, "explanation": explanation,
        }
        self._persist_proposals()
        self.session.note_proposal(proposal_id)

        extra = self._proposal_response_extra(files)
        status = "Tests pass in verify." if tests_ok else "Tests still failing — review diff or try again."
        intro = (
            f"**Fix proposal** for `{path}` ({status})\n\n"
            f"{explanation or 'Changes ready to review.'}"
        )
        if diag_summary:
            intro += f"\n\n**Syntax check:**\n{diag_summary}"
        if verify and not tests_ok:
            intro += f"\n\n**Verify:**\n{verify}"
        intro += "\n\nReview the diff and hit **Apply changes** or say `apply`."

        yield {"type": "status", "message": "Proposal ready"}
        yield _stream_done({
            "ok": True,
            "message": intro,
            "module": "coding",
            "result_type": "proposal",
            "proposal_id": proposal_id,
            "path": path,
            "diff": diff,
            "explanation": explanation,
            "diagnostics": diag_dicts,
            "syntax_ok": syntax_ok,
            "agent_steps": [
                {"step": 1, "action": "pytest", "detail": "failures loaded", "ok": False},
            ],
            **extra,
        })

    def _coding_fix_tests(self, params: dict, message: str) -> dict:
        for event in self._coding_fix_tests_stream(params, message):
            if event.get("type") == "done":
                return event
        return _err("Fix task did not complete.")

    def _coding_fix(self, params: dict, message: str) -> dict:
        path = self._resolve_coding_path(params.get("path", ""))
        if not path:
            return _err(
                "Which file should I fix? Open a file in Cursor (with the ARIA extension) "
                "or say e.g. `fix data/scripts/duration.py`."
            )
        diagnosis = self._diagnosis_for_path(path)
        task = f"Fix based on diagnosis:\n{diagnosis}" if diagnosis else None
        if params.get("use_selection"):
            task = (task or "Fix the selected code.") + "\n\nSee Editor context for the selection."
        return self._coding_propose(
            path, "fix", task=task, editor_prompt=self._editor_task_suffix(params),
        )

    def _coding_improve(self, params: dict, message: str) -> dict:
        path = self._resolve_coding_path(params.get("path", ""))
        if not path:
            return _err("Which file should I improve?")
        return self._coding_propose(
            path, "improve", editor_prompt=self._editor_task_suffix(params),
        )

    def _coding_find(self, params: dict, message: str) -> dict:
        query = params.get("query") or message
        matches = fs.find_files(query, self.coding._base())
        if not matches:
            return _ok(f"I couldn't find any files matching '{query}'.", module="coding")
        for m in matches[:3]:
            self.session.note_file(m)
        lines = "\n".join(matches[:30])
        return _ok(f"Found {len(matches)} file(s):\n\n{lines}", module="coding")

    def _coding_search(self, params: dict, message: str) -> dict:
        query = params.get("query") or message
        self.session.note_search(query)
        results = fs.search_files(query, self.coding._base())
        if not results:
            return _ok(f"No matches for '{query}'.", module="coding")
        lines = "\n".join(f"{p}:{n}: {line}" for p, n, line in results[:40])
        return _ok(f"Found {len(results)} match(es):\n\n{lines}", module="coding")

    def _coding_run(self, params: dict, message: str) -> dict:
        from jarvis.project_runner import run_script, runner_info
        path = self.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file should I run?")
        try:
            resolved = fs.resolve_path(path, base=self.coding._base())
            self.session.note_file(str(resolved))
            result = run_script(resolved, self.coding._base(), timeout=60)
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += f"\n--- stderr ---\n{result.stderr}"
            info = runner_info(self.coding._base())
            header = f"_Runner: `{info['python']}`"
            if info.get("firejail"):
                header += " (firejail)"
            return _ok(f"{header}\n\n{output or '(no output)'}", module="coding", type="code_output")
        except Exception as e:
            return _err(str(e))

    def _coding_project(self, params: dict, message: str) -> dict:
        path = params.get("path") or str(PROJECT_ROOT)
        self.coding.project_root, self.coding.project_files = fs.scan_project(path)
        self.coding.search_root = self.coding.project_root
        return _ok(
            f"I've indexed **{len(self.coding.project_files)}** files. "
            "Ask me to review the project whenever you're ready.",
            module="coding",
        )

    def _coding_review(self, params: dict, message: str) -> dict:
        if not self.coding.project_root:
            self._coding_project({}, message)
        if not self.coding.project_root:
            return _err("No project loaded.")
        important = []
        for p in self.coding.project_files:
            lower = p.lower()
            if (
                ".history" not in lower and ".log" not in lower
                and (
                    "readme" in lower
                    or lower.endswith(("main.py", "app.py", "server.py", "config.py"))
                )
            ):
                important.append(p)
        if not important:
            important = [
                p for p in self.coding.project_files
                if p.lower().endswith((".py", ".sh", ".json", ".yml"))
            ][:25]
        context = ""
        for p in important[:20]:
            full = self.coding.project_root / p
            c = fs.read_file(str(full), base=self.coding.project_root)
            if c.startswith("ERROR:"):
                continue
            chunk = f"\n\nFILE: {p}\n\n{c[:1000]}"
            if len(context) + len(chunk) > 12000:
                break
            context += chunk
        prompt = f"""You are a senior software architect. Review this project. Do NOT generate code.
Focus on risks, improvements, and architecture.

PROJECT ROOT: {self.coding.project_root}
PROJECT: {context}"""
        answer = llm.ask(llm.review_model(), [{"role": "user", "content": prompt}])
        return _ok(answer, module="coding", type="review")

    def _coding_show(self, params: dict, message: str) -> dict:
        path = self.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file should I show?")
        content = fs.read_file(path, base=self.coding._base())
        if content.startswith("ERROR:"):
            return _err(content)
        self.session.note_file(path)
        numbered = "\n".join(f"{i}: {line}" for i, line in enumerate(content.splitlines(), 1))
        return _ok(f"**{path}**\n\n```\n{numbered[:8000]}\n```", module="coding")

    def _data_ok(self, answer: str, **extra) -> dict:
        preview = self.data.preview() if self.data.dataset else {}
        if preview:
            extra.setdefault("data_preview", preview)
            extra.setdefault("data_path", preview.get("path", ""))
        return _ok(answer, module="data", **extra)

    def _ensure_data_loaded(self, message: str) -> dict | None:
        if self.data.dataset:
            return None
        if not self.session.last_data_path:
            return _err("No dataset loaded — attach a CSV, JSON, XLSX, or SQLite file.")
        loaded = self._data_load({"path": self.session.last_data_path}, message)
        if not loaded.get("ok"):
            return loaded
        return None

    def _data_load(self, params: dict, message: str) -> dict:
        path = self.session.resolve_data(params.get("path", ""))
        if not path:
            return _err("Which data file should I load? Attach one or give me a path.")
        result = self.data.load_dataset(path)
        if result.startswith("ERROR:"):
            return _err(result)
        self.session.note_data(path)
        self.session.note_module("data")
        summary = self.data.describe_stats()
        return self._data_ok(
            f"I've loaded **{Path(path).name}**.\n\n{summary}\n\n"
            "Try: row count, average of a column, chart, export, or clean duplicates.",
        )

    def _data_query(self, params: dict, message: str) -> dict:
        err = self._ensure_data_loaded(message)
        if err:
            return err
        question = params.get("question") or message
        computed = self.data.compute_answer(question)
        if computed:
            return self._data_ok(computed)
        ctx = self.data.describe_stats()
        answer = llm.ask(llm.general_model(), [{
            "role": "user",
            "content": f"Dataset:\n{ctx}\n\nQuestion: {question}\n\nAnswer from the data only.",
        }])
        return self._data_ok(answer)

    def _data_summary(self, params: dict, message: str) -> dict:
        err = self._ensure_data_loaded(message)
        if err:
            return err
        return self._data_ok(self.data.describe_stats())

    def _data_clean(self, params: dict, message: str) -> dict:
        err = self._ensure_data_loaded(message)
        if err:
            return err
        instruction = params.get("instruction") or message
        summary, _ = self.data.clean(instruction)
        if summary.startswith("ERROR"):
            return _err(summary)
        return self._data_ok(f"{summary}\n\n{self.data.describe_stats()}")

    def _data_export(self, params: dict, message: str) -> dict:
        err = self._ensure_data_loaded(message)
        if err:
            return err
        if re.search(r"\bpdf\b", message, re.I):
            fmt = "pdf"
        elif re.search(r"\bjson\b", message, re.I):
            fmt = "json"
        else:
            fmt = "csv"
        m = re.search(r"\bto\s+[`'\"]?([^\s`'\"]+\.(?:csv|json|pdf))[`'\"]?", message, re.I)
        out = m.group(1) if m else None
        path = self.data.export(out, fmt=fmt)
        if path.startswith("ERROR"):
            return _err(path)
        return self._data_ok(f"Exported **{Path(path).name}** to `{path}`", export_path=path)

    def _transcribe(self, params: dict, message: str) -> dict:
        path = self.session.resolve_audio(params.get("path", ""))
        if not path:
            return _err("Which audio file should I transcribe? Attach one or record first.")
        model = params.get("model") or None
        result = self.audio.transcribe(path, model=model)
        if result.startswith("ERROR:"):
            return _err(result)
        return _ok(f"Here's the transcript:\n\n{result}", module="audio", audio_path=path, transcript=result)

    def _record_transcribe(self, params: dict, message: str) -> dict:
        duration = float(params.get("duration") or 5)
        path, text = self.audio.record_and_transcribe(duration, model=params.get("model"))
        if path.startswith("ERROR:"):
            return _err(path)
        if text.startswith("ERROR:"):
            return _err(text)
        self.session.note_audio(path)
        return _ok(
            f"**Recorded** `{path}`\n\n**Transcript:**\n\n{text}",
            module="audio",
            audio_path=path,
            transcript=text,
        )

    def _analyze_audio(self, params: dict, message: str) -> dict:
        path = self.session.resolve_audio(params.get("path", ""))
        if not path:
            return _err("Which audio file?")
        transcript = self.audio.transcribe(path)
        if transcript.startswith("ERROR:"):
            return _err(transcript)
        answer = llm.ask(llm.general_model(), [{
            "role": "user",
            "content": f"Summarize this transcript. Key points and action items.\n\n{transcript}",
        }])
        return _ok(f"**Summary:**\n\n{answer}\n\n---\n\n**Transcript:**\n{transcript[:2000]}", module="audio", audio_path=path)

    def _generate_audio(self, params: dict, message: str) -> dict:
        text = params.get("text") or message
        text = re.sub(
            r"^(please\s+)?(generate|create|make|read|speak|say)\s+(an?\s+)?(audio|voice|speech|recording\s+)?(that\s+)?(says?|reading?|of)?\s*[:\-]?\s*",
            "",
            text,
            flags=re.I,
        ).strip()
        if not text:
            return _err("What should the audio say?")
        result = self.audio.generate(
            text,
            voice=params.get("voice") or None,
            speed=int(params.get("speed") or 175),
            fmt=params.get("format") or "wav",
        )
        if result.startswith("ERROR:"):
            return _err(result)
        self.session.note_audio(result)
        played = ""
        if self.audio.devices.get("auto_play"):
            play_result = self.audio.play(result)
            if not play_result.startswith("ERROR:"):
                played = f"\n\nPlaying on **{self.audio.devices.get('name', 'Creative Sound Blaster')}**."
        return _ok(
            f"Generated audio saved to `{result}`{played}",
            module="audio",
            audio_path=result,
        )

    def _play_audio(self, params: dict, message: str) -> dict:
        path = self.session.resolve_audio(params.get("path", "")) or self.audio.last_output
        if not path:
            return _err("No audio file to play. Generate or attach one first.")
        if path.endswith(".txt") or not Path(path).exists():
            return self._generate_audio({"text": message or params.get("text", "")}, message)
        result = self.audio.play(path)
        if result.startswith("ERROR:"):
            return _err(result)
        return _ok(
            f"Playing on **{self.audio.devices.get('name', 'Creative Sound Blaster')}**: `{result}`",
            module="audio",
            audio_path=result,
        )

    def _process_audio_vst(self, params: dict, message: str) -> dict:
        path = self.session.resolve_audio(params.get("path", "")) or self.audio.last_output
        if not path:
            return _err("Which audio file? Attach one or generate speech first.", module="audio")
        chain = (params.get("chain") or params.get("preset") or "voice").strip().lower()
        from jarvis.audio_settings import save_settings
        from jarvis.audio_vst import list_chains, process_file

        valid = {c["id"] for c in list_chains()}
        if chain not in valid:
            chain = "voice"
        if params.get("set_playback"):
            save_settings({"vst_playback_chain": chain})
        result = process_file(path, chain)
        if result.startswith("ERROR:"):
            return _err(result, module="audio")
        self.session.note_audio(result)
        label = next((c["label"] for c in list_chains() if c["id"] == chain), chain)
        return _ok(
            f"Applied **{label}** → `{Path(result).name}`",
            module="audio",
            audio_path=result,
        )

    def _set_vst_live(self, params: dict, message: str) -> dict:
        preset = (params.get("preset") or params.get("chain") or "off").strip().lower()
        lower = (message or "").lower()
        if "off" in lower or "direct" in lower or "disable" in lower:
            preset = "off"
        elif "music" in lower:
            preset = "music"
        elif "scout" in lower or "surround" in lower:
            preset = "scout"
        elif "gaming" in lower or "game" in lower:
            preset = "gaming"
        elif "voice" in lower or "podcast" in lower:
            preset = "voice"

        from jarvis.audio_vst_live import activate_live, deactivate_live, install_filter_configs

        if preset in ("off", "none", "direct"):
            ok, msg = deactivate_live()
        else:
            if params.get("install"):
                install_filter_configs()
            ok, msg = activate_live(preset)
        if not ok:
            return _err(msg, module="audio")
        return _ok(msg, module="audio")

    def _edit_audio(self, params: dict, message: str) -> dict:
        path = self.session.resolve_audio(params.get("path", ""))
        if not path:
            return _err("Which audio file should I edit? Attach one or give me a path.")
        instruction = params.get("instruction") or message
        result = self.audio.edit(path, instruction=instruction)
        if result.startswith("ERROR:"):
            return _err(result)
        self.session.note_audio(result)
        return _ok(
            f"Edited audio saved to `{result}`",
            module="audio",
            audio_path=result,
        )

    def _speak(self, params: dict, message: str) -> dict:
        return self._generate_audio(params, message)

    def _vision_warnings(self) -> list[str]:
        model = llm.vision_model().lower()
        if self._vision_llava_warned:
            return []
        heavy = "llava" in model and "13" in model
        big_llama = "llama3.2-vision" in model or "llama3.2-vision" in model.replace("_", ".")
        if not heavy and not big_llama:
            return []
        self._vision_llava_warned = True
        if heavy:
            return [
                "Vision is using llava:13b — heavy on 8GB GPUs. "
                "Use Fast mode (moondream) or llama3.2-vision:11b if you see freezes.",
            ]
        return [
            "Vision is using llama3.2-vision:11b — moderate VRAM use on 8GB. "
            "Switch to Fast mode if responses stall.",
        ]

    def _vision_ok(self, answer: str, *, image_path: str | None = None) -> dict:
        extra: dict = {}
        if image_path:
            extra["image_path"] = image_path
        warnings = self._vision_warnings()
        if warnings:
            extra["warnings"] = warnings
        return _ok(answer, module="vision", **extra)

    def _describe_image(self, params: dict, message: str) -> dict:
        path = self.session.resolve_image(params.get("path", ""))
        if not path:
            return _err("Which image? Attach one or give me a path.")
        answer = self.vision.analyze("Describe this image in detail.", path)
        if answer.startswith("ERROR:"):
            return _err(answer)
        return self._vision_ok(answer, image_path=path)

    def _analyze_image(self, params: dict, message: str) -> dict:
        from jarvis.vision_media import build_vision_prompt, vision_task_for_question

        path = self.session.resolve_image(params.get("path", ""))
        question = params.get("question") or message
        if not path:
            return _err("Which image?")
        task = vision_task_for_question(question)
        prompt = build_vision_prompt(question, task)
        answer = self.vision.analyze(prompt, path, task=task)
        if answer.startswith("ERROR:"):
            return _err(answer)
        return self._vision_ok(answer, image_path=path)

    def _ocr_image(self, params: dict, message: str) -> dict:
        path = self.session.resolve_image(params.get("path", ""))
        if not path:
            return _err("Which image? Attach one or give me a path.")
        answer = self.vision.ocr(path)
        if answer.startswith("ERROR:"):
            return _err(answer)
        return self._vision_ok(answer, image_path=path)

    def _compare_from_result(self, payload: dict) -> dict:
        answer = payload.get("answer", "")
        if answer.startswith("ERROR:"):
            return _err(answer)
        extra = {
            "compare_paths": [payload.get("path1"), payload.get("path2")],
            "action": "compare_images",
        }
        if payload.get("diff_path"):
            extra["diff_path"] = payload["diff_path"]
        warnings = self._vision_warnings()
        if warnings:
            extra["warnings"] = warnings
        return _ok(answer, module="vision", **extra)

    def _compare_images(self, params: dict, message: str) -> dict:
        path1 = params.get("path1", "")
        path2 = params.get("path2", "")
        if not path1 or not path2:
            return _err("Usage: compare <image1> with <image2>")
        question = params.get("question") or message
        result = self.vision.compare(
            path1, path2, question if question != message else None, uploads_dir=UPLOAD_DIR,
        )
        return self._compare_from_result(result)

    def _ocr_structured_image(self, params: dict, message: str) -> dict:
        path = self.session.resolve_image(params.get("path", ""))
        if not path:
            return _err("Which image? Attach one or give me a path.")
        answer = self.vision.ocr_structured(path)
        if answer.startswith("ERROR:"):
            return _err(answer)
        return self._vision_ok(answer, image_path=path)

    def _image_to_code(self, params: dict, message: str) -> dict:
        path = self.session.resolve_image(params.get("path", ""))
        if not path:
            return _err("Attach a UI screenshot to convert to code.")
        answer = self.vision.image_to_code(path)
        if answer.startswith("ERROR:"):
            return _err(answer)
        return self._vision_ok(answer, image_path=path)

    def _analyze_region(self, params: dict, message: str) -> dict:
        path = self.session.resolve_image(params.get("path", ""))
        if not path:
            return _err("Which image?")
        crop = parse_region(message, params.get("crop"))
        analyze_path = path
        if crop:
            try:
                cropped = apply_crop_bytes(Path(path).read_bytes(), crop)
                region_file = UPLOAD_DIR / f"region_{Path(path).stem}.jpg"
                region_file.write_bytes(cropped)
                analyze_path = str(region_file)
            except Exception as e:
                return _err(str(e))
        question = params.get("question") or message or "What is in this region?"
        answer = self.vision.analyze(question, analyze_path, task="region")
        if answer.startswith("ERROR:"):
            return _err(answer)
        return self._vision_ok(answer, image_path=analyze_path)

    def _batch_vision(self, params: dict, message: str) -> dict:
        from jarvis import fs
        from jarvis.config import PROJECT_ROOT

        folder = params.get("folder", "")
        try:
            root = fs.resolve_path(folder, base=PROJECT_ROOT)
        except fs.PathError as e:
            return _err(str(e))
        if not root.is_dir():
            return _err(f"Not a folder: {folder}")
        images = sorted(
            p for p in root.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        )[:15]
        if not images:
            return _err(f"No images found in {folder}")
        lines = []
        for img in images:
            desc = self.vision.analyze(
                "Briefly describe this image in 2-3 sentences.",
                str(img),
                task="batch",
            )
            if desc.startswith("ERROR:"):
                lines.append(f"**{img.name}**: (failed)")
            else:
                lines.append(f"**{img.name}**: {desc}")
        return _ok("\n\n".join(lines), module="vision")

    def _enqueue_coding(self, params: dict, message: str) -> dict:
        from jarvis.coding_jobs import submit_coding_agent

        job_id = submit_coding_agent(self, params, message)
        title = (params.get("task") or message)[:80]
        return self._coding_job_result(
            f"**Coding agent** queued in the background — **{title}**\n\n"
            "Keep chatting; the result appears here when finished.",
            job_id,
            "coding_agent",
        )

    def _coding_job_result(self, message: str, job_id: str, action: str) -> dict:
        return _ok(
            message,
            module="coding",
            type="coding_job",
            job_id=job_id,
            pending=True,
            action=action,
        )

    def _enqueue_fix_tests(self, params: dict, message: str) -> dict:
        from jarvis.coding_jobs import submit_fix_tests

        path = self._resolve_coding_path(params.get("path", "")) or params.get("path", "")
        job_id = submit_fix_tests(self, {**params, "path": path}, message)
        return self._coding_job_result(
            f"**Debug until tests pass** queued for `{path or 'file'}`.\n\n"
            "Keep chatting — results appear here when pytest + fix finish.",
            job_id,
            "coding_fix_tests",
        )

    def _enqueue_background(self, action: str, params: dict, message: str) -> dict:
        from jarvis.background_jobs import ACTION_LABELS, ACTION_MODULES, submit_action

        job_id = submit_action(self, action, params, message)
        label = ACTION_LABELS.get(action, action)
        module = ACTION_MODULES.get(action, "general")
        return _ok(
            f"**{label}** queued in the background.\n\n"
            "Keep chatting — open **Job center** in the sidebar or wait for the result here.",
            module=module,
            type="background_job",
            job_id=job_id,
            pending=True,
            action=action,
        )

    def _enqueue_media(self, action: str, params: dict, message: str) -> dict:
        from jarvis.media_jobs import (
            ACTION_LABELS,
            ACTION_MODULES,
            ETA_HINTS,
            submit_assistant_action,
        )
        from jarvis.resource_router import check_media_enqueue

        check = check_media_enqueue(action)
        if check.get("blocked"):
            return _err(check.get("message") or "Media queue full — wait or cancel a job.", module="image")

        job_id = submit_assistant_action(self, action, params, message)
        label = ACTION_LABELS.get(action, action)
        hint = ETA_HINTS.get(action, "")
        msg = f"**{label}** queued in the background."
        if check.get("queue_position", 1) > 1:
            msg += f" Queue position: **{check['queue_position']}**."
        if hint:
            msg += f" {hint.capitalize()}."
        if check.get("advisory"):
            msg += f"\n\n_{check['advisory']}_"
        for warn in check.get("warnings") or []:
            if warn not in msg:
                msg += f"\n\n⚠ {warn}"
        msg += "\n\nKeep chatting — the result appears when ready."
        return _ok(
            msg,
            module=ACTION_MODULES.get(action, "image"),
            type="media_job",
            job_id=job_id,
            pending=True,
            action=action,
            queue_position=check.get("queue_position"),
        )

    def _yield_media_job(self, action: str, params: dict, message: str):
        from jarvis.media_jobs import ACTION_LABELS

        yield {"type": "status", "message": f"Queuing {ACTION_LABELS.get(action, action)}…"}
        yield _stream_done(self._enqueue_media(action, params, message))

    def _generate_image(self, params: dict, message: str) -> dict:
        return self._media.generate_image(params, message)

    def _generate_video(self, params: dict, message: str) -> dict:
        return self._media.generate_video(params, message)

    def _generate_meme(self, params: dict, message: str) -> dict:
        return self._media.generate_meme(params, message)

    def _upscale_image(self, params: dict, message: str) -> dict:
        return self._media.upscale_image(params, message)

    def _inpaint_image(self, params: dict, message: str) -> dict:
        return self._media.inpaint_image(params, message)

    def _edit_image(self, params: dict, message: str) -> dict:
        return self._media.edit_image(params, message)

    def _enhance_prompt(self, params: dict, message: str) -> dict:
        return self._media.enhance_prompt(params, message)

    def _clear(self, params: dict, message: str) -> dict:
        bid = self.branches.active_id or "main"
        return self.clear_branch_messages(bid)

    def _weather_forecast(self, params: dict, message: str) -> dict:
        from jarvis.journal_weather import parse_weather_day, weather_forecast_text

        day = (params.get("day") or "").strip() or parse_weather_day(message)
        return _ok(
            weather_forecast_text(day, message=message),
            module="general",
            type="weather",
        )

    def _web_search(self, params: dict, message: str) -> dict:
        from jarvis.profiles import web_search_disabled
        if web_search_disabled():
            return _err("Web search is disabled (offline profile). Switch profile in the sidebar.", module="general")
        from jarvis import web_search
        query = params.get("query") or re.sub(r"^(search (the )?web for|web search)[:\s]+", "", message, flags=re.I).strip()
        if not query:
            return _err("What should I search for?")
        results = web_search.search(query)
        if not results:
            return _err(
                f"No web results for that query ({web_search.backend_name()}). "
                "Try again or run: `./venv/bin/pip install ddgs`",
                module="general",
            )
        answer = web_search.synthesize_answer(query, results)
        return _ok(answer, module="general", type="web_search", results=results)

    def _rename_symbol(self, params: dict, message: str) -> dict:
        from jarvis import rename as rename_util
        symbol = params.get("symbol", "")
        new_name = params.get("new_name", "")
        dry_run = params.get("dry_run", False)
        if not symbol or not new_name:
            m = re.search(r"rename\s+(\w+)\s+(?:to|as)\s+(\w+)", message, re.I)
            if m:
                symbol, new_name = m.group(1), m.group(2)
        if not symbol or not new_name:
            return _err('Usage: rename SYMBOL to NEW_NAME (or "rename foo to bar")')

        from jarvis import refactor_ast
        preview = refactor_ast.preview_rename_python_symbol_project(
            symbol, new_name, self.coding._base(),
        )
        files = preview.get("files") or []
        if not files:
            files = rename_util.rename_symbol_preview(symbol, new_name, root=self.coding._base())
        if not files:
            return _ok(f"No usages of `{symbol}` found in the project.", module="coding")
        if dry_run:
            paths = ", ".join(f["path"] for f in files[:10])
            return _ok(
                f"Would rename `{symbol}` → `{new_name}` in **{len(files)}** file(s): {paths}",
                module="coding",
            )
        explanation = f"Rename `{symbol}` → `{new_name}` across {len(files)} file(s)."
        return self._store_refactor_proposal(files, explanation=explanation, mode="rename")

    def _find_references(self, params: dict, message: str) -> dict:
        from jarvis.code_context import find_references
        symbol = params.get("symbol", "")
        if not symbol:
            m = re.search(r"\b(?:find references|who uses|references for)\s+(\w+)", message, re.I)
            if m:
                symbol = m.group(1)
        if not symbol:
            return _err('Usage: find references SYMBOL (or "who uses parse_duration")')
        hits = find_references(symbol, self.coding._base())
        if not hits:
            return _ok(f"No references to `{symbol}` found.", module="coding")
        lines = "\n".join(f"- `{h['path']}:{h['line']}` — `{h['text'][:80]}`" for h in hits[:25])
        return _ok(f"**References to `{symbol}`** ({len(hits)}):\n\n{lines}", module="coding")

    def _coding_run_tests(self, params: dict, message: str) -> dict:
        path = self.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file's tests? e.g. `run tests for data/scripts/duration.py`")
        resolved = fs.resolve_path(path, base=self.coding._base())
        from jarvis.coding_verify import collect_test_failures, verify_python_files
        failures = collect_test_failures(resolved, self.coding._base())
        if failures:
            return _ok(f"**Tests failed** for `{path}`:\n\n```\n{failures[:3000]}\n```", module="coding")
        report = verify_python_files([resolved], self.coding._base(), run_scripts=False)
        if "passed" in report.lower():
            return _ok(f"**Tests passed** for `{path}`.\n\n{report}", module="coding")
        return _ok(f"**Test run** for `{path}`:\n\n{report or 'No paired tests found.'}", module="coding")

    def _coding_run_command(self, params: dict, message: str) -> dict:
        from jarvis.project_runner import run_project_command
        cmd = params.get("command", "")
        if not cmd:
            m = re.search(r"\brun command[:\s]+(.+)", message, re.I)
            if m:
                cmd = m.group(1).strip()
        if not cmd:
            return _err("Usage: run command: pytest data/scripts/test_duration.py -q")
        try:
            result = run_project_command(cmd, self.coding._base(), timeout=120)
        except ValueError as e:
            return _err(str(e))
        out = ((result.stdout or "") + (result.stderr or "")).strip()[:4000]
        status = "OK" if result.returncode == 0 else f"exit {result.returncode}"
        return _ok(f"**Command** `{cmd}` — {status}\n\n```\n{out or '(no output)'}\n```", module="coding")

    def _git_pr(self, params: dict, message: str) -> dict:
        from jarvis import git_util
        title = params.get("title", "")
        body = params.get("body", "")
        if not title:
            m = re.search(r"\bcreate (?:a )?pull request[:\s]+(.+)", message, re.I)
            title = m.group(1).strip() if m else "Jarvis coding changes"
        result = git_util.create_pull_request(title, body, path=self.coding._base())
        if result.startswith("ERROR"):
            return _err(result)
        return _ok(f"**Pull request:** {result}", module="coding")

    def _coding_editor_status(self, params: dict, message: str) -> dict:
        from jarvis.editor_context import get_context, load_context
        ctx = get_context() or load_context()
        if not ctx.relative_file:
            return _ok(
                "No editor context synced.\n\n"
                "Install the Cursor extension: `./scripts/install-cursor-extension.sh` "
                "then reload Cursor and open a file.",
                module="coding",
            )
        fresh = get_context() is not None
        body = ctx.format_for_prompt(max_selection=1500)
        note = "live from Cursor" if fresh else "stale — click in Cursor or run **ARIA: Push Editor Context Now**"
        return _ok(f"**Editor context** ({note}):\n\n{body}", module="coding")

    def _coding_explain_selection(self, params: dict, message: str) -> dict:
        from jarvis.editor_context import get_context
        ctx = get_context()
        if not ctx or not ctx.has_selection():
            return _err(
                "No selection synced from Cursor. Select code, install the extension "
                "(`./scripts/install-cursor-extension.sh`), and try **ARIA: Push Editor Context Now**."
            )
        path = ctx.relative_file
        content = fs.read_file(path, base=self.coding._base())
        if content.startswith("ERROR:"):
            return _err(content)
        explanation = llm.diagnose_code(
            message or "Explain what this selected code does and any issues.",
            path=path,
            content=content,
            context=ctx.format_for_prompt(),
            errors="",
        )
        self.session.note_file(path)
        return _ok(
            f"**Selection in `{path}`:**\n\n{explanation}",
            module="coding",
            type="diagnose",
            path=path,
        )

    def _coding_lsp(self, params: dict, message: str) -> dict:
        return self._syntax_check(params, message)

    def _lsp_line_col(self, params: dict) -> tuple[int, int]:
        try:
            line = int(params.get("line") or 1)
        except (TypeError, ValueError):
            line = 1
        try:
            column = int(params.get("column") or 1)
        except (TypeError, ValueError):
            column = 1
        return max(1, line), max(1, column)

    def _lsp_definition(self, params: dict, message: str) -> dict:
        from jarvis.lsp_bridge import lsp_definition

        path = self.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file? Give a path or open one in Cursor.", module="coding")
        line, col = self._lsp_line_col(params)
        out = lsp_definition(path, self.coding._base(), line, col)
        if not out.get("ok"):
            return _err(out.get("message", "LSP definition failed"), module="coding")
        locs = out.get("locations") or []
        if not locs:
            return _ok(f"No definition found at `{path}`:{line}", module="coding", locations=[])
        lines = [f"- `{loc['path']}`:{loc['line']}:{loc['column']}" for loc in locs[:10]]
        return _ok(
            f"**Definition** ({len(locs)}):\n" + "\n".join(lines),
            module="coding",
            locations=locs,
        )

    def _lsp_references(self, params: dict, message: str) -> dict:
        from jarvis.lsp_bridge import lsp_references

        path = self.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file?", module="coding")
        line, col = self._lsp_line_col(params)
        out = lsp_references(path, self.coding._base(), line, col)
        if not out.get("ok"):
            return _err(out.get("message", "LSP references failed"), module="coding")
        refs = out.get("references") or []
        if not refs:
            return _ok(f"No references for `{path}`:{line}", module="coding", references=[])
        lines = [f"- `{r['path']}`:{r['line']}" for r in refs[:20]]
        more = f"\n… and {len(refs) - 20} more" if len(refs) > 20 else ""
        return _ok(
            f"**References** ({len(refs)}):\n" + "\n".join(lines) + more,
            module="coding",
            references=refs,
        )

    def _lsp_hover(self, params: dict, message: str) -> dict:
        from jarvis.lsp_bridge import lsp_hover

        path = self.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file?", module="coding")
        line, col = self._lsp_line_col(params)
        out = lsp_hover(path, self.coding._base(), line, col)
        if not out.get("ok"):
            return _err(out.get("message", "LSP hover failed"), module="coding")
        text = (out.get("hover") or "").strip() or "(no hover info)"
        return _ok(f"**Hover** `{path}`:{line}\n\n{text}", module="coding", hover=text)

    def _lsp_format(self, params: dict, message: str) -> dict:
        from jarvis.lsp_bridge import lsp_format

        path = self.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file should I format?", module="coding")
        write = bool(params.get("write", True))
        out = lsp_format(path, self.coding._base(), write=write)
        if not out.get("ok"):
            return _err(out.get("message", "LSP format failed"), module="coding")
        if write:
            return _ok(f"Formatted **`{path}`** via language server.", module="coding", path=path)
        return _ok(f"Format preview for **`{path}`** (not written).", module="coding", formatted=out.get("formatted", ""))

    def _lsp_symbols(self, params: dict, message: str) -> dict:
        from jarvis.lsp_bridge import lsp_symbols

        path = self.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file?", module="coding")
        out = lsp_symbols(path, self.coding._base())
        if not out.get("ok"):
            return _err(out.get("message", "LSP symbols failed"), module="coding")
        symbols = out.get("symbols") or []
        if not symbols:
            return _ok(f"No symbols in `{path}`", module="coding", symbols=[])
        lines = [f"- {s['name']} (L{s['line']})" for s in symbols[:40]]
        more = f"\n… and {len(symbols) - 40} more" if len(symbols) > 40 else ""
        return _ok(
            f"**Symbols in `{path}`** ({len(symbols)}):\n" + "\n".join(lines) + more,
            module="coding",
            symbols=symbols,
        )

    def _syntax_check(self, params: dict, message: str) -> dict:
        from jarvis.lsp import check_any, tools_status as lsp_tools
        path = self.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file should I check?")
        resolved = fs.resolve_path(path, base=self.coding._base())
        if not resolved.exists():
            return _err(f"File not found: {path}")
        deep = params.get("deep", True)
        if isinstance(deep, str):
            deep = deep.lower() not in ("0", "false", "no")
        diags = check_any(resolved, deep=deep)
        tools = {**available_tools(), **lsp_tools()}
        tool_line = ", ".join(k for k, v in tools.items() if v)
        if not diags:
            return _ok(
                f"No issues in **{path}**.\n\n_Checkers: {tool_line}_",
                module="coding",
                diagnostics=[],
                syntax_ok=True,
            )
        summary = format_diagnostics(diags)
        ok = not any(d.severity == "error" for d in diags)
        return _ok(
            f"**Syntax/lint for `{path}`:**\n\n{summary}\n\n_Checkers: {tool_line}_",
            module="coding",
            diagnostics=diagnostics_to_dicts(diags),
            syntax_ok=ok,
        )

    def _coding_agent(self, params: dict, message: str, on_step=None) -> dict:
        task_text = params.get("task") or message
        path = self.session.resolve_path(params.get("path", "")) or None
        mode = params.get("mode", "agent")
        task_id = params.get("task_id") or ""
        ct = None
        initial_errors = ""

        if not task_id:
            ct = self.task_manager.create(task_text[:120], path=path or "", mode=mode)
            task_id = ct.id
        else:
            ct = self.task_manager.get(task_id)
            if ct:
                self.task_manager.resume(task_id)
                path = path or ct.path or None
                task_text = ct.checkpoint.get("task") or task_text
                mode = ct.checkpoint.get("mode") or mode
                initial_errors = ct.checkpoint.get("last_errors") or ""

        agent = CodingAgent(self.coding._base(), max_steps=int(params.get("max_steps") or 5))
        result = agent.run(
            task_text,
            path=path,
            mode=mode,
            initial_errors=initial_errors,
        )
        for s in result.steps:
            step_dict = {"step": s.step, "action": s.action, "detail": s.detail, "ok": s.ok}
            if on_step:
                on_step(step_dict)
            self.task_manager.add_step(task_id, s.action, s.detail, ok=s.ok)

        if not result.ok:
            self.task_manager.save_state(task_id, last_errors=result.message)
            self.task_manager.complete(task_id, ok=False)
            return _err(result.message)

        if result.diagnose_only:
            self.task_manager.complete(task_id, ok=True)
            return _ok(result.message, module="coding", type="diagnose", task_id=task_id)

        proposal_id, payload = self._store_agent_proposal(
            result.files, mode=result.mode, explanation=result.explanation, task_id=task_id,
        )
        self.task_manager.save_state(
            task_id,
            task_text=task_text,
            path=path or "",
            mode=mode,
            files=[f["path"] for f in result.files],
            proposal_id=proposal_id,
        )
        self.task_manager.complete(task_id, ok=True)

        extra = self._proposal_response_extra(result.files)
        steps_note = "\n".join(f"{s.step}. {s.action}: {s.detail}" for s in result.steps[-6:])
        diag_summary = payload.get("_diag_summary", "")
        intro = f"{result.message}\n\n**Steps:**\n{steps_note}"
        if diag_summary:
            intro += f"\n\n**Syntax check:**\n{diag_summary}"
        if extra.get("test_impact"):
            intro += f"\n\n{extra['test_impact']}"
        return _ok(
            intro,
            module="coding",
            type="proposal",
            proposal_id=proposal_id,
            path=result.files[0]["path"] if result.files else "",
            diff=result.diff,
            explanation=result.explanation,
            agent_steps=[{"step": s.step, "action": s.action, "detail": s.detail} for s in result.steps],
            diagnostics=payload.get("diagnostics", []),
            syntax_ok=payload.get("syntax_ok", True),
            task_id=task_id,
            **extra,
        )

    def _coding_task(self, params: dict, message: str) -> dict:
        action = (params.get("action") or "").lower()
        lower = message.lower().strip()

        if re.search(r"\b(list|show)\b.*\b(tasks?)\b", lower) or action == "list":
            tasks = self.task_manager.list_tasks()
            if not tasks:
                return _ok("No coding tasks yet.", module="coding")
            lines = "\n".join(
                f"- `{t.id}` **{t.title[:60]}** — {t.status} ({len(t.steps)} steps)"
                for t in tasks[:15]
            )
            return _ok(f"**Coding tasks:**\n\n{lines}", module="coding")

        if re.search(r"\bpause\b.*\b(task|coding)\b", lower) or action == "pause":
            active = self.task_manager.active()
            tid = params.get("task_id") or (active.id if active else "")
            if not tid:
                return _err("No active coding task to pause.")
            self.task_manager.pause(tid)
            return _ok(f"Paused task `{tid}`. Say **resume task** to continue.", module="coding", task_id=tid)

        if re.search(r"\bresume\b.*\b(task|coding)\b", lower) or action == "resume":
            tid = params.get("task_id") or ""
            task = self.task_manager.get(tid) if tid else self.task_manager.active()
            if not task:
                return _err("No task to resume.")
            self.task_manager.resume(task.id)
            checkpoint = task.checkpoint
            resume_msg = checkpoint.get("task") or task.title
            return self._enqueue_coding(
                {
                    "task": resume_msg,
                    "path": task.path,
                    "mode": task.mode,
                    "task_id": task.id,
                    "max_steps": 5,
                },
                resume_msg,
            )

        active = self.task_manager.active()
        if active:
            lines = "\n".join(f"{s.step}. {s.action}: {s.detail}" for s in active.steps[-10:])
            return _ok(
                f"**Active task** `{active.id}` — {active.status}\n\n{lines}",
                module="coding",
                task_id=active.id,
            )
        return _ok("No active coding task. Start one with **implement …**", module="coding")

    def _extract_function(self, params: dict, message: str) -> dict:
        from jarvis import refactor_ast
        path = self.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file?")
        resolved = fs.resolve_path(path, base=self.coding._base())
        func_name = params.get("name", "")
        start = int(params.get("start_line") or params.get("start") or 0)
        end = int(params.get("end_line") or params.get("end") or 0)
        if not func_name or not start or not end:
            m = re.search(
                r"extract\s+(?:lines?\s+)?(\d+)\s*[-–]\s*(\d+)\s+(?:as|into|to)\s+(\w+)",
                message, re.I,
            )
            if m:
                start, end, func_name = int(m.group(1)), int(m.group(2)), m.group(3)
        if not func_name or not start or not end:
            return _err('Usage: extract lines 10-25 as my_function from path/to/file.py')
        dry_run = params.get("dry_run", False)
        result = refactor_ast.extract_function(resolved, start, end, func_name, dry_run=True)
        if result.get("error"):
            return _err(result["error"])
        if not result.get("changed") or not result.get("code"):
            return _ok(f"No changes for `{func_name}` in **{path}**.", module="coding")
        if dry_run:
            return _ok(f"Would extract `{func_name}` from lines {start}-{end} in **{path}**.", module="coding")
        files = [{"path": result["path"], "code": result["code"]}]
        return self._store_refactor_proposal(
            files,
            explanation=f"Extract lines {start}-{end} as `{func_name}()` in **{path}**.",
            mode="extract",
        )

    def _move_module(self, params: dict, message: str) -> dict:
        from jarvis import refactor_ast
        from_p = params.get("from") or params.get("from_path", "")
        to_p = params.get("to") or params.get("to_path", "")
        if not from_p or not to_p:
            m = re.search(r"move\s+(\S+)\s+to\s+(\S+)", message, re.I)
            if m:
                from_p, to_p = m.group(1), m.group(2)
        if not from_p or not to_p:
            return _err('Usage: move jarvis/old_module.py to jarvis/new_module.py')
        dry_run = params.get("dry_run", False)
        preview = refactor_ast.preview_move_module(
            fs.resolve_path(from_p, base=self.coding._base()),
            fs.resolve_path(to_p, base=self.coding._base()),
            self.coding._base(),
        )
        if preview.get("error"):
            return _err(preview["error"])
        files = preview.get("files") or []
        if not files:
            return _ok(f"Nothing to change for move `{from_p}` → `{to_p}`.", module="coding")
        if dry_run:
            return _ok(
                f"Would move `{preview['from']}` → `{preview['to']}` "
                f"and update **{preview.get('imports_updated', 0)}** import(s).",
                module="coding",
            )
        return self._store_refactor_proposal(
            files,
            explanation=f"Move `{preview['from']}` → `{preview['to']}` and update imports.",
            mode="move",
        )

    def _coding_refactor(self, params: dict, message: str) -> dict:
        params = dict(params)
        params["mode"] = "refactor"
        params["task"] = params.get("task") or message
        return self._coding_agent(params, message)

    def _coding_diagnose(self, params: dict, message: str) -> dict:
        path = self.session.resolve_path(params.get("path", ""))
        if not path:
            return _err("Which file should I diagnose?")
        agent = CodingAgent(self.coding._base())
        result = agent.diagnose(path, params.get("task") or message)
        if not result.ok:
            return _err(result.message)
        diag_id = str(uuid.uuid4())[:8]
        self.pending_diagnoses[diag_id] = {"path": path, "explanation": result.message}
        self.session.note_file(path)
        return _ok(
            f"**Diagnosis for `{path}`:**\n\n{result.message}\n\n"
            "Say **fix it** to apply a fix based on this diagnosis.",
            module="coding",
            type="diagnose",
            diagnose_id=diag_id,
            path=path,
        )

    def _coding_chat(self, params: dict, message: str) -> dict:
        from jarvis import code_index
        from jarvis.trust_memory import filter_trusted_content

        query = params.get("query") or message
        parts = []
        code_ctx = code_index.context_for_query(query, limit=5)
        if code_ctx:
            parts.append(code_ctx)
        mem_hits = self.memory.search(query, limit=4)
        if mem_hits:
            mem_lines = []
            for m in mem_hits:
                line = filter_trusted_content(m.get("content", ""))
                if line:
                    mem_lines.append(f"- {line}")
            if mem_lines:
                parts.append("Relevant memory:\n" + "\n".join(mem_lines))
        if self.session.last_file:
            content = fs.read_file(self.session.last_file, base=self.coding._base())
            if not content.startswith("ERROR:"):
                parts.append(f"Last file ({self.session.last_file}):\n{content[:4000]}")
        doc_ctx, doc_warnings = rag.context_for_query(query)
        if doc_ctx:
            parts.append(doc_ctx)
        if doc_warnings:
            parts.extend(doc_warnings)
        context = "\n\n".join(parts)
        answer = llm.coding_chat_answer(query, context=context)
        return _ok(answer, module="coding", type="coding_chat")

    def _code_index(self, params: dict, message: str) -> dict:
        from jarvis import code_index
        root = params.get("path") or str(self.coding._base())
        chunks = code_index.build_index(Path(root))
        return _ok(
            f"Indexed **{len(chunks)}** code chunks from `{root}`. "
            "Ask coding questions or say \"search code for …\".",
            module="coding",
        )

    def _code_search(self, params: dict, message: str) -> dict:
        from jarvis import code_index
        query = params.get("query") or re.sub(
            r"^(search code for|find in code|where is)\s*",
            "",
            message,
            flags=re.I,
        ).strip()
        if not query:
            return _err("What should I search for in the codebase?")
        hits = code_index.search(query, limit=8)
        if not hits:
            return _ok(f"No semantic matches for '{query}'. Try `index code` first.", module="coding")
        lines = "\n\n".join(
            f"**{h['source']}**\n```\n{h['text'][:600]}\n```" for h in hits
        )
        for h in hits[:3]:
            self.session.note_file(h["source"])
        return _ok(f"Found {len(hits)} match(es) for **{query}**:\n\n{lines}", module="coding")

    def _git_commit(self, params: dict, message: str) -> dict:
        from jarvis import git_util
        msg = params.get("message") or ""
        if not msg:
            m = re.search(r"commit(?:\s+with\s+message)?[:\s]+(.+)", message, re.I)
            msg = m.group(1).strip() if m else ""
        if not msg:
            return _err('Provide a commit message, e.g. "commit: fix hello world script"')
        files = params.get("files")
        if isinstance(files, str):
            files = [files]
        result = git_util.commit(msg, path=self.coding._base(), files=files)
        if result.startswith("ERROR:"):
            return _err(result)
        return _ok(f"```\n{result}\n```", module="coding")

    def _git_branch(self, params: dict, message: str) -> dict:
        from jarvis import git_util
        name = params.get("name") or ""
        if not name:
            m = re.search(r"(?:create\s+)?branch\s+[`'\"]?([\w./-]+)", message, re.I)
            name = m.group(1) if m else ""
        if not name:
            return _err('Provide a branch name, e.g. "create branch feature/coding-agent"')
        result = git_util.create_branch(name, path=self.coding._base())
        if result.startswith("ERROR:"):
            return _err(result)
        return _ok(result, module="coding")

    def _git_summarize(self, params: dict, message: str) -> dict:
        from jarvis import git_util
        f = params.get("file", "")
        diff_text = git_util.summarize_diff(path=self.coding._base(), file=f or None)
        if diff_text in ("No changes.", "Not a git repository."):
            return _ok(diff_text, module="coding")
        summary = llm.ask(llm.general_model(), [{
            "role": "user",
            "content": f"Summarize this git diff in plain English (bullet points):\n\n```diff\n{diff_text[:12000]}\n```",
        }])
        return _ok(f"**Changes summary:**\n\n{summary}", module="coding")

    def _generate_music(self, params: dict, message: str) -> dict:
        from jarvis import music_gen
        prompt = params.get("prompt") or re.sub(
            r"^(generate|create|make)\s+(?:some\s+)?music\s+(?:about|for|of)?\s*[:\-]?\s*",
            "",
            message,
            flags=re.I,
        ).strip()
        if not prompt:
            return _err("What kind of music should I generate?")
        duration = int(params.get("duration") or 10)
        result = music_gen.generate_music(prompt, duration=duration)
        if result.startswith("ERROR:"):
            return _err(result)
        if not result.lower().endswith((".wav", ".mp3", ".ogg", ".flac", ".m4a")):
            return _err(f"Music output is not audio: {result}")
        self.session.note_audio(result)
        return _ok(f"Music saved to `{result}`", module="audio", audio_path=result)

    def _transform_genre(self, params: dict, message: str) -> dict:
        path = self.session.resolve_audio(params.get("path", ""))
        if not path:
            return _err("Attach a song or give me an audio path.")
        genre = params.get("genre") or params.get("prompt") or message
        genre = re.sub(
            r"^(turn|transform|convert|remix|make)\s+(?:this|it|the song)?\s*(?:into|as|to)?\s*",
            "", genre, flags=re.I,
        ).strip() or "jazz"
        duration = int(params.get("duration") or 30)
        result = self.audio.transform_genre(path, genre, duration=duration)
        if result.startswith("ERROR:"):
            return _err(result)
        self.session.note_audio(result)
        return _ok(
            f"Genre remix saved to `{result}`\n\n**Style:** {genre}",
            module="audio", audio_path=result,
        )

    def _generate_song(self, params: dict, message: str) -> dict:
        topic = params.get("topic") or params.get("prompt") or message
        topic = re.sub(
            r"^(write|compose|create|generate)\s+(?:a\s+)?song\s+(?:about|on)?\s*",
            "", topic, flags=re.I,
        ).strip()
        if not topic:
            return _err("What should the song be about?")
        genre = params.get("genre") or "pop"
        mood = params.get("mood") or "uplifting"
        duration = int(params.get("duration") or 30)
        result = self.audio.generate_full_song(topic, genre=genre, mood=mood, duration=duration)
        if not result.get("ok"):
            return _err(result.get("error", "Song generation failed"))
        self.session.note_audio(result.get("audio_path", ""))
        lyrics = result.get("lyrics", "")
        return _ok(
            f"**{result.get('title', 'Song')}**\n\n{lyrics}\n\nSaved: `{result.get('audio_path')}`",
            module="audio",
            audio_path=result.get("audio_path"),
            transcript=lyrics,
        )

    def _voice_to_song(self, params: dict, message: str) -> dict:
        path = self.session.resolve_audio(params.get("path", "")) or self.audio.last_output
        if not path:
            return _err("Record your voice first or attach a vocal recording.")
        lyrics = params.get("lyrics") or ""
        title = params.get("title") or ""
        style = params.get("style") or "pop ballad"
        genre = params.get("genre") or "pop"
        duration = int(params.get("duration") or 30)
        result = self.audio.voice_to_song(
            path, lyrics=lyrics, title=title, style=style, genre=genre, duration=duration,
        )
        if not result.get("ok"):
            return _err(result.get("error", "Voice-to-song failed"))
        self.session.note_audio(result.get("audio_path", ""))
        return _ok(
            f"**{result.get('title', 'Your song')}**\n\n{result.get('lyrics', '')}\n\nMixed track: `{result.get('audio_path')}`",
            module="audio",
            audio_path=result.get("audio_path"),
            transcript=result.get("lyrics", ""),
        )

    def _diarize_audio(self, params: dict, message: str) -> dict:
        path = self.session.resolve_audio(params.get("path", ""))
        if not path:
            return _err("Which audio file should I diarize?")
        n = int(params.get("num_speakers") or 0) or None
        result = self.audio.diarize(path, num_speakers=n)
        if not result.get("ok"):
            return _err(result.get("error", "Diarization failed"))
        text = result.get("transcript") or ""
        segs = result.get("segments", [])
        lines = [f"- **{s.get('speaker')}** ({s.get('start')}s–{s.get('end')}s): {s.get('text', '')}" for s in segs[:20]]
        body = text or "\n".join(lines)
        hint = f"\n\n_{result.get('hint')}_" if result.get("hint") else ""
        return _ok(
            f"**Speakers** ({result.get('engine', 'unknown')}):\n\n{body}{hint}",
            module="audio",
            audio_path=path,
            transcript=body,
        )

    def _branch_create(self, params: dict, message: str) -> dict:
        name = params.get("name") or message.strip() or "Branch"
        bid = self.create_branch(name)
        return _ok(f"Created branch **{name}** (`{bid}`). You're now on it.", module="general", branch_id=bid)

    def _branch_switch(self, params: dict, message: str) -> dict:
        bid = params.get("branch_id") or message.strip()
        if not self.switch_branch(bid):
            branches = self.branches.list_branches()
            lines = "\n".join(f"- `{b['id']}` {b['name']}" for b in branches)
            return _err(f"Unknown branch `{bid}`. Available:\n{lines}")
        return _ok(f"Switched to branch `{bid}`.", module="general", branch_id=bid)

    def _branch_list(self, params: dict, message: str) -> dict:
        branches = self.branches.list_branches()
        active = self.branches.active_id
        lines = "\n".join(
            f"{'→' if b['id'] == active else ' '} `{b['id']}` **{b['name']}** ({b['messages']} msgs)"
            for b in branches
        )
        return _ok(f"**Chat branches:**\n\n{lines}", module="general")

    def _branch_delete(self, params: dict, message: str) -> dict:
        raw = params.get("branch_ids") or params.get("branch_id") or message.strip()
        if isinstance(raw, list):
            ids = [str(x).strip() for x in raw if str(x).strip()]
        else:
            ids = [p.strip() for p in re.split(r"[\s,]+", str(raw)) if p.strip()]
        if not ids:
            return _err("Name one or more branch ids to delete (main cannot be removed).")
        result = self.delete_branches(ids)
        if not result["deleted"]:
            return _err("No branches deleted — check ids (main is protected).")
        names = ", ".join(f"`{b}`" for b in result["deleted"])
        return _ok(
            f"Deleted {len(result['deleted'])} branch(es): {names}. Active: `{result['active']}`.",
            module="general",
            branch_id=result["active"],
        )

    def _data_sql(self, params: dict, message: str) -> dict:
        if not self.data.dataset:
            loaded = self._data_load({"path": self.session.last_data_path}, message)
            if not loaded.get("ok"):
                return loaded
        query = params.get("query") or message
        if not query.strip().upper().startswith("SELECT"):
            m = re.search(r"(SELECT\s+.+)", message, re.I | re.S)
            query = m.group(1) if m else query
        result = self.data.sql_query(query)
        if result.startswith("ERROR:"):
            return _err(result)
        return _ok(f"**Query results:**\n\n```json\n{result[:6000]}\n```", module="data")

    def _journal_log(self, params: dict, message: str) -> dict:
        text = params.get("text") or message
        text = re.sub(r"^(log|journal|add to journal)[:\s]+", "", text, flags=re.I).strip()
        bullets = self.journal.parse_rapid_log(text)
        lines = "\n".join(f"• {b['content']}" for b in bullets)
        return _ok(f"Added to today's log:\n\n{lines}", module="journal")

    def _journal_today(self, params: dict, message: str) -> dict:
        day = params.get("day") or ""
        page = self.journal.format_page("daily", day or None)
        return _ok(page, module="journal")

    def _journal_monthly(self, params: dict, message: str) -> dict:
        from jarvis.modules.journal import _month_key

        month = params.get("month") or _month_key()
        page = self.journal.format_page("monthly", month)
        return _ok(page, module="journal")

    def _journal_open_tasks(self, params: dict, message: str) -> dict:
        tasks = self.journal.open_tasks()
        if not tasks:
            return _ok("No open journal tasks — you're clear.", module="journal")
        from jarvis.modules.journal import _format_bullet

        lines = "\n".join(f"• [{t.get('section')}] {_format_bullet(t)}" for t in tasks)
        return _ok(f"**Open tasks ({len(tasks)}):**\n\n{lines}", module="journal")

    def _journal_reflect(self, params: dict, message: str) -> dict:
        scope = "month" if "month" in message.lower() else "week" if "week" in message.lower() else "today"
        reflection = self.journal.ai_reflect(scope)
        return _ok(reflection, module="journal")

    def _journal_migrate(self, params: dict, message: str) -> dict:
        from jarvis.modules.journal import _month_key
        mk = _month_key()
        y, m = map(int, mk.split("-"))
        nm = f"{y:04d}-{m+1:02d}" if m < 12 else f"{y+1:04d}-01"
        r = self.journal.migrate_month(mk, nm)
        return _ok(f"Monthly migration: moved {r['migrated']} tasks to {nm}.", module="journal")

    def _journal_search(self, params: dict, message: str) -> dict:
        q = params.get("query") or re.sub(r"^search journal\s*", "", message, flags=re.I)
        hits = self.journal.search(q)
        if not hits:
            return _ok("No journal entries found.", module="journal")
        from jarvis.modules.journal import _format_bullet
        lines = "\n".join(f"[{h.get('section')}] {_format_bullet(h)}" for h in hits)
        return _ok(lines, module="journal")

    def _journal_review(self, params: dict, message: str) -> dict:
        scope = "week" if "week" in message.lower() else "month"
        text = self.journal.ai_reflect_review(scope)
        return _ok(text, module="journal")

    def _data_chart(self, params: dict, message: str) -> dict:
        err = self._ensure_data_loaded(message)
        if err:
            return err
        from jarvis.modules.data import parse_chart_request
        spec = parse_chart_request(message)
        col = params.get("column") or spec.get("column")
        chart_type = params.get("chart_type") or spec.get("chart_type") or "bar"
        result = self.data.chart(col or None, chart_type=chart_type)
        if result.startswith("ERROR:"):
            return _err(result)
        label = f"**{col}** ({chart_type})" if col else chart_type
        return self._data_ok(f"Chart for {label}:", chart_path=result)
