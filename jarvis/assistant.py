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
            from jarvis.handlers import ensure_handlers_loaded
            from jarvis.handlers.registry import call_action

            ensure_handlers_loaded()
            return call_action(
                self,
                "compare_images",
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
            from jarvis.behaviors.engineering.context import EngineeringContext
            from jarvis.behaviors.engineering.engine import EngineeringEngine
            EngineeringEngine.apply_editor_params(EngineeringContext.from_orchestrator(self), params, message, action)

        handlers = {
            "chat": self._chat,
            "apply_proposal": self._apply_proposal_nl,
            "dismiss_proposal": self._dismiss_proposal,
            "undo_apply": self._undo_apply,
            "record_transcribe": self._record_transcribe,
            "transcribe": self._transcribe,
            "analyze_audio": self._analyze_audio,
            "speak": self._generate_audio,
            "generate_audio": self._generate_audio,
            "edit_audio": self._edit_audio,
            "play_audio": self._play_audio,
            "process_audio_vst": self._process_audio_vst,
            "set_vst_live": self._set_vst_live,
            "generate_image": self._generate_image,
            "generate_video": self._generate_video,
            "generate_meme": self._generate_meme,
            "upscale_image": self._upscale_image,
            "inpaint_image": self._inpaint_image,
            "edit_image": self._edit_image,
            "enhance_prompt": self._enhance_prompt,
            "generate_music": self._generate_music,
            "transform_genre": self._transform_genre,
            "generate_song": self._generate_song,
            "voice_to_song": self._voice_to_song,
            "diarize_audio": self._diarize_audio,
            "upgrade_wizard": self._upgrade_wizard,
            "upgrade_verify": self._upgrade_verify,
            "upgrade_apply": self._upgrade_apply,
            "upgrade_rollback": self._upgrade_rollback,
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
                    from jarvis.behaviors.vision.context import VisionContext
                    from jarvis.behaviors.vision.engine import VisionActionEngine

                    result = VisionActionEngine.compare_from_result(
                        VisionContext.from_orchestrator(self),
                        payload,
                    )
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
            from jarvis.behaviors.engineering.context import EngineeringContext
            from jarvis.behaviors.engineering.engine import EngineeringEngine
            EngineeringEngine.apply_editor_params(EngineeringContext.from_orchestrator(self), params, message, action)

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
            for event in self._engineering_stream('coding_agent_stream', 
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
            path = self._engineering_resolve_path(params.get('path', ''))
            mode = "fix" if action == "coding_fix" else "improve"
            task = None
            if mode == "fix":
                diagnosis = self._engineering_diagnosis_for_path(path) if path else ""
                task = f"Fix based on diagnosis:\n{diagnosis}" if diagnosis else None
                if params.get("use_selection"):
                    task = (task or "Fix the selected code.") + "\n\nSee Editor context for the selection."
            editor_prompt = self._engineering_editor_suffix(params)
            if lite_ui:
                from jarvis.coding_jobs import submit_coding_propose

                job_id = submit_coding_propose(
                    self, path, mode, task=task, editor_prompt=editor_prompt,
                )
                yield _stream_done(self._engineering_job_result(
                    f"**Coding** queued — `{path or 'file'}` ({mode})\n\n"
                    "Working in the background — result appears here when ready.",
                    job_id,
                    action,
                ), lite_ui=True)
                return
            for event in self._engineering_stream('coding_propose_stream', 
                path, mode, task=task, message=message, editor_prompt=editor_prompt,
            ):
                yield event
            return

        if action == "coding_create":
            if lite_ui:
                from jarvis.coding_jobs import submit_coding_create

                job_id = submit_coding_create(self, intent.get("params", {}), message)
                yield _stream_done(self._engineering_job_result(
                    "**Coding** queued — new script\n\n"
                    "Working in the background — result appears here when ready.",
                    job_id,
                    "coding_create",
                ), lite_ui=True)
                return
            for event in self._engineering_stream('coding_create_stream', intent.get("params", {}), message):
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
                for event in self._engineering_stream('coding_agent_stream', 
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
                from jarvis.handlers.registry import call_action

                result = call_action(self, "analyze_region", params, message)
                yield _stream_done(result)
                return
            elif action == "compare_images":
                from jarvis.handlers.registry import call_action

                result = call_action(self, "compare_images", params, message)
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

    def _engineering_ctx(self):
        from jarvis.behaviors.engineering.context import EngineeringContext

        return EngineeringContext.from_orchestrator(self)

    def _engineering_stream(self, method: str, *args, **kwargs):
        from jarvis.behaviors.engineering.engine import EngineeringEngine

        fn = getattr(EngineeringEngine, method)
        yield from fn(self._engineering_ctx(), *args, **kwargs)

    def _engineering_resolve_path(self, path: str) -> str:
        from jarvis.behaviors.engineering.engine import EngineeringEngine

        return EngineeringEngine.resolve_coding_path(self._engineering_ctx(), path)

    def _engineering_job_result(self, message: str, job_id: str, action: str) -> dict:
        from jarvis.behaviors.engineering.engine import EngineeringEngine

        return EngineeringEngine.coding_job_result(self._engineering_ctx(), message, job_id, action)

    def _engineering_diagnosis_for_path(self, path: str) -> str:
        return self._diagnosis_for_path(path)

    def _engineering_editor_suffix(self, params: dict) -> str:
        return self._editor_task_suffix(params)

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



    def _editor_task_suffix(self, params: dict) -> str:
        return params.get("_editor_prompt", "") or ""


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





    def _tests_verify_ok(self, verify: str) -> bool:
        if not verify.strip():
            return False
        lower = verify.lower()
        if "syntax check failed" in lower:
            return False
        if "pytest:** failed" in lower:
            return False
        return "pytest:** passed" in lower











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

    def _enqueue_coding(self, params: dict, message: str) -> dict:
        from jarvis.coding_jobs import submit_coding_agent

        job_id = submit_coding_agent(self, params, message)
        title = (params.get("task") or message)[:80]
        return self._engineering_job_result(
            f"**Coding agent** queued in the background — **{title}**\n\n"
            "Keep chatting; the result appears here when finished.",
            job_id,
            "coding_agent",
        )


    def _enqueue_fix_tests(self, params: dict, message: str) -> dict:
        from jarvis.coding_jobs import submit_fix_tests

        path = self._engineering_resolve_path(params.get('path', '')) or params.get("path", "")
        job_id = submit_fix_tests(self, {**params, "path": path}, message)
        return self._engineering_job_result(
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
