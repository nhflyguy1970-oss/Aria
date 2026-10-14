"""Image quality routing, follow-up image requests and context limits (2026-10-14).

* Complex scenes (counts, spatial relations, in-image text, long descriptions) go to
  Qwen-Image; simple ones stay on Flux Schnell; Uncensored mode always keeps Lustify.
* Detailed descriptions reach the model verbatim; rewrites get an output budget that fits them.
* "Again but at night" rebuilds the previous full description; "now add a dragon" edits it.
* Chat history is trimmed by tokens to the model window, never cutting the newest message.
"""
from __future__ import annotations

import json

import pytest

from jarvis import qwen_image as _qwen_image
from jarvis.router import route
from jarvis.session import SessionContext

REAL_QWEN_GENERATE = _qwen_image.generate

WITCHES = ("Photorealistic cinematic image of a modern fighter pilot flying directly toward the camera in a military "
           "fighter jet. The pilot is clearly visible through the cockpit canopy. Exactly five terrifying witches on "
           "flying broomsticks are chasing the aircraft from behind. All five witches must be visible through or "
           "around the cockpit canopy. Dark storm clouds, lightning, magical green and purple trails, cinematic "
           "lighting, 16:9 widescreen.")
COUNTING = ("A photorealistic photograph of a white kitchen counter. Exactly five red apples are lined up in a single "
            "row in the center. Two green pears sit to the left of the apples, and one yellow banana lies behind them.")
SIGN = 'A street photo of a bakery storefront with a wooden sign that reads "ARIA BAKERY" above the door.'


@pytest.fixture
def regular(monkeypatch):
    """Regular mode, default Flux choice, Qwen-Image installed."""
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: False)
    monkeypatch.setattr("jarvis.comfyui_settings.load_settings", lambda: {"mode": "auto", "checkpoint": "flux"})
    monkeypatch.setattr("jarvis.comfyui_settings.effective_workflow_path", lambda: "")
    monkeypatch.setattr("jarvis.qwen_image.installed", lambda: True)
    monkeypatch.delenv("JARVIS_COMFYUI_CKPT", raising=False)
    monkeypatch.delenv("JARVIS_IMAGE_QUALITY_ROUTING", raising=False)


# Automatic fast / high-quality selection ------------------------------------------------------
@pytest.mark.parametrize("prompt", ["a cat on a sofa", "a fast red sports car on a mountain road",
                                    "three kittens in a basket", "a sunset over the ocean, photorealistic, 16:9",
                                    "a woman holding an umbrella in the rain"])
def test_simple_requests_stay_fast(regular, prompt):
    from jarvis.image_quality import choose

    assert choose(prompt)["tier"] == "fast"


@pytest.mark.parametrize("prompt", [WITCHES, COUNTING, SIGN,
                                    "A dog to the left of a cat, a bird above them and a bowl between them"])
def test_complex_scenes_use_the_quality_model(regular, prompt):
    from jarvis.image_quality import choose

    out = choose(prompt)
    assert out["tier"] == "quality" and out["reasons"]


def test_user_can_ask_for_fast_or_high_quality(regular):
    from jarvis.image_quality import choose

    assert choose("just a quick image: " + COUNTING)["tier"] == "fast"
    assert choose("a cat on a sofa, high quality")["tier"] == "quality"


def test_routing_setting_overrides(regular, monkeypatch):
    from jarvis.image_quality import choose

    monkeypatch.setenv("JARVIS_IMAGE_QUALITY_ROUTING", "fast")
    assert choose(WITCHES)["tier"] == "fast"
    monkeypatch.setenv("JARVIS_IMAGE_QUALITY_ROUTING", "quality")
    assert choose("a cat")["tier"] == "quality"


def test_uncensored_mode_never_uses_the_quality_model(regular, monkeypatch):
    from jarvis.image_quality import choose

    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: True)
    assert choose(WITCHES)["tier"] == "fast"


@pytest.mark.parametrize("pinned", [
    {"checkpoint": "flux", "checkpoint_file": "lustifySDXLNSFWSFW_v10.safetensors"},
    {"checkpoint": "zimage"},
    {"checkpoint": "quality"},
])
def test_a_model_the_user_picked_is_respected(regular, monkeypatch, pinned):
    from jarvis.image_quality import choose

    monkeypatch.setattr("jarvis.comfyui_settings.load_settings", lambda: {"mode": "auto", **pinned})
    assert choose(WITCHES)["tier"] == "fast"
    assert choose(WITCHES, checkpoint="RealVisXL_V5.0_fp16.safetensors")["tier"] == "fast"


def test_missing_quality_model_falls_back_to_fast(regular, monkeypatch):
    from jarvis.image_quality import choose

    monkeypatch.setattr("jarvis.qwen_image.installed", lambda: False)
    assert choose(WITCHES)["tier"] == "fast"


# Image engine: which backend runs, with which prompt -----------------------------------------
@pytest.fixture
def engine(regular, monkeypatch, tmp_path):
    from jarvis.modules import image as image_mod

    calls: dict = {"qwen": [], "comfy": [], "llm": []}
    out = tmp_path / "out.png"
    out.write_bytes(b"png")

    def fake_qwen(prompt, width=1344, height=768, *, seed=None, count_prompt=None):
        calls["qwen"].append({"prompt": prompt, "w": width, "h": height})
        return calls.get("qwen_result", str(out))

    def fake_comfy(prompt, **kw):
        calls["comfy"].append({"prompt": prompt, **kw})
        return str(out)

    def fake_llm(model, system, user, **kw):
        calls["llm"].append({"user": user, **kw})
        return json.dumps({"positive": "rewritten: " + user, "negative": ""})

    monkeypatch.setattr("jarvis.qwen_image.generate", fake_qwen)
    monkeypatch.setattr("jarvis.comfyui.generate", fake_comfy)
    monkeypatch.setattr(image_mod.llm, "ask_with_system", fake_llm)
    monkeypatch.setattr(image_mod, "_active_model_family", lambda: "flux")
    monkeypatch.setattr("jarvis.media_jobs.report_progress", lambda *a, **k: None)
    monkeypatch.setattr("jarvis.gpu_scheduler.helper_ready", lambda: False)
    calls["released"] = []
    monkeypatch.setattr("jarvis.qwen_image.release_memory", lambda: calls["released"].append(1))
    image_mod.clear_prompt_cache()
    eng = image_mod.ImageEngine()
    eng.calls = calls  # type: ignore[attr-defined]
    return eng


def test_complex_scene_runs_on_qwen_with_the_full_description(engine):
    engine.generate(WITCHES)
    assert engine.calls["comfy"] == []
    sent = engine.calls["qwen"][0]
    assert sent["prompt"] == WITCHES.rstrip(".")  # detailed: verbatim, no rewrite to drop "Exactly five"
    assert (sent["w"], sent["h"]) == (1344, 768)
    assert engine.calls["llm"] == []
    assert engine.last_tier["tier"] == "quality" and "Qwen-Image" in engine.last_model_label
    assert engine.calls["released"] == [1]  # ComfyUI's ~30 GB is returned after the job


def test_simple_scene_runs_on_the_fast_model(engine):
    engine.generate("a cat on a sofa")
    assert engine.calls["qwen"] == [] and len(engine.calls["comfy"]) == 1
    assert engine.last_tier["tier"] == "fast"


def test_quality_failure_falls_back_to_fast_and_says_so(engine):
    engine.calls["qwen_result"] = "ERROR: CUDA out of memory"
    result = engine.generate(WITCHES)
    assert not result.startswith("ERROR") and len(engine.calls["comfy"]) == 1
    assert engine.calls["comfy"][0]["prompt"] == WITCHES.rstrip(".")
    assert "out of memory" in engine.last_tier["fallback"]


@pytest.mark.parametrize("err", ["ERROR: Image job stopped to protect the system: RTX at 83 C",
                                 "ERROR: Image job not started: GPU busy", "ERROR: cancelled"])
def test_cutoffs_and_cancels_are_not_retried_on_another_model(engine, err):
    engine.calls["qwen_result"] = err
    assert engine.generate(WITCHES) == err and engine.calls["comfy"] == []


def test_uncensored_generation_stays_on_lustify_path(engine, monkeypatch):
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: True)
    engine.generate(WITCHES)
    assert engine.calls["qwen"] == [] and len(engine.calls["comfy"]) == 1


def test_long_prompt_rewrite_gets_room_for_every_detail(engine, monkeypatch):
    from jarvis.modules import image as image_mod

    monkeypatch.setattr(image_mod, "_active_model_family", lambda: "sdxl")
    long = " ".join(["a detailed clause about object number %d placed precisely" % i for i in range(40)])
    image_mod.ImageEngine().prepare_prompt(long)
    assert engine.calls["llm"][0]["options"]["num_predict"] > 320


def test_style_words_survive_request_cleanup():
    from jarvis.modules.image import normalize_image_prompt

    assert normalize_image_prompt("Create a photorealistic cinematic image of a pilot").startswith(
        "Photorealistic cinematic image of a pilot")
    assert normalize_image_prompt("Create an image of a cat") == "a cat"
    assert normalize_image_prompt("Make me a watercolor painting showing a red barn") == (
        "Watercolor painting showing a red barn")


def test_qwen_workflow_carries_the_prompt_and_lightning_settings():
    from jarvis import qwen_image

    wf = qwen_image.build_workflow(WITCHES, 1344, 768, seed=7)
    assert wf["6"]["inputs"]["text"] == WITCHES
    k = wf["9"]["inputs"]
    assert (k["steps"], k["cfg"], k["seed"]) == (8, 1.0, 7)
    assert wf["4"]["inputs"]["lora_name"].startswith("Qwen-Image-2512-Lightning-8steps")
    assert qwen_image.fit_size(1664, 928)[0] * qwen_image.fit_size(1664, 928)[1] <= qwen_image.MAX_PIXELS


# Follow-up image requests ----------------------------------------------------------------------
def _after_image(tmp_path, **extra) -> SessionContext:
    img = tmp_path / "jarvis_00200_.png"
    img.write_bytes(b"png")
    s = SessionContext()
    s.note_image(str(img), prompt=WITCHES)
    s.last_action, s.last_module = "generate_image", "image"
    for k, v in extra.items():
        setattr(s, k, v)
    return s


@pytest.mark.parametrize("message,change", [
    ("Now make another one with seven witches instead of five", "with seven witches instead of five"),
    ("Do it again but at night", "at night"),
    ("Same scene but photorealistic", "photorealistic"),
    ("Create another image of that scene at sunset", "at sunset"),
    ("One more, but the witches should be in front of the jet", "the witches should be in front of the jet"),
    ("Try again", ""),
])
def test_regenerate_follow_ups_rebuild_the_previous_description(tmp_path, message, change):
    out = route(message, _after_image(tmp_path))
    assert out["action"] == "generate_image" and out["route_reason"] == "image_followup_regenerate"
    assert out["params"]["base_prompt"] == WITCHES and out["params"]["change"] == change
    assert "Exactly five terrifying witches" in out["params"]["prompt"]


@pytest.mark.parametrize("message", ["now add a dragon", "Make the jet red", "remove the lightning"])
def test_edit_follow_ups_edit_the_last_image(tmp_path, message):
    s = _after_image(tmp_path)
    out = route(message, s)
    assert out["action"] == "edit_image" and out["params"]["path"] == s.last_image


def test_a_new_subject_is_a_new_image_not_a_follow_up(tmp_path):
    out = route("make another image of a dog", _after_image(tmp_path))
    assert out["action"] == "generate_image" and out["params"]["prompt"] == "a dog"
    assert "base_prompt" not in out["params"]


@pytest.mark.parametrize("message", ["add milk to my shopping list", "what's the weather tomorrow?"])
def test_unrelated_requests_after_an_image_are_not_captured(tmp_path, message):
    assert route(message, _after_image(tmp_path))["action"] not in ("generate_image", "edit_image")


def test_try_again_without_an_image_in_play_is_not_an_image_request(tmp_path):
    s = _after_image(tmp_path, last_action="web_search", last_module="research")
    s.last_image_at = 0
    assert route("Try again", s)["action"] != "generate_image"


def test_follow_up_merge_uses_the_model_and_falls_back_safely(monkeypatch):
    from jarvis.modules import image as image_mod

    merged = WITCHES.replace("Exactly five", "Exactly seven").replace("All five", "All seven")
    monkeypatch.setattr(image_mod.llm, "ask_with_system", lambda *a, **k: merged)
    assert image_mod.merge_followup_prompt(WITCHES, "seven witches instead of five") == merged
    monkeypatch.setattr(image_mod.llm, "ask_with_system", lambda *a, **k: "Sure! Seven witches.")
    out = image_mod.merge_followup_prompt(WITCHES, "seven witches instead of five")
    assert out.startswith(WITCHES[:-1]) and "seven witches instead of five" in out


def test_handler_merges_follow_ups_and_records_the_full_prompt(monkeypatch, tmp_path):
    from unittest.mock import MagicMock

    from jarvis.handlers.media import MediaHandler

    img = tmp_path / "jarvis_00201_.png"
    img.write_bytes(b"png")
    monkeypatch.setattr("jarvis.modules.image.merge_followup_prompt", lambda base, change: base + " At night.")
    monkeypatch.setattr("jarvis.media_jobs.report_progress", lambda *a, **k: None)
    assistant = MagicMock()
    assistant.session = SessionContext()
    assistant.image.generate.return_value = str(img)
    assistant.image.last_enhanced_prompt = WITCHES + " At night."
    assistant.image.last_negative_prompt = ""
    assistant.image.last_model_label = "Qwen-Image 2512 (high quality)"
    assistant.image.last_tier = {"tier": "quality", "reasons": ["object counts"]}
    res = MediaHandler(assistant).generate_image(
        {"prompt": "fallback", "base_prompt": WITCHES, "change": "at night", "enhance": False}, "Do it again but at night")
    assert res["ok"]
    assert assistant.image.generate.call_args[0][0].endswith("At night")
    assert assistant.session.last_image_prompt.endswith("At night")
    assert "Qwen-Image" in res["message"] and "object counts" in res["message"]


def test_session_keeps_the_last_image_prompt_across_restarts(tmp_path):
    s = _after_image(tmp_path)
    restored = SessionContext.from_dict(json.loads(json.dumps(s.to_dict())))
    assert restored.last_image_prompt == WITCHES and restored.last_image_at > 0


# Context limits ------------------------------------------------------------------------------------
def test_history_is_trimmed_by_tokens_and_the_newest_message_stays_whole():
    from jarvis.config import CONTEXT_TOKEN_BUDGET
    from jarvis.conversation import Conversation, estimate_tokens

    c = Conversation("system prompt")
    for i in range(20):
        c.add_user(f"turn {i} " + "x" * 3000)
        c.add_assistant("y" * 400)
    long = "Paragraph. " * 2000  # a ~22k-character image description
    c.add_user(long)
    assert c.messages[-1]["content"] == long and c.messages[0]["role"] == "system"
    c.add_assistant("ok")
    c.add_user("And make it at night")
    assert sum(estimate_tokens(m["content"]) for m in c.messages) <= CONTEXT_TOKEN_BUDGET
    assert c.messages[-1]["content"] == "And make it at night"


def test_recent_turns_are_kept_when_they_fit():
    from jarvis.conversation import Conversation

    c = Conversation("sys")
    for i in range(6):
        c.add_user("u" * 1000)
        c.add_assistant("a" * 1000)
    assert len(c.messages) == 13  # ~3.5k tokens fit the default 5.6k budget


def test_action_log_keeps_long_requests(monkeypatch):
    from jarvis import action_log

    rows: list = []
    monkeypatch.setattr(action_log, "_load", lambda: rows)
    monkeypatch.setattr(action_log, "_save", lambda entries: None)
    long = WITCHES * 6  # ~2.9k characters; the old cut was 120-500
    action_log.log_action("generate_image", "image", long, True, prompt=long)
    assert rows[-1]["detail"] == long and rows[-1]["prompt"] == long


# Dual GPU: prompt preparation on the RX 7600 helper ------------------------------------------------
@pytest.fixture
def gpu(monkeypatch):
    """The scheduler with both GPUs faked (same shape as tests/test_phase8_finalize.py)."""
    from jarvis import gpu_scheduler as gs

    gs.reset_for_tests()
    state = {"amd_temp": 50, "helper": True}
    monkeypatch.setattr(gs, "cuda", lambda: {"ok": True, "temp_c": 55, "free_mib": 12200})
    monkeypatch.setattr(gs, "amd", lambda: {"ok": True, "temp_c": state["amd_temp"], "free_mib": 7000})
    monkeypatch.setattr(gs, "host_available_mib", lambda: 50000)
    monkeypatch.setattr(gs, "ftr_busy", lambda eps: [])
    monkeypatch.setattr(gs, "helper_ready", lambda: state["helper"])
    monkeypatch.setattr(gs, "model_size", lambda m: 1_400_000_000)
    monkeypatch.setattr(gs, "_get_json", lambda url, timeout=2.0: {"models": []})
    monkeypatch.setattr(gs, "_post_json", lambda url, body, timeout=30.0: {})
    monkeypatch.setattr(gs, "MONITOR_INTERVAL_S", 0.05)
    monkeypatch.setattr(gs, "SHARED_WAIT_S", 1)
    monkeypatch.setattr(gs, "COOL_WAIT_S", 1)
    yield state
    gs.reset_for_tests()


def test_prefer_helper_places_small_requests_on_the_rx7600_while_the_rtx_is_idle(gpu):
    from jarvis import gpu_scheduler as gs

    with gs.prefer_helper("image prompt preparation"):
        with gs.admit_ollama("qwen3:1.7b", {"num_ctx": 4096, "num_predict": 512}) as job:
            assert job.kind == "helper" and job.host == gs.HELPER_URL
    with gs.admit_ollama("qwen3:1.7b", {"num_ctx": 4096}) as job:
        assert job.kind == "shared"  # outside the scope: normal RTX placement
    gpu["helper"] = False
    with gs.prefer_helper("image prompt preparation"):
        with gs.admit_ollama("qwen3:1.7b", {"num_ctx": 4096}) as job:
            assert job.kind == "shared"  # helper down: the RTX still serves it
    gpu["helper"], gpu["amd_temp"] = True, 82
    with gs.prefer_helper("image prompt preparation"):
        with gs.admit_ollama("qwen3:1.7b", {"num_ctx": 4096}) as job:
            assert job.kind == "shared"  # hot RX 7600: never pushed further


def _capture_rewrite(monkeypatch, *, helper=True, size=3_390_000_000):
    from jarvis import gpu_scheduler
    from jarvis.modules import image as image_mod

    seen = []
    monkeypatch.setattr(gpu_scheduler, "helper_ready", lambda: helper)
    monkeypatch.setattr(gpu_scheduler, "model_size", lambda m: size)

    def fake(model, system, user, **kw):
        seen.append({"model": model, "scope": gpu_scheduler._PREFER_HELPER.get(), **kw})
        return json.dumps({"positive": "a tabby cat on a grey sofa", "negative": ""})

    monkeypatch.setattr(image_mod.llm, "ask_with_system", fake)
    image_mod.clear_prompt_cache()
    return seen


def test_regular_prompt_rewrite_runs_on_the_helper_lane(monkeypatch):
    from jarvis.modules import image as image_mod

    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: False)
    seen = _capture_rewrite(monkeypatch)
    image_mod.ImageEngine().prepare_prompt("a cat on a sofa", family="flux")
    assert seen[0]["model"] == "qwen3.5:4b" and seen[0]["scope"]
    assert seen[0]["options"]["num_ctx"] == 4096 and seen[0]["think"] is False
    assert seen[0]["explicit_model"] is True  # the role policy must not swap in the RTX chat model


def test_uncensored_rewrite_never_uses_the_helper(monkeypatch):
    from jarvis.modules import image as image_mod

    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: True)
    monkeypatch.setattr(image_mod, "_uncensored_prompt_model", lambda: "huihui_ai/gemma-4-abliterated:12b")
    seen = _capture_rewrite(monkeypatch)
    image_mod.ImageEngine().prepare_prompt("a woman on a beach", family="sdxl")
    assert seen[0]["model"] == "huihui_ai/gemma-4-abliterated:12b" and not seen[0]["scope"]


def test_rewrite_falls_back_to_the_rtx_model_when_the_helper_cannot_take_it(monkeypatch):
    from jarvis.modules import image as image_mod

    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: False)
    seen = _capture_rewrite(monkeypatch, helper=False)
    image_mod.ImageEngine().prepare_prompt("a cat on a sofa", family="flux")
    assert seen[0]["model"] == image_mod._standard_prompt_model() and not seen[0]["scope"]
    seen = _capture_rewrite(monkeypatch)
    huge = " ".join(f"clause {i} about a specific object placed precisely" for i in range(400))
    image_mod.ImageEngine().prepare_prompt(huge, family="sdxl")  # too long for the helper's 4K window
    assert seen[0]["model"] == image_mod._standard_prompt_model()


# Count check on the RX 7600 helper -------------------------------------------------------------
def test_expected_counts_reads_the_numbers_a_prompt_asks_for():
    from jarvis.image_verify import expected_counts

    assert expected_counts(WITCHES) == [(5, "witches")]
    assert expected_counts(COUNTING) == [(5, "apples"), (2, "pears")]
    assert expected_counts("a cat, 16:9, rendered in 4 steps, two styles") == []


def _count_engine(engine, monkeypatch, tmp_path, counts):
    """The real qwen_image.generate with a fake RTX session that renders new files, and a
    helper that 'counts' from the given sequence. Returns (rendered files, admissions)."""
    from contextlib import contextmanager

    from jarvis import comfyui, image_verify, qwen_image

    gen = tmp_path / "generated"
    gen.mkdir(exist_ok=True)
    monkeypatch.setattr("jarvis.modules.image.IMAGE_DIR", gen)
    made, sessions = [], []

    @contextmanager
    def session(label, **kw):
        sessions.append(label)

        def run(workflow, filename_prefix=label):
            p = gen / f"jarvis_qwen_{len(made):05d}_.png"
            p.write_bytes(b"png")
            made.append(p)
            return str(p)

        yield run

    seq = iter(counts)
    monkeypatch.setattr("jarvis.qwen_image.generate", REAL_QWEN_GENERATE)
    monkeypatch.setattr(qwen_image, "installed", lambda: True)
    monkeypatch.setattr(qwen_image, "gpu_text_encoder_available", lambda: True)
    monkeypatch.setattr("jarvis.vram_guard.prepare_for_comfyui", lambda *a, **k: None)
    monkeypatch.setattr("jarvis.services.ensure_comfyui_nvidia", lambda *a, **k: True)
    monkeypatch.setattr(comfyui, "is_available", lambda: True)
    monkeypatch.setattr(comfyui, "image_session", session)
    monkeypatch.setattr(image_verify, "count_objects", lambda path, noun: next(seq))
    return made, sessions


def test_a_miscount_renders_again_and_keeps_the_closer_attempt(engine, monkeypatch, tmp_path):
    made, sessions = _count_engine(engine, monkeypatch, tmp_path, [4, 5])
    result = engine.generate(WITCHES)
    assert result == str(made[1]) and len(made) == 2
    assert sessions == ["jarvis_qwen"]  # the retry reused the same RTX admission (weights stay loaded)
    assert not made[0].exists() and (tmp_path / "generated_rejected" / made[0].name).exists()  # set aside, not deleted
    assert engine.last_count_check["misses"] == 0 and engine.last_count_check["attempts"] == 2


def test_a_correct_count_is_not_rendered_again(engine, monkeypatch, tmp_path):
    made, _ = _count_engine(engine, monkeypatch, tmp_path, [5])
    engine.generate(WITCHES)
    assert len(made) == 1 and engine.last_count_check["attempts"] == 1


def test_a_worse_retry_keeps_the_first_image(engine, monkeypatch, tmp_path):
    made, _ = _count_engine(engine, monkeypatch, tmp_path, [4, 3])
    assert engine.generate(WITCHES) == str(made[0])
    assert (tmp_path / "generated_rejected" / made[1].name).exists()
    from jarvis.image_verify import summary

    assert "asked 5, counted 4" in summary(engine.last_count_check)


def test_no_helper_means_no_check_and_no_retry(engine, monkeypatch, tmp_path):
    made, _ = _count_engine(engine, monkeypatch, tmp_path, [None])
    engine.generate(WITCHES)
    assert len(made) == 1 and not engine.last_count_check.get("ran")


def test_count_check_never_runs_on_the_rtx(monkeypatch, tmp_path):
    from contextlib import contextmanager
    from types import SimpleNamespace

    from jarvis import gpu_scheduler, image_verify

    monkeypatch.setattr(gpu_scheduler, "helper_ready", lambda: True)
    monkeypatch.setattr(gpu_scheduler, "model_size", lambda m: 3_300_000_000)

    @contextmanager
    def rtx_only(model, options=None, *, label=""):
        yield SimpleNamespace(kind="shared", host=None)

    monkeypatch.setattr(gpu_scheduler, "admit_ollama", rtx_only)
    monkeypatch.setattr(image_verify, "_jpeg_b64", lambda p: "")
    assert image_verify.count_objects(str(tmp_path / "x.png"), "witches") is None


# Returning Qwen-Image's host memory -----------------------------------------------------------------
@pytest.fixture
def comfy_proc(monkeypatch):
    from jarvis import services

    stopped = []
    monkeypatch.setattr(services, "_comfy_proc", None)
    monkeypatch.setattr(services, "_aria_comfy_pid", lambda: 4242)
    monkeypatch.setattr(services, "_terminate_pid", lambda pid: stopped.append(pid))
    monkeypatch.setattr(services, "_log", lambda msg: None)
    monkeypatch.setattr("jarvis.media_jobs.busy_state", lambda: {"pending": 0})
    return stopped


def test_comfyui_holding_memory_after_free_is_stopped(comfy_proc, monkeypatch):
    from jarvis import services

    monkeypatch.setattr(services, "_comfy_last_activity", lambda started: started)
    monkeypatch.setattr(services, "_retained_mib", lambda pid: 27_000)
    assert services.release_comfyui("a Qwen-Image job", settle_s=0) and comfy_proc == [4242]


def test_comfyui_that_returned_its_memory_keeps_running(comfy_proc, monkeypatch):
    from jarvis import services

    monkeypatch.setattr(services, "_comfy_last_activity", lambda started: started)
    monkeypatch.setattr(services, "_retained_mib", lambda pid: 1_830)  # measured with the mmap fix
    assert not services.release_comfyui("a Qwen-Image job", settle_s=0) and comfy_proc == []


def test_comfyui_launch_returns_freed_memory_and_loads_aria_nodes(monkeypatch):
    from jarvis import services

    monkeypatch.delenv("JARVIS_COMFYUI_ARGS", raising=False)
    monkeypatch.delenv("JARVIS_COMFYUI_MMAP_THRESHOLD", raising=False)
    monkeypatch.setattr("jarvis.comfyui_settings.effective_cpu_mode", lambda: False)
    assert services._comfy_env()["MALLOC_MMAP_THRESHOLD_"] == "1048576"
    args = services._comfy_extra_args()
    cfg = args[args.index("--extra-model-paths-config") + 1]
    assert cfg.endswith("comfy_nodes/extra_paths.yaml") and "--lowvram" in args and "--fp32-text-enc" in args
    assert (services.PROJECT_ROOT / "comfy_nodes" / "aria_nodes" / "__init__.py").is_file()


def test_qwen_workflow_uses_the_gpu_text_encoder_only_when_comfyui_has_it():
    from jarvis import qwen_image

    assert qwen_image.build_workflow("x", 1344, 768, 1, gpu_text_encoder=True)["2"]["class_type"] == "ARIATextEncoderLoaderGPU"
    stock = qwen_image.build_workflow("x", 1344, 768, 1)["2"]
    assert stock["class_type"] == "CLIPLoader" and stock["inputs"]["type"] == "qwen_image"


def test_busy_comfyui_or_a_queued_job_keeps_it_running(comfy_proc, monkeypatch):
    from jarvis import services

    monkeypatch.setattr(services, "_retained_mib", lambda pid: 27_000)
    monkeypatch.setattr(services, "_comfy_last_activity", lambda started: None)  # prompt running / RTX admitted
    assert not services.release_comfyui("a Qwen-Image job", settle_s=0)
    monkeypatch.setattr(services, "_comfy_last_activity", lambda started: started)
    monkeypatch.setattr("jarvis.media_jobs.busy_state", lambda: {"pending": 1})
    assert not services.release_comfyui("a Qwen-Image job", settle_s=0) and comfy_proc == []


def test_test_runs_never_auto_route_to_the_real_quality_model():
    import os

    assert os.environ.get("JARVIS_IMAGE_QUALITY_ROUTING") == "fast"


def test_a_fixed_seed_is_rendered_once_without_count_retries(engine, monkeypatch, tmp_path):
    made, _ = _count_engine(engine, monkeypatch, tmp_path, [4, 4])
    engine.generate(WITCHES, seed=123)
    assert len(made) == 1 and not engine.last_count_check


def test_a_model_already_on_the_helper_does_not_block_the_next_one(gpu, monkeypatch):
    """Live 2026-10-14: the count-check vision model (3.3 GB) was still loaded on the RX 7600,
    so the next prompt rewrite looked like it would not fit and fell back to a cold RTX load
    (80 s). The helper runs one model at a time and evicts it, so its VRAM is available."""
    from jarvis import gpu_scheduler as gs

    monkeypatch.setattr(gs, "amd", lambda: {"ok": True, "temp_c": 50, "free_mib": 2854})  # live reading
    monkeypatch.setattr(gs, "model_size", lambda m: 3_390_000_000)
    monkeypatch.setattr(gs, "_get_json", lambda url, timeout=2.0: {"models": [{"size_vram": 4_666_000_000}]}  # ~4.45 GiB measured
                        if url.endswith("/api/ps") else {"models": []})
    with gs.prefer_helper("image prompt preparation"):
        with gs.admit_ollama("qwen3.5:4b", {"num_ctx": 4096, "num_predict": 320}) as job:
            assert job.kind == "helper"
    monkeypatch.setattr(gs, "_get_json", lambda url, timeout=2.0: {"models": []})
    gs._cache.pop("helper_ps", None)
    with gs.prefer_helper("image prompt preparation"):
        with gs.admit_ollama("qwen3.5:4b", {"num_ctx": 4096, "num_predict": 320}) as job:
            assert job.kind == "shared"  # genuinely full (e.g. FTR or the desktop): RTX instead


@pytest.mark.parametrize("message", [
    "The code word for today is PELICAN-47. " + "Filler sentence about nothing. " * 60
    + "Without using any tools, what code word did I give you at the very start? Reply with just the code word.",
    "Do not use any tools: what is the boiling point of water in Fahrenheit?",
])
def test_no_tools_requests_are_never_web_searches(message):
    """Live 2026-10-14: "Without using any tools, what code word …" ran web_search (Wordle results)."""
    out = route(message, SessionContext())
    assert out["action"] not in ("web_search", "research_run", "briefing_news_detail", "browser_search", "deep_research")


def test_a_long_message_reaches_the_model_whole(assistant, monkeypatch):
    """The 120-160 character cut was only in logs: the full text reaches the chat model."""
    seen = []
    monkeypatch.setattr("jarvis.ollama_health.check_ollama", lambda *a, **k: {"running": True, "models": ["qwen2.5:14b"]})
    monkeypatch.setattr("jarvis.inference.gateway._ollama_chat_with_usage",
                        lambda model, messages, **kw: seen.append(messages) or ("PELICAN-47", {}))
    long = "The code word is PELICAN-47. " + "Filler sentence about nothing. " * 100 + "What was the code word?"
    assistant.process(long)
    assert any(long in str(m.get("content")) for m in seen[-1])


def test_a_failing_helper_falls_back_to_the_rtx_prompt_model(monkeypatch):
    from jarvis import gpu_scheduler
    from jarvis.modules import image as image_mod

    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: False)
    monkeypatch.setattr(gpu_scheduler, "helper_ready", lambda: True)
    monkeypatch.setattr(gpu_scheduler, "model_size", lambda m: 3_390_000_000)
    calls = []

    def flaky(model, system, user, **kw):
        calls.append(model)
        if model == "qwen3.5:4b":
            raise RuntimeError("helper connection reset")
        return "rewritten"

    monkeypatch.setattr(image_mod.llm, "ask_with_system", flaky)
    assert image_mod._rewrite_llm("s", "u", num_predict=320, temperature=0.2) == "rewritten"
    assert calls == ["qwen3.5:4b", image_mod._prompt_model()]


@pytest.mark.parametrize("env,renders", [(None, 2), ("0", 1), ("1", 2), ("2", 3), ("99", 3), ("-5", 1), ("abc", 2)])
def test_count_retries_are_strictly_bounded(engine, monkeypatch, tmp_path, env, renders):
    """A counter that always disagrees can never cause more than 1 + 2 renders."""
    if env is None:
        monkeypatch.delenv("JARVIS_IMAGE_COUNT_RETRIES", raising=False)
    else:
        monkeypatch.setenv("JARVIS_IMAGE_COUNT_RETRIES", env)
    made, sessions = _count_engine(engine, monkeypatch, tmp_path, [4] * 50)
    engine.generate(WITCHES)
    assert len(made) == renders and len(sessions) == 1
    assert engine.last_count_check["attempts"] == renders


def test_a_failed_retry_render_stops_the_loop(engine, monkeypatch, tmp_path):
    from contextlib import contextmanager

    from jarvis import comfyui

    made, _ = _count_engine(engine, monkeypatch, tmp_path, [4] * 10)
    monkeypatch.setenv("JARVIS_IMAGE_COUNT_RETRIES", "2")
    calls = []

    @contextmanager
    def session(label, **kw):
        def run(workflow, filename_prefix=label):
            calls.append(1)
            if len(calls) > 1:
                return "ERROR: ComfyUI execution error"
            p = tmp_path / "generated" / "jarvis_qwen_first_.png"
            p.write_bytes(b"png")
            return str(p)
        yield run

    monkeypatch.setattr(comfyui, "image_session", session)
    assert engine.generate(WITCHES).endswith("jarvis_qwen_first_.png") and len(calls) == 2


def test_a_required_helper_fails_fast_instead_of_queueing_for_the_rtx(gpu):
    """Live 2026-10-14: a count check waited 150 s for the RTX that ARIA's own image job held."""
    import threading
    import time

    from jarvis import gpu_scheduler as gs

    release, started = threading.Event(), threading.Event()

    def hold():
        with gs.admit_image(label="jarvis_qwen"):
            started.set()
            release.wait(10)

    t = threading.Thread(target=hold)
    t.start()
    started.wait(5)
    gpu["helper"] = False
    t0 = time.monotonic()
    with pytest.raises(gs.GpuUnavailable, match="helper lane"):
        with gs.prefer_helper("count check", required=True):
            with gs.admit_ollama("qwen3-vl:4b", {"num_ctx": 4096, "num_predict": 8}):
                pass
    assert time.monotonic() - t0 < 2
    release.set()
    t.join()


def test_a_model_already_resident_on_the_helper_is_admitted(gpu, monkeypatch):
    """Live 2026-10-14: qwen3-vl (3,397 MiB) was loaded, 2,854 MiB free — the second count check
    was refused because the scheduler wanted room for a second copy."""
    from jarvis import gpu_scheduler as gs

    monkeypatch.setattr(gs, "amd", lambda: {"ok": True, "temp_c": 42, "free_mib": 2854})
    monkeypatch.setattr(gs, "model_size", lambda m: 3_300_000_000)
    monkeypatch.setattr(gs, "_get_json", lambda url, timeout=2.0: {"models": [
        {"name": "qwen3-vl:4b-instruct-q4_K_M", "size_vram": 3_397 * 1048576}]} if url.endswith("/api/ps") else {"models": []})
    with gs.prefer_helper("count check", required=True):
        with gs.admit_ollama("qwen3-vl:4b-instruct-q4_K_M", {"num_ctx": 4096, "num_predict": 8}) as job:
            assert job.kind == "helper"
