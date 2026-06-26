"""HTTP API tests for chat branches, personality, and export."""

from jarvis.config import build_system_prompt, load_personality_preset, save_personality_preset


def test_personality_get_and_set(chat_app):
    save_personality_preset("default")
    get = chat_app.get("/api/personality")
    assert get.status_code == 200
    assert get.json()["personality"] == "default"

    post = chat_app.post("/api/personality", data={"preset": "brief"})
    assert post.status_code == 200
    assert post.json()["personality"] == "brief"
    assert chat_app.get("/api/personality").json()["personality"] == "brief"


def test_branch_fork_api(chat_app):
    assistant = chat_app.assistant
    assistant.conversation.messages = [
        {"role": "system", "content": build_system_prompt(load_personality_preset())},
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "a1"},
    ]
    assistant.branches.persist()

    resp = chat_app.post("/api/branches/fork", data={"name": "Forked", "display_index": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    bid = data["branch_id"]

    msgs = chat_app.get(f"/api/branches/{bid}/messages").json()["messages"]
    assert len(msgs) == 2
    assert msgs[0]["content"] == "u1"
    assert msgs[1]["content"] == "a1"


def test_chat_export_filename(chat_app):
    assistant = chat_app.assistant
    assistant.branches._data["branches"]["main"]["name"] = "Main Chat"

    resp = chat_app.get("/api/chat/export")
    assert resp.status_code == 200
    assert "Main Chat" in resp.text
    disposition = resp.headers.get("content-disposition", "")
    assert "attachment" in disposition.lower()
    assert "jarvis-chat-Main-Chat" in disposition


def test_briefing_hidden_after_dismiss(chat_app, monkeypatch):
    monkeypatch.setattr("jarvis.morning_briefing.mark_briefing_shown", lambda day=None: None)
    monkeypatch.setattr("jarvis.morning_briefing.should_show_launch_briefing", lambda **kw: False)
    resp = chat_app.get("/api/briefing")
    assert resp.status_code == 200
    data = resp.json()
    assert data["show"] is False
    assert "markdown" not in data


def test_clear_main_branch_api(chat_app):
    assistant = chat_app.assistant
    assistant.conversation.messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    assistant.branches.persist()

    resp = chat_app.post("/api/branches/main/clear")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    msgs = chat_app.get("/api/branches/main/messages").json()["messages"]
    assert msgs == []


def test_clear_branch_form_api(chat_app):
    assistant = chat_app.assistant
    assistant.conversation.messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    assistant.branches.persist()

    resp = chat_app.post("/api/branches/clear", data={"branch_id": "main"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert chat_app.get("/api/branches/main/messages").json()["messages"] == []
