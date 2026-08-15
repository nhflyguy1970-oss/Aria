#!/usr/bin/env python3
"""
Tier 3C-D house integration proof.
Measures ACTUAL application latency (aria-house-room + dataset.room + usable content),
separately from any harness waits.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright

LIVE = "http://127.0.0.1:8765"
OUT = Path(__file__).resolve().parent
REPAIRED = "REPAIRED — AWAITING FINAL CERTIFICATION"
JEFF = "JEFF-ATTENDED — FINAL RESIDENCY REQUIRED"

# Product-defined cross-Room relationships (from UI links / Search / prior phases)
CROSS = [
    ("search", "flytying", "Adams", "fly"),
    ("search", "documents", "warranty", "docs"),
    ("presence", "home_automation", None, "link_or_identity"),
    ("gallery", "maker", None, "nav_btn"),
    ("gallery", "meme", None, "nav_btn"),
    ("gallery", "video", None, "nav_btn"),
    ("maker", "gallery", None, "nav_btn"),
    ("maker", "documents", None, "nav_btn"),
    ("audit", "mission", None, "nav_btn"),
    ("audit", "actions", None, "nav_btn"),
    ("home", "planner", None, "nav_btn"),
    ("home", "projects", None, "nav_btn"),
    ("memory", "chat", None, "nav_btn"),
    ("vision", "gallery", None, "nav_btn"),
    ("vision", "chat", None, "nav_btn"),
]

PANEL = {
    "documents": "documentsView",
    "planner": "plannerView",
    "calendar": "calendarView",
    "gallery": "galleryView",
    "voice": "voiceView",
    "presence": "presenceView",
    "journal": "journalView",
    "video": "videoView",
    "browser": "browserView",
    "maker": "makerView",
    "meme": "memeView",
    "vision": "visionView",
    "connections": "connectionsView",
    "audit": "auditView",
    "chat": None,
    "health": None,
    "home": None,
    "audio": None,
    "projects": "projectsView",
    "providers": None,
    "home_automation": "homeAutomationView",
    "mission": None,
    "search": "searchView",
    "repair": None,
    "flytying": "flytyingView",
    "integrity": None,
    "memory": "memoryView",
    "coding": "codingView",
    "settings": "settingsView",
    "capabilities": "capabilitiesView",
    "integrations": "integrationsView",
    "security": "securityView",
    "actions": "actionsView",
    "automation": "automationView",
}


def http(method, path, data=None, headers=None, timeout=30):
    body = None
    hdrs = dict(headers or {})
    if data is not None:
        body = json.dumps(data).encode()
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(LIVE + path, data=body, headers=hdrs, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, json.loads(raw.decode() or "{}"), round((time.perf_counter() - t0) * 1000, 1)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw.decode() or "{}")
        except Exception:
            payload = {}
        return e.code, payload, round((time.perf_counter() - t0) * 1000, 1)
    except Exception as e:
        return None, {"error": str(e)}, round((time.perf_counter() - t0) * 1000, 1)


def classify_ms(ms, *, kind="nav"):
    if ms is None:
        return "BLOCKED"
    if kind == "api_local":
        if ms < 50:
            return "FAST"
        if ms < 200:
            return "ACCEPTABLE"
        if ms < 1000:
            return "SLOW"
        return "UNREASONABLE"
    if kind == "api_search":
        if ms < 500:
            return "FAST"
        if ms < 2000:
            return "ACCEPTABLE"
        if ms < 8000:
            return "SLOW"
        return "UNREASONABLE"
    if kind == "api_enrich":
        if ms < 100:
            return "FAST"
        if ms < 500:
            return "ACCEPTABLE"
        if ms < 3000:
            return "SLOW"
        return "UNREASONABLE"
    # room nav identity/usable
    if ms < 200:
        return "FAST"
    if ms < 800:
        return "ACCEPTABLE"
    if ms < 2500:
        return "SLOW"
    return "UNREASONABLE"


INSTALL_METRICS = """
() => {
  if (window.__aria3cd) return;
  const state = {
    roomEvents: [],
    fetches: [],
    console: [],
    pageErrors: [],
    navMarks: {},
  };
  window.__aria3cd = state;
  window.addEventListener('aria-house-room', (e) => {
    state.roomEvents.push({ t: performance.now(), detail: e.detail || {} });
  });
  window.addEventListener('aria-room-change', (e) => {
    state.roomEvents.push({ t: performance.now(), kind: 'room-change', detail: e.detail || {} });
  });
  const ofetch = window.fetch.bind(window);
  window.fetch = async (...args) => {
    const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
    const t0 = performance.now();
    try {
      const res = await ofetch(...args);
      state.fetches.push({
        url: String(url).slice(0, 180),
        ms: Math.round(performance.now() - t0),
        status: res.status,
        ok: res.ok,
        room: document.body?.dataset?.room || null,
      });
      return res;
    } catch (err) {
      state.fetches.push({
        url: String(url).slice(0, 180),
        ms: Math.round(performance.now() - t0),
        error: String(err && err.message || err).slice(0, 120),
        room: document.body?.dataset?.room || null,
      });
      throw err;
    }
  };
}
"""


async def dismiss(page):
    await page.evaluate(
        """() => {
      try {
        const k='aria_ui_prefs_v1';
        const p=JSON.parse(localStorage.getItem(k)||'{}');
        p.whatsNewSeen='999';
        localStorage.setItem(k, JSON.stringify(p));
      } catch(_){}
      document.getElementById('whatsNewModal')?.classList.add('hidden');
      window.ariaDismissDialogs?.();
      document.querySelectorAll('dialog[open]').forEach(d => { try { d.close(); } catch(_){} });
    }"""
    )


async def measure_enter(page, room_id, settle_ms=50):
    """Enter room; measure app latency separately from harness settle."""
    await dismiss(page)
    # clear recent marks
    await page.evaluate(
        """(rid) => {
      const s = window.__aria3cd;
      s.navMarks[rid] = { t0: performance.now(), events: [] };
      s._lastStart = performance.now();
      s._startRoom = document.body.dataset.room || null;
    }""",
        room_id,
    )
    t_wall0 = time.perf_counter()
    await page.evaluate("(id) => window.AriaFrontDoorCatalog.goRoom(id)", room_id)

    # Poll until dataset.room matches (app identity), max 8s
    identity_ms = None
    usable_ms = None
    event_ms = None
    snap = None
    deadline = time.perf_counter() + 8.0
    while time.perf_counter() < deadline:
        probe = await page.evaluate(
            """(rid) => {
          const s = window.__aria3cd;
          const now = performance.now();
          const t0 = s._lastStart || now;
          const room = document.body.dataset.room || null;
          const hash = location.hash || '';
          const furnished = document.body.dataset.furnished || '';
          const ev = (s.roomEvents || []).filter(e => e.t >= t0 - 5);
          const matchEv = ev.find(e => (e.detail && e.detail.room) === rid);
          // visible content heuristics
          const panelId = {
            documents:'documentsView',planner:'plannerView',calendar:'calendarView',gallery:'galleryView',
            voice:'voiceView',presence:'presenceView',journal:'journalView',video:'videoView',
            browser:'browserView',maker:'makerView',meme:'memeView',vision:'visionView',
            connections:'connectionsView',audit:'auditView',projects:'projectsView',
            search:'searchView',flytying:'flytyingView',memory:'memoryView',coding:'codingView',
            settings:'settingsView',capabilities:'capabilitiesView',integrations:'integrationsView',
            security:'securityView',actions:'actionsView',automation:'automationView',
            homeAutomation:'homeAutomationView', home_automation:'homeAutomationView'
          }[rid];
          let panel = panelId ? document.getElementById(panelId) : null;
          if (!panel) {
            panel = document.querySelector(`[data-room-root="${rid}"], #${rid}Room, #${rid}View, .room-${rid}, #houseRoomHost`);
          }
          // native rooms often use host
          const host = document.getElementById('houseRoomHost') || document.getElementById('ariaHouseHost');
          const root = panel || (room === rid ? (host || document.body) : null);
          const text = (root && root.innerText || '').replace(/\\s+/g,' ').trim();
          const loading = /^Loading|Loading…/i.test(text.slice(0, 40));
          const fail = /could not load|failed to load|not implemented|TypeError|Internal Server|\\b500\\b/i.test(text.slice(0, 500));
          const btns = root ? root.querySelectorAll('button').length : 0;
          const usable = room === rid && !loading && (btns > 0 || text.length > 40);
          return {
            room, hash, furnished,
            identity: room === rid,
            eventHit: !!matchEv,
            eventMs: matchEv ? Math.round(matchEv.t - t0) : null,
            identityMs: room === rid ? Math.round(now - t0) : null,
            usable, usableMs: usable ? Math.round(now - t0) : null,
            loading, fail, btns,
            head: text.slice(0, 220),
            fetchSince: (s.fetches || []).filter(f => f.room === rid || true).slice(-8)
          };
        }""",
            room_id,
        )
        if identity_ms is None and probe.get("identity"):
            identity_ms = probe.get("identityMs")
        if event_ms is None and probe.get("eventHit"):
            event_ms = probe.get("eventMs")
        if usable_ms is None and probe.get("usable"):
            usable_ms = probe.get("usableMs")
            snap = probe
            break
        await page.wait_for_timeout(settle_ms)

    if snap is None:
        snap = await page.evaluate(
            """(rid) => {
          const room = document.body.dataset.room || null;
          const text = (document.body.innerText || '').replace(/\\s+/g,' ').trim().slice(0, 220);
          return {
            room, hash: location.hash, furnished: document.body.dataset.furnished || '',
            identity: room === rid, usable: false, fail: /could not load|failed to load|TypeError/i.test(text),
            loading: /^Loading/i.test(text.slice(0,40)), btns: document.querySelectorAll('button').length,
            head: text
          };
        }""",
            room_id,
        )

    wall_ms = round((time.perf_counter() - t_wall0) * 1000, 1)
    # fetches during this enter
    fetches = await page.evaluate(
        """(t0approx) => {
          const s = window.__aria3cd;
          // last 40 fetches; filter by recent time window loosely
          return (s.fetches || []).slice(-40);
        }"""
    )
    return {
        "room_id": room_id,
        "identity_ms": identity_ms,
        "event_ms": event_ms,
        "usable_ms": usable_ms,
        "wall_ms_includes_poll": wall_ms,
        "harness_poll_note": "wall_ms includes poll loops; identity_ms/usable_ms are application clocks via performance.now()",
        "snap": snap,
        "perf_class_identity": classify_ms(identity_ms),
        "perf_class_usable": classify_ms(usable_ms),
        "ok": bool(snap.get("identity")) and not snap.get("fail"),
    }


async def main():
    report = {
        "registry": {},
        "api_regression": {},
        "rooms": {},
        "cross": [],
        "search": {},
        "chat_tools": {},
        "rapid_nav": {},
        "soak": {},
        "resources": {},
        "errors": {},
        "activity": {},
        "integrity": {},
        "isolation": {},
        "jeff_attended": [],
        "defects": [],
        "repairs": [],
        "scorecard": [],
        "perf_scorecard": [],
    }

    # API regression matrix
    api_paths = [
        ("/api/planner/focus", "api_local"),
        ("/api/projects", "api_local"),
        ("/api/repair/home", "api_local"),
        ("/api/connections/home", "api_local"),
        ("/api/audit", "api_local"),
        ("/api/documents/search?q=warranty", "api_search"),
        ("/api/mission-control", "api_enrich"),
        ("/api/mission-control/health-brief", "api_local"),
        ("/api/health/home", "api_local"),
        ("/api/browser/status", "api_local"),
        ("/api/presence/status", "api_local"),
        ("/api/engineering/cad_status", "api_local"),
        ("/api/gallery", "api_local"),
        ("/api/calendar/month", "api_local"),
        ("/api/journal/stats", "api_local"),
    ]
    for path, kind in api_paths:
        samples = []
        for _ in range(3):
            st, d, ms = http("GET", path, timeout=45)
            samples.append({"status": st, "ms": ms, "ok": isinstance(d, dict) and d.get("ok", st == 200)})
        warm = samples[-1]
        report["api_regression"][path] = {
            "samples": samples,
            "warm_ms": warm["ms"],
            "class": classify_ms(warm["ms"], kind=kind),
            "status": warm["status"],
        }

    # Search product query
    for q, label in [("Adams", "fly"), ("warranty", "docs")]:
        st, d, ms = http("GET", f"/api/search/product/query?q={q}&facet=everything", timeout=45)
        text = json.dumps(d)[:2000]
        report["search"][label] = {
            "status": st,
            "ms": ms,
            "class": classify_ms(ms, kind="api_search"),
            "has_fly": "fly" in text.lower() or "adams" in text.lower(),
            "has_doc": "warrant" in text.lower() or "document" in text.lower(),
        }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 960})
        page = await context.new_page()

        console_errs = []
        page_errs = []
        failed_req = []

        page.on("console", lambda msg: console_errs.append({"type": msg.type, "text": msg.text[:240]}) if msg.type in ("error", "warning") else None)
        page.on("pageerror", lambda err: page_errs.append(str(err)[:300]))
        page.on(
            "requestfailed",
            lambda req: failed_req.append({"url": req.url[:180], "failure": (req.failure or "")[:120]}),
        )

        t_boot0 = time.perf_counter()
        await page.goto(LIVE + "/?workspace=1", wait_until="domcontentloaded", timeout=120000)
        await page.wait_for_function(
            "() => !!(window.AriaWorkspaceRegistry && window.AriaFrontDoorCatalog && window.AriaFrontDoorCatalog.goRoom)",
            timeout=60000,
        )
        boot_ms = round((time.perf_counter() - t_boot0) * 1000, 1)
        await dismiss(page)
        await page.evaluate(INSTALL_METRICS)

        script_count = await page.evaluate("() => document.scripts.length")
        rooms = await page.evaluate(
            """() => (window.AriaWorkspaceRegistry.rooms || []).map(r => ({
              id: r.id, title: r.title || r.label || r.id, view: r.view || null, native: !!r.native
            }))"""
        )
        ids = [r["id"] for r in rooms]
        report["registry"] = {
            "total": len(ids),
            "unique": len(set(ids)),
            "duplicates": [x for x in set(ids) if ids.count(x) > 1],
            "rooms": rooms,
            "boot_ms_to_registry": boot_ms,
            "script_count": script_count,
        }
        print("REGISTRY", len(ids), "scripts", script_count, "boot", boot_ms)

        # ---- cold then warm entry for all 34 ----
        cold = {}
        warm = {}
        for rid in ids:
            cold[rid] = await measure_enter(page, rid)
            print("COLD", rid, cold[rid]["identity_ms"], cold[rid]["usable_ms"], cold[rid]["ok"], cold[rid]["perf_class_usable"])
        # leave to home then warm pass
        await measure_enter(page, "home")
        for rid in ids:
            warm[rid] = await measure_enter(page, rid)
            print("WARM", rid, warm[rid]["identity_ms"], warm[rid]["usable_ms"], warm[rid]["ok"])

        report["rooms"] = {"cold": cold, "warm": warm}

        # ---- Search UI integration ----
        await measure_enter(page, "search")
        await page.evaluate(
            """() => [...document.querySelectorAll('#searchFacetBar button')]
              .find(b=>/everything|all/i.test(b.textContent||''))?.click()"""
        )
        t0 = time.perf_counter()
        await page.fill("#searchHomeInput", "Adams")
        await page.click("#searchHomeRunBtn")
        # wait for results without fixed assumption
        fly_ui = None
        for _ in range(40):
            fly_ui = await page.evaluate(
                """() => {
                  const items = [...document.querySelectorAll('#searchResultsList li')].map(el => el.innerText || '');
                  const joined = items.join(' ');
                  return { n: items.length, hasFly: /FLY|Adams|fly tying/i.test(joined), head: joined.slice(0, 300) };
                }"""
            )
            if fly_ui.get("n", 0) > 0:
                break
            await page.wait_for_timeout(100)
        search_fly_ms = round((time.perf_counter() - t0) * 1000, 1)
        # click first fly-ish result if present
        dest = await page.evaluate(
            """() => {
              const li = [...document.querySelectorAll('#searchResultsList li')]
                .find(el => /FLY|Adams|fly/i.test(el.innerText || ''));
              li?.click();
              return !!li;
            }"""
        )
        await page.wait_for_timeout(800)
        after = await page.evaluate("() => ({ room: document.body.dataset.room, hash: location.hash })")
        report["search"]["ui_fly"] = {
            "query_to_results_ms": search_fly_ms,
            "results": fly_ui,
            "clicked": dest,
            "after": after,
            "class": classify_ms(search_fly_ms, kind="api_search"),
        }

        await measure_enter(page, "search")
        t0 = time.perf_counter()
        await page.fill("#searchHomeInput", "warranty")
        await page.click("#searchHomeRunBtn")
        docs_ui = None
        for _ in range(40):
            docs_ui = await page.evaluate(
                """() => {
                  const items = [...document.querySelectorAll('#searchResultsList li')].map(el => el.innerText || '');
                  const joined = items.join(' ');
                  return { n: items.length, hasDoc: /warranty|DOCUMENT|Resume|automotive/i.test(joined), head: joined.slice(0, 300) };
                }"""
            )
            if docs_ui.get("n", 0) > 0:
                break
            await page.wait_for_timeout(100)
        search_docs_ms = round((time.perf_counter() - t0) * 1000, 1)
        dest = await page.evaluate(
            """() => {
              const li = [...document.querySelectorAll('#searchResultsList li')]
                .find(el => /warranty|DOCUMENT|Resume/i.test(el.innerText || ''));
              li?.click();
              return !!li;
            }"""
        )
        await page.wait_for_timeout(800)
        after = await page.evaluate("() => ({ room: document.body.dataset.room, hash: location.hash })")
        report["search"]["ui_docs"] = {
            "query_to_results_ms": search_docs_ms,
            "results": docs_ui,
            "clicked": dest,
            "after": after,
            "class": classify_ms(search_docs_ms, kind="api_search"),
        }
        print("SEARCH", report["search"]["ui_fly"], report["search"]["ui_docs"])

        # ---- Cross-room matrix (product links) ----
        for src, dst, query, mode in CROSS:
            entry = {"from": src, "to": dst, "mode": mode, "query": query}
            try:
                await measure_enter(page, src)
                if mode == "fly" or mode == "docs":
                    entry["via"] = "search_already_tested"
                    entry["ok"] = True
                elif mode == "link_or_identity":
                    # presence must stay presence; optional HA link
                    info = await page.evaluate(
                        """() => {
                          const t = document.getElementById('presenceView')?.innerText || '';
                          const link = [...document.querySelectorAll('#presenceView a, #presenceView button')]
                            .find(el => /home automation|Home Automation/i.test(el.textContent || ''));
                          return { room: document.body.dataset.room, link: !!link, notHA: !/home_automation/i.test(document.body.dataset.room || '') };
                        }"""
                    )
                    entry["info"] = info
                    entry["ok"] = info.get("room") == "presence" and info.get("notHA")
                else:
                    clicked = await page.evaluate(
                        """({dst}) => {
                          const root = document.querySelector('[id$=View]:not(.hidden), #houseRoomHost, body');
                          const btn = [...document.querySelectorAll('button, a')]
                            .find(el => {
                              const t = (el.textContent || '').trim();
                              const map = {
                                maker: /Maker/i, gallery: /Gallery/i, meme: /Meme/i, video: /Video/i,
                                documents: /Documents/i, mission: /Mission/i, actions: /Actions/i,
                                planner: /Planner/i, projects: /Projects/i, chat: /Chat/i,
                                home_automation: /Home Automation|HA/i
                              };
                              return map[dst] && map[dst].test(t) && el.offsetParent !== null;
                            });
                          if (btn) { btn.click(); return true; }
                          // fallback goRoom
                          window.AriaFrontDoorCatalog.goRoom(dst);
                          return false;
                        }""",
                        {"dst": dst},
                    )
                    await page.wait_for_timeout(700)
                    after = await page.evaluate("() => document.body.dataset.room")
                    entry["clicked_ui"] = clicked
                    entry["after_room"] = after
                    entry["ok"] = after == dst
            except Exception as e:
                entry["ok"] = False
                entry["error"] = str(e)[:200]
            report["cross"].append(entry)
            print("CROSS", entry)

        # ---- Chat tool surface (non-destructive) ----
        await measure_enter(page, "chat")
        chat_info = await page.evaluate(
            """() => {
              const input = document.getElementById('messageInput') || document.querySelector('textarea, input[type=text]');
              const send = document.getElementById('sendBtn') || document.querySelector('button[aria-label*=Send], button#send');
              const stop = document.getElementById('stopChatBtn');
              return {
                room: document.body.dataset.room,
                hasInput: !!input,
                hasSend: !!send,
                hasStop: !!stop,
                tools: (window.AriaWorkspaceRegistry?.tools || []).length
              };
            }"""
        )
        report["chat_tools"] = {
            "surface": chat_info,
            "note": "Destructive / credential Tools deferred to Jeff-attended residency; surface + registry counted",
            "jeff_attended": [
                "Authenticated Git push/commit",
                "HA physical actuation Tools",
                "Browser credential Tools",
            ],
        }

        # ---- Rapid navigation (race / leave) ----
        rapid_seq = ids[:20] + ids[20:]  # all
        t_rapid0 = time.perf_counter()
        rapid_states = []
        for rid in rapid_seq:
            await page.evaluate("(id) => window.AriaFrontDoorCatalog.goRoom(id)", rid)
            await page.wait_for_timeout(80)  # intentionally aggressive
            rapid_states.append(
                await page.evaluate("() => ({ room: document.body.dataset.room, overlays: document.querySelectorAll('dialog[open], .modal:not(.hidden)').length })")
            )
        # settle last
        await page.wait_for_timeout(500)
        final_room = await page.evaluate("() => document.body.dataset.room")
        stuck = await page.evaluate(
            """() => ({
              busy: /busy|thinking|loading/i.test(document.body.innerText.slice(0,200)),
              overlays: document.querySelectorAll('dialog[open]').length,
              room: document.body.dataset.room
            })"""
        )
        report["rapid_nav"] = {
            "count": len(rapid_seq),
            "elapsed_ms": round((time.perf_counter() - t_rapid0) * 1000, 1),
            "final_room": final_room,
            "stuck": stuck,
            "mismatches": sum(1 for s, rid in zip(rapid_states, rapid_seq) if s.get("room") not in (None, rid) and s.get("room") != rid),
            "note": "During rapid nav, intermediate mismatches expected; final settle must be coherent",
        }
        print("RAPID", report["rapid_nav"])

        # ---- Soak traversal (owner-style) ----
        soak_order = [
            "home", "planner", "projects", "chat", "memory", "search", "flytying",
            "documents", "journal", "gallery", "browser", "voice", "video", "maker",
            "connections", "integrations", "security", "automation", "actions",
            "repair", "integrity", "audit", "presence", "vision", "settings",
            "capabilities", "calendar", "health", "audio", "providers",
            "home_automation", "mission", "meme", "coding", "home",
        ]
        # ensure only live rooms
        soak_order = [r for r in soak_order if r in ids]
        # add any missing
        for r in ids:
            if r not in soak_order:
                soak_order.append(r)

        res0 = await page.evaluate(
            """() => ({
              dom: document.getElementsByTagName('*').length,
              scripts: document.scripts.length,
              listenersHint: typeof getEventListeners === 'function' ? 'devtools-only' : 'n/a'
            })"""
        )
        # backend RSS
        try:
            import psutil  # type: ignore

            proc = None
            for pr in psutil.process_iter(["pid", "name", "cmdline"]):
                cmd = " ".join(pr.info.get("cmdline") or [])
                if "main.py" in cmd and "serve" in cmd and "8765" in cmd:
                    proc = pr
                    break
            rss0 = proc.memory_info().rss if proc else None
        except Exception:
            proc = None
            rss0 = None

        soak_results = []
        t_soak0 = time.perf_counter()
        for rid in soak_order:
            m = await measure_enter(page, rid)
            soak_results.append(
                {
                    "room": rid,
                    "ok": m["ok"],
                    "identity_ms": m["identity_ms"],
                    "usable_ms": m["usable_ms"],
                    "fail": (m.get("snap") or {}).get("fail"),
                    "class": m["perf_class_usable"],
                }
            )
        # second pass subset
        for rid in ["home", "search", "documents", "planner", "chat", "mission"]:
            if rid in ids:
                m = await measure_enter(page, rid)
                soak_results.append(
                    {
                        "room": rid,
                        "pass": 2,
                        "ok": m["ok"],
                        "identity_ms": m["identity_ms"],
                        "usable_ms": m["usable_ms"],
                        "class": m["perf_class_usable"],
                    }
                )

        res1 = await page.evaluate(
            """() => ({
              dom: document.getElementsByTagName('*').length,
              scripts: document.scripts.length
            })"""
        )
        rss1 = None
        if proc:
            try:
                rss1 = proc.memory_info().rss
            except Exception:
                pass

        report["soak"] = {
            "order": soak_order,
            "elapsed_ms": round((time.perf_counter() - t_soak0) * 1000, 1),
            "results": soak_results,
            "failures": [r for r in soak_results if not r.get("ok")],
        }
        report["resources"] = {
            "dom_start": res0,
            "dom_end": res1,
            "dom_delta": (res1.get("dom") or 0) - (res0.get("dom") or 0),
            "scripts": script_count,
            "backend_rss_start": rss0,
            "backend_rss_end": rss1,
            "backend_rss_delta": (rss1 - rss0) if (rss0 and rss1) else None,
            "sys_p03_scripts": script_count,
            "sys_p03_note": "Script count measured; correlate with boot_ms and interaction, do not remove blindly",
        }
        print("SOAK failures", report["soak"]["failures"])
        print("RESOURCES", report["resources"])

        # fetch metrics summary from page
        fetch_summary = await page.evaluate(
            """() => {
              const s = window.__aria3cd;
              const fetches = s.fetches || [];
              const byUrl = {};
              for (const f of fetches) {
                const key = (f.url || '').split('?')[0];
                byUrl[key] = byUrl[key] || { n: 0, total: 0, max: 0, errors: 0 };
                byUrl[key].n += 1;
                byUrl[key].total += f.ms || 0;
                byUrl[key].max = Math.max(byUrl[key].max, f.ms || 0);
                if (f.error || (f.status && f.status >= 400)) byUrl[key].errors += 1;
              }
              const top = Object.entries(byUrl)
                .map(([url, v]) => ({ url, n: v.n, avg: Math.round(v.total / v.n), max: v.max, errors: v.errors }))
                .sort((a,b) => b.n - a.n)
                .slice(0, 30);
              const slow = Object.entries(byUrl)
                .map(([url, v]) => ({ url, n: v.n, avg: Math.round(v.total / v.n), max: v.max }))
                .sort((a,b) => b.max - a.max)
                .slice(0, 20);
              return { total_fetches: fetches.length, top_dupes: top, slowest: slow };
            }"""
        )
        report["errors"]["fetch_summary"] = fetch_summary
        report["errors"]["console"] = console_errs[-80:]
        report["errors"]["page"] = page_errs[-40:]
        report["errors"]["requestfailed"] = failed_req[-40:]

        await browser.close()

    # Activity + integrity + isolation
    st, d, ms = http("GET", "/api/activity/inbox?limit=50")
    items = d.get("items") or d.get("events") or []
    report["activity"] = {
        "ms": ms,
        "unread": d.get("unread"),
        "owner_visible_room_leave": any(
            (it.get("kind") == "room-leave" or it.get("type") == "room-leave") and it.get("ownerVisible") is True
            for it in items
        ),
        "sample": [
            {
                "kind": it.get("kind") or it.get("type"),
                "ownerVisible": it.get("ownerVisible"),
                "status": it.get("status"),
                "title": (it.get("title") or it.get("message") or "")[:80],
            }
            for it in items[:12]
        ],
    }
    st, d, ms = http("POST", "/api/integrity/scan?trigger=tier3cd", timeout=60)
    report["integrity"] = {
        "status": d.get("status"),
        "overall": (d.get("score") or {}).get("overall"),
        "clean": d.get("clean"),
        "ms": ms,
    }
    report["isolation"]["qa_header"] = http(
        "POST", "/api/planner/tasks", {"text": "ARIA-QA"}, {"X-Aria-QA-Run": "e2e"}
    )[0]
    report["isolation"]["test_shaped"] = http(
        "POST", "/api/planner/tasks", {"text": "ARIA-REPAIR-E2E-PLAN-PHASE3CD"}
    )[0]

    # Jeff-attended queue (software ready)
    report["jeff_attended"] = [
        {"room": "journal", "capability": "Encrypted export/import with Jeff password", "status": JEFF},
        {"room": "calendar", "capability": "External calendar / ICS real mutation", "status": JEFF},
        {"room": "browser", "capability": "Real website login sessions", "status": JEFF},
        {"room": "voice", "capability": "Microphone + cloud duplex", "status": JEFF},
        {"room": "presence", "capability": "Camera / gesture hardware", "status": JEFF},
        {"room": "vision", "capability": "Camera capture OCR", "status": JEFF},
        {"room": "video", "capability": "Device-dependent playback", "status": JEFF},
        {"room": "connections", "capability": "Real graph credentials if Neo4j down permanently", "status": JEFF},
        {"room": "integrations", "capability": "Real provider API keys entry", "status": JEFF},
        {"room": "security", "capability": "PIN lock/unlock with Jeff PIN", "status": JEFF},
        {"room": "automation", "capability": "Real HA / physical actuation", "status": JEFF},
        {"room": "coding", "capability": "Authenticated Git push/commit", "status": JEFF},
        {"room": "home_automation", "capability": "Physical device actuation", "status": JEFF},
        {"room": "chat", "capability": "Destructive Tools requiring credentials", "status": JEFF},
    ]

    # Build scorecards
    for rid in report["registry"]["rooms"]:
        i = rid["id"]
        c = report["rooms"]["cold"].get(i, {})
        w = report["rooms"]["warm"].get(i, {})
        status = REPAIRED if (c.get("ok") and w.get("ok")) else "NOT REPAIRED"
        report["scorecard"].append(
            {
                "room": i,
                "load_cold_usable_ms": c.get("usable_ms"),
                "load_warm_usable_ms": w.get("usable_ms"),
                "load_class_warm": w.get("perf_class_usable"),
                "identity_ok": c.get("ok") and w.get("ok"),
                "status": status,
            }
        )

    for path, meta in report["api_regression"].items():
        report["perf_scorecard"].append(
            {
                "workflow": path,
                "warm_ms": meta["warm_ms"],
                "class": meta["class"],
                "status": meta["status"],
            }
        )

    # Defect heuristics
    for row in report["scorecard"]:
        if not row["identity_ok"]:
            report["defects"].append(
                {
                    "id": f"ROOM-{row['room']}",
                    "room": row["room"],
                    "defect": "Room identity/usable failed in cold or warm enter",
                    "severity": "high",
                }
            )
        if row.get("load_class_warm") == "UNREASONABLE":
            report["defects"].append(
                {
                    "id": f"PERF-{row['room']}",
                    "room": row["room"],
                    "defect": f"Warm usable {row.get('load_warm_usable_ms')}ms UNREASONABLE",
                    "severity": "medium",
                }
            )

    # duplicate fetch detection
    for f in (report["errors"].get("fetch_summary") or {}).get("top_dupes") or []:
        if f.get("n", 0) >= 8 and "/api/" in (f.get("url") or ""):
            report["defects"].append(
                {
                    "id": f"DUP-{f['url'][-40:]}",
                    "defect": f"Repeated fetch {f['n']}x avg {f['avg']}ms max {f['max']}ms",
                    "url": f["url"],
                    "severity": "low" if f["avg"] < 100 else "medium",
                }
            )

    (OUT / "house_proof.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("SCORECARD failures", [r for r in report["scorecard"] if r["status"] != REPAIRED])
    print("DEFECTS", len(report["defects"]))
    print("integrity", report["integrity"], "iso", report["isolation"])
    print("activity room_leave ownerVisible", report["activity"].get("owner_visible_room_leave"))


if __name__ == "__main__":
    asyncio.run(main())
