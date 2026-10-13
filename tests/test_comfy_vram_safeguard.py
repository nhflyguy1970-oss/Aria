"""ComfyUI keeps its last model on the RTX after a prompt; ARIA releases it only when idle."""
from __future__ import annotations

import pytest

from jarvis import gpu_scheduler as gs

MiB = 1048576


@pytest.fixture
def comfy(monkeypatch):
    gs.reset_for_tests()
    state = {"held_mib": 4600, "running": [], "pending": [], "posts": [], "free_mib": 3000,
             "frees_work": True}

    def get_json(url, timeout=2.0):
        if url.endswith("/system_stats"):
            return {"devices": [{"torch_vram_total": state["held_mib"] * MiB}]}
        if url.endswith("/queue"):
            return {"queue_running": state["running"], "queue_pending": state["pending"]}
        return {"models": []}

    def post_json(url, body, timeout=30.0):
        state["posts"].append(url)
        if url.endswith("/free") and state["frees_work"]:
            state["held_mib"] = 32
            state["free_mib"] = 12000
        return {}

    monkeypatch.setattr(gs, "_get_json", get_json)
    monkeypatch.setattr(gs, "_post_json", post_json)
    monkeypatch.setattr(gs, "cuda", lambda: {"ok": True, "temp_c": 50, "free_mib": state["free_mib"],
                                             "total_mib": 12288, "used_mib": 12288 - state["free_mib"]})
    monkeypatch.setattr(gs, "amd", lambda: {"ok": True, "temp_c": 40, "free_mib": 7000})
    monkeypatch.setattr(gs, "host_available_mib", lambda: 50_000)
    monkeypatch.setattr(gs, "ftr_busy", lambda eps: [])
    monkeypatch.setattr(gs, "helper_ready", lambda: False)
    monkeypatch.setattr(gs, "model_size", lambda m: 7_600_000_000)
    monkeypatch.setattr(gs, "MONITOR_INTERVAL_S", 0.05)
    monkeypatch.setattr(gs, "RELEASE_SETTLE_S", 0)
    monkeypatch.setattr(gs, "VRAM_SETTLE_S", 3)
    yield state
    gs.reset_for_tests()


def _frees(state):
    return [u for u in state["posts"] if u.endswith("/free")]


def test_idle_residue_is_freed_before_a_chat_when_the_rtx_is_short(comfy):
    with gs.admit_ollama("gemma4:12b", label="chat"):
        pass
    assert len(_frees(comfy)) == 1
    assert any(e["event"] == "comfy_freed" and e["mib"] == 4600 for e in gs.SCHEDULER._events)


def test_chat_with_plenty_of_free_vram_does_not_touch_comfyui(comfy):
    comfy["free_mib"] = 9000
    with gs.admit_ollama("gemma4:12b", label="chat"):
        pass
    assert _frees(comfy) == []


@pytest.mark.parametrize("busy", ["running", "pending"])
def test_a_queued_comfyui_prompt_is_never_interrupted(comfy, busy):
    comfy[busy] = [[1, "prompt-id"]]  # e.g. queued from ComfyUI's own web UI
    assert gs.SCHEDULER._free_idle_comfy("test") == 0
    assert _frees(comfy) == []


def test_small_residue_is_left_alone(comfy):
    comfy["held_mib"] = 192  # CUDA context only
    assert gs.SCHEDULER._free_idle_comfy("test") == 0


def test_an_admitted_image_job_is_never_freed_by_someone_else(comfy):
    with gs.admit_image(label="image"):
        comfy["posts"].clear()
        assert gs.SCHEDULER._free_idle_comfy("chat") == 0
    assert _frees(comfy) == ["http://127.0.0.1:8188/free"]  # only admit_image's own release


def test_image_admission_clears_stale_residue_for_itself(comfy):
    comfy["free_mib"] = 3000  # stale SDXL residue: Flux would not fit
    with gs.admit_image(label="jarvis_edit_klein"):
        pass
    assert any(e["event"] == "comfy_freed" for e in gs.SCHEDULER._events)


def test_settle_timeout_warns_and_asks_again(comfy, monkeypatch, caplog):
    monkeypatch.setattr(gs, "RELEASE_SETTLE_S", 0.2)
    comfy["frees_work"] = False
    comfy["free_mib"], comfy["held_mib"] = 12000, 32  # clean start; the job's residue is not returned
    with gs.admit_image(label="gallery"):
        comfy["free_mib"] = 7600
    assert len(_frees(comfy)) == 2
    assert "re-sending /free" in caplog.text
