"""Chat while the RTX 3060 renders: answer on the RX 7600 helper instead of waiting.

An image job holds the RTX exclusively, and ARIA's chat models (gemma4:12b 8.6 GB,
deepseek-r1:14b 10.7 GB) are too large for the RX 7600 helper lane, so a chat turn sent
during an image waited for the whole render and then a cold reload (101.8 s live,
2026-10-14). Measured on the RX 7600 (eight everyday questions + a 3-turn continuity
check): qwen3:4b-instruct-2507 answered all correctly with a 0.8 s median and 88 tok/s in
3.0 GB; smaller candidates got the arithmetic wrong. So while an exclusive RTX job runs,
a Regular-mode chat turn is answered there, with the reply saying so.

Never used when the owner picked a chat model, in Uncensored mode (its abliterated model
stays the only Uncensored chat model), or when the helper is down, busy, hot or full —
then the turn waits for the RTX as before.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator

HELPER_CTX = 4096
HELPER_PREDICT = 1024
NOTE = "_(Answered by {model} on the RX 7600 while the RTX 3060 renders an image.)_"


def helper_chat_model() -> str:
    env = os.getenv("JARVIS_HELPER_CHAT_MODEL", "qwen3:4b-instruct-2507-q4_K_M").strip()
    return "" if env.lower() in ("", "0", "off", "false", "no") else env


@dataclass
class Lane:
    model: str
    note: str
    kwargs: dict[str, Any] = field(default_factory=dict)

    @contextmanager
    def scope(self) -> Iterator[None]:
        from jarvis import gpu_scheduler

        with gpu_scheduler.prefer_helper("chat while the RTX 3060 runs an exclusive job", required=True):
            yield

    def fit(self, messages: list[dict]) -> list[dict]:
        """Keep the system prompt and the newest turns that fit the helper's 4K window."""
        from jarvis.conversation import estimate_tokens

        budget = HELPER_CTX - HELPER_PREDICT - 128
        system = [m for m in messages if m.get("role") == "system"][:1]
        rest = [m for m in messages if m.get("role") != "system"]
        used = sum(estimate_tokens(str(m.get("content") or "")) for m in system)
        kept: list[dict] = []
        for m in reversed(rest):
            cost = estimate_tokens(str(m.get("content") or ""))
            if kept and used + cost > budget:
                break
            kept.insert(0, m)
            used += cost
        return system + kept


COLD_NOTE = "_(Answered by {model} on the RX 7600 while {big} loads on the RTX 3060.)_"


def rtx_busy() -> bool:
    """An exclusive RTX job runs or waits — or a media job is queued/running and about to
    claim the RTX (a chat sent right after an image request raced its admission and then
    queued behind the whole render, 80 s live)."""
    from jarvis import gpu_scheduler

    st = gpu_scheduler.status()
    if st.get("heavy_active") or st.get("heavy_waiting"):
        return True
    try:
        from jarvis.media_jobs import busy_state

        media = busy_state()
        return bool(media.get("busy") or media.get("pending"))
    except Exception:  # noqa: BLE001
        return False


def rtx_resident(model: str) -> bool:
    from jarvis import gpu_scheduler

    data = gpu_scheduler._get_json(f"{gpu_scheduler.DEFAULT_OLLAMA}/api/ps", timeout=2.0) or {}
    names = {str(m.get("name") or m.get("model") or "") for m in data.get("models") or []}
    return model in names or f"{model}:latest" in names


def _warm_in_background(model: str) -> None:
    import threading

    def run() -> None:
        from jarvis import gpu_scheduler, ollama_runtime

        if not gpu_scheduler.defer_direct_load(model):
            ollama_runtime.warmup_chat_model(model=model)

    threading.Thread(target=run, name="chat-cold-warm", daemon=True).start()


def lane_for(chat_model: str, *, explicit: bool, role: str = "conversation") -> Lane | None:
    """The RX 7600 lane for this turn, or None to use ``chat_model`` as usual.

    Used while the RTX is busy (any role), and for an everyday (conversation-role) turn whose
    RTX model is not loaded — e.g. right after an image evicted it: that turn is answered on
    the RX 7600 while the RTX model loads in the background for the next one. Reasoning and
    specialist turns still wait for their model when the RTX is merely cold."""
    helper = helper_chat_model()
    if not helper or explicit or chat_model == helper:
        return None
    try:
        from jarvis.config import is_uncensored

        if is_uncensored():
            return None
    except Exception:  # noqa: BLE001
        return None
    from jarvis import gpu_scheduler

    if not gpu_scheduler.helper_ready() or gpu_scheduler.model_size(helper) <= 0:
        return None
    label = helper.split(":")[0] + " 4B" if "4b" in helper else helper
    kwargs = {"options": {"num_ctx": HELPER_CTX, "num_predict": HELPER_PREDICT}, "think": False, "explicit_model": True}
    if rtx_busy():
        return Lane(model=helper, note=NOTE.format(model=label), kwargs=kwargs)
    cold_ok = os.getenv("JARVIS_HELPER_CHAT_WHEN_COLD", "1").strip().lower() not in ("0", "false", "no", "off")
    from jarvis.inference.boundary import needs_local_runtime

    if cold_ok and role == "conversation" and needs_local_runtime(chat_model) and not rtx_resident(chat_model):
        _warm_in_background(chat_model)
        return Lane(model=helper, note=COLD_NOTE.format(model=label, big=chat_model), kwargs=kwargs)
    return None
