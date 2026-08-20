"""Browser / computer use — actions, sessions, permissions, safety, workflows.

Contract tests use a fake driver so the suite never needs a browser or the
internet. The real-browser tests run against a local fixture server and skip
cleanly when Playwright/Chromium are unavailable.
"""

from __future__ import annotations

import http.server
import json
import os
import threading
from pathlib import Path

import pytest

from jarvis import missions
from jarvis import specialized_agents as agents
from jarvis.computer_use import actions as A
from jarvis.computer_use import engine, permissions, retention, sessions
from jarvis.missions import store as mstore
from jarvis.specialized_agents import registry

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _clean():
    sessions.reset()
    registry.reset()
    yield
    sessions.reset()
    registry.reset()


class FakeDriver:
    """Deterministic stand-in for the Playwright driver."""

    def __init__(self, *, pages=None, fail=None):
        self.pages = pages or {"https://example.com/": {"title": "Example", "text": "hello world"}}
        self.fail = fail or {}
        self.url = ""
        self.calls: list[tuple[str, tuple]] = []
        self.closed = False
        self.typed: list[tuple[str, str]] = []

    def _maybe_fail(self, op):
        if op in self.fail:
            raise self.fail[op]

    def navigate(self, url):
        self.calls.append(("navigate", (url,)))
        self._maybe_fail("navigate")
        if url not in self.pages:
            raise engine.NavigationFailure(f"host unreachable: {url}")
        self.url = url
        return {"url": url, "title": self.pages[url]["title"]}

    def state(self):
        self.calls.append(("state", ()))
        self._maybe_fail("state")
        return {"url": self.url, "title": self.pages.get(self.url, {}).get("title", "")}

    def extract(self, limit):
        self.calls.append(("extract", (limit,)))
        self._maybe_fail("extract")
        text = self.pages.get(self.url, {}).get("text", "")
        return {"text": text[:limit], "truncated": len(text) > limit, "url": self.url}

    def click(self, target):
        self.calls.append(("click", (target,)))
        self._maybe_fail("click")
        if target == "missing":
            raise engine.TargetNotFound(target)
        return {"url": self.url, "title": "clicked"}

    def type(self, target, text):
        self.calls.append(("type", (target, text)))
        self._maybe_fail("type")
        self.typed.append((target, text))
        return {"url": self.url, "title": "typed"}

    def select(self, target, value):
        self.calls.append(("select", (target, value)))
        return {"url": self.url, "title": "selected"}

    def scroll(self, amount):
        self.calls.append(("scroll", (amount,)))
        return {"url": self.url, "title": "scrolled"}

    def history(self, direction):
        self.calls.append(("history", (direction,)))
        return {"url": self.url, "title": direction}

    def screenshot(self, label):
        self.calls.append(("screenshot", (label,)))
        self._maybe_fail("screenshot")
        return {"path": f"/tmp/{label}.png"}

    def close(self):
        self.closed = True
        return {"closed": True}


def _session(owner="") -> str:
    return engine.open_session(owner=owner)["id"]


# ------------------------------------------------------------------ actions


def test_action_catalog_impact_classes(data_dir: Path):
    assert A.impact_of("navigate") == A.READ
    assert A.impact_of("click") == A.INTERACT
    assert A.impact_of("submit") == A.HIGH_IMPACT
    assert set(A.READ_ACTIONS) & set(A.HIGH_IMPACT_ACTIONS) == set()


def test_unknown_action_rejected(data_dir: Path):
    with pytest.raises(A.ActionError):
        A.impact_of("mine_bitcoin")
    with pytest.raises(A.ActionError):
        A.validate("mine_bitcoin", {})


def test_required_params_enforced(data_dir: Path):
    with pytest.raises(A.ActionError, match="requires"):
        A.validate("click", {})
    with pytest.raises(A.ActionError):
        A.validate("type", {"target": "x"})
    A.validate("type", {"target": "x", "text": "y"})


# -------------------------------------------------------------- URL safety


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:8765/x",
        "https://127.0.0.1/",
        "http://10.0.0.5/",
        "https://192.168.1.9/",
        "http://169.254.169.254/latest/meta-data",
        "https://172.16.0.1/",
    ],
)
def test_internal_hosts_blocked(data_dir: Path, url):
    with pytest.raises(A.NavigationBlocked):
        A.check_url(url)


def test_internal_host_allowed_when_explicit(data_dir: Path):
    assert A.check_url("http://127.0.0.1:9/x", allow_local=True).startswith("http://127.0.0.1")


def test_non_http_schemes_blocked(data_dir: Path):
    for url in ("file:///etc/passwd", "ftp://x/y", "javascript:alert(1)"):
        with pytest.raises(A.NavigationBlocked):
            A.check_url(url)


def test_malformed_url_rejected(data_dir: Path):
    with pytest.raises(A.NavigationBlocked):
        A.check_url("")
    with pytest.raises(A.NavigationBlocked):
        A.check_url("https://")


def test_bare_host_normalized_to_https(data_dir: Path):
    assert A.check_url("example.com").startswith("https://example.com")


# --------------------------------------------------------------- redaction


def test_secret_keys_redacted(data_dir: Path):
    out = A.redact({"password": "hunter2", "api_key": "abc", "safe": "keep"})
    assert out["password"] == A.REDACTED
    assert out["api_key"] == A.REDACTED
    assert out["safe"] == "keep"


def test_secret_shaped_values_redacted(data_dir: Path):
    assert A.REDACTED in A.redact("Authorization: Bearer abcdef1234567890")
    assert A.REDACTED in A.redact("token sk-abcdefghijklmno")


def test_typing_into_password_field_is_redacted(data_dir: Path):
    safe = A.redact_params("type", {"target": "#password", "text": "hunter2"})
    assert safe["text"] == A.REDACTED
    plain = A.redact_params("type", {"target": "#search", "text": "kittens"})
    assert plain["text"] == "kittens"


def test_result_payload_is_redacted(data_dir: Path):
    sid = _session()
    drv = FakeDriver()
    engine.perform(sid, "navigate", {"url": "https://example.com/"}, driver=drv)
    out = engine.perform(sid, "type", {"target": "#password", "text": "hunter2"}, driver=drv)
    assert out["ok"] is True
    assert "hunter2" not in json.dumps(out)


# ---------------------------------------------------------------- sessions


def test_session_lifecycle(data_dir: Path):
    s = engine.open_session(owner="research_specialist", label="t")
    assert s["state"] == sessions.OPEN
    assert sessions.get(s["id"])["owner"] == "research_specialist"
    assert sessions.close(s["id"]) is True
    assert sessions.get(s["id"])["state"] == sessions.CLOSED


def test_unknown_session_rejected(data_dir: Path):
    out = engine.perform("cus_missing", "inspect", {}, driver=FakeDriver())
    assert out["ok"] is False
    assert out["error_kind"] == engine.ERR_SESSION


def test_closed_session_rejected(data_dir: Path):
    sid = _session()
    sessions.close(sid)
    out = engine.perform(sid, "inspect", {}, driver=FakeDriver())
    assert out["error_kind"] == engine.ERR_SESSION


def test_session_isolation_between_owners(data_dir: Path):
    sid = _session(owner="research_specialist")
    out = engine.perform(sid, "inspect", {}, driver=FakeDriver(), owner="analysis_specialist")
    assert out["ok"] is False
    assert out["error_kind"] == engine.ERR_SESSION
    assert "belongs to" in out["error"]


def test_sessions_do_not_share_state(data_dir: Path):
    a, b = _session(), _session()
    da, db = FakeDriver(), FakeDriver()
    engine.perform(a, "navigate", {"url": "https://example.com/"}, driver=da)
    assert sessions.get(a)["url"] == "https://example.com/"
    assert sessions.get(b)["url"] == ""
    assert db.calls == []


def test_expired_session_is_reaped(data_dir: Path, monkeypatch):
    sid = _session()
    monkeypatch.setitem(A.LIMITS, "session_ttl_s", -1)
    assert sid in sessions.reap_expired()
    assert sessions.get(sid)["state"] == sessions.CLOSED


# -------------------------------------------------------------- permissions


def test_permission_gates_map_to_impact(data_dir: Path):
    assert permissions.gate_for("navigate") == permissions.READ_ACTION
    assert permissions.gate_for("click") == permissions.INTERACT_ACTION
    assert permissions.gate_for("submit") == permissions.HIGH_IMPACT_ACTION


def test_specialist_browser_permissions_are_least_privilege(data_dir: Path):
    assert agents.get("research_specialist").permits("browser_use_read") is True
    assert agents.get("research_specialist").permits("browser_use_interact") is True
    assert agents.get("research_specialist").permits("browser_use_high_impact") is False
    assert agents.get("analysis_specialist").permits("browser_use_read") is True
    assert agents.get("analysis_specialist").permits("browser_use_interact") is False
    for aid in ("coding_specialist", "general_specialist"):
        assert agents.get(aid).permits("browser_use_read") is False


def test_unauthorized_agent_denied(data_dir: Path):
    sid = _session()
    out = engine.perform(
        sid,
        "navigate",
        {"url": "https://example.com/"},
        driver=FakeDriver(),
        agent_id="coding_specialist",
    )
    assert out["ok"] is False
    assert "not permitted" in out["error"]


def test_read_only_agent_cannot_interact(data_dir: Path):
    sid = _session()
    drv = FakeDriver()
    ok_nav = engine.perform(
        sid, "navigate", {"url": "https://example.com/"}, driver=drv, agent_id="analysis_specialist"
    )
    assert ok_nav["ok"] is True
    denied = engine.perform(
        sid, "click", {"target": "Submit"}, driver=drv, agent_id="analysis_specialist"
    )
    assert denied["ok"] is False
    assert "interact" in denied["error"]


def test_high_impact_denied_for_all_builtin_specialists(data_dir: Path):
    for agent in agents.list_agents():
        assert permissions.agent_may(agent.id, "submit") is False, agent.id


def test_high_impact_not_implemented_even_if_granted(data_dir: Path):
    """Defence in depth: no default implementation exists for side-effect actions."""
    from jarvis.specialized_agents.definitions import AgentDefinition

    agents.register(
        AgentDefinition(
            id="power_agent",
            name="Power",
            role="testing",
            description="d",
            capabilities=("testing",),
            allowed_actions=("browser_use_high_impact", "browser_use_read"),
        )
    )
    sid = _session()
    out = engine.perform(
        sid, "submit", {"target": "#f"}, driver=FakeDriver(), agent_id="power_agent"
    )
    assert out["ok"] is False
    assert out["error_kind"] == engine.ERR_PERMISSION


def test_deny_beats_wildcard_for_browser(data_dir: Path):
    from jarvis.specialized_agents.definitions import AgentDefinition

    agents.register(
        AgentDefinition(
            id="wild_browser",
            name="W",
            role="testing",
            description="d",
            capabilities=("testing",),
            allowed_actions=("*",),
            denied_actions=("browser_use_interact",),
        )
    )
    assert permissions.agent_may("wild_browser", "navigate") is True
    assert permissions.agent_may("wild_browser", "click") is False


# ----------------------------------------------------------------- actions


def test_navigate_and_inspect(data_dir: Path):
    sid = _session()
    drv = FakeDriver()
    out = engine.perform(sid, "navigate", {"url": "https://example.com/"}, driver=drv)
    assert out["ok"] and out["url"] == "https://example.com/" and out["title"] == "Example"
    assert sessions.get(sid)["actions"] == 1
    ins = engine.perform(sid, "inspect", {}, driver=drv)
    assert ins["ok"] and ins["url"] == "https://example.com/"


def test_extract_is_bounded(data_dir: Path):
    sid = _session()
    drv = FakeDriver(pages={"https://example.org/big": {"title": "B", "text": "x" * 999999}})
    engine.perform(sid, "navigate", {"url": "https://example.org/big"}, driver=drv)
    out = engine.perform(sid, "extract", {"limit": 10**9}, driver=drv)
    assert len(out["result"]["text"]) <= A.LIMITS["max_extract_chars"]
    assert out["result"]["truncated"] is True


def test_click_type_select_scroll_history(data_dir: Path):
    sid = _session()
    drv = FakeDriver()
    engine.perform(sid, "navigate", {"url": "https://example.com/"}, driver=drv)
    for action, params in (
        ("click", {"target": "Go"}),
        ("type", {"target": "#q", "text": "kittens"}),
        ("select", {"target": "#s", "value": "a"}),
        ("scroll", {"amount": 300}),
        ("back", {}),
        ("forward", {}),
        ("reload", {}),
    ):
        out = engine.perform(sid, action, params, driver=drv)
        assert out["ok"] is True, (action, out)
    assert ("type", ("#q", "kittens")) in drv.calls


def test_screenshot_bounded_per_session(data_dir: Path, monkeypatch):
    monkeypatch.setitem(A.LIMITS, "max_screenshots_per_session", 2)
    sid = _session()
    drv = FakeDriver()
    assert engine.perform(sid, "screenshot", {}, driver=drv)["ok"]
    assert engine.perform(sid, "screenshot", {}, driver=drv)["ok"]
    third = engine.perform(sid, "screenshot", {}, driver=drv)
    assert third["ok"] is False and third["error_kind"] == "bounded"


def test_max_actions_per_session(data_dir: Path, monkeypatch):
    monkeypatch.setitem(A.LIMITS, "max_actions_per_session", 3)
    sid = _session()
    drv = FakeDriver()
    for _ in range(3):
        assert engine.perform(sid, "inspect", {}, driver=drv)["ok"]
    out = engine.perform(sid, "inspect", {}, driver=drv)
    assert out["ok"] is False and out["error_kind"] == engine.ERR_SESSION


def test_close_action_closes_session(data_dir: Path):
    sid = _session()
    drv = FakeDriver()
    assert engine.perform(sid, "close", {}, driver=drv)["ok"]
    assert drv.closed is True
    assert sessions.get(sid)["state"] == sessions.CLOSED


# ------------------------------------------------------- error classification


def test_navigation_failure_classified(data_dir: Path):
    sid = _session()
    out = engine.perform(sid, "navigate", {"url": "https://example.org/nope"}, driver=FakeDriver())
    assert out["ok"] is False and out["error_kind"] == engine.ERR_NAVIGATION


def test_blocked_url_classified(data_dir: Path):
    sid = _session()
    out = engine.perform(sid, "navigate", {"url": "http://127.0.0.1/x"}, driver=FakeDriver())
    assert out["error_kind"] == engine.ERR_BLOCKED


def test_missing_target_classified(data_dir: Path):
    sid = _session()
    drv = FakeDriver()
    engine.perform(sid, "navigate", {"url": "https://example.com/"}, driver=drv)
    out = engine.perform(sid, "click", {"target": "missing"}, driver=drv)
    assert out["ok"] is False and out["error_kind"] == engine.ERR_TARGET


def test_stale_target_classified(data_dir: Path):
    sid = _session()
    drv = FakeDriver(fail={"click": RuntimeError("Element is not attached to the DOM")})
    engine.perform(sid, "navigate", {"url": "https://example.com/"}, driver=drv)
    out = engine.perform(sid, "click", {"target": "x"}, driver=drv)
    assert out["error_kind"] == engine.ERR_STALE


def test_timeout_classified(data_dir: Path):
    sid = _session()
    drv = FakeDriver(fail={"extract": TimeoutError("Timeout 10000ms exceeded")})
    engine.perform(sid, "navigate", {"url": "https://example.com/"}, driver=drv)
    assert engine.perform(sid, "extract", {}, driver=drv)["error_kind"] == engine.ERR_TIMEOUT


def test_browser_unavailable_marks_session_failed(data_dir: Path):
    sid = _session()
    drv = FakeDriver(fail={"state": RuntimeError("browser session unavailable")})
    out = engine.perform(sid, "inspect", {}, driver=drv)
    assert out["error_kind"] == engine.ERR_BROWSER
    assert sessions.get(sid)["state"] == sessions.FAILED


def test_failure_never_reports_content(data_dir: Path):
    sid = _session()
    out = engine.perform(sid, "navigate", {"url": "https://example.org/nope"}, driver=FakeDriver())
    assert out["result"] is None
    assert out["ok"] is False


# ------------------------------------------------------------- cancellation


def test_cancel_check_stops_before_acting(data_dir: Path):
    sid = _session()
    drv = FakeDriver()
    out = engine.perform(
        sid, "navigate", {"url": "https://example.com/"}, driver=drv, cancel_check=lambda: True
    )
    assert out["ok"] is False and out["error_kind"] == "cancelled"
    assert drv.calls == [], "action ran despite cancellation"


def test_run_steps_stops_at_first_failure(data_dir: Path):
    sid = _session()
    drv = FakeDriver()
    out = engine.run_steps(
        sid,
        [
            {"action": "navigate", "params": {"url": "https://example.com/"}},
            {"action": "click", "params": {"target": "missing"}},
            {"action": "extract", "params": {}},
        ],
        driver=drv,
    )
    assert out["ok"] is False
    assert out["steps_run"] == 2
    assert out["failed"]["error_kind"] == engine.ERR_TARGET


# ------------------------------------------------------------ mission workflows


def _mission_runner():
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    return lambda step, ctx: call_action(None, step["action"], step["params"], "")


def test_workflow_d_mission_browser_task(data_dir: Path, monkeypatch):
    """WORKFLOW D: mission drives multiple browser steps with checkpoints."""
    drv = FakeDriver()
    monkeypatch.setattr(engine, "PlaywrightDriver", lambda **kw: drv)
    sid = _session()
    steps = [
        {
            "name": "nav",
            "action": "browser_step",
            "params": {
                "session_id": sid,
                "action": "navigate",
                "params": {"url": "https://example.com/"},
            },
        },
        {
            "name": "extract",
            "action": "browser_step",
            "params": {"session_id": sid, "action": "extract", "params": {}},
        },
        {
            "name": "shot",
            "action": "browser_step",
            "params": {"session_id": sid, "action": "screenshot", "params": {}},
        },
    ]
    mid = missions.create_mission("browser mission", steps=steps)
    missions.run(mid, _mission_runner())
    assert missions.get(mid)["state"] == mstore.COMPLETED
    assert len(mstore.checkpoints(mid)) == 3
    assert sessions.get(sid)["actions"] == 3


def test_workflow_e_mission_cancellation_stops_browser(data_dir: Path, monkeypatch):
    """WORKFLOW E: cancelling the mission stops browser work at a safe boundary."""
    drv = FakeDriver()
    monkeypatch.setattr(engine, "PlaywrightDriver", lambda **kw: drv)
    sid = _session()
    mid = missions.create_mission(
        "cancel browser",
        steps=[
            {
                "name": f"s{i}",
                "action": "browser_step",
                "params": {"session_id": sid, "action": "inspect", "params": {}},
            }
            for i in range(4)
        ],
    )
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    calls = {"n": 0}

    def runner(step, ctx):
        calls["n"] += 1
        params = dict(step["params"])
        params["mission_id"] = mid
        if calls["n"] == 2:
            mstore.request_cancel(mid)
        return call_action(None, step["action"], params, "")

    missions.run(mid, runner)
    assert missions.get(mid)["state"] in (mstore.CANCELLED, mstore.FAILED)
    assert sessions.get(sid)["actions"] < 4


def test_workflow_f_browser_failure_recovers(data_dir: Path, monkeypatch):
    """WORKFLOW F: a browser failure fails the mission without corrupting state."""
    drv = FakeDriver(fail={"state": RuntimeError("browser session unavailable")})
    monkeypatch.setattr(engine, "PlaywrightDriver", lambda **kw: drv)
    sid = _session()
    mid = missions.create_mission(
        "failing browser",
        steps=[
            {
                "name": "x",
                "action": "browser_step",
                "params": {"session_id": sid, "action": "inspect", "params": {}},
            }
        ],
    )
    missions.run(mid, _mission_runner())
    # A step that reports failure fails the mission: this used to finish as
    # "completed" with the failure buried in the result context. The browser
    # layer records the truth too — the session is marked failed rather than
    # silently reused.
    mission = missions.get(mid)
    assert mission["state"] == mstore.FAILED
    assert engine.ERR_BROWSER in (mission.get("error") or "") or "browser" in (
        mission.get("error") or ""
    )
    assert sessions.get(sid)["state"] == sessions.FAILED
    # A fresh session recovers cleanly.
    new_sid = _session()
    good = FakeDriver()
    assert engine.perform(new_sid, "inspect", {}, driver=good)["ok"] is True


# --------------------------------------------------- evidence / research


def test_workflow_c_browser_evidence_records_real_inspection(data_dir: Path):
    """WORKFLOW C: extracted page text becomes inspected evidence."""
    from jarvis import evidence as ev
    from jarvis.computer_use import evidence_bridge

    sid = _session()
    drv = FakeDriver(
        pages={"https://nasa.gov/a": {"title": "NASA", "text": "boiling point is 100C"}}
    )
    out = evidence_bridge.capture_page_evidence(
        sid, "https://nasa.gov/a", context_id="ctxB", driver=drv
    )
    assert out["ok"] and out["inspected"] is True
    src = ev.get_source(out["source_id"])
    assert src["access_state"] == ev.INSPECTED
    assert ev.get_evidence(out["evidence_id"])["inspected"] == 1


def test_browser_failure_does_not_fabricate_evidence(data_dir: Path):
    from jarvis import evidence as ev
    from jarvis.computer_use import evidence_bridge

    sid = _session()
    drv = FakeDriver()  # page not in fixture -> navigation fails
    out = evidence_bridge.capture_page_evidence(
        sid, "https://example.org/unreachable", context_id="ctxC", driver=drv
    )
    assert out["ok"] is False and out["inspected"] is False
    assert out["evidence_id"] is None
    assert ev.get_source(out["source_id"])["access_state"] == ev.UNAVAILABLE


def test_render_without_text_is_not_inspection(data_dir: Path):
    """A page that renders but yields no text must not count as inspected."""
    from jarvis import evidence as ev
    from jarvis.computer_use import evidence_bridge

    sid = _session()
    drv = FakeDriver(pages={"https://example.org/empty": {"title": "E", "text": "   "}})
    out = evidence_bridge.capture_page_evidence(
        sid, "https://example.org/empty", context_id="ctxD", driver=drv
    )
    assert out["ok"] is False and out["inspected"] is False
    assert ev.get_source(out["source_id"])["access_state"] == ev.UNAVAILABLE


def test_workflow_g_research_to_analysis_with_browser_evidence(data_dir: Path):
    """WORKFLOW G: browser evidence verifies, and analysis receives provenance."""
    from jarvis import evidence as ev
    from jarvis.computer_use import evidence_bridge

    claim = ev.add_claim("water boils at 100C", context_id="ctxG")
    for url, text in (
        ("https://nasa.gov/a", "water boils at 100C"),
        ("https://nih.gov/b", "boiling point 100C"),
    ):
        sid = _session(owner="research_specialist")
        drv = FakeDriver(pages={url: {"title": url, "text": text}})
        out = evidence_bridge.capture_page_evidence(
            sid,
            url,
            context_id="ctxG",
            claim_id=claim,
            driver=drv,
            agent_id="research_specialist",
        )
        assert out["inspected"] is True

    result = ev.verify(claim, verifier="analysis_specialist")
    assert result["result"] == "verified"
    assert result["independence"]["level"] == "independent"
    prov = ev.provenance(claim)
    assert all("browser:" in h["evidence"]["provenance"] for h in prov["chain"])


def test_workflow_h_unauthorized_specialist_denied(data_dir: Path):
    """WORKFLOW H: an unauthorized specialist cannot browse."""
    sid = _session()
    out = engine.perform(
        sid,
        "navigate",
        {"url": "https://example.com/"},
        driver=FakeDriver(),
        agent_id="general_specialist",
    )
    assert out["ok"] is False and "not permitted" in out["error"]


# ------------------------------------------------------------- retention


def test_artifact_usage_reports_footprint(data_dir: Path):
    shots = retention.screenshot_dir()
    shots.mkdir(parents=True, exist_ok=True)
    for i in range(5):
        (shots / f"s{i}.png").write_bytes(b"x" * 10)
    data = retention.usage()
    assert data["screenshots"] == 5
    assert data["screenshot_bytes"] == 50


def test_prune_bounds_screenshot_growth(data_dir: Path):
    shots = retention.screenshot_dir()
    shots.mkdir(parents=True, exist_ok=True)
    import time as _t

    old = _t.time() - 7200
    for i in range(20):
        p = shots / f"s{i}.png"
        p.write_bytes(b"x" * 100)
        os.utime(p, (old + i, old + i))
    result = retention.prune_screenshots(keep=5, min_age_s=60)
    assert result["pruned"] == 15
    assert len(list(shots.glob("*.png"))) == 5


def test_prune_keeps_recent_files(data_dir: Path):
    shots = retention.screenshot_dir()
    shots.mkdir(parents=True, exist_ok=True)
    for i in range(10):
        (shots / f"s{i}.png").write_bytes(b"x")
    result = retention.prune_screenshots(keep=2, min_age_s=3600)
    assert result["pruned"] == 0, "recent screenshots were pruned"
    assert len(list(shots.glob("*.png"))) == 10


def test_prune_only_touches_screenshot_dir(data_dir: Path):
    shots = retention.screenshot_dir()
    shots.mkdir(parents=True, exist_ok=True)
    outside = data_dir / "keepme.png"
    outside.write_bytes(b"x")
    retention.prune_screenshots(keep=0, min_age_s=0)
    assert outside.exists(), "pruning escaped the screenshot directory"


def test_repeated_tasks_do_not_grow_unbounded(data_dir: Path):
    shots = retention.screenshot_dir()
    shots.mkdir(parents=True, exist_ok=True)
    import time as _t

    old = _t.time() - 7200
    for i in range(60):
        p = shots / f"run{i}.png"
        p.write_bytes(b"x" * 50)
        os.utime(p, (old + i, old + i))
    retention.prune_screenshots(keep=10, min_age_s=60)
    assert len(list(shots.glob("*.png"))) == 10


# -------------------------------------------------------------- handlers


def test_browser_actions_registered(data_dir: Path):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    names = {s["action"] for s in all_actions()}
    for action in (
        "browser_use_open",
        "browser_use_act",
        "browser_use_sessions",
        "browser_use_close",
        "browser_use_capabilities",
        "browser_step",
        "browser_use_artifacts",
    ):
        assert action in names, f"{action} not registered"


def test_handler_round_trip(data_dir: Path, monkeypatch):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    drv = FakeDriver()
    monkeypatch.setattr(engine, "PlaywrightDriver", lambda **kw: drv)

    opened = call_action(None, "browser_use_open", {"owner": "research_specialist"}, "")
    assert opened["ok"] is True
    sid = opened["session_id"]

    acted = call_action(
        None,
        "browser_use_act",
        {"session_id": sid, "action": "navigate", "params": {"url": "https://example.com/"}},
        "",
    )
    assert acted["ok"] is True and acted["url"] == "https://example.com/"

    listed = call_action(None, "browser_use_sessions", {}, "")
    assert any(s["id"] == sid for s in listed["sessions"])

    caps = call_action(None, "browser_use_capabilities", {}, "")
    assert "navigate" in caps["capabilities"]["read"]
    assert "submit" in caps["capabilities"]["high_impact"]

    closed = call_action(None, "browser_use_close", {"session_id": sid}, "")
    assert closed["ok"] is True


def test_handler_reports_denied_action(data_dir: Path, monkeypatch):
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import call_action

    ensure_handlers_loaded()
    monkeypatch.setattr(engine, "PlaywrightDriver", lambda **kw: FakeDriver())
    sid = _session()
    out = call_action(
        None,
        "browser_use_act",
        {
            "session_id": sid,
            "action": "click",
            "params": {"target": "x"},
            "agent_id": "analysis_specialist",
        },
        "",
    )
    assert out["ok"] is False


def test_module_reload_durability(data_dir: Path):
    import importlib

    sid = _session()
    importlib.reload(sessions)
    importlib.reload(importlib.import_module("jarvis.computer_use"))
    # Registry is in-process by design; reload starts clean rather than corrupt.
    assert sessions.get(sid) is None or sessions.get(sid)["id"] == sid


# ------------------------------------------- real browser against local fixture

_HTML = b"""<html><head><title>Fixture</title></head><body>
<h1>Computer Use Fixture</h1><p id="para">deterministic fixture content</p>
<button id="btn" onclick="document.getElementById('para').innerText='clicked!'">Press Me</button>
<input id="field" placeholder="type here"><a href="/second">Second Page</a>
</body></html>"""
_HTML2 = b"<html><head><title>Second</title></head><body><p>second page body</p></body></html>"


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = _HTML2 if self.path.startswith("/second") else _HTML
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


@pytest.fixture
def fixture_server():
    srv = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_port}/"
    srv.shutdown()


def _browser_available() -> bool:
    try:
        from jarvis.browser_playwright import browser_stack_ready

        state = browser_stack_ready(probe_chromium=True)
        return bool(state.get("playwright") and state.get("chromium"))
    except Exception:
        return False


needs_browser = pytest.mark.skipif(
    not _browser_available(), reason="Playwright/Chromium unavailable"
)


@needs_browser
def test_real_browser_navigate_extract_click(data_dir: Path, fixture_server, monkeypatch):
    """WORKFLOW A + B against a real browser and a deterministic local page."""
    monkeypatch.setenv("JARVIS_BROWSER_AGENT", "1")
    sid = _session()
    drv = engine.PlaywrightDriver(allow_local=True)

    nav = engine.perform(sid, "navigate", {"url": fixture_server}, driver=drv, allow_local=True)
    assert nav["ok"] is True, nav
    assert "Fixture" in (nav["title"] or "")

    ext = engine.perform(sid, "extract", {}, driver=drv, allow_local=True)
    assert ext["ok"] and "deterministic fixture content" in ext["result"]["text"]

    clicked = engine.perform(sid, "click", {"target": "Press Me"}, driver=drv, allow_local=True)
    assert clicked["ok"] is True, clicked
    after = engine.perform(sid, "extract", {}, driver=drv, allow_local=True)
    assert "clicked!" in after["result"]["text"]

    typed = engine.perform(
        sid, "type", {"target": "type here", "text": "hello"}, driver=drv, allow_local=True
    )
    assert typed["ok"] is True, typed
    engine.perform(sid, "close", {}, driver=drv)


# ------------------------------------------- live-found: stack-unavailable classing


@pytest.mark.parametrize(
    "message",
    [
        "Playwright/Chromium not available",
        "Playwright/Chromium not available — navigation did not occur",
        "browser agent disabled",
        "no live browser page",
        "browser session unavailable",
    ],
)
def test_browser_stack_unavailable_is_not_internal(data_dir: Path, message):
    """Regression: live ARIA reported 'Playwright/Chromium not available' as an
    internal error, so a caller could not tell a retryable environment problem
    from a genuine defect."""
    sid = _session()
    drv = FakeDriver(fail={"state": RuntimeError(message)})
    out = engine.perform(sid, "inspect", {}, driver=drv)
    assert out["ok"] is False
    assert out["error_kind"] == engine.ERR_BROWSER, out
    assert sessions.get(sid)["state"] == sessions.FAILED


def test_navigation_stack_failure_classified_as_browser(data_dir: Path):
    sid = _session()
    drv = FakeDriver(
        fail={"navigate": engine.NavigationFailure("Playwright/Chromium not available")}
    )
    out = engine.perform(sid, "navigate", {"url": "https://example.com/"}, driver=drv)
    assert out["error_kind"] == engine.ERR_BROWSER
