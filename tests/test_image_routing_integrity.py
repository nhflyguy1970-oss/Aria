"""Image-generation routing and response integrity (2026-10-13 fighter-pilot/witches incident).

Observed: one request reached three wrong tools —
  A) briefing_news_detail: two words shared with a local headline → NH/VT news research
  B) generate_image with prompt ", not a written description." → a generated mountain lake
  C) coding_show: "display it" + a stale last_file → ARIA's own pyproject.toml
"""
from __future__ import annotations

import json
import os
import time
from unittest.mock import MagicMock

import pytest

from jarvis.router import route
from jarvis.session import SessionContext

SCENE = ("a modern fighter pilot flying a powerful military fighter jet directly toward the camera. The pilot is "
         "clearly visible through the cockpit canopy. Exactly five terrifying witches on flying broomsticks are "
         "chasing the aircraft from behind. Dark storm clouds, lightning, magical green and purple trails, "
         "cinematic lighting, 16:9 widescreen.")
ACCEPT = ("Generate a photorealistic cinematic image of a modern fighter pilot flying directly toward the camera in a "
          "military fighter jet. The pilot is clearly visible through the cockpit canopy. Exactly five terrifying "
          "witches on flying broomsticks are chasing the aircraft from behind. All five witches must be visible "
          "through or around the cockpit canopy. Dark storm clouds, lightning, magical green and purple trails, "
          "cinematic lighting, 16:9 widescreen.")
MARKDOWN = ("**Cinematic Fighter Pilot Being Chased by Five Witches**\r\n\r\n"
            "Create an ultra-realistic, cinematic, high-action image of " + SCENE)
NO_WEB = ("**IMAGE GENERATION ONLY — DO NOT SEARCH THE WEB**\r\n\r\n"
          "Generate an original, photorealistic cinematic image. This is a fictional scene: " + SCENE +
          "\r\n\r\nCreate the image, not a written description.")
COMFY = ("Generate an image using ComfyUI. Do not search the web, use research tools, or provide citations.\r\n\r\n"
         "Create a photorealistic cinematic action scene of " + SCENE + " Display it when it is done.")
HEADLINES = [{"title": "Mary Page Obituary (2026) - Claremont, NH - Valley News", "category": "local"},
             {"title": "Schedule - Newport Tigers (Newport, NH) Football 26-27", "category": "local"}]


@pytest.fixture(autouse=True)
def local_headlines(monkeypatch):
    monkeypatch.setattr("jarvis.briefing_news.load_recent_headlines", lambda *a, **k: list(HEADLINES))


def _session(**ctx) -> SessionContext:
    s = SessionContext()
    for k, v in ctx.items():
        setattr(s, k, v)
    return s


# 1. Natural-language image requests select image generation ------------------------------
@pytest.mark.parametrize("message", [
    "Create an image of a fighter pilot being chased by five witches.",
    "create an image of a pilot in a jet fighter cockpit flying being chased by five witches",
    "can you generate an image of a cat?",
    "Make me a picture showing a red barn in the snow",
    "Please render an illustration of a lighthouse at night",
    MARKDOWN, NO_WEB, ACCEPT,
])
def test_image_requests_select_image_generation(message):
    out = route(message, _session())
    assert out["action"] == "generate_image", out


# 2. Explicit ComfyUI requests ------------------------------------------------------------
def test_explicit_comfyui_request_generates_and_strips_the_backend_instruction():
    out = route("Generate an image of a cat using ComfyUI", _session())
    assert out["action"] == "generate_image" and out["params"]["prompt"] == "a cat"


def test_bare_comfyui_request_asks_what_to_draw_then_uses_the_reply():
    s = _session()
    first = route("Generate an image using ComfyUI", s)
    assert first["action"] == "clarify" and first["clarification_question"] == "What should the image show?"
    reply = route("a red barn in a snowy field at sunset", s)
    assert reply["action"] == "generate_image"
    assert reply["params"]["prompt"] == "a red barn in a snowy field at sunset"


# 3. Complete prompt preservation ---------------------------------------------------------
@pytest.mark.parametrize("message", [MARKDOWN, NO_WEB, COMFY, ACCEPT])
def test_full_description_reaches_the_backend(message):
    prompt = route(message, _session())["params"]["prompt"]
    for must in ("fighter pilot", "cockpit canopy", "Exactly five terrifying witches", "broomsticks",
                 "green and purple trails", "16:9 widescreen"):
        assert must in prompt, (must, prompt)
    for meta in ("not a written description", "DO NOT SEARCH", "Do not search", "citations", "ComfyUI", "**"):
        assert meta not in prompt, (meta, prompt)


def test_prompt_is_not_reduced_to_a_line_tail():
    """The exact live failure: the old extractor sent ', not a written description.'"""
    prompt = route(NO_WEB, _session())["params"]["prompt"]
    assert len(prompt) > 200 and not prompt.startswith(",")


def test_widescreen_ratio_is_respected(monkeypatch):
    from jarvis.modules import image as image_mod

    monkeypatch.setattr(image_mod, "_active_model_family", lambda: "flux")
    assert image_mod._scene_dimensions(ACCEPT) == (1344, 768)
    assert image_mod._scene_dimensions("a lighthouse, 9:16 vertical") == (768, 1344)
    assert image_mod._scene_dimensions("a cat") == (1024, 1024)


# 4. Result association -------------------------------------------------------------------
def test_workflow_result_comes_from_its_own_prompt_id(monkeypatch, tmp_path):
    from jarvis import comfyui

    monkeypatch.setattr(comfyui, "OUTPUT_DIR", tmp_path)
    histories = {"mine": {"outputs": {"9": {"images": [{"filename": "jarvis_00500_.png", "subfolder": "", "type": "output"}]}},
                          "status": {"completed": True, "messages": []}},
                 "other": {"outputs": {"9": {"images": [{"filename": "jarvis_00499_.png", "subfolder": "", "type": "output"}]}},
                           "status": {"completed": True, "messages": []}}}

    class Resp:
        def __init__(self, body):
            self.body = json.dumps(body).encode()

        def read(self):
            return self.body

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(req, timeout=0):
        url = req if isinstance(req, str) else req.full_url
        if url.endswith("/prompt"):
            return Resp({"prompt_id": "mine"})
        if "/history/mine" in url:
            return Resp({"mine": histories["mine"]})  # only this request's entry
        raise AssertionError(f"unexpected {url}")

    downloaded = []
    monkeypatch.setattr(comfyui.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(comfyui, "_download_output", lambda url, out, timeout=None: downloaded.append(url) or out.write_bytes(b"png"))
    monkeypatch.setattr(comfyui.time, "sleep", lambda s: None)
    out = comfyui._run_workflow_queued({}, "jarvis", "client", timeout_sec=5, cancel_check=lambda: False)
    assert out.endswith("jarvis_00500_.png") and "jarvis_00499" not in downloaded[0]


# 5. No unrelated web research ------------------------------------------------------------
def test_headline_word_overlap_does_not_hijack_an_image_request():
    out = route("Create an image of Mary standing in a misty valley at dawn, photorealistic", _session())
    assert out["action"] == "generate_image"


def test_long_unrelated_message_is_not_matched_to_a_headline():
    from jarvis.briefing_news import briefing_news_intent

    msg = ("I have been thinking about Mary and the valley trip we took last summer, the long drive, the hiking, "
           "the old mill, the covered bridge and the diner by the river")
    assert briefing_news_intent(msg, _session()) is None


def test_short_headline_follow_up_still_works():
    from jarvis.briefing_news import briefing_news_intent

    out = briefing_news_intent("tell me more about the Mary Page story", _session(last_module="briefing"))
    assert out and out["action"] == "briefing_news_detail"


def test_do_not_search_the_web_never_routes_to_web_search(monkeypatch):
    from jarvis import router

    intent = router._respect_negated_web({"action": "web_search", "params": {}},
                                         "Summarize the plot of Dune. Do not search the web.")
    assert intent["action"] == "chat"
    intent = router._respect_negated_web({"action": "web_search", "params": {}}, NO_WEB)
    assert intent["action"] == "generate_image"
    plain = router._respect_negated_web({"action": "web_search", "params": {}}, "search the web for Dune reviews")
    assert plain["action"] == "web_search"


# 6. No unrelated source-code / config responses ------------------------------------------
def test_display_it_with_a_stale_last_file_does_not_show_the_file():
    s = _session(last_file="/media/jeff/AI/jarvis/pyproject.toml", last_module="coding")
    out = route(COMFY, s)
    assert out["action"] == "generate_image"
    assert "pyproject" not in json.dumps(out)


def test_show_it_follow_up_still_shows_the_last_file_when_not_an_image_request():
    s = _session(last_file="/media/jeff/AI/jarvis/pyproject.toml", last_module="coding")
    assert route("show it", s)["action"] == "coding_show"


# 7. No stale gallery images presented as new ----------------------------------------------
@pytest.fixture
def quick_jobs(monkeypatch):
    monkeypatch.setattr("jarvis.resource_router.prepare_for_media_job", lambda kind: None)
    monkeypatch.setattr("jarvis.resource_router.record_media_outcome", lambda *a, **k: None)


def _run_media_job(monkeypatch, result: dict) -> dict:
    from jarvis import media_jobs

    job_id = media_jobs.submit("generate_image", "Image generation", lambda: result)
    deadline = time.time() + 60
    while time.time() < deadline:
        job = media_jobs.get_job(job_id)
        if job and job.get("done"):
            return job
        time.sleep(0.05)
    raise AssertionError("job did not finish")


def test_an_existing_image_is_never_reported_as_a_new_result(monkeypatch, tmp_path, quick_jobs):
    old = tmp_path / "jarvis_00001_.png"
    old.write_bytes(b"png")
    past = time.time() - 3600
    os.utime(old, (past, past))
    job = _run_media_job(monkeypatch, {"ok": True, "image_path": str(old), "image_name": old.name, "module": "image"})
    assert job["result"]["ok"] is False and "existed before this request" in job["result"]["message"]


def test_a_fresh_image_completes(monkeypatch, tmp_path, quick_jobs):
    new = tmp_path / "jarvis_00002_.png"

    def make():
        new.write_bytes(b"png")
        return {"ok": True, "image_path": str(new), "image_name": new.name, "module": "image"}

    from jarvis import media_jobs

    job_id = media_jobs.submit("generate_image", "Image generation", make)
    deadline = time.time() + 60
    while time.time() < deadline and not (media_jobs.get_job(job_id) or {}).get("done"):
        time.sleep(0.05)
    assert media_jobs.get_job(job_id)["result"]["ok"] is True


# 8. ComfyUI unavailable --------------------------------------------------------------------
def test_comfyui_unavailable_reports_an_image_error_not_another_tool(monkeypatch):
    from jarvis import comfyui

    monkeypatch.setattr(comfyui, "is_available", lambda: False)
    monkeypatch.setattr("jarvis.vram_guard.prepare_for_comfyui", lambda *a, **k: None)
    monkeypatch.setattr("jarvis.services.ensure_comfyui_nvidia", lambda *a, **k: False)
    monkeypatch.setattr(comfyui, "_selected_zimage", lambda: False)
    monkeypatch.setattr("jarvis.comfyui_settings.auto_fallback_enabled", lambda: False)
    out = comfyui.generate("a fighter pilot chased by five witches")
    assert out.startswith("ERROR: ComfyUI is not running")

    from jarvis.handlers.media import MediaHandler

    assistant = MagicMock()
    assistant.image.generate.return_value = out
    res = MediaHandler(assistant).generate_image({"prompt": "a fighter pilot", "enhance": False}, "")
    assert res["ok"] is False and res["module"] == "image" and "ComfyUI is not running" in res["message"]
    assert res.get("actions")  # retry / Mission Control, never a silent switch to research


# 9. Context changes ------------------------------------------------------------------------
@pytest.mark.parametrize("ctx", [
    {"last_module": "briefing"},
    {"last_module": "coding", "last_file": "/media/jeff/AI/jarvis/pyproject.toml"},
    {"last_module": "research"},
    {"last_module": "image", "last_image": "/tmp/old.png"},
])
def test_image_request_after_any_context(ctx):
    assert route(ACCEPT, _session(**ctx))["action"] == "generate_image"


def test_edit_of_the_previous_image_is_still_an_edit(tmp_path):
    img = tmp_path / "jarvis_00003_.png"
    img.write_bytes(b"png")
    s = _session(last_image=str(img), last_action="generate_image", last_module="image")
    assert route("make the previous image brighter", s)["action"] != "generate_image"


# 10. Consecutive tool requests ---------------------------------------------------------------
def test_consecutive_requests_each_get_their_own_tool():
    s = _session(last_file="/media/jeff/AI/jarvis/pyproject.toml", last_module="coding")
    seq = [
        (ACCEPT, "generate_image"),
        ("show it", "coding_show"),
        ("Create an image of a lighthouse at night", "generate_image"),
        (COMFY, "generate_image"),
    ]
    for message, expected in seq:
        out = route(message, s)
        assert out["action"] == expected, (message[:40], out["action"])
        if expected == "generate_image":
            s.last_action, s.last_module = "generate_image", "image"
        else:
            s.last_module = "coding"


# 11. Error reporting and fallback restrictions -----------------------------------------------
def test_questions_about_image_generation_are_not_generation_requests():
    from jarvis.image_request import is_image_generation_request

    assert not is_image_generation_request("how do you create images?")
    assert not is_image_generation_request("what model do you use to generate images?")
    assert not is_image_generation_request("don't create an image, just describe the scene")


def test_action_log_records_route_reason_and_full_prompt(monkeypatch, tmp_path):
    from jarvis import action_log

    monkeypatch.setattr(action_log, "LOG_FILE", tmp_path / "action_log.json", raising=False)
    rows = []
    monkeypatch.setattr(action_log, "_load", lambda: rows)
    monkeypatch.setattr(action_log, "_save", lambda entries: None)
    action_log.log_action("generate_image", "image", ACCEPT, True, route_reason="explicit_image_request", prompt=ACCEPT)
    assert rows[-1]["route_reason"] == "explicit_image_request" and rows[-1]["prompt"] == ACCEPT
