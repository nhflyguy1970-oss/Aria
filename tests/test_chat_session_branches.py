"""Session persistence and branch fork/switch behavior."""

from jarvis.branches import BranchManager
from jarvis.session import SessionContext


def test_session_round_trip():
    s = SessionContext(last_file="a.py", last_proposal_id="p1", recent_files=["a.py", "b.py"])
    s.pending_clarification = {"action": "coding_fix", "choices": ["a.py"]}
    restored = SessionContext.from_dict(s.to_dict())
    assert restored.last_file == "a.py"
    assert restored.last_proposal_id == "p1"
    assert restored.recent_files == ["a.py", "b.py"]
    assert restored.pending_clarification["action"] == "coding_fix"


def test_branch_session_isolation(data_dir):
    bm = BranchManager()
    bm.save_session("main", SessionContext(last_file="main.py"))
    bm.create_branch("experiment", from_branch="main")
    bm.save_session(bm.active_id, SessionContext(last_file="fork.py"))
    assert bm.load_session("main").last_file == "main.py"
    assert bm.load_session(bm.active_id).last_file == "fork.py"


def test_fork_at_display_index(data_dir):
    bm = BranchManager()
    conv = bm.get_conversation("main", "sys")
    conv.messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
        {"role": "assistant", "content": "a2"},
    ]
    bm.persist()

    bid_early = bm.fork_at_display_index("early", display_index=0, from_branch="main")
    early = bm.get_conversation(bid_early, "sys")
    assert [m.get("content") for m in early.messages] == ["sys", "u1"]

    bid_mid = bm.fork_at_display_index("mid", display_index=1, from_branch="main")
    mid = bm.get_conversation(bid_mid, "sys")
    assert [m.get("content") for m in mid.messages] == ["sys", "u1", "a1"]

    bid_full = bm.fork_at_display_index("full", display_index=3, from_branch="main")
    full = bm.get_conversation(bid_full, "sys")
    assert [m.get("content") for m in full.messages] == ["sys", "u1", "a1", "u2", "a2"]


def test_list_branches_excludes_system_from_count(data_dir):
    bm = BranchManager()
    bm._data["branches"]["main"]["messages"] = [
        {"role": "system", "content": "x"},
        {"role": "user", "content": "hi"},
    ]
    listed = bm.list_branches()
    main = next(b for b in listed if b["id"] == "main")
    assert main["messages"] == 1


def test_update_system_prompt(data_dir):
    bm = BranchManager()
    bm.update_system_prompt("main", "personality prompt")
    conv = bm.get_conversation("main", "ignored")
    assert conv.messages[0]["content"] == "personality prompt"


def test_delete_branch(data_dir):
    bm = BranchManager()
    bid = bm.create_branch("temp", from_branch="main")
    assert bid in bm._data["branches"]
    assert not bm.delete_branch("main")
    assert bm.delete_branch(bid)
    assert bid not in bm._data["branches"]
    assert bm.active_id == "main"


def test_delete_branches_active_switches_to_main(data_dir):
    bm = BranchManager()
    bid = bm.create_branch("gone", from_branch="main")
    bm.switch(bid)
    assert bm.active_id == bid
    result = bm.delete_branches([bid])
    assert result["deleted"] == [bid]
    assert result["active"] == "main"
    assert bm.active_id == "main"


def test_clear_branch_messages(data_dir):
    bm = BranchManager()
    conv = bm.get_conversation("main", "sys")
    conv.messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]
    bm.persist()
    assert bm.clear_messages("main", "new sys")
    cleared = bm.get_conversation("main", "ignored")
    assert [m.get("content") for m in cleared.messages] == ["new sys"]
    assert bm.load_session("main").last_file == ""
    assert not bm.clear_messages("missing", "sys")
