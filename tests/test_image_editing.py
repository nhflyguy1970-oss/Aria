"""Image editing reliability (2026-10-14 jet-scene experiment).

Covers: local object edits (plan → locate → crop edit → masked paste → recount), the count
sanity checks that caught a contradictory instruction, edit routing and history, and the
reliability fixes behind the 16:56 watchdog restart (blocking recovery probe, deepseek's
hidden thinking timed out as "no first token").
"""
from __future__ import annotations

import asyncio
import contextlib
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from jarvis.image_edit_plan import plan

USER_INSTRUCTION = (
    "Keep the fighter jet, visible pilot, all five warriors, their armor colors, the glowing green sword, "
    "aircraft carrier, storm, lightning, ocean waves, lighting, and camera angle exactly as they are.\r\n\r\n"
    "There are FOUR helicopters in the sky. Remove exactly ONE helicopter so that exactly THREE remain.\r\n\r\n"
    "Do not change anything else. Preserve the readable \"ARIA ONE\" lettering and the photorealistic 16:9 composition."
)
# qwen3-vl's boxes for the three helicopters in jarvis_qwen_00012_.png (0-1 fractions)
HELIS = [(0.093, 0.085, 0.307, 0.25), (0.677, 0.072, 0.955, 0.253), (0.618, 0.188, 0.714, 0.26)]


# --- planning ----------------------------------------------------------------------------------
def test_the_experiment_instruction_is_one_local_removal():
    p = plan(USER_INSTRUCTION)
    assert p and p.op == "remove" and p.noun == "helicopter"
    assert (p.count, p.target_total, p.claimed_total) == (1, 3, 4)


@pytest.mark.parametrize("text,expected", [
    ("remove one helicopter", ("remove", "helicopter", 1, "", False)),
    ("remove the small distant helicopter", ("remove", "helicopter", None, "small", False)),
    ("remove the helicopter on the left", ("remove", "helicopter", None, "left", False)),
    ("remove all the helicopters", ("remove", "helicopter", None, "", True)),
    ("remove the helicopters", ("remove", "helicopter", None, "", True)),
    ("erase the bird", ("remove", "bird", None, "", False)),
    ("replace the left helicopter with a red dragon", ("replace", "helicopter", 1, "left", False)),
    ("change the helicopter on the right into a hot air balloon", ("replace", "helicopter", 1, "right", False)),
])
def test_single_object_operations_are_planned(text, expected):
    p = plan(text)
    assert p and (p.op, p.noun, p.count, p.which, p.remove_all) == expected


@pytest.mark.parametrize("text", [
    "make the sky orange",                                      # global change
    "remove the background",                                    # not an object
    "remove the left helicopter and add a dragon",              # two changes
    "Keep the existing image composition. Correct only these details: 1. The warrior must wear "
    "black armor. 2. Add the words ARIA ONE.",                  # several corrections
])
def test_everything_else_stays_a_whole_image_edit(text):
    assert plan(text) is None


def test_contradictory_counts_change_nothing_and_say_why():
    from jarvis.comfyui_local_edit import _how_many

    k, why, ask = _how_many(plan(USER_INSTRUCTION), found=3)
    assert k == 0 and ask
    assert "I count 3 helicopters in this image, not 4" in why and "would leave 2, not 3" in why


@pytest.mark.parametrize("text,found,k", [
    ("remove helicopters so that only two remain", 3, 1),
    ("remove one helicopter", 3, 1),
    ("remove all the helicopters", 3, 3),
    ("remove the left helicopter", 3, 1),
    ("remove the helicopter", 1, 1),
])
def test_how_many_to_remove(text, found, k):
    from jarvis.comfyui_local_edit import _how_many

    assert _how_many(plan(text), found)[0] == k


def test_an_ambiguous_object_is_asked_about_not_guessed():
    from jarvis.comfyui_local_edit import _how_many

    k, why, ask = _how_many(plan("remove the helicopter"), found=3)
    assert k == 0 and ask and "Which one" in why


def test_already_at_the_target_count_changes_nothing():
    from jarvis.comfyui_local_edit import _how_many

    k, why, ask = _how_many(plan("remove helicopters so that exactly three remain"), found=3)
    assert k == 0 and not ask and "already 3" in why


@pytest.mark.parametrize("which,expected", [
    ("", HELIS[2]), ("smallest", HELIS[2]), ("distant", HELIS[2]), ("left", HELIS[0]),
    ("right", HELIS[1]), ("largest", HELIS[1]),
])
def test_choosing_which_object(which, expected):
    from jarvis.comfyui_local_edit import choose

    assert choose(HELIS, which, 1) == [expected]


# --- locating ------------------------------------------------------------------------------------
def test_grounding_json_becomes_fraction_boxes():
    from jarvis.image_verify import parse_boxes

    text = ('[{"bbox_2d": [93, 85, 307, 250], "label": "helicopter"}, {"bbox_2d": [677, 72, 955, 253]},'
            ' {"bbox_2d": [94, 86, 306, 251]}]')  # third is a duplicate of the first
    assert parse_boxes(text) == [(0.093, 0.085, 0.307, 0.25), (0.677, 0.072, 0.955, 0.253)]
    assert parse_boxes("[]") == [] and parse_boxes("no idea") == []


def test_locating_never_falls_back_to_the_rtx(monkeypatch, tmp_path):
    from jarvis import gpu_scheduler, image_verify

    monkeypatch.setenv("JARVIS_IMAGE_COUNT_MODEL", "qwen3-vl:4b-instruct-q4_K_M")
    monkeypatch.setattr(gpu_scheduler, "helper_ready", lambda: True)
    monkeypatch.setattr(gpu_scheduler, "model_size", lambda m: 3_300_000_000)

    @contextlib.contextmanager
    def rtx_only(model, options=None, *, label=""):
        yield SimpleNamespace(kind="shared", host=None)

    monkeypatch.setattr(gpu_scheduler, "admit_ollama", rtx_only)
    monkeypatch.setattr(image_verify, "_jpeg_b64", lambda p: "")
    assert image_verify.locate(str(tmp_path / "x.png"), "helicopter") is None


# --- the local edit itself -----------------------------------------------------------------------
@pytest.fixture
def edit_env(monkeypatch, tmp_path):
    """A 1344x768 source, a fake ComfyUI that paints the crop green, and scripted locate() answers."""
    from jarvis import comfyui, comfyui_edit, image_verify

    gallery = tmp_path / "generated"
    gallery.mkdir()
    src = gallery / "jarvis_qwen_00012_.png"
    rng = np.random.default_rng(0)
    Image.fromarray(rng.integers(0, 255, (768, 1344, 3), dtype=np.uint8)).save(src)
    monkeypatch.setattr("jarvis.config.DATA_DIR", tmp_path)
    monkeypatch.setattr(comfyui, "OUTPUT_DIR", gallery)
    monkeypatch.setattr(comfyui, "is_available", lambda: True)
    comfy = tmp_path / "ComfyUI"
    (comfy / "input").mkdir(parents=True)
    (comfy / "output").mkdir()
    monkeypatch.setattr("jarvis.comfyui_settings.COMFY_ROOT", comfy)

    def upload(p):
        (comfy / "input" / Path(p).name).write_bytes(Path(p).read_bytes())
        return Path(p).name

    monkeypatch.setattr(comfyui, "upload_image", upload)
    monkeypatch.setattr(comfyui, "workflow_ram_mib", lambda wf: 1000)
    monkeypatch.setattr(comfyui_edit, "klein_installed", lambda: True)
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: False)
    env = SimpleNamespace(src=src, gallery=gallery, comfy=comfy, workflows=[], answers=[], sessions=0)

    @contextlib.contextmanager
    def session(label, **kw):
        env.sessions += 1

        def run(wf, prefix="x"):
            env.workflows.append(wf)
            w = h = 512
            for node in wf.values():
                if node["class_type"] in ("EmptyFlux2LatentImage",):
                    w, h = node["inputs"]["width"], node["inputs"]["height"]
            out = gallery / f"{prefix}_{len(env.workflows):05d}_.png"
            Image.new("RGB", (w, h), (0, 255, 0)).save(out)
            Image.new("RGB", (w, h), (0, 255, 0)).save(comfy / "output" / out.name)  # ComfyUI's own copy
            return str(out)

        yield run

    monkeypatch.setattr(comfyui, "image_session", session)
    monkeypatch.setattr(image_verify, "locate", lambda path, noun: env.answers.pop(0) if env.answers else [])
    return env


def test_removal_keeps_every_pixel_outside_the_mask(edit_env):
    from jarvis import comfyui_local_edit

    edit_env.answers = [list(HELIS), HELIS[:2]]
    out = comfyui_local_edit.run(edit_env.src, plan("remove exactly one helicopter"))
    assert out.path and out.after == 2 and out.expected == 2
    assert "count check: 2 left ✓" in out.message and "smallest one" in out.message
    before = np.asarray(Image.open(edit_env.src).convert("RGB")).astype(int)
    after_img = Image.open(out.path)
    assert after_img.size == (1344, 768)  # full resolution, not 1024 px
    after = np.asarray(after_img.convert("RGB")).astype(int)
    changed = np.any(before != after, axis=2)
    ys, xs = np.nonzero(changed)
    x1, y1, x2, y2 = HELIS[2]
    # every changed pixel lies within the grown, feathered box around the chosen helicopter
    assert xs.min() >= (x1 - 0.06) * 1344 and xs.max() <= (x2 + 0.06) * 1344
    assert ys.min() >= (y1 - 0.06) * 768 and ys.max() <= (y2 + 0.06) * 768
    assert changed[int((y1 + y2) / 2 * 768), int((x1 + x2) / 2 * 1344)]
    # the raw crop render is not left in the gallery, and the working files are gone
    assert sorted(p.name for p in edit_env.gallery.iterdir()) == ["jarvis_edit_local_00001_.png",
                                                                   "jarvis_qwen_00012_.png"]
    assert not any((edit_env.src.parent.parent / "edit_work").iterdir())
    assert not any((edit_env.comfy / "input").iterdir()) and not any((edit_env.comfy / "output").iterdir())
    assert '"before": 3' in after_img.info["aria_edit"]


def test_a_failed_removal_is_retried_once_only(edit_env):
    from jarvis import comfyui_local_edit

    edit_env.answers = [list(HELIS), list(HELIS), list(HELIS)]  # the helicopter "never goes away"
    out = comfyui_local_edit.run(edit_env.src, plan("remove one helicopter"))
    assert len(edit_env.workflows) == 2 and edit_env.sessions == 1
    assert out.path and out.detail["attempts"] == 2
    assert "still finds 3 (expected 2)" in out.message and not out.message.startswith("Removed")


def test_nothing_is_rendered_when_the_counts_contradict(edit_env):
    from jarvis import comfyui_local_edit

    edit_env.answers = [list(HELIS)]
    out = comfyui_local_edit.run(edit_env.src, plan(USER_INSTRUCTION))
    assert not out.path and out.question and edit_env.workflows == []


def test_without_the_helper_it_falls_back_to_a_whole_image_edit(edit_env, monkeypatch):
    from jarvis import comfyui_local_edit, image_verify

    monkeypatch.setattr(image_verify, "locate", lambda path, noun: None)
    out = comfyui_local_edit.run(edit_env.src, plan("remove one helicopter"))
    assert not out.handled and edit_env.workflows == []


@pytest.mark.parametrize("uncensored", [False, True])
def test_each_mode_keeps_its_own_editing_model(edit_env, monkeypatch, uncensored):
    from jarvis import comfyui_local_edit

    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: uncensored)
    monkeypatch.setattr("jarvis.comfyui._find_checkpoint", lambda c=None: "lustifySDXLNSFWSFW_v10.safetensors")
    edit_env.answers = [list(HELIS), HELIS[:2]]
    assert comfyui_local_edit.run(edit_env.src, plan("remove one helicopter")).path
    classes = {node["class_type"]: node["inputs"] for node in edit_env.workflows[0].values()}
    if uncensored:
        assert classes["CheckpointLoaderSimple"]["ckpt_name"].startswith("lustify")
        assert "UNETLoader" not in classes
    else:
        assert classes["UNETLoader"]["unet_name"].startswith("flux-2-klein")
        assert "CheckpointLoaderSimple" not in classes


def test_whole_image_klein_edits_keep_the_source_resolution(tmp_path):
    from jarvis.comfyui_edit import _klein_dims

    for size, expected in [((1344, 768), (1344, 768)), ((1024, 1024), (1024, 1024))]:
        p = tmp_path / f"{size[0]}.png"
        Image.new("RGB", size).save(p)
        assert _klein_dims(p) == expected
    big = tmp_path / "big.png"
    Image.new("RGB", (2688, 1536)).save(big)
    w, h = _klein_dims(big)
    assert w * h <= 1_050_000 and abs(w / h - 1.75) < 0.02


# --- handler: replies and history ----------------------------------------------------------------
@pytest.fixture
def handler(monkeypatch, tmp_path):
    from jarvis.handlers import media

    recorded = []
    a = SimpleNamespace(
        session=SimpleNamespace(last_image=str(tmp_path / "a.png"), note_image=lambda p: recorded.append(("note", p))),
        image=SimpleNamespace(last_image=""),
        conversation=SimpleNamespace(add_assistant=lambda text: recorded.append(("assistant", text))),
        branches=SimpleNamespace(persist=lambda session=None: recorded.append(("persist", None))),
    )
    monkeypatch.setattr(media, "_mark_edit_output", lambda *a: None)
    monkeypatch.setattr("jarvis.cache_state.invalidate_gallery", lambda: None)
    monkeypatch.setattr(media, "raise_if_cancelled", lambda: None)
    return SimpleNamespace(h=media.MediaHandler(a), recorded=recorded, tmp=tmp_path)


def test_a_local_edit_reply_is_kept_in_the_conversation(handler, monkeypatch):
    from jarvis.comfyui_local_edit import Outcome

    out_path = str(handler.tmp / "jarvis_edit_local_00001_.png")
    monkeypatch.setattr("jarvis.image_post.local_edit", lambda path, prompt: Outcome(
        path=out_path, message="Removed 1 helicopter (the smallest one, middle right); everything else is unchanged"))
    res = handler.h.edit_image({"prompt": "remove one helicopter"}, "")
    assert res["ok"] and res["image_path"] == out_path and "Removed 1 helicopter" in res["message"]
    texts = [t for kind, t in handler.recorded if kind == "assistant"]
    assert texts and "/api/gallery/jarvis_edit_local_00001_.png" in texts[0]
    assert ("note", out_path) in handler.recorded


def test_a_question_is_answered_without_an_image(handler, monkeypatch):
    from jarvis.comfyui_local_edit import Outcome

    monkeypatch.setattr("jarvis.image_post.local_edit", lambda path, prompt: Outcome(
        message="I count 3 helicopters in this image, not 4. …", question=True))
    called = []
    monkeypatch.setattr("jarvis.image_post.edit_image", lambda *a, **k: called.append(1) or "x")
    res = handler.h.edit_image({"prompt": USER_INSTRUCTION}, "")
    assert res["ok"] and res.get("type") == "image_edit_question" and "image_path" not in res
    assert not called
    assert any(kind == "assistant" and "I count 3" in t for kind, t in handler.recorded)


def test_a_failed_local_edit_asks_before_a_full_redraw(handler, monkeypatch):
    from jarvis.comfyui_local_edit import Outcome

    handler.h.a.session.pending_clarification = None
    called = []
    monkeypatch.setattr("jarvis.image_post.local_edit", lambda path, prompt: Outcome(
        handled=False, message="I couldn't find a car in this image"))
    monkeypatch.setattr("jarvis.image_post.edit_image", lambda *a, **k: called.append(1) or "x")
    res = handler.h.edit_image({"prompt": "make the car red"}, "")
    assert res["ok"] and res["type"] == "image_edit_question" and res["no_media_expected"]
    assert "I couldn't find a car" in res["message"] and "redraw it" in res["message"] and not called
    assert handler.h.a.session.pending_clarification["type"] == "image_full_redraw"


def test_a_confirmed_full_redraw_runs_the_whole_image_editor(handler, monkeypatch):
    out_path = str(handler.tmp / "jarvis_edit_klein_00001_.png")
    monkeypatch.setattr("jarvis.image_post.local_edit", lambda *a: pytest.fail("local edit after a confirmed redraw"))
    monkeypatch.setattr("jarvis.image_post.edit_image", lambda path, prompt, denoise=None: out_path)
    res = handler.h.edit_image({"prompt": "add a dragon in the sky", "full_redraw": True}, "")
    assert res["ok"] and res["image_path"] == out_path and "whole image" in res["message"]


@pytest.mark.parametrize("prompt", ["make it look like winter", "make the sky orange", "turn it into a watercolor painting"])
def test_whole_picture_changes_need_no_confirmation(handler, monkeypatch, prompt):
    out_path = str(handler.tmp / "jarvis_edit_klein_00002_.png")
    monkeypatch.setattr("jarvis.image_post.local_edit", lambda path, p: None)
    monkeypatch.setattr("jarvis.image_post.edit_image", lambda path, p, denoise=None: out_path)
    assert handler.h.edit_image({"prompt": prompt}, "")["image_path"] == out_path


def test_an_explicit_denoise_skips_the_local_editor(handler, monkeypatch):
    called = []
    monkeypatch.setattr("jarvis.image_post.local_edit", lambda *a: called.append(1))
    monkeypatch.setattr("jarvis.image_post.edit_image", lambda path, prompt, denoise=None: str(handler.tmp / "e.png"))
    assert handler.h.edit_image({"prompt": "remove one helicopter", "denoise": 0.6}, "")["ok"]
    assert not called


# --- routing ------------------------------------------------------------------------------------
def _session_with_image(tmp_path):
    from jarvis.session import SessionContext

    img = tmp_path / "jarvis_qwen_00012_.png"
    Image.new("RGB", (8, 8)).save(img)
    s = SessionContext()
    s.note_image(str(img), prompt="a jet on a carrier")
    s.last_image_at = time.time() - 3600  # well outside the 20-minute follow-up window
    s.last_action = "chat"
    return s


def test_edit_the_image_you_just_generated_drops_the_relative_clause(tmp_path):
    from jarvis.router import route

    msg = "Edit the image you just generated.\r\n\r\nKeep the fighter jet exactly as it is.\r\n\r\nRemove exactly ONE helicopter."
    out = route(msg, _session_with_image(tmp_path))
    assert out["action"] == "edit_image"
    assert out["params"]["prompt"].startswith("Keep the fighter jet")


def test_a_keep_the_existing_image_directive_is_an_edit_not_chat(tmp_path):
    from jarvis.router import route

    msg = ("Keep the existing image composition, all five warriors, three helicopters, pilot, jet, storm, lighting, "
           "and camera angle exactly as they are.\r\n\r\nCorrect only these details:\r\n\r\n1. The warrior directly "
           "in front of the jet must wear completely black armor.")
    out = route(msg, _session_with_image(tmp_path))
    assert out["action"] == "edit_image" and out["params"]["prompt"] == msg.strip()


def test_the_directive_without_an_image_asks_which_image():
    from jarvis.router import route
    from jarvis.session import SessionContext

    out = route("Keep the existing image composition and make the sky darker.", SessionContext())
    assert out["action"] != "edit_image"


# --- count check ---------------------------------------------------------------------------------
def test_per_item_counts_are_not_scene_counts():
    from jarvis.image_verify import expected_counts

    prompt = ("Exactly FIVE adult female warriors, all fully visible, with realistic human anatomy, two arms and two "
              "legs each. TWO warriors to the LEFT of the jet. BACKGROUND: Exactly THREE helicopters in the sky.")
    assert expected_counts(prompt) == [(5, "warriors"), (3, "helicopters")]


# --- false "edited" claims -----------------------------------------------------------------------
@pytest.mark.parametrize("reply,claim", [
    ("The image has been adjusted to meet your specifications.", True),
    ("I've updated the image so the armor is black.", True),
    ("An edit model changes the image you give it.", False),
])
def test_chat_cannot_claim_an_edit_that_never_ran(reply, claim):
    from jarvis.capability_truthfulness import _MEDIA_CLAIM

    assert bool(_MEDIA_CLAIM.search(reply)) is claim


# --- reliability behind the 16:56 watchdog restart -----------------------------------------------
def test_provider_recovery_does_not_block_the_event_loop(monkeypatch):
    from fastapi import FastAPI

    from jarvis.provider_health import recovery
    from jarvis.provider_health.api import register_product_routes

    monkeypatch.setattr(recovery, "recover", lambda **kw: time.sleep(0.6) or {"ok": True})
    app = FastAPI()
    register_product_routes(app, None)
    endpoint = next(r for r in app.routes if getattr(r, "path", None) == "/api/provider/recover").endpoint

    class Req:
        async def json(self):
            return {"code": "FIRST_PROGRESS_TIMEOUT"}

    async def main():
        ticks = 0

        async def ticker():
            nonlocal ticks
            while True:
                await asyncio.sleep(0.05)
                ticks += 1

        t = asyncio.create_task(ticker())
        out = await endpoint(Req())
        t.cancel()
        return out, ticks

    out, ticks = asyncio.run(main())
    assert out == {"ok": True} and ticks >= 6  # the loop kept running while recovery waited


def test_hidden_thinking_counts_as_provider_progress(monkeypatch):
    from jarvis import gpu_scheduler, stream_progress
    from jarvis.inference import gateway

    @contextlib.contextmanager
    def admit(model, options=None, *, label=""):
        yield SimpleNamespace(kind="shared", host=None, options={}, check=lambda: None)

    monkeypatch.setattr(gpu_scheduler, "admit_ollama", admit)
    monkeypatch.setattr(gateway.boundary, "require_local_model_name", lambda m: None)
    monkeypatch.setattr(gateway, "_ollama_client_chat", lambda job: lambda **kw: iter(
        [{"message": {"thinking": "hmm", "content": ""}}, {"message": {"content": "Hi"}}]))
    stream_progress.clear("req-1")
    stream_progress.bind("req-1")
    try:
        assert list(gateway._ollama_stream("deepseek-r1:14b", [{"role": "user", "content": "x"}])) == ["Hi"]
    finally:
        stream_progress.bind("")
    assert stream_progress.last("req-1") > 0


def test_cancel_closes_the_provider_stream_and_its_gpu_slot(monkeypatch):
    from jarvis import chat_cancel, llm

    released = []

    def provider():
        try:
            yield "a"
            time.sleep(0.2)
            yield "b"
            yield "c"
        finally:
            released.append(time.monotonic())

    chat_cancel.cancel("cancel-key")
    gen = provider()  # still referenced, as the gateway stream is by its callers: no GC rescue
    list(llm._iter_blocking_cancellable(gen, cancel_key="cancel-key"))
    deadline = time.monotonic() + 2
    while not released and time.monotonic() < deadline:
        time.sleep(0.02)
    assert released, "the provider generator (and its GPU admission) was left suspended"


def test_a_heavy_timeout_names_the_jobs_holding_the_rtx(monkeypatch):
    from jarvis import gpu_scheduler

    monkeypatch.setattr(gpu_scheduler, "HEAVY_WAIT_S", 0.3)
    sched = gpu_scheduler._Scheduler()
    holder = gpu_scheduler.Job("shared", "deepseek-r1:14b chat")
    sched._active.add(holder)
    sched._shared = 1
    with pytest.raises(gpu_scheduler.GpuUnavailable) as exc:
        sched._acquire_heavy(gpu_scheduler.Job("image", "jarvis_edit"), {"vram_mib": 1, "ram_mib": 1})
    assert "shared deepseek-r1:14b chat idle" in exc.value.reason


# --- live findings (2026-10-14 18:00) ------------------------------------------------------------
LIGHTHOUSES = [(0.100, 0.072, 0.177, 0.372), (0.517, 0.397, 0.535, 0.424)]  # red tower + tiny beacon


def test_the_obvious_object_is_edited_without_asking(edit_env):
    from jarvis import comfyui_local_edit

    edit_env.answers = [list(LIGHTHOUSES)]
    out = comfyui_local_edit.run(edit_env.src, plan("replace the lighthouse with a stone castle tower"))
    assert out.path and "largest one" in out.message and len(edit_env.workflows) == 1


def test_similar_objects_are_still_asked_about(edit_env):
    from jarvis import comfyui_local_edit

    edit_env.answers = [list(HELIS[:2])]
    out = comfyui_local_edit.run(edit_env.src, plan("replace the helicopter with a dragon"))
    assert out.question and not out.path and edit_env.workflows == []


def test_an_edit_that_changes_nothing_reaches_the_owner(monkeypatch):
    from jarvis import media_jobs

    monkeypatch.setattr("jarvis.resource_router.prepare_for_media_job", lambda kind: None)
    monkeypatch.setattr("jarvis.resource_router.record_media_outcome", lambda *a, **k: None)
    reply = {"ok": True, "message": "I count 3 helicopters in this image, not 4. …", "module": "image",
             "no_media_expected": True, "type": "image_edit_question"}
    job_id = media_jobs.submit("edit_image", "Image edit", lambda: reply)
    deadline = time.time() + 60
    while time.time() < deadline and not (media_jobs.get_job(job_id) or {}).get("done"):
        time.sleep(0.05)
    result = media_jobs.get_job(job_id)["result"]
    assert result["ok"] is True and result["message"].startswith("I count 3 helicopters")
