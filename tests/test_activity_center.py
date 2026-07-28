"""Activity Center — store semantics, wiring, unread contract, AI helpers."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "jarvis" / "gui" / "static"
DOCS = ROOT / "docs"


def _read(*parts: str) -> str:
    return (STATIC.joinpath(*parts)).read_text(encoding="utf-8")


def test_activity_stack_files_exist():
    for name in (
        "activity_store.js",
        "activity_actions.js",
        "activity_center.js",
        "activity_producers.js",
    ):
        assert (STATIC / name).is_file(), name


def test_html_wires_activity_stack_after_aria_actions():
    html = _read("index.html")
    assert "activity_store.js" in html
    assert "activity_actions.js" in html
    assert "activity_center.js" in html
    assert "activity_producers.js" in html
    assert html.index("aria_actions.js") < html.index("activity_store.js")
    assert html.index("activity_store.js") < html.index("activity_actions.js")
    assert html.index("activity_actions.js") < html.index("activity_center.js")
    assert html.index("activity_center.js") < html.index("activity_producers.js")
    for eid in (
        "activityCenterModal",
        "activityCenterList",
        "activityCenterLive",
        "activityUnreadSummary",
        "activityCorrelation",
        "activityMarkReadBtn",
        "activityClearReadBtn",
        "activityUndoBtn",
        "activityExportBtn",
        "activitySummarizeBtn",
        "activityHelp",
        "activitySearchInput",
    ):
        assert f'id="{eid}"' in html, eid
    assert 'data-activity-filter="unread"' in html
    assert 'data-activity-filter="pinned"' in html


def test_unread_not_marked_on_render():
    center = _read("activity_center.js")
    assert "do NOT mark read on render" in center or "IMPORTANT: do NOT mark read" in center
    assert "markAllRead" in center
    render_fn = center.split("function render()")[1].split("function syncActive")[0]
    assert "markAllRead" not in render_fn
    assert "store().markAllRead" not in render_fn


def test_center_uses_aria_actions_not_silent_clicks():
    center = _read("activity_center.js")
    actions = _read("activity_actions.js")
    assert "AriaActivityActions" in center
    assert "openDeepLink" in actions
    assert "askAbout" in actions
    assert "whatsWrong" in actions
    assert "AriaActions" in actions


def test_schema_fields_present():
    store = _read("activity_store.js")
    for field in (
        "version",
        "timestamp",
        "severity",
        "priority",
        "category",
        "source",
        "type",
        "title",
        "summary",
        "detail",
        "deepLink",
        "actions",
        "read",
        "pinned",
        "muted",
        "dismissed",
        "groupId",
        "metadata",
        "snoozedUntil",
    ):
        assert field in store, field


def test_docs_exist():
    assert (DOCS / "ACTIVITY_CENTER_IMPLEMENTATION.md").is_file()


def test_command_palette_activity_commands():
    catalog = _read("command_catalog.js")
    assert "act:activity-whats-wrong" in catalog
    assert "act:activity-unread" in catalog
    assert "act:activity-errors" in catalog


def test_product_boundary_copy():
    html = _read("index.html")
    center = _read("activity_center.js")
    assert "Job Center" in html or "Job Center" in center
    assert "Mission Control" in html or "Mission Control" in center
    assert "durable" in html.lower() or "durable" in center.lower()


def _run_node_store_script() -> str:
    script = r"""
const fs = require('fs');
const vm = require('vm');
const store = {};
const localStorage = {
  getItem: (k) => (k in store ? store[k] : null),
  setItem: (k, v) => { store[k] = String(v); },
  removeItem: (k) => { delete store[k]; },
};
const sandbox = {
  window: {
    dispatchEvent: () => true,
    addEventListener: () => {},
  },
  console,
  localStorage,
  Date,
  Math,
  CustomEvent: class CustomEvent {
    constructor(type, init) { this.type = type; this.detail = init && init.detail; }
  },
  setTimeout,
  clearTimeout,
};
sandbox.window.CustomEvent = sandbox.CustomEvent;
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync('jarvis/gui/static/activity_store.js', 'utf8'), sandbox);
const S = sandbox.window.AriaActivityStore;
if (!S) throw new Error('no store');

S.clearAll();

const a = S.publish({ category: 'chat', type: 'failure', severity: 'error', title: 'Chat failure', detail: 'timeout', source: 'chat', deepLink: 'chat' });
if (!a || a.read) throw new Error('new event must be unread');
if (S.unreadCount() < 1) throw new Error('unread count');

S.setFilter('all');
S.setQuery('');
const before = S.unreadCount();
S.queryEvents();
if (S.unreadCount() !== before) throw new Error('query changed unread');

S.markRead(a.id, true);
if (S.unreadCount() !== before - 1) throw new Error('mark read failed');
S.markUnread(a.id);
if (S.get(a.id).read !== false) throw new Error('mark unread failed');

S.togglePin(a.id);
if (!S.get(a.id).pinned) throw new Error('pin failed');

S.muteSource('noisy');
const muted = S.publish({ title: 'Noisy', source: 'noisy', severity: 'warning' });
if (muted) throw new Error('muted source should not publish');

S.publish({ title: 'Dup', source: 'x', severity: 'error', summary: '1' });
const d2 = S.publish({ title: 'Dup', source: 'x', severity: 'error', summary: '2' });
if ((d2.metadata.count || 1) < 2) throw new Error('dedupe rollup failed');

const nl = S.parseSearchQuery('unread error chat');
if (!nl.constraints.unread || nl.constraints.severity !== 'error') throw new Error('nl parse failed');

S.publish({ category: 'providers', severity: 'error', title: 'Provider offline', detail: 'ollama down' });
S.publish({ category: 'chat', severity: 'error', title: 'Chat failure 2', detail: 'provider timeout ollama' });
const corr = S.correlate();
if (!Array.isArray(corr)) throw new Error('correlate');

const sum = S.summarizeUnread();
if (!sum || !/unread/i.test(sum)) throw new Error('summarize');

S.markAllRead();
S.clearRead();
const exp = JSON.parse(S.exportLog());
if (exp.version !== S.SCHEMA_VERSION) throw new Error('export version');

S.publish({ title: 'Undo me', severity: 'warning' });
const row = S.queryEvents()[0];
S.dismiss(row.id);
if (!S.undo()) throw new Error('undo failed');

S.snooze(a.id, 60000);
const vis = S.visibleEvents().some((e) => e.id === a.id);
if (vis) throw new Error('snoozed should hide');

console.log(JSON.stringify({ ok: true, unread: S.unreadCount(), schema: S.SCHEMA_VERSION }));
"""
    proc = subprocess.run(
        ["node", "-e", script],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stderr or proc.stdout or "node failed")
    return proc.stdout.strip()


def test_store_behavior_node():
    out = _run_node_store_script()
    data = json.loads(out.splitlines()[-1])
    assert data["ok"] is True
    assert data["schema"] == 2


def test_producers_export_domains():
    prod = _read("activity_producers.js")
    for domain in (
        "chat",
        "memory",
        "documents",
        "connections",
        "planner",
        "calendar",
        "journal",
        "projects",
        "gallery",
        "voice",
        "vision",
        "coding",
        "automation",
        "mission",
        "providers",
        "browser",
        "home",
        "system",
    ):
        assert f"{domain}:" in prod, domain
    assert "AriaActivityProducers" in prod


def test_no_mark_read_on_open_function():
    center = _read("activity_center.js")
    open_fn = center.split("function open()")[1].split("function close()")[0]
    assert "markAllRead" not in open_fn
    assert "markRead" not in open_fn
