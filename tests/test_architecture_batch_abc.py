"""Batch A/B/C foundation tests."""

from jarvis.activity_inbox import clear_all, clear_read, dismiss, list_items, mark_all_read, publish
from jarvis.auth import is_loopback_client, is_local_client
from jarvis.conversation_pipeline import normalize_action_params
from jarvis.product_registration import register, registration_status, reset_for_tests


def test_product_registration_records_failures():
    reset_for_tests()
    assert register("ok", lambda: None) is True
    assert register("bad", lambda: (_ for _ in ()).throw(RuntimeError("boom"))) is False
    st = registration_status()
    assert st["ok"] is False
    assert "ok" in st["registered"]
    assert any(f["name"] == "bad" for f in st["failed"])


def test_normalize_action_params():
    action, params = normalize_action_params({"action": {"name": "web_search"}, "params": {"q": "x"}})
    assert action == "web_search"
    assert params == {"q": "x"}
    action2, params2 = normalize_action_params({"action": None, "params": "bad"})
    assert action2 == "chat"
    assert params2 == {}


def test_activity_inbox_server_sot(tmp_path, monkeypatch):
    import jarvis.activity_inbox as inbox

    monkeypatch.setattr(inbox, "INBOX_DIR", tmp_path / "activity")
    monkeypatch.setattr(inbox, "INBOX_FILE", tmp_path / "activity" / "inbox.jsonl")
    r = publish(title="T", body="B", event_id="e1")
    assert r["ok"]
    assert list_items()["count"] >= 1
    assert dismiss("e1")["ok"]
    assert all(i["id"] != "e1" for i in list_items()["items"])


def test_activity_inbox_bulk_mutations(tmp_path, monkeypatch):
    import jarvis.activity_inbox as inbox

    monkeypatch.setattr(inbox, "INBOX_DIR", tmp_path / "activity")
    monkeypatch.setattr(inbox, "INBOX_FILE", tmp_path / "activity" / "inbox.jsonl")
    publish(title="A", body="one", event_id="a1")
    publish(title="B", body="two", event_id="b1")

    assert mark_all_read()["updated"] == 2
    assert all(i["read"] for i in list_items()["items"])
    assert clear_read()["removed"] == 2
    assert list_items()["count"] == 0

    publish(title="C", body="three", event_id="c1")
    assert clear_all()["removed"] == 1
    assert list_items()["count"] == 0


def test_auth_local_means_loopback_only():
    class Req:
        def __init__(self, host):
            self.client = type("c", (), {"host": host})()
            self.headers = {}

    assert is_loopback_client(Req("127.0.0.1")) is True
    assert is_local_client(Req("127.0.0.1")) is True
    # Host LAN IP must NOT count as local for API-key exemption
    assert is_local_client(Req("10.0.0.5")) is False
