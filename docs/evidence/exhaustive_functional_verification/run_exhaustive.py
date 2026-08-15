#!/usr/bin/env python3
"""
Exhaustive functional verification campaign.
- Enumerate meaningful controls per Room
- Drive real owner-UI interactions
- Isol mutations only (never live production writes)
- STOP entire campaign on credential/hardware gate → WAITING FOR JEFF
"""
from __future__ import annotations

import asyncio
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

LIVE = "http://127.0.0.1:8765"
ISOL = "http://127.0.0.1:8768"
OUT = Path(__file__).resolve().parent

# Credential / hardware signals in UI
CREDENTIAL_PATTERNS = [
    r"password",
    r"passphrase",
    r"enter.?pin",
    r"\bpin\b",
    r"unlock",
    r"api.?key",
    r"access.?token",
    r"sign.?in",
    r"log.?in",
    r"authenticate",
    r"credential",
    r"git.?password",
    r"oauth",
]
HARDWARE_PATTERNS = [
    r"allow.?microphone",
    r"allow.?camera",
    r"request.?permission",
    r"start.?camera",
    r"enable.?microphone",
    r"speak.?now",
]

# Rooms with known credential/hardware gates (still enumerate; stop when gate hit)
KNOWN_GATES = {
    "journal": ["encrypted export", "encrypted import"],
    "security": ["PIN", "lock", "unlock"],
    "integrations": ["API keys", "provider credentials"],
    "browser": ["website login"],
    "voice": ["microphone", "cloud live"],
    "presence": ["camera", "gestures"],
    "vision": ["camera capture"],
    "video": ["device playback"],
    "home_automation": ["HA auth", "device actuation"],
    "automation": ["real actuation"],
    "coding": ["git auth/push"],
    "connections": ["graph credentials"],
    "calendar": ["external calendar mutation"],
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def http(base, method, path, data=None, headers=None, timeout=30, form=False):
    body = None
    hdrs = dict(headers or {})
    if data is not None:
        if form:
            body = urllib.parse.urlencode(data).encode()
            hdrs["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(base + path, data=body, headers=hdrs, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            try:
                payload = json.loads(raw.decode() or "{}")
            except Exception:
                payload = {"raw": raw[:200].decode(errors="replace")}
            return r.status, payload, round((time.perf_counter() - t0) * 1000, 1)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw.decode() or "{}")
        except Exception:
            payload = {"raw": raw[:200].decode(errors="replace")}
        return e.code, payload, round((time.perf_counter() - t0) * 1000, 1)
    except Exception as e:
        return None, {"error": str(e)}, round((time.perf_counter() - t0) * 1000, 1)


ENUM_JS = """
(rid) => {
  const panelMap = {
    documents:'documentsView',planner:'plannerView',calendar:'calendarView',gallery:'galleryView',
    voice:'voiceView',presence:'presenceView',journal:'journalView',video:'videoView',
    browser:'browserView',maker:'makerView',meme:'memeView',vision:'visionView',
    connections:'connectionsView',audit:'auditView',projects:'projectsView',search:'searchView',
    flytying:'flytyingView',memory:'memoryView',coding:'codingView',settings:'settingsView',
    capabilities:'capabilitiesView',integrations:'integrationsView',security:'securityView',
    actions:'actionsView',automation:'automationView',home_automation:'homeAutomationView',
    chat:'chatView',health:'healthRoom',home:'homeRoom',mission:'missionRoom',
    repair:'repairRoom',integrity:'integrityRoom',providers:'providersRoom',audio:'audioRoom'
  };
  const isVisible = (el) => {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return !!(r.width && r.height) && s.visibility !== 'hidden' && s.display !== 'none';
  };
  const pid = panelMap[rid];
  let root = pid ? document.getElementById(pid) : null;
  if (!root || root.classList.contains('hidden')) {
    root = document.querySelector('#houseRoomHost .room-root, #houseRoomHost [data-room-root], #houseRoomHost > *');
  }
  if (!root) root = document.getElementById('houseRoomHost');
  // Last resort: visible main only — NEVER full document.body (chrome inflates counts)
  if (!root) root = document.querySelector('main, #main, .workspace-main, #workspaceMain');
  if (!root) {
    return { room: document.body.dataset.room, hash: location.hash, control_count: 0, visible_count: 0,
      credential_controls: [], hardware_controls: [], controls: [], error: 'no_room_root' };
  }
  const controls = [];
  const seen = new Set();
  const push = (el, kind) => {
    const id = el.id || '';
    const text = (el.innerText || el.value || el.getAttribute('aria-label') || el.title || el.name || '').trim().replace(/\\s+/g,' ').slice(0,80);
    const key = kind + '|' + id + '|' + text.slice(0,40);
    if (seen.has(key)) return;
    // Skip global chrome that leaked into host
    if (/whatsNew|sidebar|nav-rail|activityCenter|commandPalette|lockScreen/i.test(id)) return;
    seen.add(key);
    const visible = isVisible(el);
    controls.push({
      kind, id, text, visible,
      tag: el.tagName.toLowerCase(),
      type: el.getAttribute('type') || '',
      role: el.getAttribute('role') || '',
      href: el.getAttribute('href') || '',
      disabled: !!el.disabled,
      credentialish: /password|passphrase|\\bpin\\b|unlock|api.?key|token|sign.?in|log.?in|credential|encrypt/i.test(text+' '+id+' '+(el.type||'')),
      hardwareish: /camera|microphone|\\bmic\\b|speak|gesture|hardware|device/i.test(text+' '+id),
      destructiveish: /delete|remove|wipe|destroy|purge|reset.?all/i.test(text+' '+id),
      consequentialish: /\\bpush\\b|commit|deploy|actuate|toggle.?all|send.?to|\\bprint\\b|slice/i.test(text+' '+id),
    });
  };
  root.querySelectorAll('button').forEach(el => push(el, 'button'));
  root.querySelectorAll('a[href]').forEach(el => push(el, 'link'));
  root.querySelectorAll('input').forEach(el => push(el, 'input'));
  root.querySelectorAll('textarea').forEach(el => push(el, 'textarea'));
  root.querySelectorAll('select').forEach(el => push(el, 'select'));
  root.querySelectorAll('[role=tab], .bujo-tab, [data-tab], [data-bujo]').forEach(el => push(el, 'tab'));
  root.querySelectorAll('[role=switch], input[type=checkbox], input[type=radio]').forEach(el => push(el, 'toggle'));
  return {
    room: document.body.dataset.room,
    hash: location.hash,
    root_id: root.id || root.className?.toString?.()?.slice?.(0,60) || '',
    control_count: controls.length,
    visible_count: controls.filter(c => c.visible).length,
    credential_controls: controls.filter(c => c.credentialish),
    hardware_controls: controls.filter(c => c.hardwareish),
    controls
  };
}
"""


async def dismiss(page):
    await page.evaluate(
        """() => {
      const ver = window.AriaDiscoverability?.WHATS_NEW_VERSION || '2026.07.29-global-ux';
      try {
        const k='aria_ui_prefs_v1';
        const p=JSON.parse(localStorage.getItem(k)||'{}');
        p.whatsNewSeen=ver;
        localStorage.setItem(k, JSON.stringify(p));
      } catch(_){}
      window.dismissWhatsNew?.();
      document.getElementById('whatsNewModal')?.classList.add('hidden');
      window.ariaDismissDialogs?.();
    }"""
    )


async def go_room(page, rid):
    await dismiss(page)
    t0 = time.perf_counter()
    t_app0 = await page.evaluate("() => performance.now()")
    await page.evaluate("(id) => window.AriaFrontDoorCatalog.goRoom(id)", rid)
    # wait identity
    for _ in range(80):
        room = await page.evaluate("() => document.body.dataset.room")
        if room == rid:
            break
        await page.wait_for_timeout(25)
    identity_ms = round(await page.evaluate(f"() => performance.now() - {t_app0}"), 1)
    await dismiss(page)
    return {"identity_ms": identity_ms, "wall_ms": round((time.perf_counter() - t0) * 1000, 1)}


def write_waiting(report, gate):
    report["status"] = "WAITING FOR JEFF"
    report["waiting_for_jeff"] = gate
    report["stopped_at"] = now_iso()
    (OUT / "WAITING_FOR_JEFF.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    (OUT / "campaign_state.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


async def detect_open_credential_gate(page):
    """Return gate info. needsCred only for REAL owner secrets — not confirm dialogs / Pin-to-sidebar."""
    return await page.evaluate(
        """() => {
      const isVisible = (el) => {
        if (!el) return false;
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return !!(r.width && r.height) && s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0';
      };
      const pwdVisible = [...document.querySelectorAll('input[type=password]')].filter(isVisible);
      const aria = document.getElementById('ariaPromptDialog');
      const ariaOpen = !!(aria && (aria.open === true || aria.hasAttribute('open')) && isVisible(aria));
      const ariaText = ariaOpen
        ? ((document.getElementById('ariaPromptIntro')?.textContent || '') + ' ' + (document.getElementById('ariaPromptTitle')?.textContent || ''))
        : '';
      const ariaCred = ariaOpen && /password|passphrase|encrypt|import password|export password|api.?key|access.?token|enter.?pin|security.?pin|unlock.?pin/i.test(ariaText);
      // Visible lock-screen / security PIN field only
      const lockPin = [...document.querySelectorAll('#lockScreen input, #securityView input, input#pin, input[name=pin], input[name=password]')].filter(isVisible);
      const lockCred = lockPin.some(i => i.type === 'password' || /pin|password/i.test(i.id+' '+(i.name||'')));
      const dialogs = [...document.querySelectorAll('dialog[open], .modal:not(.hidden), [role=dialog]:not(.hidden)')]
        .filter(isVisible);
      const credDialog = dialogs.find(d => {
        const t = d.innerText || '';
        if (/job center|scrub|shortcut|confirm\\?|remove test/i.test(t) && !/password|passphrase|encrypt|enter.?pin/i.test(t)) return false;
        return /password|passphrase|export password|import password|enter.?your.?pin|security.?pin|api.?key|sign.?in to|log.?in to/i.test(t);
      });
      const needsCred = pwdVisible.length > 0 || ariaCred || lockCred || !!credDialog;
      return {
        needsCred,
        pwd: pwdVisible.length > 0,
        ariaCred,
        lockCred,
        dialogCount: dialogs.length,
        text: (credDialog?.innerText || ariaText || '').slice(0, 500),
        pwdCountVisible: pwdVisible.length
      };
    }"""
    )


async def main():
    report = {
        "campaign": "exhaustive_functional_verification",
        "started_at": now_iso(),
        "status": "IN_PROGRESS",
        "phase3cd_audit": {},
        "rooms": {},
        "capabilities": [],
        "waiting_for_jeff": None,
        "integrity": {},
        "isolation": {},
        "stats": {
            "rooms_entered": 0,
            "controls_discovered": 0,
            "controls_exercised": 0,
            "workflows_completed": 0,
            "forms_submitted": 0,
            "state_mutations": 0,
            "persistence_checks": 0,
            "leave_return_checks": 0,
            "credential_gates_hit": 0,
        },
    }

    # ---- Phase 3C-D audit (evidence-backed, not inferred) ----
    house_path = Path("/media/jeff/AI/jarvis/docs/evidence/room_repair_phase3c_d/house_proof.json")
    house = json.loads(house_path.read_text()) if house_path.exists() else {}
    report["phase3cd_audit"] = {
        "wall_clock_house_proof_ms": 91249,
        "wall_clock_retest_ms": 30191,
        "rooms_entered_cold_warm": 34,
        "measurement_per_room": "identity_ms + usable_ms via goRoom + dataset.room + button/text heuristic",
        "controls_clicked_documented": "NOT PROVEN — no per-control exercise log in house_proof.json",
        "forms_submitted_documented": "NOT PROVEN in house_proof (retest had Search fill/click only)",
        "state_mutations_live": "NOT PROVEN in 3C-D house soak (read-mostly); isol mutations were 3C-C",
        "persistence_checks_3cd": "NOT PROVEN for most Rooms in 3C-D evidence",
        "leave_return_3cd": "PARTIAL — some leave/return in earlier phases; 3C-D soak was enter-only identity",
        "restart_checks_3cd": "NOT PROVEN",
        "cross_room_count": len(house.get("cross") or []),
        "search_ui_after_repair": "PARTIALLY PROVEN (Adams→Fly, warranty→Documents in later retests)",
        "chat_tools": "SURFACE ONLY — registry count + input/send/stop presence; no Tool execution proof",
        "scorecard_label": "REPAIRED — AWAITING FINAL CERTIFICATION was integration/surface status — NOT exhaustive functional proof",
        "verdict": "Five-minute-class run (~91s house proof) cannot exhaustively exercise 34 Rooms × meaningful controls. Claims of complete functional testing are NOT PROVEN.",
        "claim_reclassification": "All 34 prior REPAIRED labels treated as UNPROVEN for exhaustive functional standard unless re-proven here.",
    }

    # Ensure isol server for mutations
    # (caller may start it; we probe)
    st, _, _ = http(ISOL, "GET", "/api/health", timeout=3)
    report["isol_ready"] = st == 200

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 960})
        await page.goto(LIVE + "/?workspace=1", wait_until="domcontentloaded", timeout=120000)
        await page.wait_for_function(
            "() => !!(window.AriaFrontDoorCatalog && window.AriaWorkspaceRegistry)",
            timeout=60000,
        )
        await dismiss(page)

        rooms = await page.evaluate(
            """() => (window.AriaWorkspaceRegistry.rooms || []).map(r => ({
              id: r.id, title: r.title || r.label || r.id
            }))"""
        )
        report["registry"] = {"total": len(rooms), "rooms": rooms}
        assert len(rooms) == 34, f"expected 34 rooms, got {len(rooms)}"

        # ---- ENUMERATE all rooms first (discovery only — not proof) ----
        for meta in rooms:
            rid = meta["id"]
            enter = await go_room(page, rid)
            enum = await page.evaluate(ENUM_JS, rid)
            # open Journal more menu so enc buttons visible in enum
            if rid == "journal":
                await page.evaluate(
                    """() => {
                  const more=document.querySelector('#journalView details.bujo-more-menu');
                  if (more) more.open = true;
                }"""
                )
                enum = await page.evaluate(ENUM_JS, rid)
            report["rooms"][rid] = {
                "room": rid,
                "title": meta.get("title"),
                "entry_time": now_iso(),
                "identity_ms": enter["identity_ms"],
                "enumeration_only": True,
                "controls_discovered": enum.get("control_count"),
                "controls_visible": enum.get("visible_count"),
                "credential_controls": enum.get("credential_controls"),
                "hardware_controls": enum.get("hardware_controls"),
                "controls": enum.get("controls"),
                "known_gates": KNOWN_GATES.get(rid, []),
                "controls_exercised": [],
                "workflows": [],
                "status": "ENUMERATED — NOT YET EXERCISED",
            }
            report["stats"]["rooms_entered"] += 1
            report["stats"]["controls_discovered"] += enum.get("control_count") or 0
            print(
                "ENUM",
                rid,
                "controls",
                enum.get("control_count"),
                "cred",
                len(enum.get("credential_controls") or []),
                "hw",
                len(enum.get("hardware_controls") or []),
            )

        (OUT / "control_inventory.json").write_text(json.dumps(report["rooms"], indent=2), encoding="utf-8")
        (OUT / "campaign_state.json").write_text(json.dumps({
            **report,
            "rooms": {k: {kk: vv for kk, vv in v.items() if kk != "controls"} for k, v in report["rooms"].items()},
        }, indent=2), encoding="utf-8")

        # ---- Begin exhaustive exercise: order non-gated rooms first, then gated ----
        # Priority: complete rooms without known credential gates before hitting a wait.
        ungated = [r["id"] for r in rooms if r["id"] not in KNOWN_GATES]
        # Journal first among gated — first hard credential workflow we intentionally stop on
        gated_priority = [
            "journal",
            "security",
            "integrations",
            "browser",
            "voice",
            "presence",
            "vision",
            "video",
            "home_automation",
            "automation",
            "coding",
            "connections",
            "calendar",
        ]
        gated = [g for g in gated_priority if g in {r["id"] for r in rooms}]
        gated += [r["id"] for r in rooms if r["id"] in KNOWN_GATES and r["id"] not in gated]
        exercise_order = ungated + gated

        for rid in exercise_order:
            room_rec = report["rooms"][rid]
            room_rec["functional_test_start"] = now_iso()
            room_rec["enumeration_only"] = False
            t_room0 = time.perf_counter()
            enter = await go_room(page, rid)
            room_rec["cold_or_warm_enter_ms"] = enter["identity_ms"]

            # Exercise safe visible controls (non-credential, non-hardware, non-destructive, non-consequential)
            controls = [c for c in (room_rec.get("controls") or []) if c.get("visible")]
            # For gated rooms: confront credential controls FIRST (never skip behind the 25-cap)
            if rid in KNOWN_GATES:
                cred_first = [c for c in controls if c.get("credentialish") or re.search(
                    r"encrypted|export enc|import enc|set pin|change pin|unlock|api key|add key|sign in|log in|password",
                    (c.get("text") or "") + " " + (c.get("id") or ""),
                    re.I,
                )]
                controls = cred_first + [c for c in controls if c not in cred_first]
            exercised = []
            for c in controls:
                if c.get("credentialish") or c.get("hardwareish"):
                    continue
                if c.get("destructiveish") or c.get("consequentialish"):
                    continue
                if c.get("disabled"):
                    continue
                # Skip pure navigation spam of every link; allow tabs/toggles/safe buttons
                if c["kind"] not in ("button", "tab", "toggle"):
                    continue
                # Limit per room to keep campaign moving but still substantial — record honesty if capped
                if len(exercised) >= 25:
                    room_rec["control_exercise_capped"] = True
                    break

                label = c.get("text") or c.get("id") or c["kind"]

                if re.search(
                    r"encrypted|export enc|import enc|\block\b|unlock|set pin|change pin|api key|add key|sign in|log in|password",
                    label,
                    re.I,
                ):
                    # Hit credential gate — STOP entire campaign and WAIT FOR JEFF
                    gate_time = now_iso()
                    if rid == "journal":
                        await page.evaluate(
                            """() => {
                              const more=document.querySelector('#journalView details.bujo-more-menu');
                              if (more) more.open = true;
                            }"""
                        )
                        await page.wait_for_timeout(200)
                        await page.evaluate("() => document.getElementById('journalExportEncBtn')?.click()")
                    else:
                        await page.evaluate(
                            """(c) => {
                              let el = c.id ? document.getElementById(c.id) : null;
                              if (!el) {
                                el = [...document.querySelectorAll('button,a,input')].find(e => (e.innerText||'').trim() === c.text);
                              }
                              el?.click();
                            }""",
                            c,
                        )
                    await page.wait_for_timeout(500)
                    gate = await detect_open_credential_gate(page)
                    prompt_ui = await page.evaluate(
                        """() => {
                          const inputs = [...document.querySelectorAll('input')].filter(i => i.offsetParent && (i.type==='password' || /pass|pin/i.test(i.placeholder||'') || /pass|pin/i.test(i.id||'')));
                          const openDlg = document.querySelector('dialog[open], .modal:not(.hidden), [role=dialog]:not(.hidden)');
                          return {
                            pwdInputs: inputs.length,
                            dialogText: (openDlg?.innerText || '').slice(0, 400),
                            bodyHint: /password|passphrase|PIN|encrypt/i.test((document.body.innerText||'').slice(0, 2500))
                          };
                        }"""
                    )
                    if gate.get("needsCred") or prompt_ui.get("pwdInputs") or prompt_ui.get("bodyHint") or rid == "journal":
                        gf = {
                            "status": "WAITING FOR JEFF",
                            "room": rid,
                            "capability": label,
                            "workflow": f"{rid} → {label}",
                            "credential_required": (
                                "Jeff's Journal encryption password"
                                if rid == "journal"
                                else "Owner credential as prompted in Aria UI"
                            ),
                            "what_owner_must_enter": "Enter the real password/PIN/credential in the Aria UI dialog. Do not paste the secret into chat.",
                            "expected_success": "Credential accepted; operation completes; owner-visible success; underlying state correct",
                            "gate_detected_at": gate_time,
                            "waiting_began_at": now_iso(),
                            "ui_gate": gate,
                            "prompt_ui": prompt_ui,
                            "resume_instructions": "Complete the credential prompt in Aria, then tell the agent: RESUME exhaustive verification from the waiting gate.",
                            "do_not": [
                                "skip",
                                "cancel automatically",
                                "fake password",
                                "continue to next Room",
                                "mark passed/failed/skipped",
                            ],
                        }
                        room_rec["status"] = "WAITING FOR JEFF"
                        room_rec["functional_test_end"] = now_iso()
                        room_rec["total_functional_duration_ms"] = round(
                            (time.perf_counter() - t_room0) * 1000, 1
                        )
                        report["stats"]["credential_gates_hit"] = 1
                        write_waiting(report, gf)
                        print("WAITING_FOR_JEFF", json.dumps(gf, indent=2))
                        await browser.close()
                        return report
                    # If no prompt actually appeared, do not claim gate — fall through carefully
                    continue

                # Safe click
                t0 = time.perf_counter()
                result = await page.evaluate(
                    """(c) => {
                      let el = c.id ? document.getElementById(c.id) : null;
                      if (!el && c.text) {
                        el = [...document.querySelectorAll('button,a,[role=tab],.bujo-tab')].find(e => (e.innerText||'').trim().replace(/\\s+/g,' ') === c.text);
                      }
                      if (!el) return {ok:false, reason:'not_found'};
                      el.click();
                      return {ok:true, id: el.id || null, text: (el.innerText||'').trim().slice(0,60)};
                    }""",
                    c,
                )
                await page.wait_for_timeout(150)
                gate = await detect_open_credential_gate(page)
                if gate.get("needsCred"):
                    gf = {
                        "status": "WAITING FOR JEFF",
                        "room": rid,
                        "capability": label,
                        "workflow": f"{rid} → {label}",
                        "credential_required": "Owner credential as prompted in UI",
                        "what_owner_must_enter": "Enter the real credential in the Aria dialog",
                        "expected_success": "Workflow completes after credential accepted",
                        "gate_detected_at": now_iso(),
                        "waiting_began_at": now_iso(),
                        "ui_gate": gate,
                        "resume_instructions": "Complete the credential in Aria UI, then tell the agent to RESUME.",
                    }
                    room_rec["status"] = "WAITING FOR JEFF"
                    write_waiting(report, gf)
                    print("WAITING_FOR_JEFF", json.dumps(gf, indent=2))
                    await browser.close()
                    return report

                await page.evaluate(
                    """() => {
                      document.getElementById('whatsNewModal')?.classList.add('hidden');
                      document.getElementById('ariaSoftTip')?.classList.add('hidden');
                      // Close non-credential dialogs left by prior clicks (Job Center, scrub confirm, shortcuts)
                      for (const d of document.querySelectorAll('dialog[open]')) {
                        const txt = d.innerText || '';
                        if (/password|passphrase|encrypt|enter.?pin|api.?key/i.test(txt)) continue;
                        try { d.close(); } catch(_) { d.classList.add('hidden'); }
                      }
                      document.querySelectorAll('.modal:not(.hidden)').forEach(m => {
                        const txt = m.innerText || '';
                        if (/password|passphrase|encrypt|enter.?pin|api.?key/i.test(txt)) return;
                        if (m.id === 'whatsNewModal' || /job center|shortcut|scrub|confirm/i.test(txt)) m.classList.add('hidden');
                      });
                    }"""
                )
                exercised.append(
                    {
                        "control": label,
                        "kind": c["kind"],
                        "id": c.get("id"),
                        "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
                        "result": result,
                        "status": "INTERACTED — UI response observed; full workflow state may still be PARTIAL",
                    }
                )
                report["stats"]["controls_exercised"] += 1

            room_rec["controls_exercised"] = exercised
            room_rec["controls_exercised_count"] = len(exercised)

            # Leave/return check
            await go_room(page, "home")
            await go_room(page, rid)
            back = await page.evaluate("() => document.body.dataset.room")
            room_rec["leave_return"] = {"ok": back == rid, "room": back}
            report["stats"]["leave_return_checks"] += 1

            room_rec["functional_test_end"] = now_iso()
            room_rec["total_functional_duration_ms"] = round((time.perf_counter() - t_room0) * 1000, 1)
            # Honest status: enumeration+partial control clicks is still not full workflow proof
            if rid in KNOWN_GATES:
                room_rec["status"] = "PARTIALLY PROVEN — gated workflows not yet reached"
            else:
                room_rec["status"] = (
                    "PARTIALLY PROVEN — controls interacted; full create/save/persist workflows not all completed"
                )
            print("ROOM", rid, room_rec["status"], "exercised", len(exercised), "ms", room_rec["total_functional_duration_ms"])

            # Persist progress continuously
            slim = {k: {kk: vv for kk, vv in v.items() if kk != "controls"} for k, v in report["rooms"].items()}
            (OUT / "campaign_state.json").write_text(
                json.dumps({**report, "rooms": slim}, indent=2), encoding="utf-8"
            )

            # After finishing all ungated soft clicks, deliberately enter Journal encrypted export gate
            if rid == ungated[-1]:
                # Next loop will hit gated rooms starting with journal if ordered — ensure journal early in gated
                pass

        # If we somehow finish all without gate — still must hit Journal enc export gate intentionally
        await go_room(page, "journal")
        await page.evaluate(
            """() => {
              const more=document.querySelector('#journalView details.bujo-more-menu');
              if (more) more.open = true;
              document.getElementById('journalExportEncBtn')?.click();
            }"""
        )
        await page.wait_for_timeout(600)
        gate = await detect_open_credential_gate(page)
        # ariaPrompt may not use dialog[open] — check for prompt UI
        prompt_ui = await page.evaluate(
            """() => {
              const t = document.body.innerText || '';
              const hasPrompt = /password|passphrase|encrypt/i.test(t.slice(0,2000)) && !!document.querySelector('input[type=password], .aria-prompt input, #ariaPromptDialog input, dialog input');
              const inputs = [...document.querySelectorAll('input')].filter(i => i.offsetParent && (i.type==='password' || /pass/i.test(i.placeholder||'')));
              return {hasPrompt, pwdInputs: inputs.length, sample: (document.querySelector('dialog[open], .modal:not(.hidden)')?.innerText||'').slice(0,300)};
            }"""
        )
        gf = {
            "status": "WAITING FOR JEFF",
            "room": "journal",
            "capability": "Encrypted export",
            "workflow": "Journal → More → Export encrypted → password prompt → export completes",
            "credential_required": "Jeff's Journal encryption password",
            "what_owner_must_enter": "Enter the real Journal encryption password in the Aria password prompt (do not paste it into chat)",
            "expected_success": "Export payload generated; download/save offered; no error; incorrect password path separately verifiable later",
            "gate_detected_at": now_iso(),
            "waiting_began_at": now_iso(),
            "ui_gate": gate,
            "prompt_ui": prompt_ui,
            "resume_instructions": "In Aria Journal, complete the encrypted export password prompt. Then reply: RESUME exhaustive verification — Journal encrypted export completed.",
        }
        report["rooms"]["journal"]["status"] = "WAITING FOR JEFF"
        report["stats"]["credential_gates_hit"] = 1
        write_waiting(report, gf)
        print("WAITING_FOR_JEFF", json.dumps(gf, indent=2))
        await browser.close()
        return report


if __name__ == "__main__":
    # Fix: remove invalid JS regex in python source - the /encrypted/ line was a mistake in the draft
    # The file as written has a syntax error with `/encrypted|.../i.search` - need clean python only
    asyncio.run(main())
