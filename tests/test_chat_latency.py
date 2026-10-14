"""Chat responsiveness (2026-10-14).

* Short everyday questions use the conversation model (gemma4:12b), not deepseek-r1:14b.
* Chat during an RTX image job is answered on the RX 7600 helper instead of waiting.
* Models an image job evicted are restored afterwards, unless another job wants the RTX.
* The provider-stream reader thread inherits the request context.
"""
from __future__ import annotations

import contextvars
import threading
import time
from unittest.mock import patch

import pytest

from jarvis import gpu_scheduler as gs

HELPER = "qwen3:4b-instruct-2507-q4_K_M"


# Routing ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("message", [
    "why is the sky blue?", "In one sentence, what is a trout?", "explain how a jet engine works",
    "Who wrote Moby Dick, and roughly when was it published?", "tell me a joke",
])
def test_everyday_questions_use_the_conversation_model(message):
    from jarvis.capability_routing import resolve_conversation_model
    from jarvis.model_store import model_for

    model, role = resolve_conversation_model(message, {"knowledge_mode": True} if "what is" in message else {},
                                             action="chat")
    assert (model, role) == (model_for("conversation"), "conversation")


@pytest.mark.parametrize("message", [
    "compare the pros and cons of SSDs vs HDDs for a NAS",
    "why does my python script throw a KeyError when reading a dict?",
    "prove that the square root of 2 is irrational",
    "explain in detail how a jet engine works",
    "how many cores does a Ryzen 5600X have?",
    "Why is the sky blue? And why are sunsets red?",
])
def test_reasoning_questions_keep_the_reasoning_model(message):
    from jarvis.brain_routing import reasoning_model
    from jarvis.capability_routing import resolve_conversation_model

    model, role = resolve_conversation_model(message, {}, action="chat")
    assert role in ("reasoning", "specialist")
    if role == "reasoning":
        assert model == reasoning_model()


def test_deep_mode_and_the_setting_restore_reasoning_routing(monkeypatch):
    from jarvis.brain_routing import reasoning_model
    from jarvis.capability_routing import resolve_conversation_model

    assert resolve_conversation_model("why is the sky blue?", {"thinking_mode": "deep"}, action="chat")[0] == reasoning_model()
    monkeypatch.setenv("JARVIS_SIMPLE_QUESTIONS_ON_CONVERSATION", "0")
    assert resolve_conversation_model("why is the sky blue?", {}, action="chat")[0] == reasoning_model()


def test_a_chosen_chat_model_is_respected():
    from jarvis.capability_routing import resolve_conversation_model

    assert resolve_conversation_model("why is the sky blue?", {}, session_chat_model="deepseek-r1:14b",
                                      action="chat")[0] == "deepseek-r1:14b"


# RX 7600 chat lane -----------------------------------------------------------------------------------
@pytest.fixture
def lanes(monkeypatch):
    state = {"heavy": "jarvis", "helper": True, "size": 2_500_000_000, "uncensored": False}
    monkeypatch.setattr(gs, "status", lambda: {"heavy_active": state["heavy"], "heavy_waiting": 0})
    monkeypatch.setattr(gs, "helper_ready", lambda: state["helper"])
    monkeypatch.setattr(gs, "model_size", lambda m: state["size"])
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: state["uncensored"])
    monkeypatch.setattr("jarvis.media_jobs.busy_state", lambda: {"busy": False, "pending": 0})
    monkeypatch.setattr("jarvis.chat_lanes.rtx_resident", lambda model: True)
    monkeypatch.setenv("JARVIS_HELPER_CHAT_MODEL", HELPER)
    return state


def test_lane_is_used_only_while_the_rtx_runs_an_exclusive_job(lanes):
    from jarvis.chat_lanes import lane_for

    lane = lane_for("gemma4:12b", explicit=False)
    assert lane.model == HELPER and lane.kwargs["options"]["num_ctx"] == 4096 and lane.kwargs["explicit_model"]
    lanes["heavy"] = None
    assert lane_for("gemma4:12b", explicit=False) is None


@pytest.mark.parametrize("change", [{"helper": False}, {"size": 0}, {"uncensored": True}])
def test_lane_is_not_used_without_a_ready_helper_or_in_uncensored_mode(lanes, change):
    from jarvis.chat_lanes import lane_for

    lanes.update(change)
    assert lane_for("gemma4:12b", explicit=False) is None


def test_lane_respects_a_chosen_model(lanes):
    from jarvis.chat_lanes import lane_for

    assert lane_for("gemma4:12b", explicit=True) is None


def test_lane_keeps_the_system_prompt_and_newest_turns_within_4k():
    from jarvis.chat_lanes import Lane
    from jarvis.conversation import estimate_tokens

    msgs = [{"role": "system", "content": "You are Aria."}]
    for i in range(30):
        msgs += [{"role": "user", "content": f"question {i} " + "x" * 600}, {"role": "assistant", "content": "y" * 400}]
    msgs.append({"role": "user", "content": "the newest question"})
    fitted = Lane(model=HELPER, note="").fit(msgs)
    assert fitted[0]["role"] == "system" and fitted[-1]["content"] == "the newest question"
    assert sum(estimate_tokens(m["content"]) for m in fitted) <= 4096 - 1024


def _engine(assistant):
    from jarvis.behaviors.conversation import ConversationEngine

    return ConversationEngine(assistant)


def test_chat_during_an_image_is_answered_on_the_helper(assistant, lanes):
    calls = []

    def ask(model, msgs, **kw):
        calls.append((model, gs._PREFER_HELPER.get(), gs._HELPER_REQUIRED.get(), kw.get("options")))
        return "A trout is a fish.", {}

    with patch("jarvis.llm.ask_with_usage", side_effect=ask), \
            patch("jarvis.behaviors.conversation.check_ollama", return_value={"running": True}):
        out = _engine(assistant).execute({}, "tell me a joke")
    assert calls[0][0] == HELPER and calls[0][1] and calls[0][2] is True and calls[0][3]["num_ctx"] == 4096
    assert "RX 7600" in out["message"] and len(calls) == 1


def test_chat_waits_for_the_rtx_when_the_helper_refuses(assistant, lanes):
    calls = []

    def ask(model, msgs, **kw):
        calls.append(model)
        if model == HELPER:
            raise gs.GpuUnavailable("the RX 7600 helper lane is unavailable")
        return "Here's one.", {}

    with patch("jarvis.llm.ask_with_usage", side_effect=ask), \
            patch("jarvis.behaviors.conversation.check_ollama", return_value={"running": True}):
        out = _engine(assistant).execute({}, "tell me a joke")
    assert calls[0] == HELPER and len(calls) == 2 and calls[1] != HELPER
    assert out["message"].startswith("Here's one.") and "RX 7600" not in out["message"]


def _stream_run(assistant, ask_stream):
    with patch("jarvis.llm.ask_stream", side_effect=ask_stream), \
            patch("jarvis.behaviors.conversation.check_ollama", return_value={"running": True}), \
            patch("jarvis.ollama_runtime.ensure_chat_model_ready", return_value={"ok": True}):
        return list(_engine(assistant).execute_stream("tell me a joke", {}, request_id="req-lane"))


def test_streamed_chat_during_an_image_uses_the_helper(assistant, lanes):
    seen = []

    def ask_stream(model, msgs, **kw):
        seen.append((model, gs._HELPER_REQUIRED.get()))
        yield "Why did the "
        yield "trout cross the road?"

    events = _stream_run(assistant, ask_stream)
    text = "".join(e.get("content", "") for e in events if e.get("type") == "token")
    assert seen == [(HELPER, True)] and "trout cross the road" in text and "RX 7600" in text
    assert gs._HELPER_REQUIRED.get() is False  # the preference ends after admission


def test_streamed_chat_falls_back_to_the_rtx_model(assistant, lanes):
    seen = []

    def ask_stream(model, msgs, **kw):
        seen.append(model)
        if model == HELPER:
            raise RuntimeError("helper lane unavailable")
        yield "A joke."

    events = _stream_run(assistant, ask_stream)
    assert seen == [HELPER, "gemma4:12b"]
    assert "".join(e.get("content", "") for e in events if e.get("type") == "token") == "A joke."


def test_stream_reader_thread_inherits_the_request_context():
    from jarvis.llm import _iter_blocking_cancellable

    var = contextvars.ContextVar("probe", default="unset")
    seen = []

    def stream():
        seen.append(var.get())
        yield "x"

    token = var.set("request")
    try:
        assert list(_iter_blocking_cancellable(stream())) == ["x"]
    finally:
        var.reset(token)
    assert seen == ["request"]


# Restoring evicted models after an image ---------------------------------------------------------------
@pytest.fixture
def sched(monkeypatch):
    gs.reset_for_tests()
    state = {"resident": ["gemma4:12b", "nomic-embed-text:latest"], "posts": [], "warmed": [], "pending": 0}
    monkeypatch.setattr(gs, "cuda", lambda: {"ok": True, "temp_c": 50, "free_mib": 12000, "total_mib": 12288})
    monkeypatch.setattr(gs, "amd", lambda: {"ok": True, "temp_c": 45, "free_mib": 7000})
    monkeypatch.setattr(gs, "host_available_mib", lambda: 60000)
    monkeypatch.setattr(gs, "ftr_busy", lambda eps: [])
    monkeypatch.setattr(gs, "helper_ready", lambda: True)
    monkeypatch.setattr(gs, "comfy_resident_mib", lambda: 0)

    def get_json(url, timeout=2.0):
        if url.endswith("/api/ps"):
            return {"models": [{"name": n} for n in state["resident"]]}
        return {"models": []}

    def post_json(url, body, timeout=30.0):
        state["posts"].append((url, body))
        if body.get("keep_alive") == 0 and body.get("model") in state["resident"]:
            state["resident"].remove(body["model"])
        return {}

    monkeypatch.setattr(gs, "_get_json", get_json)
    monkeypatch.setattr(gs, "_post_json", post_json)
    monkeypatch.setattr(gs, "REWARM_DELAY_S", 0.05)
    monkeypatch.setattr(gs, "RELEASE_SETTLE_S", 0)
    monkeypatch.setattr(gs, "MONITOR_INTERVAL_S", 0.05)
    monkeypatch.setattr("jarvis.ollama_runtime.warmup_chat_model",
                        lambda model=None: state["warmed"].append(model) or {"ok": True})
    monkeypatch.setattr("jarvis.media_jobs.busy_state", lambda: {"pending": state["pending"]})
    yield state
    gs.reset_for_tests()


def _wait(pred, timeout=3.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end and not pred():
        time.sleep(0.02)
    return pred()


def test_models_an_image_job_evicted_are_restored(sched):
    with gs.admit_image(label="jarvis"):
        assert sched["resident"] == []
    assert _wait(lambda: sched["warmed"] == ["gemma4:12b"])
    assert _wait(lambda: any(u.endswith("/api/embed") for u, _ in sched["posts"]))


def test_no_restore_when_another_media_job_is_queued(sched):
    sched["pending"] = 1
    with gs.admit_image(label="jarvis"):
        pass
    time.sleep(0.3)
    assert sched["warmed"] == []


def test_no_restore_while_another_exclusive_job_holds_the_rtx(sched, monkeypatch):
    monkeypatch.setattr(gs, "REWARM_DELAY_S", 0.2)
    release, started = threading.Event(), threading.Event()
    with gs.admit_image(label="first"):
        pass

    def hold():
        with gs.admit_image(label="second"):
            started.set()
            release.wait(3)

    t = threading.Thread(target=hold)
    t.start()
    started.wait(2)
    time.sleep(0.4)
    assert "gemma4:12b" not in sched["warmed"]
    release.set()
    t.join()


def test_rewarm_can_be_disabled(sched, monkeypatch):
    monkeypatch.setattr(gs, "REWARM_DELAY_S", 0)
    with gs.admit_image(label="jarvis"):
        pass
    time.sleep(0.2)
    assert sched["warmed"] == []


# Follow-up regression found during live testing ----------------------------------------------------
@pytest.mark.parametrize("message", ["thanks! one more fly fishing blog name?", "another joke please",
                                     "give me another idea for dinner"])
def test_another_non_image_thing_is_not_an_image_follow_up(tmp_path, message):
    from jarvis.router import route
    from jarvis.session import SessionContext

    s = SessionContext()
    img = tmp_path / "jarvis_00300_.png"
    img.write_bytes(b"png")
    s.note_image(str(img), prompt="a red barn in the snow")
    s.last_action = "chat"
    assert route(message, s)["action"] not in ("generate_image", "edit_image")


def test_a_queued_image_job_already_counts_as_rtx_busy(lanes, monkeypatch):
    """Live 2026-10-14: a chat sent 8 s after an image request raced its admission."""
    from jarvis.chat_lanes import lane_for

    lanes["heavy"] = None
    monkeypatch.setattr("jarvis.media_jobs.busy_state", lambda: {"busy": True, "pending": 0})
    assert lane_for("gemma4:12b", explicit=False).model == HELPER


def test_a_cold_conversation_model_is_answered_on_the_helper_while_it_loads(lanes, monkeypatch):
    from jarvis import chat_lanes

    lanes["heavy"] = None
    warmed = []
    monkeypatch.setattr(chat_lanes, "rtx_resident", lambda model: False)
    monkeypatch.setattr(chat_lanes, "_warm_in_background", lambda model: warmed.append(model))
    lane = chat_lanes.lane_for("gemma4:12b", explicit=False, role="conversation")
    assert lane.model == HELPER and "loads on the RTX 3060" in lane.note and warmed == ["gemma4:12b"]
    # Reasoning turns wait for their own model; a loaded model is used directly.
    assert chat_lanes.lane_for("deepseek-r1:14b", explicit=False, role="reasoning") is None
    monkeypatch.setattr(chat_lanes, "rtx_resident", lambda model: True)
    assert chat_lanes.lane_for("gemma4:12b", explicit=False, role="conversation") is None


def test_the_cold_lane_can_be_disabled(lanes, monkeypatch):
    from jarvis import chat_lanes

    lanes["heavy"] = None
    monkeypatch.setattr(chat_lanes, "rtx_resident", lambda model: False)
    monkeypatch.setenv("JARVIS_HELPER_CHAT_WHEN_COLD", "0")
    assert chat_lanes.lane_for("gemma4:12b", explicit=False, role="conversation") is None


def test_tests_never_reach_the_live_helper_by_default():
    import os

    assert os.environ.get("JARVIS_HELPER_CHAT_MODEL") == "off"


def test_models_unloaded_before_the_image_job_are_restored_too(sched):
    """Live 2026-10-14: vram_guard unloaded gemma4 before admission, so only the embedding
    model (unloaded by admission) came back."""
    gs.note_evicted(["gemma4:12b"])
    sched["resident"] = ["nomic-embed-text:latest"]
    with gs.admit_image(label="jarvis"):
        pass
    assert _wait(lambda: sched["warmed"] == ["gemma4:12b"])


def test_vram_guard_reports_what_it_unloaded(monkeypatch):
    from jarvis import vram_guard

    noted = []
    monkeypatch.setattr(vram_guard, "vram_guard_enabled", lambda: True)
    monkeypatch.setattr(vram_guard, "unload_ollama_models", lambda: ["gemma4:12b"])
    monkeypatch.setattr(vram_guard, "release_torch_memory", lambda: None)
    monkeypatch.setattr(gs, "note_evicted", lambda models: noted.extend(models))
    vram_guard.prepare_for_comfyui()
    assert noted == ["gemma4:12b"]


def test_unloading_for_an_image_never_runs_a_generation(monkeypatch):
    """vram_guard used prompt "." — an 8 s generation on the chat model before every image,
    then HTTP 500, so the unload was never reported (and the model never restored)."""
    import io
    import json as _json

    from jarvis import ml_memory

    sent = []

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def urlopen(req, timeout=8.0):
        if isinstance(req, str):
            return Resp(_json.dumps({"models": [{"name": "gemma4:12b"}, {"name": "nomic-embed-text:latest"}]}).encode())
        sent.append((req.full_url, _json.loads(req.data)))
        return Resp(b"{}")

    monkeypatch.setenv("OLLAMA_HOST", "0.0.0.0:11434")
    monkeypatch.setattr(ml_memory.urllib.request, "urlopen", urlopen)
    assert ml_memory.unload_ollama_models() == ["gemma4:12b", "nomic-embed-text:latest"]
    assert sent[0] == ("http://127.0.0.1:11434/api/generate", {"model": "gemma4:12b", "keep_alive": 0})
    assert sent[1][0].endswith("/api/embed") and sent[1][1]["keep_alive"] == 0


def test_helper_refusals_say_why(sched, monkeypatch):
    monkeypatch.setattr(gs, "amd", lambda: {"ok": True, "temp_c": 45, "free_mib": 1500})
    monkeypatch.setattr(gs, "model_size", lambda m: 2_500_000_000)
    with pytest.raises(gs.GpuUnavailable):
        with gs.prefer_helper("chat", required=True):
            with gs.admit_ollama(HELPER, {"num_ctx": 4096, "num_predict": 512}):
                pass
    refusals = [e for e in gs.status()["recent"] if e["event"] == "helper_refused"]
    assert refusals and "MiB free" in refusals[-1]["reason"]


# Response metadata names the GPU that actually answered -------------------------------------------
@pytest.mark.parametrize("on_helper,expected", [(True, "amd"), (False, None)])
@pytest.mark.parametrize("streamed", [False, True])
def test_execution_hardware_reports_the_rx7600_for_helper_turns(monkeypatch, on_helper, expected, streamed):
    from contextlib import contextmanager
    from types import SimpleNamespace

    from jarvis.inference import gateway

    @contextmanager
    def admit(model, options=None, *, label=""):
        yield SimpleNamespace(kind="helper" if on_helper else "shared", host=gs.HELPER_URL if on_helper else None,
                              options={}, check=lambda: None)

    def client_chat(job):
        def chat(**kw):
            return iter([{"message": {"content": "hi"}, "done": True, "eval_count": 1}])
        return chat

    monkeypatch.setattr(gs, "admit_ollama", admit)
    monkeypatch.setattr(gateway, "_ollama_client_chat", client_chat)
    msgs = [{"role": "user", "content": "hello"}]
    if streamed:
        usage: dict = {}
        assert "".join(gateway.stream_chat(HELPER, msgs, role="conversation", usage=usage, explicit_model=True)) == "hi"
    else:
        _, usage = gateway.chat_with_usage(HELPER, msgs, role="conversation", explicit_model=True)
    if expected:
        assert usage["execution_hardware"] == "amd" and "RX 7600" in usage["execution_device"]
    else:
        assert usage["execution_hardware"] != "amd" and "execution_device" not in usage
