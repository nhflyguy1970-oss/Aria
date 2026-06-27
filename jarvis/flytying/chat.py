"""Dedicated fly-tying chat — RAG-backed from Blackfly scraped/gold JSONL only."""

from __future__ import annotations

import json
import os
from typing import Any, Iterator

from jarvis.config import DATA_DIR
from jarvis.flytying.config import blackfly_data_available, recipe_source_path

SETTINGS_FILE = DATA_DIR / "flytying_settings.json"
MAX_RAG_CHARS = 6000


def get_model_setting() -> dict[str, Any]:
    saved = ""
    if SETTINGS_FILE.is_file():
        try:
            saved = str(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")).get("model") or "").strip()
        except (OSError, json.JSONDecodeError):
            pass
    env_default = (os.environ.get("JARVIS_FLYTYING_MODEL") or "").strip()
    return {
        "model": saved or env_default or "qwen2.5:7b",
        "saved": saved,
        "env_default": env_default,
        "recommended": "qwen2.5:7b",
    }


def set_model_setting(model: str) -> dict[str, Any]:
    model = (model or "").strip()
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {}
    if SETTINGS_FILE.is_file():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
    data["model"] = model
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"model": model, "saved": model}


def flytying_model(*, override: str | None = None) -> str:
    if override and str(override).strip():
        return str(override).strip()
    return get_model_setting()["model"]


def _blackfly_rag_context(question: str, *, fly_type: str | None = None, limit: int = 4) -> tuple[str, list[dict[str, Any]]]:
    from jarvis.flytying import bridge

    hits = bridge.search_recipes(question, fly_type=fly_type, limit=limit, semantic=True)
    blocks: list[str] = []
    for hit in hits:
        rid = str(hit.get("recipe_id") or hit.get("name") or "")
        row = bridge.get_recipe(rid)
        if row and row.get("formatted"):
            blocks.append(str(row["formatted"]))
        elif hit.get("name"):
            blocks.append(f"- {hit.get('name')} ({hit.get('type') or '?'})")
    blob = "\n\n".join(blocks)
    return blob[:MAX_RAG_CHARS], hits


def chat_turn(
    messages: list[dict[str, Any]],
    *,
    fly_type: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    if not blackfly_data_available():
        return {
            "ok": False,
            "message": f"Blackfly scraped database not found at {recipe_source_path()}",
            "answer": "",
            "recipes": [],
        }

    question = ""
    for msg in reversed(messages or []):
        if msg.get("role") == "user":
            question = str(msg.get("content") or "")
            break

    context, hits = _blackfly_rag_context(question, fly_type=fly_type) if question else ("", [])
    chosen_model = flytying_model(override=model)

    if _prepare_semantic_rag(question):
        try:
            from blackfly_rag import answer_question

            answer = answer_question(question, fly_type=fly_type, model=chosen_model)
            if answer:
                return {"ok": True, "answer": answer, "recipes": hits, "model": chosen_model, "source": "blackfly_rag"}
        except Exception:
            pass

    try:
        from jarvis.llm import ask

        prompt = (
            "You are a fly-tying assistant. Answer ONLY from the Blackfly recipe library excerpts below. "
            "If the library lacks the answer, say so.\n\n"
            f"Question: {question}\n\nLibrary excerpts:\n{context or '(no matching patterns)'}"
        )
        answer = ask(chosen_model, [{"role": "user", "content": prompt}])
    except Exception as exc:
        return {"ok": False, "message": str(exc), "answer": "", "recipes": hits}
    return {"ok": True, "answer": answer, "recipes": hits, "model": chosen_model, "source": "blackfly_jsonl"}


def _prepare_semantic_rag(question: str) -> bool:
    if not question.strip():
        return False
    from jarvis.flytying.config import ensure_blackfly_on_path

    ensure_blackfly_on_path()
    try:
        import blackfly_rag  # noqa: F401

        return True
    except Exception:
        return False


def chat_turn_stream(
    messages: list[dict[str, Any]],
    *,
    fly_type: str | None = None,
    model: str | None = None,
) -> Iterator[str]:
    result = chat_turn(messages, fly_type=fly_type, model=model)
    text = result.get("answer") or result.get("message") or ""
    yield f"data: {json.dumps({'text': text, 'recipes': result.get('recipes') or []})}\n\n"
