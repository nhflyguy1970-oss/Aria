import base64
import io
import os
from pathlib import Path

from jarvis import fs, llm
from jarvis.config import DATA_DIR, PROJECT_ROOT
from jarvis.conversation import Conversation

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
MAX_VISION_PIXELS = int(os.getenv("JARVIS_VISION_MAX_PIXELS", "1280"))
VISION_JPEG_QUALITY = int(os.getenv("JARVIS_VISION_JPEG_QUALITY", "85"))
VISION_KEEP_ALIVE = int(os.getenv("JARVIS_VISION_KEEP_ALIVE", "0"))

COMPARE_DESCRIBE_PROMPT = (
    "Describe ONLY this one image. Include subjects, colors, visible text, layout, "
    "and distinctive details. Do not mention other images or comparisons."
)

COMPARE_SYNTHESIS_SYSTEM = (
    "You compare two images using two independent vision descriptions. "
    "Base your answer ONLY on those descriptions. "
    "If they describe the same scene, say they look the same. "
    "If they differ, list concrete differences. Never invent details missing from the descriptions."
)


def _resolve_image_path(path: str) -> Path:
    """Resolve an image path; never map a distinct upload to another file by basename."""
    seen: set[str] = set()
    candidates: list[Path] = []

    def add(candidate: Path) -> None:
        key = str(candidate)
        if key in seen:
            return
        seen.add(key)
        candidates.append(candidate)

    raw = Path(path).expanduser()
    if raw.is_absolute():
        add(raw.resolve())

    try:
        add(fs.resolve_path(path, base=PROJECT_ROOT))
    except fs.PathError:
        pass

    upload = (DATA_DIR / "uploads" / Path(path).name).resolve()
    if DATA_DIR.resolve() in upload.parents:
        add(upload)

    for resolved in candidates:
        if resolved.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if resolved.exists():
            return resolved

    raise FileNotFoundError(f"File not found: {path}")


def _prepare_image_b64(path: Path, cache: dict[tuple[str, int], str]) -> str:
    resolved = path.resolve()
    try:
        mtime = resolved.stat().st_mtime_ns
    except OSError as e:
        raise ValueError(f"Cannot read image: {resolved}") from e

    key = (str(resolved), mtime)
    cached = cache.get(key)
    if cached:
        return cached

    from PIL import Image

    with Image.open(resolved) as img:
        img = img.convert("RGB")
        width, height = img.size
        longest = max(width, height)
        if longest > MAX_VISION_PIXELS:
            scale = MAX_VISION_PIXELS / longest
            img = img.resize(
                (max(1, int(width * scale)), max(1, int(height * scale))),
                Image.Resampling.LANCZOS,
            )
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=VISION_JPEG_QUALITY, optimize=True)
        encoded = base64.b64encode(buf.getvalue()).decode("ascii")

    cache[key] = encoded
    return encoded


class VisionEngine:
    def __init__(self):
        self.conversation = Conversation(
            "You are Jarvis Vision. Describe and analyze images accurately."
        )
        self.current_image: Path | None = None
        self._session_image: Path | None = None
        self._image_cache: dict[tuple[str, int], str] = {}

    def _encode_image(self, path: Path) -> str:
        try:
            return _prepare_image_b64(path, self._image_cache)
        except (OSError, ValueError) as e:
            raise ValueError(f"Cannot prepare image: {e}") from e

    def load_image(self, path: str) -> str:
        try:
            self.current_image = _resolve_image_path(path)
            return "OK"
        except Exception as e:
            return f"ERROR: {e}"

    def _reset_session_if_image_changed(self, path: Path) -> None:
        if self._session_image and self._session_image != path:
            self.conversation.clear()
        self._session_image = path
        self.current_image = path

    def _build_ollama_messages(self, path: Path, question: str) -> list[dict]:
        """One vision request with optional prior Q&A as text (image sent once)."""
        prior: list[tuple[str, str]] = [
            (m["content"], m["role"])
            for m in self.conversation.messages
            if m["role"] in ("user", "assistant")
        ]
        if prior:
            lines = []
            for content, role in prior[-4:]:
                label = "User" if role == "user" else "Assistant"
                snippet = content.strip().replace("\n", " ")[:600]
                lines.append(f"{label}: {snippet}")
            prompt = (
                "Previous conversation about this image:\n"
                + "\n".join(lines)
                + f"\n\nFollow-up question: {question}"
            )
        else:
            prompt = question

        return [
            {
                "role": "user",
                "content": prompt,
                "images": [self._encode_image(path)],
            }
        ]

    def _format_vision_error(self, exc: Exception) -> str:
        msg = str(exc)
        if "mllama" in msg.lower() or "unknown model architecture" in msg.lower():
            from jarvis.ollama_health import ollama_version, supports_mllama

            ver = ".".join(str(x) for x in (ollama_version() or (0, 0, 0)))
            if not supports_mllama():
                return (
                    "ERROR: llama3.2-vision needs Ollama 0.24.x "
                    f"(you have {ver}). Ollama 0.30.x dropped mllama support. "
                    "Use moondream/llava in Model settings, or run ./scripts/install-ollama-0.24.sh"
                )
        return f"ERROR: {msg}"

    def _vision_chat(
        self,
        messages: list[dict],
        *,
        stream: bool = False,
        task: str = "describe",
    ):
        from ollama import chat

        model = llm.vision_model_for_task(task)
        if stream:
            return chat(
                model=model,
                messages=messages,
                stream=True,
                options={"keep_alive": VISION_KEEP_ALIVE},
            )
        response = chat(
            model=model,
            messages=messages,
            options={"keep_alive": VISION_KEEP_ALIVE},
        )
        return response["message"]["content"]

    def analyze_stream(self, question: str, image_path: str | None = None, *, task: str = "describe"):
        """Yield text tokens from Ollama vision model."""
        path = self.current_image
        if image_path:
            result = self.load_image(image_path)
            if result.startswith("ERROR:"):
                yield result
                return
            path = self.current_image
        if not path:
            yield "ERROR: No image loaded."
            return
        self._reset_session_if_image_changed(path)
        try:
            messages = self._build_ollama_messages(path, question)
            stream = self._vision_chat(messages, stream=True, task=task)
            full = ""
            for chunk in stream:
                token = chunk.get("message", {}).get("content", "")
                if token:
                    full += token
                    yield token
            if full:
                self.conversation.add_user(question)
                self.conversation.add_assistant(full)
        except Exception as e:
            yield self._format_vision_error(e)

    def ocr(self, image_path: str | None = None) -> str:
        from jarvis.vision_media import OCR_PROMPT
        return self._analyze_task(OCR_PROMPT, image_path, task="ocr")

    def ocr_structured(self, image_path: str | None = None) -> str:
        from jarvis.vision_media import OCR_STRUCTURED_PROMPT
        return self._analyze_task(OCR_STRUCTURED_PROMPT, image_path, task="ocr_structured")

    def image_to_code(self, image_path: str | None = None) -> str:
        from jarvis.vision_media import IMAGE_TO_CODE_PROMPT
        return self._analyze_task(IMAGE_TO_CODE_PROMPT, image_path, task="image_to_code")

    def _analyze_task(self, question: str, image_path: str | None, *, task: str) -> str:
        path = self.current_image
        if image_path:
            result = self.load_image(image_path)
            if result.startswith("ERROR:"):
                return result
            path = self.current_image
        if not path:
            return "ERROR: No image loaded."
        self._reset_session_if_image_changed(path)
        try:
            messages = self._build_ollama_messages(path, question)
            answer = self._vision_chat(messages, task=task)
            self.conversation.add_user(question)
            self.conversation.add_assistant(answer)
            return answer
        except ValueError as e:
            return f"ERROR: {e}"
        except Exception as e:
            return self._format_vision_error(e)

    def analyze(self, question: str, image_path: str | None = None, *, task: str = "describe") -> str:
        path = self.current_image
        if image_path:
            result = self.load_image(image_path)
            if result.startswith("ERROR:"):
                return result
            path = self.current_image

        if not path:
            return "ERROR: No image loaded. Use: load <path>"

        self._reset_session_if_image_changed(path)

        try:
            messages = self._build_ollama_messages(path, question)
            answer = self._vision_chat(messages, task=task)
            self.conversation.add_user(question)
            self.conversation.add_assistant(answer)
            return answer
        except ValueError as e:
            return f"ERROR: {e}"
        except Exception as e:
            return self._format_vision_error(e)

    def _analyze_isolated(self, path: Path, question: str, *, task: str = "describe") -> str:
        """Single vision call without conversation history (for compare passes)."""
        messages = [
            {"role": "user", "content": question, "images": [self._encode_image(path)]},
        ]
        return self._vision_chat(messages, task=task)

    def compare_events(
        self,
        path1: str,
        path2: str,
        question: str | None = None,
        *,
        uploads_dir: Path | None = None,
    ):
        """Yield (event_type, payload) for compare progress + result."""
        user_q = (question or "").strip()
        if user_q.lower() in (
            "",
            "please analyze the attached file.",
            "(attachment)",
            "compare these two images.",
            "compare these two images. describe similarities and differences.",
        ):
            user_q = "Compare both images: describe similarities and differences."
        try:
            img1 = _resolve_image_path(path1)
            img2 = _resolve_image_path(path2)
            if img1.resolve() == img2.resolve():
                yield ("error", "Both attachments are the same file. Attach two different images.")
                return

            probe1 = _prepare_image_b64(img1, {})
            probe2 = _prepare_image_b64(img2, {})
            if probe1 == probe2:
                yield (
                    "error",
                    "Both attachments look identical. Pick two different images.",
                )
                return

            yield ("status", "Analyzing image 1/2…")
            desc1 = self._analyze_isolated(img1, COMPARE_DESCRIBE_PROMPT, task="describe")
            if desc1.startswith("ERROR:"):
                yield ("error", desc1)
                return

            yield ("status", "Analyzing image 2/2…")
            desc2 = self._analyze_isolated(img2, COMPARE_DESCRIBE_PROMPT, task="describe")
            if desc2.startswith("ERROR:"):
                yield ("error", desc2)
                return

            diff_path = None
            if uploads_dir:
                yield ("status", "Building visual diff…")
                from jarvis.vision_media import build_visual_diff
                diff_path = build_visual_diff(img1, img2, uploads_dir)

            yield ("status", "Synthesizing comparison…")
            synthesis_user = (
                f"Image A ({img1.name}):\n{desc1}\n\n"
                f"Image B ({img2.name}):\n{desc2}\n\n"
                f"Task: {user_q}"
            )
            answer = llm.ask_with_system(
                llm.general_model(),
                COMPARE_SYNTHESIS_SYSTEM,
                synthesis_user,
            )
            text = f"**Compared {img1.name} ↔ {img2.name}**\n\n{answer.strip()}"
            yield ("result", {
                "answer": text,
                "path1": str(img1),
                "path2": str(img2),
                "diff_path": str(diff_path) if diff_path else None,
            })
        except ValueError as e:
            yield ("error", f"ERROR: {e}")
        except Exception as e:
            yield ("error", f"ERROR: {e}")

    def compare(
        self,
        path1: str,
        path2: str,
        question: str | None = None,
        *,
        uploads_dir: Path | None = None,
    ) -> dict:
        for kind, payload in self.compare_events(
            path1, path2, question, uploads_dir=uploads_dir,
        ):
            if kind == "error":
                return {"answer": payload, "diff_path": None, "path1": path1, "path2": path2}
            if kind == "result":
                return payload
        return {"answer": "ERROR: Compare failed.", "diff_path": None, "path1": path1, "path2": path2}

    def handle(self, prompt: str) -> bool:
        if prompt.lower() == "exit":
            return False

        if prompt.startswith("load "):
            result = self.load_image(prompt[5:].strip())
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print(f"\nImage loaded: {self.current_image}\n")
            return True

        if prompt == "describe":
            answer = self.analyze("Describe this image in detail.")
            print()
            print(answer)
            print()
            return True

        if prompt.startswith("analyze "):
            question = prompt[8:].strip()
            answer = self.analyze(question)
            if answer.startswith("ERROR:"):
                print(f"\n{answer}\n")
            else:
                print()
                print(answer)
                print()
            return True

        if prompt.startswith("compare "):
            paths = prompt[8:].strip().split(maxsplit=1)
            if len(paths) < 2:
                print("\nUsage: compare <image1> <image2>\n")
                return True
            compare_result = self.compare(paths[0], paths[1])
            answer = compare_result.get("answer", "")
            if answer.startswith("ERROR:"):
                print(f"\n{answer}\n")
            else:
                print()
                print(answer)
                print()
            return True

        if prompt == "clear":
            self.current_image = None
            self._session_image = None
            self.conversation.clear()
            print("\nCleared.\n")
            return True

        if self.current_image:
            answer = self.analyze(prompt)
            if answer.startswith("ERROR:"):
                print(f"\n{answer}\n")
            else:
                print()
                print(answer)
                print()
            return True

        print("\nLoad an image first: load <path>\n")
        return True


def main():
    engine = VisionEngine()
    print("\nJarvis Vision Module")
    print("Type 'exit' to quit.")
    print("Commands:")
    print("  load <path>           load an image")
    print("  describe              describe loaded image")
    print("  analyze <question>    ask about loaded image")
    print("  compare <img1> <img2> compare two images")
    print("  clear                 reset state")
    print(f"  Model: {llm.vision_model()}\n")

    while True:
        try:
            prompt = input("Vision > ")
            if not engine.handle(prompt):
                break
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"\nERROR: {e}\n")
