"""Vision routing and handler tests (mocked Ollama)."""

from pathlib import Path

import pytest
from jarvis.router import route
from jarvis.session import SessionContext
from PIL import Image


def _write_test_png(path: Path, size: tuple[int, int] = (8, 8), color: str = "red") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)


@pytest.fixture
def session():
    return SessionContext()


def test_image_attachment_describe(session):
    attachment = {"path": "/tmp/photo.png", "kind": "image", "name": "photo.png"}
    intent = route("", session, attachment)
    assert intent["action"] == "describe_image"
    assert intent["params"]["path"] == "/tmp/photo.png"


def test_image_attachment_analyze(session):
    attachment = {"path": "/tmp/photo.png", "kind": "image", "name": "photo.png"}
    intent = route("How many people are in this photo?", session, attachment)
    assert intent["action"] == "analyze_image"
    assert intent["params"]["question"] == "How many people are in this photo?"


def test_image_attachment_ocr(session):
    attachment = {"path": "/tmp/photo.png", "kind": "image", "name": "photo.png"}
    intent = route("What text is visible in this screenshot?", session, attachment)
    assert intent["action"] == "ocr_image"


def test_describe_follow_up(session):
    session.last_image = "/tmp/photo.png"
    intent = route("describe it", session)
    assert intent["action"] == "describe_image"
    assert intent["params"]["path"] == "/tmp/photo.png"


def test_vision_follow_up_question(session):
    session.last_image = "/tmp/photo.png"
    session.last_module = "vision"
    intent = route("What color is the car?", session)
    assert intent["action"] == "analyze_image"
    assert intent["params"]["path"] == "/tmp/photo.png"


def test_capabilities_not_hijacked_after_vision(session):
    session.last_image = "/tmp/photo.png"
    session.last_module = "vision"
    intent = route("what can you do?", session)
    assert intent["action"] == "capabilities"


def test_compare_images_route(session):
    intent = route("compare data/a.png with data/b.png", session)
    assert intent["action"] == "compare_images"
    assert intent["params"]["path1"] == "data/a.png"
    assert intent["params"]["path2"] == "data/b.png"


def test_describe_image_handler(assistant, data_dir, monkeypatch):
    img = data_dir / "uploads" / "test.png"
    _write_test_png(img)
    monkeypatch.setattr(
        "jarvis.modules.vision.chat",
        lambda **kwargs: {"message": {"content": "A red square on white background."}},
        raising=False,
    )
    monkeypatch.setattr(
        "ollama.chat",
        lambda **kwargs: {"message": {"content": "A red square on white background."}},
    )

    result = assistant.process("", attachment={"path": str(img), "kind": "image"})
    assert result["ok"] is True
    assert result["module"] == "vision"
    assert "red square" in result["message"].lower()


def test_analyze_image_handler(assistant, data_dir, monkeypatch):
    img = data_dir / "uploads" / "chart.png"
    _write_test_png(img, color="green")
    monkeypatch.setattr(
        "ollama.chat",
        lambda **kwargs: {"message": {"content": "Three bars labeled A, B, C."}},
    )

    result = assistant.process(
        "How many bars are in the chart?",
        attachment={"path": str(img), "kind": "image"},
    )
    assert result["ok"] is True
    assert result["module"] == "vision"
    assert "bars" in result["message"].lower()


def test_compare_images_handler(assistant, data_dir, monkeypatch):
    img1 = data_dir / "uploads" / "one.png"
    img2 = data_dir / "uploads" / "two.png"
    _write_test_png(img1, color="white")
    _write_test_png(img2, color="black")
    monkeypatch.setattr("jarvis.modules.vision.DATA_DIR", data_dir)
    monkeypatch.setattr(
        "ollama.chat",
        lambda **kwargs: {"message": {"content": "Image one is brighter than image two."}},
    )

    result = assistant.process(f"compare {img1.name} with {img2.name}")
    assert result["ok"] is True
    assert result["module"] == "vision"
    assert "brighter" in result["message"].lower()


def test_uploads_api_serves_image(chat_app, data_dir):
    img = data_dir / "uploads" / "serve-me.png"
    _write_test_png(img)

    missing = chat_app.get("/api/uploads/missing.png")
    assert missing.status_code == 404

    ok = chat_app.get("/api/uploads/serve-me.png")
    assert ok.status_code == 200
    assert ok.content == img.read_bytes()


def test_vision_multi_turn_context(assistant, data_dir, monkeypatch):
    img = data_dir / "uploads" / "scene.png"
    _write_test_png(img, color="yellow")
    calls: list[list] = []

    def fake_chat(**kwargs):
        calls.append(kwargs.get("messages", []))
        if len(calls) == 1:
            return {"message": {"content": "A dog in a park."}}
        return {"message": {"content": "The dog is golden."}}

    monkeypatch.setattr("ollama.chat", fake_chat)

    assistant.process("", attachment={"path": str(img), "kind": "image"})
    result = assistant.process("What color is the dog?")
    assert result["ok"] is True

    assert len(calls) == 2
    assert len(calls[0]) == 1
    assert "images" in calls[0][0]
    assert len(calls[1]) == 1
    assert "images" in calls[1][0]
    assert "Follow-up question" in calls[1][0]["content"]


def test_ocr_route(session):
    attachment = {"path": "/tmp/screen.png", "kind": "image", "name": "screen.png"}
    intent = route("Read all text in this image", session, attachment)
    assert intent["action"] == "ocr_image"
    assert intent["params"]["path"] == "/tmp/screen.png"


def test_dual_attachment_compare(assistant, data_dir, monkeypatch):
    img1 = data_dir / "uploads" / "a.png"
    img2 = data_dir / "uploads" / "b.png"
    _write_test_png(img1, color="red")
    _write_test_png(img2, color="blue")

    def fake_chat(**kwargs):
        msgs = kwargs.get("messages", [])
        if msgs and msgs[0].get("images"):
            return {"message": {"content": "A colored square."}}
        return {"message": {"content": "Image A is redder; Image B is bluer."}}

    monkeypatch.setattr("ollama.chat", fake_chat)
    result = assistant.process(
        "Compare these",
        attachment={"path": str(img1), "kind": "image", "name": "a.png"},
        attachment2={"path": str(img2), "kind": "image", "name": "b.png"},
    )
    assert result["ok"] is True
    assert result["module"] == "vision"
    assert "compared" in result["message"].lower()


def test_ocr_image_handler(assistant, data_dir, monkeypatch):
    img = data_dir / "uploads" / "text.png"
    _write_test_png(img)
    monkeypatch.setattr(
        "ollama.chat",
        lambda **kwargs: {"message": {"content": "HELLO WORLD"}},
    )
    result = assistant.process(
        "Read all text in this image",
        attachment={"path": str(img), "kind": "image"},
    )
    assert result["ok"] is True
    assert result["module"] == "vision"
    assert "hello" in result["message"].lower()


def test_vision_quality_settings(data_dir):
    from jarvis.config import load_vision_quality, save_vision_quality

    assert load_vision_quality() == "custom"
    save_vision_quality("quality")
    assert load_vision_quality() == "quality"
    save_vision_quality("custom")
    assert load_vision_quality() == "custom"
    save_vision_quality("invalid")
    assert load_vision_quality() == "custom"


def test_status_includes_vision_block(assistant):
    status = assistant.get_status()
    assert "vision" in status
    assert "model" in status["vision"]
    assert "quality_mode" in status["vision"]


def test_save_upload_unique_names(assistant, data_dir):
    r1 = assistant.save_upload("photo.png", b"first")
    r2 = assistant.save_upload("photo.png", b"second")
    assert r1["path"] != r2["path"]
    assert Path(r2["path"]).read_bytes() == b"second"


def test_compare_two_pass_vision(assistant, data_dir, monkeypatch):
    img1 = data_dir / "uploads" / "left.png"
    img2 = data_dir / "uploads" / "right.png"
    _write_test_png(img1, color="red")
    _write_test_png(img2, color="blue")
    vision_calls: list[dict] = []

    def fake_chat(**kwargs):
        msgs = kwargs.get("messages", [])
        if msgs and msgs[0].get("images"):
            vision_calls.append(kwargs)
            color = "red square" if len(vision_calls) == 1 else "blue square"
            return {"message": {"content": f"A {color}."}}
        return {"message": {"content": "Image A is red; Image B is blue."}}

    monkeypatch.setattr("ollama.chat", fake_chat)
    result = assistant.process(
        "Compare these",
        attachment={"path": str(img1), "kind": "image", "name": "left.png"},
        attachment2={"path": str(img2), "kind": "image", "name": "right.png"},
    )
    assert result["ok"] is True
    assert len(vision_calls) == 2
    assert result.get("compare_paths") == [str(img1), str(img2)]
    assert "left.png" in result["message"]
    assert "right.png" in result["message"]


def test_chat_api_dual_upload(assistant, data_dir, monkeypatch):
    from io import BytesIO

    import jarvis.gui.server as gui_server
    from fastapi.testclient import TestClient
    from PIL import Image

    monkeypatch.setattr(gui_server, "assistant", assistant)
    vision_calls = 0

    def fake_chat(**kwargs):
        nonlocal vision_calls
        msgs = kwargs.get("messages", [])
        if msgs and msgs[0].get("images"):
            vision_calls += 1
            return {"message": {"content": f"vision pass {vision_calls}"}}
        return {"message": {"content": "Compared: different images."}}

    monkeypatch.setattr("ollama.chat", fake_chat)

    def png_bytes(color: str) -> bytes:
        buf = BytesIO()
        Image.new("RGB", (16, 16), color).save(buf, format="PNG")
        return buf.getvalue()

    client = TestClient(gui_server.app)
    resp = client.post(
        "/api/chat",
        data={"message": "Compare these two images", "stream": "false"},
        files=[
            ("file", ("left.png", png_bytes("red"), "image/png")),
            ("file2", ("right.png", png_bytes("blue"), "image/png")),
        ],
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["module"] == "vision"
    assert vision_calls == 2
    assert len(body.get("compare_paths", [])) == 2
