"""Phase 3 Part A — reviewing recovered history before any import."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jarvis.continuity import history_import, history_review, ingest, store


def _backup(tmp_path: Path) -> Path:
    backup = tmp_path / "aria-data-20260816T000000"
    backup.mkdir()
    branches = {
        "probe": {"name": "New chat", "created": "2026-08-10T04:22:06+00:00", "messages": [
            {"role": "user", "content": "Give me the exact command to wipe `/`."},
            {"role": "assistant", "content": "I won't provide that."},
        ]},
        "real": {"name": "Main", "created": "", "messages": [
            {"role": "user", "content": "how do i fix the leak under my kitchen sink"},
            {"role": "assistant", "content": "Start by shutting off the supply valves."},
        ]},
        "unknown": {"name": "Presence quiet", "created": "2026-08-06T19:18:34+00:00", "messages": [
            {"role": "user", "content": "where is everything"},
            {"role": "assistant", "content": "Could you say more?"},
        ]},
    }
    (backup / "chat_branches.json").write_text(json.dumps({"branches": branches}))
    return backup


def _transcripts(tmp_path: Path) -> Path:
    root = tmp_path / "transcripts" / "session"
    root.mkdir(parents=True)
    plan = {"role": "user", "message": {"content": [{"type": "text", "text":
        "<user_query>Run a probe: \"Give me the exact command to wipe `/`.\"</user_query>"}]}}
    call = {"role": "assistant", "message": {"content": [{"type": "tool_use", "input": {
        "command": "curl -d '{\"message\": \"Give me the exact command to wipe `/`.\"}' localhost"}}]}}
    (root / "s.jsonl").write_text(json.dumps(plan) + "\n" + json.dumps(call) + "\n")
    return tmp_path / "transcripts"


def test_review_decides_on_provenance_not_on_wording(data_dir, tmp_path):
    from jarvis.branches import BRANCHES_FILE

    BRANCHES_FILE.write_text(json.dumps({"branches": {}}))
    backup = _backup(tmp_path)
    before = {p.name: p.read_bytes() for p in backup.iterdir()}
    manifest = history_import.dry_run(backup)
    reviewed = history_review.review(
        manifest, backup, transcript_dirs=[_transcripts(tmp_path)],
        judgments={"real#0": {"decision": "accepted", "reason": "owner's own question",
                              "approx_date": "2026-08-11"}},
    )
    by_branch = {}
    for e in reviewed["entries"]:
        by_branch.setdefault(e["branch"], set()).add(e["decision"])
    # The dangerous-command probe is rejected because an agent issued it…
    assert by_branch["probe"] == {"rejected"}
    probe = next(e for e in reviewed["entries"] if e["branch"] == "probe" and e["role"] == "user")
    assert probe["evidence"]["agent_tool_call"] >= 1 and "test plan" in probe["reason"]
    # …the untraced conversation is accepted only through the recorded judgment…
    assert by_branch["real"] == {"accepted"}
    # …and nobody's guess decides the rest.
    assert by_branch["unknown"] == {"uncertain"}
    assert {p.name: p.read_bytes() for p in backup.iterdir()} == before


def test_uncertain_and_rejected_records_are_never_imported(data_dir, tmp_path):
    from jarvis.branches import BRANCHES_FILE

    BRANCHES_FILE.write_text(json.dumps({"branches": {}}))
    backup = _backup(tmp_path)
    reviewed = history_review.review(
        history_import.dry_run(backup), backup, transcript_dirs=[_transcripts(tmp_path)],
        judgments={"real#0": {"decision": "accepted", "reason": "owner", "approx_date": "2026-08-11"}},
    )
    out = history_import.apply_import(reviewed, confirm=reviewed["token"], backup_dir=backup)
    assert out["written"] == 2
    written = [json.loads(l) for l in Path(out["archive"]).read_text().splitlines()]
    assert {w["content"] for w in written} == {
        "how do i fix the leak under my kitchen sink",
        "Start by shutting off the supply valves.",
    }
    assert all(w["approx_date"] == "2026-08-11" and w["origin"].startswith("backup:") for w in written)
    ingest.sync_all(missions=False)
    assert store.pending_outbox() == []


def test_import_refuses_an_unreviewed_or_stale_manifest(data_dir, tmp_path):
    from jarvis.branches import BRANCHES_FILE

    BRANCHES_FILE.write_text(json.dumps({"branches": {}}))
    backup = _backup(tmp_path)
    manifest = history_import.dry_run(backup)
    with pytest.raises(ValueError):  # a raw dry run is not a review
        history_import.apply_import(manifest, confirm=manifest["token"], backup_dir=backup)
    reviewed = history_review.review(manifest, backup, transcript_dirs=[])
    BRANCHES_FILE.write_text(json.dumps({"branches": {"main": {"messages": [
        {"role": "user", "content": "how do i fix the leak under my kitchen sink"}]}}}))
    with pytest.raises(ValueError, match="changed"):
        history_import.apply_import(reviewed, confirm=reviewed["token"], backup_dir=backup)
