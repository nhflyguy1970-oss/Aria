"""Idle RTX load (2026-10-14 evening) and conversational local image edits.

The RTX 3060 ran at 70-86 % while ARIA was idle: the tray's 30-minute git sync re-embedded the
whole ARIA repository (21,084 chunks, one request each) whenever the working tree had
uncommitted changes — about 40,000 embed requests an hour, around the clock since at least
Oct 12. And ARIA's own health probe kept the chat model loaded forever.
"""
from __future__ import annotations

import contextlib
import json
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image, ImageDraw

from jarvis.image_edit_plan import plan, whole_image_reason


# --- repository index: reuse and batch embeddings --------------------------------------------------
@pytest.fixture
def embeds(monkeypatch):
    from jarvis import llm

    calls = SimpleNamespace(requests=0, texts=0, busy=False)

    def batch(texts):
        calls.requests += 1
        calls.texts += len(texts)
        return [[float(len(t)), 1.0] for t in texts]

    monkeypatch.setattr(llm, "embed_batch", batch)
    monkeypatch.setattr(llm, "embed_text", lambda t: pytest.fail("one request per chunk"))
    monkeypatch.setattr(llm, "embed_session", contextlib.nullcontext)
    monkeypatch.setattr("jarvis.ollama_runtime.chat_priority_active", lambda: calls.busy)
    return calls


def _repo(tmp_path, n_files=5):
    root = tmp_path / "repo"
    root.mkdir()
    for i in range(n_files):
        (root / f"m{i}.py").write_text("\n".join(f"def f{i}_{j}():\n    return {j}" for j in range(400)))
    return root


def test_an_unchanged_repository_is_not_embedded_again(tmp_path, embeds):
    from jarvis.knowledge.repo_index import build_repo_index

    root, index = _repo(tmp_path), tmp_path / "index.json"
    chunks = build_repo_index(root, index_path=index)
    first = embeds.texts
    assert first == chunks and embeds.requests <= first // 32 + 5  # batched, not one per chunk
    embeds.requests = embeds.texts = 0
    assert build_repo_index(root, index_path=index) == chunks
    assert embeds.texts == 0  # was: every chunk again, every 30 minutes


def test_only_changed_chunks_are_embedded(tmp_path, embeds):
    from jarvis.knowledge.repo_index import build_repo_index

    root, index = _repo(tmp_path), tmp_path / "index.json"
    build_repo_index(root, index_path=index)
    embeds.texts = 0
    (root / "m0.py").write_text("def changed():\n    return 'new'\n")
    build_repo_index(root, index_path=index)
    assert 0 < embeds.texts <= 2


def test_indexing_yields_to_chat_and_catches_up_later(tmp_path, embeds):
    from jarvis.knowledge.repo_index import build_repo_index

    root, index = _repo(tmp_path, 2), tmp_path / "index.json"
    embeds.busy = True
    build_repo_index(root, index_path=index)
    assert embeds.texts == 0
    embeds.busy = False
    build_repo_index(root, index_path=index)
    stored = json.loads(index.read_text())
    assert embeds.texts == len(stored) and all(c["embedding"] for c in stored)


# --- git sync: first sync of a new repo, dirty trees ------------------------------------------------
@pytest.fixture
def git_env(monkeypatch, tmp_path):
    from jarvis.knowledge import git_sync

    state = tmp_path / "git_repos.json"
    state.write_text(json.dumps({"repos": {"someone-else": {"id": "x", "path": "/x", "label": "x"}}}))
    monkeypatch.setattr(git_sync, "REPOS_STATE_FILE", state)
    monkeypatch.setattr(git_sync, "REPOS_INDEX_ROOT", tmp_path / "repos")
    monkeypatch.setattr(git_sync, "_register_in_knowledge_registry", lambda st: None)
    monkeypatch.setattr(git_sync, "_open_pull_requests", lambda r: [])
    monkeypatch.setattr(git_sync, "_remote_url", lambda r: "")
    monkeypatch.setattr(git_sync, "current_branch", lambda r: "main")
    monkeypatch.setattr(git_sync, "_head_commit", lambda r: "abc123")
    env = SimpleNamespace(dirty=True, fingerprint="fp1", builds=0, state=state)
    monkeypatch.setattr(git_sync, "has_local_changes", lambda r: env.dirty)
    monkeypatch.setattr(git_sync, "_worktree_fingerprint", lambda r, head: env.fingerprint)

    def build(root, *, index_path, changed_files=None, cancel_check=None):
        env.builds += 1
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text("[]")
        return 7

    monkeypatch.setattr("jarvis.knowledge.repo_index.build_repo_index", build)
    return env


def test_a_newly_tracked_repository_completes_its_first_sync(git_env, tmp_path):
    from jarvis.knowledge.git_sync import sync_repository

    st = sync_repository(tmp_path)  # used to raise TypeError: from_dict({}) — ok=False since July
    assert st.indexing_status == "indexed" and st.chunk_count == 7 and git_env.builds == 1


def test_a_dirty_tree_is_reindexed_only_when_it_changes(git_env, tmp_path):
    from jarvis.knowledge.git_sync import sync_repository

    sync_repository(tmp_path)
    sync_repository(tmp_path)
    sync_repository(tmp_path)
    assert git_env.builds == 1  # was: a full rebuild on every 30-minute sync while dirty
    git_env.fingerprint = "fp2"  # an uncommitted file was edited
    sync_repository(tmp_path)
    assert git_env.builds == 2


def test_the_worktree_fingerprint_follows_file_edits(tmp_path):
    import subprocess

    from jarvis.knowledge.git_sync import _worktree_fingerprint

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    f = tmp_path / "a.py"
    f.write_text("x = 1\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "a.py"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"],
                   check=True)
    clean = _worktree_fingerprint(tmp_path, "h")
    f.write_text("x = 2\n")
    dirty = _worktree_fingerprint(tmp_path, "h")
    assert clean != dirty and dirty == _worktree_fingerprint(tmp_path, "h")
    time.sleep(0.01)
    f.write_text("x = 33\n")
    assert _worktree_fingerprint(tmp_path, "h") != dirty


# --- health probe must not pin the chat model ------------------------------------------------------
def test_the_health_probe_keeps_the_models_remaining_keep_alive(monkeypatch):
    from datetime import datetime, timedelta, timezone

    from jarvis import ollama_health

    expires = (datetime.now(timezone.utc) + timedelta(seconds=200)).isoformat()
    sent = {}

    class Resp:
        def __init__(self, body):
            self.body = body

        def read(self):
            return json.dumps(self.body).encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def urlopen(req, timeout=0):
        url = req if isinstance(req, str) else req.full_url
        if url.endswith("/api/ps"):
            return Resp({"models": [{"name": "gemma4:12b", "expires_at": expires}]})
        sent.update(json.loads(req.data))
        return Resp({"response": ""})

    monkeypatch.setattr(ollama_health.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr("jarvis.gpu_scheduler.defer_direct_load", lambda m: "")
    ollama_health._soft_generate_probe("http://127.0.0.1:11434", "gemma4:12b", timeout=5)
    assert 190 <= int(sent["keep_alive"].rstrip("s")) <= 200  # was: unset → reset to 5 min each probe


# --- conversational edit language -----------------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    ("Get rid of the helicopter.", ("remove", "helicopter", "")),
    ("Take that person out.", ("remove", "person", "")),
    ("Make the car red.", ("change", "car", "red")),
    ("Move the object to the left.", ("move", "object", "left")),
    ("Remove the fishing rod too.", ("remove", "fishing rod", "")),
    ("Remove the man. Keep everything else exactly the same.", ("remove", "man", "")),
    ("paint the boat on the left bright yellow", ("change", "boat", "bright yellow")),
    ("change the car to dark green", ("change", "car", "dark green")),
    ("turn the man's shirt red", ("change", "man's shirt", "red")),
    ("move the boat a little to the right", ("move", "boat", "right")),
    ("Move the seagull on the left a little to the right.", ("move", "seagull", "right")),
    ("change the car into a truck", ("replace", "car", "a truck")),
])
def test_conversational_phrasings_are_local_edits(text, expected):
    p = plan(text)
    assert p and (p.op, p.target, p.replacement or p.direction) == expected


def test_only_the_object_means_no_attached_parts():
    assert plan("remove the man").with_attached and not plan("remove only the man").with_attached


@pytest.mark.parametrize("text,asks", [
    ("make it look like winter", False), ("make the sky orange", False), ("turn it into a watercolor painting", False),
    ("add a dragon in the sky", True), ("make the warrior look angrier", True),
    ("remove the man and replace the boat with a car", True), ("full redraw: add a dragon", False),
])
def test_when_a_full_redraw_needs_asking(text, asks):
    assert bool(whole_image_reason(text)) is asks


def _session(tmp_path, *, in_play=True):
    from jarvis.session import SessionContext

    img = tmp_path / "harbor.png"
    Image.new("RGB", (8, 8)).save(img)
    s = SessionContext()
    s.note_image(str(img), prompt="a harbor")
    s.last_action = "edit_image" if in_play else "chat"
    if not in_play:
        s.last_image_at = time.time() - 7200
    return s


@pytest.mark.parametrize("msg", ["Get rid of the helicopter.", "Take that person out.", "Paint the boat dark blue.",
                                 "Remove the fishing rod too.", "Make the car red."])
def test_local_edit_phrasings_reach_the_editor(tmp_path, msg):
    from jarvis.router import route

    out = route(msg, _session(tmp_path))
    assert out["action"] == "edit_image" and out["params"]["prompt"] == msg


@pytest.mark.parametrize("msg", ["get rid of the reminder for tomorrow", "move the meeting to the left",
                                 "take a note that I like boats"])
def test_non_picture_requests_are_not_image_edits(tmp_path, msg):
    from jarvis.router import route

    assert route(msg, _session(tmp_path))["action"] != "edit_image"


@pytest.mark.parametrize("reply,action,full", [("redraw it", "edit_image", True), ("yes, go ahead", "edit_image", True),
                                               ("no thanks", "chat", None)])
def test_a_redraw_question_is_answered_in_chat(tmp_path, reply, action, full):
    from jarvis.router import route

    s = _session(tmp_path)
    s.pending_clarification = {"type": "image_full_redraw", "image_path": s.last_image, "prompt": "add a dragon"}
    out = route(reply, s)
    assert out["action"] == action
    if full:
        assert out["params"] == {"path": s.last_image, "prompt": "add a dragon", "full_redraw": True}


# --- attached parts, masks, move and colour checks -------------------------------------------------
MAN = (0.899, 0.374, 0.95, 0.577)
ROD = (0.727, 0.334, 0.857, 0.42)


def test_what_a_person_holds_is_found_but_not_the_surroundings(monkeypatch, tmp_path):
    from jarvis import image_verify

    img = tmp_path / "x.png"
    Image.new("RGB", (64, 64)).save(img)
    monkeypatch.setattr(image_verify, "_ask_helper", lambda *a, **k: "fishing rod, hat, jacket, pier")
    finds = {"fishing rod": [ROD], "shadow of the man": [(0.9, 0.5, 0.948, 0.578)],  # inside his own box
             "reflection of the man": [(0.1, 0.8, 0.2, 0.9)]}  # far away: not his
    asked = []
    monkeypatch.setattr(image_verify, "locate", lambda p, q: asked.append(q) or finds.get(q, []))
    assert image_verify.locate_attached(str(img), "man", MAN) == [(ROD, "fishing rod")]
    assert "hat" not in asked and "pier" not in asked  # worn things and surroundings are never searched


def test_the_mask_follows_what_changed_not_the_whole_rectangle():
    from jarvis.comfyui_local_edit import changed_mask

    rng = np.random.default_rng(1)
    before = Image.fromarray(rng.integers(90, 110, (300, 400, 3), dtype=np.uint8))
    after = before.copy()
    ImageDraw.Draw(after).line([(20, 280), (380, 20)], fill=(250, 250, 250), width=4)  # a thin diagonal rod
    hard = Image.new("L", before.size, 255)
    m = np.asarray(changed_mask(before, after, hard)) > 8
    assert m.mean() < 0.12  # a band around the rod, not its 100 % bounding rectangle
    assert m[150, 200]  # on the line


@pytest.mark.parametrize("direction,amount,expected", [
    ("left", "", (0.3, 0.4, 0.4, 0.5)), ("right", "a little", (0.45, 0.4, 0.55, 0.5)), ("up", "", (0.4, 0.3, 0.5, 0.4)),
])
def test_where_a_move_puts_the_object(direction, amount, expected):
    from jarvis.comfyui_local_edit import moved_box

    got = moved_box((0.4, 0.4, 0.5, 0.5), direction, amount)
    assert got == pytest.approx(expected)


def test_no_room_to_move_is_said_not_attempted():
    from jarvis.comfyui_local_edit import moved_box

    assert moved_box((0.0, 0.4, 0.1, 0.5), "left") is None


@pytest.fixture
def local_env(monkeypatch, tmp_path):
    from jarvis import comfyui, comfyui_edit, image_verify

    gallery = tmp_path / "generated"
    gallery.mkdir()
    src = gallery / "harbor.png"
    Image.fromarray(np.random.default_rng(0).integers(0, 255, (512, 768, 3), dtype=np.uint8)).save(src)
    comfy = tmp_path / "ComfyUI"
    (comfy / "input").mkdir(parents=True)
    (comfy / "output").mkdir()
    monkeypatch.setattr("jarvis.comfyui_settings.COMFY_ROOT", comfy)
    monkeypatch.setattr("jarvis.config.DATA_DIR", tmp_path)
    monkeypatch.setattr(comfyui, "OUTPUT_DIR", gallery)
    monkeypatch.setattr(comfyui, "is_available", lambda: True)
    monkeypatch.setattr(comfyui, "upload_image", lambda p: Path(p).name)
    monkeypatch.setattr(comfyui, "workflow_ram_mib", lambda wf: 1000)
    monkeypatch.setattr(comfyui_edit, "klein_installed", lambda: True)
    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: False)
    env = SimpleNamespace(src=src, prompts=[], locate=[], attached=[], yes=None)

    @contextlib.contextmanager
    def session(label, **kw):
        def run(wf, prefix="x"):
            env.prompts.append(wf["6"]["inputs"]["text"])
            w, h = wf["5"]["inputs"]["width"], wf["5"]["inputs"]["height"]
            out = gallery / f"{prefix}_{len(env.prompts):05d}_.png"
            Image.new("RGB", (w, h), (0, 200, 0)).save(out)
            return str(out)

        yield run

    monkeypatch.setattr(comfyui, "image_session", session)
    monkeypatch.setattr(image_verify, "locate", lambda p, q: env.locate.pop(0) if env.locate else [])
    monkeypatch.setattr(image_verify, "locate_attached", lambda p, t, b: env.attached)
    monkeypatch.setattr(image_verify, "ask_yes_no", lambda p, q, b=None: env.yes)
    return env


def test_removing_a_person_takes_what_they_hold(local_env):
    from jarvis import comfyui_local_edit

    local_env.locate = [[MAN], []]
    local_env.attached = [(ROD, "fishing rod")]
    out = comfyui_local_edit.run(local_env.src, plan("Take that person out."))
    assert "Remove the person and its fishing rod" in local_env.prompts[0]
    assert out.path and "together with its fishing rod" in out.message and out.detail["attached"] == ["fishing rod"]


def test_removing_only_the_object_leaves_what_it_holds(local_env):
    from jarvis import comfyui_local_edit

    local_env.locate = [[MAN], []]
    local_env.attached = [(ROD, "fishing rod")]
    out = comfyui_local_edit.run(local_env.src, plan("remove only the man"))
    assert out.path and local_env.prompts == ["Remove the man. Keep everything else exactly the same."]


@pytest.mark.parametrize("seen,word", [(True, "✓"), (False, "may not have worked")])
def test_a_colour_change_is_checked(local_env, seen, word):
    from jarvis import comfyui_local_edit

    local_env.locate = [[(0.3, 0.5, 0.5, 0.7)]]
    local_env.yes = seen
    out = comfyui_local_edit.run(local_env.src, plan("Make the car red."))
    assert local_env.prompts == ["Make the car red. Keep everything else exactly the same."]
    assert out.path and word in out.message


def test_a_move_removes_the_object_and_pastes_it_at_the_new_place(local_env):
    """Klein does not move objects (live: 0.1 % changed), so a move is a removal plus a paste of
    the object's own pixels through the silhouette the removal revealed."""
    from jarvis import comfyui_local_edit

    from jarvis import comfyui

    @contextlib.contextmanager
    def object_only(label, **kw):  # the editor changes the object itself, not its surroundings
        def run(wf, prefix="x"):
            local_env.prompts.append(wf["6"]["inputs"]["text"])
            crop = Image.open(Path(comfyui_local_edit._work_dir()) / wf["10"]["inputs"]["image"]).convert("RGB")
            cw, ch = crop.size
            ImageDraw.Draw(crop).ellipse([cw * 0.46, ch * 0.45, cw * 0.54, ch * 0.55], fill=(0, 200, 0))
            out = Path(local_env.src).parent / f"{prefix}_00001_.png"
            crop.save(out)
            return str(out)

        yield run

    comfyui.image_session = object_only
    # a smooth picture (as photos are): resampling a noise image would "change" every pixel
    yy, xx = np.mgrid[0:512, 0:768]
    smooth = np.stack([xx * 255 / 768, yy * 255 / 512, (xx + yy) * 255 / 1280], axis=2).astype(np.uint8)
    smooth[266:297, 400:445] = (200, 40, 40)  # the boat
    Image.fromarray(smooth).save(local_env.src)
    local_env.locate = [[(0.5, 0.5, 0.6, 0.6)], [(0.4, 0.5, 0.5, 0.6)]]
    out = comfyui_local_edit.run(local_env.src, plan("Move the boat to the left."))
    assert local_env.prompts == ["Remove the boat. Keep everything else exactly the same."]
    assert out.path and "moved ✓" in out.message
    before = np.asarray(Image.open(local_env.src).convert("RGB"))
    after = np.asarray(Image.open(out.path).convert("RGB"))
    h, w = before.shape[:2]
    # the object's pixels now sit one object-width to the left
    assert (after[int(0.55 * h), int(0.45 * w)] == before[int(0.55 * h), int(0.55 * w)]).all()
    assert not (after[int(0.55 * h), int(0.55 * w)] == before[int(0.55 * h), int(0.55 * w)]).all()
    # far from both places nothing changed
    assert (after[int(0.1 * h), int(0.1 * w)] == before[int(0.1 * h), int(0.1 * w)]).all()


def test_uncensored_mode_does_not_move_objects(local_env, monkeypatch):
    from jarvis import comfyui_local_edit

    monkeypatch.setattr("jarvis.config.is_uncensored", lambda: True)
    out = comfyui_local_edit.run(local_env.src, plan("Move the boat to the left."))
    assert not out.handled and "Klein" in out.message and local_env.prompts == []


def test_an_object_with_something_running_through_it_is_not_moved():
    from jarvis.comfyui_local_edit import crosses_edge

    w = h = 400
    box = (0.4, 0.4, 0.6, 0.6)
    free = Image.new("L", (w, h), 0)
    ImageDraw.Draw(free).ellipse([170, 170, 230, 230], fill=255)  # the object alone, inside its box
    crossed = free.copy()
    ImageDraw.Draw(crossed).line([(200, 130), (200, 270)], fill=255, width=4)  # a mast through the box
    assert not crosses_edge(free, box, w, h) and crosses_edge(crossed, box, w, h)


def test_a_brighter_fill_is_matched_to_its_surroundings():
    """Klein's fill came back a few levels brighter and left a ghost of the moved gull."""
    from jarvis.comfyui_local_edit import match_tone

    before = Image.new("RGB", (200, 200), (120, 140, 170))
    after = Image.new("RGB", (200, 200), (132, 150, 178))  # the editor's slightly brighter sky
    mask = Image.new("L", (200, 200), 0)
    ImageDraw.Draw(mask).ellipse([70, 70, 130, 130], fill=255)
    fixed = np.asarray(match_tone(before, after, mask)).astype(int)
    assert np.abs(fixed[100, 100] - np.array([120, 140, 170])).max() <= 1
