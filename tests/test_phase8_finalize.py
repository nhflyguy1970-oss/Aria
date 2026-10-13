"""Phase 8 closure: chat approval authority and coding-agent routing with file names."""
from __future__ import annotations

import pytest

from jarvis.action_routing import is_coding_agent_request


def test_chat_start_asks_owner_for_git_write_step_up(monkeypatch):
    from jarvis.handlers import coding_agent_cli_handlers as cli
    from jarvis.security.owner import provider_credentials

    seen = {}

    class Owner:
        def authorize(self, capability, *, room=None, session_token=None):
            seen.update(capability=capability, room=room)
            return {"ok": False, "reason": "Step-up authentication required"}

    monkeypatch.setattr(provider_credentials, "bound_owner_service", lambda: Owner())
    assert cli._owner_step_up() == {"ok": False, "reason": "Step-up authentication required"}
    assert seen == {"capability": "git.write", "room": "coding"}


@pytest.mark.parametrize("message,agent_request", [
    ("Use Codex on the ARIA project in read-only mode: read pyproject.toml and report the name.", True),
    ("Ask Codex to read jarvis/comfyui.py and explain run_workflow", True),
    ("Have Claude review tests/test_x.py", True),
    ("read pyproject.toml", False),
    ("open ~/Documents/notes.txt", False),
    ("can you read the codex docs in notes.md", False),
])
def test_agent_requests_with_file_names_are_recognised(message, agent_request):
    assert is_coding_agent_request(message) is agent_request


@pytest.mark.parametrize("message,action", [
    ("Use Codex on the ARIA project in read-only mode: read pyproject.toml and report the name.", "coding_agent_plan"),
    ("Ask Codex to read jarvis/comfyui.py and explain run_workflow", "coding_agent_plan"),
    ("read pyproject.toml", "coding_read"),
    ("load config.yaml", "coding_read"),
])
def test_file_mentions_route_to_codex_only_when_addressed_to_it(message, action):
    from jarvis.router import route
    from jarvis.session import SessionContext

    assert route(message, SessionContext())["action"] == action


# ---------------------------------------------------------------- GPU scheduler (all probes stubbed)

import threading  # noqa: E402
import time  # noqa: E402

from jarvis import gpu_scheduler as gs  # noqa: E402

BIG = "huihui_ai/qwen3.8-abliterated:27b"


@pytest.fixture
def gpu(monkeypatch):
    gs.reset_for_tests()
    state = {"cuda_temp": 55, "amd_temp": 50, "cuda_free": 12200, "amd_free": 7000, "ram": 50000,
             "ftr_cuda": [], "ftr_amd": [], "helper": True, "posts": []}
    monkeypatch.setattr(gs, "cuda", lambda: {"ok": True, "temp_c": state["cuda_temp"], "free_mib": state["cuda_free"]})
    monkeypatch.setattr(gs, "amd", lambda: {"ok": True, "temp_c": state["amd_temp"], "free_mib": state["amd_free"]})
    monkeypatch.setattr(gs, "host_available_mib", lambda: state["ram"])
    monkeypatch.setattr(gs, "ftr_busy", lambda eps: state["ftr_cuda"] if eps == gs.FTR_CUDA else state["ftr_amd"])
    monkeypatch.setattr(gs, "helper_ready", lambda: state["helper"])
    monkeypatch.setattr(gs, "model_size", lambda m: {BIG: 17_700_000_000, "gemma4:12b": 7_600_000_000,
                                                     "qwen3:1.7b": 1_400_000_000}.get(m, 0))
    monkeypatch.setattr(gs, "_get_json", lambda url, timeout=2.0: {"models": []})
    monkeypatch.setattr(gs, "_post_json", lambda url, body, timeout=30.0: state["posts"].append((url, body)) or {})
    monkeypatch.setattr(gs, "MONITOR_INTERVAL_S", 0.05)
    monkeypatch.setattr(gs, "SHARED_WAIT_S", 1)
    monkeypatch.setattr(gs, "HEAVY_WAIT_S", 1)
    monkeypatch.setattr(gs, "COOL_WAIT_S", 1)
    monkeypatch.setattr(gs, "RAM_SETTLE_S", 0.3)
    return state


def _hold_heavy(release: threading.Event, started: threading.Event):
    with gs.admit_ollama(BIG):
        started.set()
        release.wait(5)


def test_heavy_job_is_exclusive_and_gets_the_measured_profile(gpu):
    with gs.admit_ollama(BIG, {"num_ctx": 32768}) as job:
        assert job.kind == "heavy" and job.options == {"num_gpu": 24, "num_thread": 4, "num_ctx": 8192}
        with pytest.raises(gs.GpuUnavailable, match="exclusive"):
            with gs.admit_ollama("gemma4:12b"):
                pass
    assert (f"{gs.DEFAULT_OLLAMA}/api/generate", {"model": BIG, "keep_alive": 0}) in gpu["posts"]  # residency restored


def test_second_heavy_job_waits_then_is_refused(gpu):
    release, started = threading.Event(), threading.Event()
    t = threading.Thread(target=_hold_heavy, args=(release, started))
    t.start()
    started.wait(2)
    with pytest.raises(gs.GpuUnavailable):
        with gs.admit_image("second"):
            pass
    release.set()
    t.join()
    with gs.admit_image("after"):
        pass  # slot free again


def test_queue_is_bounded(gpu, monkeypatch):
    monkeypatch.setattr(gs, "MAX_WAITING", 0)
    release, started = threading.Event(), threading.Event()
    t = threading.Thread(target=_hold_heavy, args=(release, started))
    t.start()
    started.wait(2)
    t0 = time.monotonic()
    with pytest.raises(gs.GpuUnavailable, match="queue is full"):
        with gs.admit_ollama("gemma4:12b"):
            pass
    assert time.monotonic() - t0 < 0.5
    release.set()
    t.join()


def test_small_request_goes_to_rx7600_helper_while_rtx_is_exclusive(gpu):
    release, started = threading.Event(), threading.Event()
    t = threading.Thread(target=_hold_heavy, args=(release, started))
    t.start()
    started.wait(2)
    with gs.admit_ollama("qwen3:1.7b", {"num_ctx": 2048, "num_predict": 256}) as job:
        assert job.kind == "helper" and job.host == gs.HELPER_URL
    with pytest.raises(gs.GpuUnavailable):  # beyond proven helper limits -> waits for RTX, times out
        with gs.admit_ollama("qwen3:1.7b", {"num_ctx": 8192}):
            pass
    gpu["ftr_amd"] = ["http://127.0.0.1:11436"]  # FTR owns the RX right now
    with pytest.raises(gs.GpuUnavailable):
        with gs.admit_ollama("qwen3:1.7b", {"num_ctx": 2048}):
            pass
    release.set()
    t.join()
    with gs.admit_ollama("qwen3:1.7b", {"num_ctx": 2048}) as job:
        assert job.kind == "shared" and job.host is None  # RTX free: normal placement


def test_thermal_cutoff_refuses_admission_and_stops_running_jobs(gpu):
    gpu["cuda_temp"] = 82
    with pytest.raises(gs.GpuUnavailable, match="cooling"):
        with gs.admit_ollama("gemma4:12b"):
            pass
    gpu["cuda_temp"] = 70
    with gs.admit_ollama(BIG) as job:
        gpu["cuda_temp"] = 83
        deadline = time.monotonic() + 2
        while not job.cut_off and time.monotonic() < deadline:
            time.sleep(0.02)
        with pytest.raises(gs.WorkloadCutoff, match="83"):
            job.check()
    gpu["cuda_temp"] = 77  # below resume threshold: hold released
    with gs.admit_ollama("gemma4:12b"):
        pass


def test_image_admission_counts_ram_after_unloading_the_prompt_model(gpu, monkeypatch):
    # 2026-10-13: the prompt-expansion LLM was still loaded when the image job arrived, so the
    # RAM check (then done before unloading) refused a job that would have fit a moment later.
    resident = {"models": [{"name": "huihui_ai/gemma-4-abliterated:12b"}]}
    gpu["ram"] = 23776

    def get_json(url, timeout=2.0):
        return resident if url.endswith("/api/ps") else {"models": []}

    def post_json(url, body, timeout=30.0):
        if body.get("keep_alive") == 0:
            resident["models"] = []
            gpu["ram"] = 38000
        return {}

    monkeypatch.setattr(gs, "_get_json", get_json)
    monkeypatch.setattr(gs, "_post_json", post_json)
    with gs.admit_image(label="jarvis"):
        pass


def test_host_ram_reserve_and_ftr_activity_block_heavy_jobs(gpu):
    gpu["ram"] = 20000
    with pytest.raises(gs.GpuUnavailable, match="host RAM"):
        with gs.admit_ollama(BIG):
            pass
    gpu["ram"] = 50000
    gpu["ftr_cuda"] = ["http://127.0.0.1:11435"]
    with pytest.raises(gs.GpuUnavailable, match="FTR"):
        with gs.admit_image():
            pass
    assert not any("11435" in url for url, _ in gpu["posts"])  # never manages FTR


def test_vram_reserve_is_checked_after_unloading_aria_models(gpu):
    gpu["cuda_free"] = 9000  # < 9800 image + 2048 reserve
    with pytest.raises(gs.GpuUnavailable, match="2 GiB reserve"):
        with gs.admit_image():
            pass
    with gs.admit_ollama("gemma4:12b"):
        pass  # slot released after the refusal


def test_specialist_is_selective_and_falls_back_visibly(gpu, monkeypatch):
    from jarvis import brain_routing, model_store

    assert brain_routing.needs_specialist("Debug this carefully: race condition in the job queue implementation")
    assert brain_routing.needs_specialist("fix this\n```python\nx = 1\n```")
    assert not brain_routing.needs_specialist("what's a good name for a python script?")
    assert not brain_routing.needs_specialist("tell me a story about a hard winter")
    monkeypatch.setattr(model_store, "explicit_saved_model", lambda role: BIG if role == "specialist" else None)
    hard = "Plan a multi-step migration of the image pipeline architecture"
    assert brain_routing.specialist_model(hard) == (BIG, f"hard coding/planning request → specialist {BIG}")
    gpu["cuda_temp"] = 85
    model, note = brain_routing.specialist_model(hard)
    assert model == "" and note.startswith(f"specialist {BIG} skipped: RTX 3060 cooling")
    params = {}
    gpu["cuda_temp"] = 60
    assert brain_routing.select_chat_model(hard, params) == BIG and "specialist" in params["_specialist_note"]
    assert brain_routing.select_chat_model(hard, {"model": "gemma4:12b"}) == "gemma4:12b"  # explicit wins
    assert brain_routing.select_chat_model(hard, {"knowledge_mode": True}) == BIG  # KnowledgeEngine route too
    assert brain_routing.select_chat_model("who invented the dry fly?", {"knowledge_mode": True}) \
        == brain_routing.reasoning_model()


def test_comfyui_refusal_is_a_clear_error_and_never_queues(gpu, monkeypatch):
    from jarvis import comfyui

    gpu["cuda_temp"] = 90
    monkeypatch.setattr(comfyui, "_run_workflow", lambda *a, **k: pytest.fail("queued despite refusal"))
    assert comfyui.run_workflow({}, "t").startswith("ERROR: Image job not started: RTX 3060 is cooling")


def test_klein_reference_edit_graph_uses_core_nodes_only():
    from jarvis.comfyui_edit import build_klein_edit_workflow

    wf = build_klein_edit_workflow("in.png", "make the mug red", 1024, 768, seed=1)
    kinds = {n["class_type"] for n in wf.values()}
    assert {"UNETLoader", "ReferenceLatent", "EmptyFlux2LatentImage", "Flux2Scheduler"} <= kinds
    assert wf["20"]["inputs"]["device"] == "cpu" and wf["24"]["inputs"]["steps"] == 4


def test_missing_telemetry_refuses_heavy_but_not_ordinary_requests(gpu, monkeypatch):
    monkeypatch.setattr(gs, "cuda", lambda: {"ok": False, "error": "FileNotFoundError"})
    with gs.admit_ollama("gemma4:12b") as job:
        assert job.kind == "shared"
    with pytest.raises(gs.GpuUnavailable, match="telemetry unavailable"):
        with gs.admit_image():
            pass


def test_cutoff_event_is_recorded_and_monitor_survives(gpu):
    with gs.admit_ollama("gemma4:12b") as job:
        gpu["cuda_temp"] = 84
        deadline = time.monotonic() + 2
        while not job.cut_off and time.monotonic() < deadline:
            time.sleep(0.02)
        assert job.cut_off
        time.sleep(0.2)
        assert gs.SCHEDULER._monitor.is_alive()
    assert any(e["event"] == "cutoff" and e["kind"] == "shared" for e in gs.status()["recent"])


def test_abandoned_stream_slot_is_reclaimed_for_a_heavy_job(gpu, monkeypatch):
    monkeypatch.setattr(gs, "STALE_S", 0.2)
    ctx = gs.admit_ollama("gemma4:12b")
    ctx.__enter__()  # a stream whose consumer went away: never exits
    time.sleep(0.3)
    with gs.admit_ollama(BIG) as job:
        assert job.kind == "heavy"
    assert any(e["event"] == "reaped_stale" for e in gs.status()["recent"])
    ctx.__exit__(None, None, None)  # late close must not corrupt the count
    assert gs.status()["shared_active"] == 0


def test_direct_warmups_and_probes_never_bypass_the_exclusive_slot(gpu):
    from jarvis import ollama_health, ollama_runtime

    assert gs.defer_direct_load(BIG) == "heavy models load only through GPU admission"
    assert gs.defer_direct_load("gemma4:12b") == ""
    release, started = threading.Event(), threading.Event()
    t = threading.Thread(target=_hold_heavy, args=(release, started))
    t.start()
    started.wait(2)
    assert ollama_runtime.ensure_chat_model_ready("gemma4:12b")["action"] == "deferred"
    assert ollama_runtime.run_inference_probe("gemma4:12b")["deferred"] is True
    probe = ollama_health._soft_generate_probe("http://127.0.0.1:1", "gemma4:12b", timeout=1)
    assert probe["ok"] and probe["deferred"]
    release.set()
    t.join()


def test_heavy_admission_waits_for_a_loading_warmup_to_be_unloadable(gpu, monkeypatch):
    frees = iter([3000, 3000, 12200])
    monkeypatch.setattr(gs, "cuda", lambda: {"ok": True, "temp_c": 55, "free_mib": next(frees, 12200)})
    with gs.admit_ollama(BIG) as job:
        assert job.kind == "heavy"


def test_cutoff_aborts_an_ordinary_sync_chat_mid_generation(gpu, monkeypatch):
    from jarvis.inference import gateway

    closed = {"n": 0}

    class Stream:
        def __iter__(self):
            for i in range(200):
                if i == 3:
                    gpu["cuda_temp"] = 85  # heats up mid-generation
                time.sleep(0.02)
                yield {"message": {"content": "x"}}

        def close(self):
            closed["n"] += 1

    monkeypatch.setattr(gateway, "_ollama_client_chat", lambda job: (lambda **kw: Stream()))
    with pytest.raises(gs.WorkloadCutoff, match="85"):
        gateway._ollama_chat_with_usage("gemma4:12b", [{"role": "user", "content": "hi"}])
    assert closed["n"] == 1


def test_gpu_reasons_reach_the_owner_instead_of_a_generic_error():
    from jarvis.behaviors.conversation import ConversationEngine

    eng = ConversationEngine.__new__(ConversationEngine)
    eng._requested_model = lambda params: ""
    eng._model_override_selected = lambda params: False
    try:
        try:
            raise gs.WorkloadCutoff("RTX 3060 reached 83°C (cutoff 82°C)")
        except gs.WorkloadCutoff as exc:
            raise RuntimeError("Ollama error with model 'gemma4:12b'") from exc
    except RuntimeError as wrapped:
        msg = eng._inference_error({}, wrapped)
    assert "protect the system" in msg and "83°C" in msg and "gemma4" not in msg


def test_uncensored_round_trip_restores_the_standard_image_checkpoint(tmp_path, monkeypatch):
    from jarvis import comfyui_settings as cs

    monkeypatch.setattr(cs, "SETTINGS_FILE", tmp_path / "comfyui_settings.json")
    monkeypatch.setattr(cs, "recommended_uncensored_checkpoint", lambda: "RealVisXL_V5.0_fp16.safetensors")
    cs.save_checkpoint("flux")
    on = cs.apply_uncensored_defaults()
    assert on["checkpoint_file"] == "RealVisXL_V5.0_fp16.safetensors"
    off = cs.clear_uncensored_auto_checkpoint()
    assert off["checkpoint"] == "flux" and "checkpoint_file" not in off


# ---------------------------------------------------------------- image-edit routing (deferred item 6)

@pytest.fixture
def img_session(tmp_path):
    from jarvis.session import SessionContext

    last, other = tmp_path / "last.png", tmp_path / "other.png"
    last.write_bytes(b"png")
    other.write_bytes(b"png")
    s = SessionContext()
    s.last_image, s.last_action = str(last), "generate_image"
    return s, str(last), str(other)


@pytest.mark.parametrize("message,prompt", [
    ("Edit the last image: make the wings red", "make the wings red"),
    ("Change its wings to red", "Change its wings to red"),
    ("Make the previous image brighter", "make it brighter"),
    ("Edit the image to make the wings red", "make the wings red"),
])
def test_recent_image_edits_target_the_last_image(img_session, message, prompt):
    from jarvis.router import route

    s, last, _ = img_session
    intent = route(message, s)
    assert intent["action"] == "edit_image" and intent["params"] == {"path": last, "prompt": prompt}


def test_edit_without_instruction_or_image_asks_instead_of_guessing(img_session):
    from jarvis.router import route
    from jarvis.session import SessionContext

    s, last, _ = img_session
    assert route("Edit the last image", s)["action"] == "clarify"
    answer = route("make the wings red", s)  # reply to "What should I change?"
    assert answer["action"] == "edit_image" and answer["params"] == {"path": last, "prompt": "make the wings red"}
    assert route("Edit the last image", s)["action"] == "clarify"
    assert route("never mind", s)["action"] != "edit_image"
    empty = SessionContext()
    for message in ("Edit the last image: make it red", "Make the previous image brighter"):
        intent = route(message, empty)
        assert intent["action"] == "clarify" and "Which image" in intent.get("clarification_question", ""), intent
    assert route("Change its wings to red", empty)["action"] != "edit_image"  # no image in play


def test_explicit_path_wins_and_other_requests_are_untouched(img_session):
    from jarvis.router import route

    s, last, other = img_session
    intent = route(f"edit {other} to make it brighter", s)
    assert intent["params"] == {"path": other, "prompt": "make it brighter"}
    assert route(f"Edit '{other}'", s)["action"] == "clarify"
    assert route("edit my resume", s)["action"] != "edit_image"
    assert route("make a new image of a trout", s)["action"] == "generate_image"
    assert route("read pyproject.toml", s)["action"] == "coding_read"
    assert route("find the last image I downloaded", s)["action"] == "coding_find"


# ---------------------------------------------------------------- Z-Image (deferred item 1)

def test_zimage_graph_is_the_qualified_int8_workflow():
    from jarvis import zimage

    wf = zimage.build_workflow("a trout fly", 1000, 760, seed=7)
    assert wf["1"]["inputs"]["unet_name"] == "z_image_turbo_int8_convrot.safetensors"
    assert wf["2"]["inputs"] == {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2", "device": "cpu"}
    assert wf["3"]["inputs"]["steps"] == 8 and wf["3"]["inputs"]["sampler_name"] == "res_multistep"
    assert wf["12"]["inputs"]["shift"] == 3


def test_zimage_is_selectable_and_routes_through_the_image_slot(gpu, monkeypatch, tmp_path):
    from jarvis import comfyui, comfyui_settings as cs, zimage

    monkeypatch.setattr(cs, "SETTINGS_FILE", tmp_path / "s.json")
    monkeypatch.setattr(zimage, "installed", lambda: True)
    cs.save_checkpoint("zimage")
    assert cs.resolve_checkpoint_name() == zimage.CHECKPOINT and cs.checkpoint_label() == "Z-Image Turbo"
    calls = []
    monkeypatch.setattr(zimage, "_systemctl", lambda *a: calls.append(a))
    monkeypatch.setattr(zimage, "_ready", lambda: True)
    monkeypatch.setattr(zimage, "_free_main_comfyui", lambda: None)

    def fake_run(wf, prefix, **kw):
        calls.append(("run", comfyui._base(), prefix, kw.get("vram_mib")))
        return "/tmp/x.png"

    monkeypatch.setattr(comfyui, "run_workflow", fake_run)
    assert comfyui._generate_once("a fly", 1024, 1024) == "/tmp/x.png"
    assert calls == [("start",), ("run", zimage.ZIMAGE_URL, "jarvis_zimage", gs.ZIMAGE_VRAM_MIB), ("stop",)]
    assert comfyui._base() == comfyui.COMFY_URL  # target scoped to the job


def test_zimage_job_is_refused_by_thermal_gate_and_worker_still_stops(gpu, monkeypatch):
    from jarvis import comfyui, zimage

    monkeypatch.setattr(zimage, "installed", lambda: True)
    stops = []
    monkeypatch.setattr(zimage, "_systemctl", lambda *a: stops.append(a))
    monkeypatch.setattr(zimage, "_ready", lambda: True)
    monkeypatch.setattr(zimage, "_free_main_comfyui", lambda: None)
    monkeypatch.setattr(comfyui, "_run_workflow", lambda *a, **k: pytest.fail("rendered despite cutoff"))
    gpu["cuda_temp"] = 90
    out = zimage.generate("x")
    assert out.startswith("ERROR: Image job not started: RTX 3060 is cooling") and ("stop",) in stops


def test_zimage_stays_inside_its_qualified_size_envelope():
    from jarvis import zimage

    assert zimage.qualified_size(1024, 768) == (1024, 768)
    assert zimage.qualified_size(768, 512) == (768, 512)
    w, h = zimage.qualified_size(1024, 1024)
    assert w * h <= 1024 * 768 and w == h and w % 16 == 0


def test_image_jobs_start_cool_and_wait_boundedly(gpu, monkeypatch):
    gpu["cuda_temp"] = 75
    with pytest.raises(gs.GpuUnavailable, match="start limit"):
        with gs.admit_image("warm"):
            pass
    temps = iter([75, 74, 69])
    monkeypatch.setattr(gs, "cuda", lambda: {"ok": True, "temp_c": next(temps, 69), "free_mib": 12200})
    monkeypatch.setattr(gs, "COOL_WAIT_S", 30)
    with gs.admit_image("cooled"):
        pass
    assert any(e["event"] == "cool_start_wait" for e in gs.status()["recent"])
    with gs.admit_ollama("gemma4:12b"):
        pass  # ordinary chat is not held to the image start limit
