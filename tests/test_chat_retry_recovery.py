"""Living Room Retry: a failed turn is retried under the bubble already on screen.

Retry used to call ``sendMessage(text)`` like a fresh composer send, so the
user's message was drawn a second time, the old recovery card stayed behind, and
each extra click queued another turn. On the server, a stream dropped after its
first token left the user turn in context without a reply, so a retry added the
same turn twice. The frontend half runs the real static JS under node.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from jarvis.conversation import Conversation

REPO = Path(__file__).resolve().parent.parent
STATIC = REPO / "jarvis" / "gui" / "static"
HARNESS = Path(__file__).resolve().parent / "js" / "retry_recovery_harness.mjs"

CHECKS = [
    "failure shows one recovery card",
    "failed message stays visible",
    "busy state reset after failure",
    "retry sends the same request text",
    "retry draws no second user bubble",
    "retry removes its recovery card",
    "successful retry renders the reply once",
    "busy state reset after retry",
    "transcript holds exactly one user message",
    "repeated Retry clicks send once",
    "repeated Retry clicks add no bubbles",
    "chained retries keep one user bubble",
    "chained retries leave no stale cards",
    "chained retries end in one reply",
    "chained retries send four requests",
    "retry while a reply is running does not start a turn",
    "retry while busy explains why",
    "retry works once the chat is free",
    "restart provider then retries without a new bubble",
    "non-retryable failure focuses the composer instead of resending",
]


@pytest.fixture(scope="module")
def harness_results() -> dict[str, dict]:
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed — skipping frontend behavioural tests")
    proc = subprocess.run(
        [node, str(HARNESS), str(STATIC)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=REPO,
    )
    assert proc.returncode == 0, f"harness crashed:\n{proc.stderr}"
    payload = json.loads(proc.stdout)
    return {r["name"]: r for r in payload["results"]}


@pytest.mark.parametrize("check", CHECKS)
def test_retry_frontend(harness_results: dict[str, dict], check: str) -> None:
    assert check in harness_results, f"harness did not run check {check!r}"
    assert harness_results[check]["ok"], f"{check} failed: {harness_results[check]['detail']}"


class _Archive:
    def __init__(self) -> None:
        self.records: list[tuple[str, str]] = []
        self.marks: list[str] = []

    def record(self, role: str, content: str) -> None:
        self.records.append((role, content))

    def mark(self, kind: str, **_kw) -> None:
        self.marks.append(kind)


def test_resend_of_unanswered_turn_is_not_duplicated() -> None:
    archive = _Archive()
    conv = Conversation("system", archive=archive)
    conv.add_user("What should we work on?")  # stream dropped after first token
    conv.add_user("What should we work on?")  # Retry
    conv.add_assistant("The hatch-matching feature.")
    assert [m["role"] for m in conv.messages] == ["system", "user", "assistant"]
    assert archive.records == [("user", "What should we work on?"),
                               ("assistant", "The hatch-matching feature.")]


def test_failed_retry_still_withdraws_the_turn() -> None:
    conv = Conversation("system", archive=_Archive())
    conv.add_user("hello")
    conv.add_user("hello")
    assert conv.pop_last_user() is True
    assert [m["role"] for m in conv.messages] == ["system"]


def test_same_text_after_a_reply_is_a_new_turn() -> None:
    conv = Conversation("system")
    conv.add_user("thanks")
    conv.add_assistant("You're welcome.")
    conv.add_user("thanks")
    assert [m["role"] for m in conv.messages] == ["system", "user", "assistant", "user"]


def test_different_text_is_never_merged() -> None:
    conv = Conversation("system")
    conv.add_user("first")
    conv.add_user("second")
    assert [m["content"] for m in conv.messages[1:]] == ["first", "second"]
