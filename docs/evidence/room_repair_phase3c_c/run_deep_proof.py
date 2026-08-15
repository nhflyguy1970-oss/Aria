#!/usr/bin/env python3
"""Tier 3C-C deep isol CRUD + Vision re-proof."""
from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright

LIVE = "http://127.0.0.1:8765"
ISOL = "http://127.0.0.1:8767"
OUT = Path(__file__).resolve().parent
REPAIRED = "REPAIRED — AWAITING FINAL CERTIFICATION"
NOT_REPAIRED = "NOT REPAIRED"


def http(base, method, path, data=None, headers=None, timeout=30):
    body = None
    hdrs = dict(headers or {})
    if data is not None:
        body = json.dumps(data).encode()
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(base + path, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode() or "{}")
        except Exception:
            payload = {}
        return e.code, payload
    except Exception as e:
        return None, {"error": str(e)}


def form_post(base, path, fields, timeout=20):
    body = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(
        base + path,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode() or "{}")
        except Exception:
            payload = {}
        return e.code, payload
    except Exception as e:
        return None, {"error": str(e)}


async def main():
    report = {
        "isol_deep": {},
        "vision": {},
        "docs_rag": {},
        "controls_deep": {},
        "leave_return": {},
        "vision_api": {},
        "activity": {},
        "integrity": {},
        "cross_extra": {},
    }

    for label, path in [
        ("default", "/api/documents/search?q=warranty"),
        ("keyword_hint", "/api/documents/search?q=warranty&prefer=keyword"),
        ("semantic_hint", "/api/documents/search?q=warranty&prefer=semantic"),
    ]:
        t0 = time.perf_counter()
        st, d = http(LIVE, "GET", path, timeout=45)
        report["docs_rag"][label] = {
            "status": st,
            "ms": round((time.perf_counter() - t0) * 1000, 1),
            "hits": len(d.get("hits") or d.get("results") or []),
            "meta": {
                k: d.get(k)
                for k in [
                    "mode",
                    "search_mode",
                    "path",
                    "strategy",
                    "embed_resident",
                    "fallback",
                    "message",
                    "ok",
                    "engine",
                ]
                if isinstance(d, dict) and k in d
            },
            "sample_keys": list(d.keys())[:24] if isinstance(d, dict) else [],
        }
    t0 = time.perf_counter()
    st, d = http(LIVE, "GET", "/api/documents/search?q=warranty", timeout=45)
    report["docs_rag"]["warm_repeat"] = {
        "status": st,
        "ms": round((time.perf_counter() - t0) * 1000, 1),
        "hits": len(d.get("hits") or d.get("results") or []),
    }

    for path in [
        "/api/vision/product",
        "/api/vision/honesty",
        "/api/vision/history?limit=5",
        "/api/vision/profiles",
        "/api/vision/actions",
    ]:
        t0 = time.perf_counter()
        st, d = http(LIVE, "GET", path, timeout=15)
        report["vision_api"][path] = {
            "status": st,
            "ms": round((time.perf_counter() - t0) * 1000, 1),
            "ok": d.get("ok") if isinstance(d, dict) else None,
            "keys": list(d.keys())[:12] if isinstance(d, dict) else [],
        }

    isol = {}
    st, d = form_post(ISOL, "/api/journal/daily", {"content": "ARIA-3CC-ISOL-J2", "bullet_type": "note"})
    bid = (d.get("bullet") or {}).get("id")
    isol["journal_create2"] = {"status": st, "id": bid, "ok": st == 200}
    if bid:
        for path, payload in [
            (f"/api/journal/bullets/{bid}", {"content": "ARIA-3CC-ISOL-J2-EDITED"}),
            ("/api/journal/daily/update", {"id": bid, "content": "ARIA-3CC-ISOL-J2-EDITED"}),
            (f"/api/journal/daily/{bid}", {"content": "ARIA-3CC-ISOL-J2-EDITED"}),
        ]:
            st2, d2 = http(ISOL, "POST", path, payload)
            if st2 and st2 != 404:
                isol["journal_edit"] = {"path": path, "status": st2, "ok": isinstance(d2, dict) and d2.get("ok")}
                break
        st3, d3 = http(ISOL, "DELETE", f"/api/journal/daily/{bid}")
        if st3 == 404:
            st3, d3 = http(ISOL, "POST", "/api/journal/daily/delete", {"id": bid})
        if st3 == 404:
            st3, d3 = form_post(ISOL, "/api/journal/daily/delete", {"id": bid})
        if st3 == 404:
            st3, d3 = http(ISOL, "DELETE", f"/api/journal/bullets/{bid}")
        isol["journal_delete"] = {"status": st3, "body": str(d3)[:160]}

    st, d = http(LIVE, "GET", "/api/journal/daily")
    isol["journal_live_clean"] = "ARIA-3CC-ISOL" not in json.dumps(d)

    st, d = http(ISOL, "POST", "/api/planner/tasks", {"text": "ARIA-3CC-ISOL-P2"})
    tid = (d.get("task") or {}).get("id") or d.get("id")
    isol["planner_create2"] = {"status": st, "id": tid}
    if tid:
        st, d = http(ISOL, "POST", f"/api/planner/tasks/{tid}/complete", {})
        if st == 404:
            st, d = http(ISOL, "POST", "/api/planner/tasks/complete", {"id": tid})
        isol["planner_complete"] = {"status": st, "ok": st == 200 or (isinstance(d, dict) and d.get("ok"))}
        st, d = http(ISOL, "DELETE", f"/api/planner/tasks/{tid}")
        if st == 404:
            st, d = http(ISOL, "POST", "/api/planner/tasks/delete", {"id": tid})
        isol["planner_delete"] = {"status": st, "ok": st in (200, 204) or (isinstance(d, dict) and d.get("ok"))}

    st, d = http(LIVE, "GET", "/api/planner/snapshot")
    isol["planner_live_clean"] = "ARIA-3CC-ISOL" not in json.dumps(d)

    st, d = http(
        ISOL,
        "POST",
        "/api/calendar/items",
        {
            "title": "ARIA-3CC-ISOL-CAL",
            "day": "2099-06-15",
            "time": "10:00",
            "duration_min": 30,
            "target": "planner",
        },
    )
    isol["calendar_create"] = {
        "status": st,
        "body": {k: d.get(k) for k in list(d.keys())[:14]} if isinstance(d, dict) else d,
    }
    cid = (d.get("item") or {}).get("id") or d.get("id") or (d.get("commitment") or {}).get("id")
    if not cid and isinstance(d, dict):
        # nested shapes
        for key in ("item", "commitment", "event", "task"):
            if isinstance(d.get(key), dict) and d[key].get("id"):
                cid = d[key]["id"]
                break
    if cid:
        st, d = http(ISOL, "POST", f"/api/calendar/items/{cid}/update", {"title": "ARIA-3CC-ISOL-CAL-EDIT"})
        isol["calendar_update"] = {"status": st, "ok": st == 200 or (isinstance(d, dict) and d.get("ok"))}
        st, d = http(ISOL, "DELETE", f"/api/calendar/items/{cid}")
        isol["calendar_delete"] = {"status": st, "ok": st in (200, 204) or (isinstance(d, dict) and d.get("ok"))}

    st, d = http(LIVE, "GET", "/api/calendar/month")
    isol["calendar_live_clean"] = "ARIA-3CC-ISOL" not in json.dumps(d)
    st, d = http(LIVE, "GET", "/api/calendar/agenda?days=30")
    isol["calendar_agenda_live_clean"] = "ARIA-3CC-ISOL" not in json.dumps(d)

    st, d = http(ISOL, "GET", "/api/gallery")
    isol["gallery_isol"] = {"status": st, "total": d.get("total") if isinstance(d, dict) else None}
    st, d = http(LIVE, "GET", "/api/gallery")
    isol["gallery_live"] = {
        "status": st,
        "total": d.get("total"),
        "images": len(d.get("images") or []),
    }

    # isol journal encrypted export with temp password (no live)
    st, d = http(
        ISOL,
        "POST",
        "/api/journal/export/encrypted",
        {"password": "tier3cc-temp-pass-NOT-JEFF"},
    )
    if st == 404:
        st, d = http(
            ISOL,
            "POST",
            "/api/journal/export_encrypted",
            {"password": "tier3cc-temp-pass-NOT-JEFF"},
        )
    isol["journal_enc_export_isol"] = {
        "status": st,
        "ok": st == 200 or (isinstance(d, dict) and (d.get("ok") or d.get("data"))),
        "keys": list(d.keys())[:10] if isinstance(d, dict) else [],
    }

    report["isol_deep"] = isol

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 960})
        await page.goto(LIVE + "/?workspace=1", wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_timeout(1200)
        await page.evaluate(
            """() => {
          try {
            const k='aria_ui_prefs_v1';
            const p=JSON.parse(localStorage.getItem(k)||'{}');
            p.whatsNewSeen='999';
            localStorage.setItem(k, JSON.stringify(p));
          } catch(_){}
          document.getElementById('whatsNewModal')?.classList.add('hidden');
        }"""
        )

        async def go(rid, wait=2000):
            await page.evaluate("(id)=>window.AriaFrontDoorCatalog?.goRoom?.(id)", rid)
            await page.wait_for_timeout(wait)

        await go("vision", 2500)
        v = await page.evaluate(
            """() => {
          const t=document.getElementById('visionView')?.innerText||'';
          const realFail=/could not load|failed to load|not implemented|TypeError|Internal Server|\\b500\\b/i.test(t.slice(0,500));
          return {
            room: document.body.dataset.room,
            realFail,
            hasModel:/moondream|llava|vision|OCR/i.test(t),
            hasControls: document.querySelectorAll('#visionView button').length,
            head: t.replace(/\\s+/g,' ').trim().slice(0,360)
          };
        }"""
        )
        await page.evaluate(
            """() => [...document.querySelectorAll('#visionView button')]
              .find(b=>/refresh/i.test(b.textContent||''))?.click()"""
        )
        await page.wait_for_timeout(1500)
        v2 = await page.evaluate(
            """() => {
          const t=document.getElementById('visionView')?.innerText||'';
          return {head:t.replace(/\\s+/g,' ').trim().slice(0,280), state:/State:\\s*\\w+/i.exec(t)?.[0]};
        }"""
        )
        report["vision"] = {
            "snap": v,
            "after_refresh": v2,
            "status": REPAIRED
            if v.get("room") == "vision" and not v.get("realFail") and v.get("hasModel")
            else NOT_REPAIRED,
        }

        await go("calendar", 2000)
        report["controls_deep"]["calendar"] = await page.evaluate(
            """() => {
          const t=document.getElementById('calendarView')?.innerText||'';
          const add=[...document.querySelectorAll('#calendarView button')]
            .find(b=>/add|new|create|\\+/i.test(b.textContent||''));
          return {
            hasMonth:/August|2026|Sun|Mon/i.test(t),
            addPresent:!!add,
            btns:document.querySelectorAll('#calendarView button').length
          };
        }"""
        )

        await go("maker", 2000)
        report["controls_deep"]["maker"] = await page.evaluate(
            """() => {
          const tabs=[...document.querySelectorAll('#makerView button, #makerView [role=tab]')]
            .map(b=>(b.textContent||'').trim()).filter(Boolean).slice(0,20);
          const line=document.getElementById('cadStatusLine')?.textContent||'';
          return {tabs, cad:line, hasUndefined: line.includes('undefined')};
        }"""
        )

        await go("meme", 2000)
        report["controls_deep"]["meme"] = await page.evaluate(
            """() => {
          const t=document.getElementById('memeView')?.innerText||'';
          return {
            btns:document.querySelectorAll('#memeView button').length,
            hasGen:/generate|template|caption|meme/i.test(t),
            fail:/failed to load|TypeError|\\b500\\b/i.test(t.slice(0,200)),
            head:t.replace(/\\s+/g,' ').trim().slice(0,240)
          };
        }"""
        )

        await go("browser", 2000)
        await page.evaluate(
            """() => [...document.querySelectorAll('#browserView button')]
              .find(b=>/refresh/i.test(b.textContent||''))?.click()"""
        )
        await page.wait_for_timeout(1200)
        report["controls_deep"]["browser"] = await page.evaluate(
            """() => {
          const t=document.getElementById('browserView')?.innerText||'';
          return {
            idle:/idle|ready|paused/i.test(t),
            fail:/agent failed|\\b500\\b/i.test(t),
            head:t.replace(/\\s+/g,' ').trim().slice(0,220)
          };
        }"""
        )

        await go("video", 2500)
        report["controls_deep"]["video"] = await page.evaluate(
            """() => {
          const t=document.getElementById('videoView')?.innerText||'';
          return {
            btns:document.querySelectorAll('#videoView button').length,
            hasMedia:/video|clip|generate|queue|empty|no /i.test(t),
            fail:/failed to load|TypeError|\\b500\\b/i.test(t.slice(0,300)),
            head:t.replace(/\\s+/g,' ').trim().slice(0,260)
          };
        }"""
        )

        await go("audit", 2000)
        await page.wait_for_timeout(2500)
        report["controls_deep"]["audit"] = await page.evaluate(
            """() => {
          const t=document.getElementById('auditView')?.innerText||'';
          return {
            progress:/phase|percent|progress|Audit/i.test(t),
            qaLeak:/ARIA-QA|smoke test|certification leftover/i.test(t),
            head:t.replace(/\\s+/g,' ').trim().slice(0,300)
          };
        }"""
        )

        await go("documents", 2000)
        report["controls_deep"]["documents"] = await page.evaluate(
            """() => {
          const t=document.getElementById('documentsView')?.innerText||'';
          return {
            hasLibrary:/library|document|import|search|index/i.test(t),
            btns:document.querySelectorAll('#documentsView button').length,
            inputs:document.querySelectorAll('#documentsView input').length
          };
        }"""
        )

        await go("gallery", 2000)
        report["controls_deep"]["gallery"] = await page.evaluate(
            """() => {
          const t=document.getElementById('galleryView')?.innerText||'';
          return {
            comfyFail:/ComfyUI settings unavailable/i.test(t),
            count:/(\\d+)\\s+images/i.exec(t)?.[1],
            btns:document.querySelectorAll('#galleryView button').length
          };
        }"""
        )

        for rid in ["journal", "planner", "documents", "gallery", "connections", "vision"]:
            await go(rid, 1100)
            await go("home", 500)
            await go(rid, 1100)
            report["leave_return"][rid] = await page.evaluate("()=>document.body.dataset.room")

        await go("presence", 1500)
        report["controls_deep"]["presence"] = await page.evaluate(
            """() => {
          const t=document.getElementById('presenceView')?.innerText||'';
          return {
            identity: document.body.dataset.room,
            hash: location.hash,
            hasGestures:/gesture|camera|presence|face/i.test(t),
            head:t.replace(/\\s+/g,' ').trim().slice(0,240)
          };
        }"""
        )

        # Calendar → Planner shared surface (focus suggestions API)
        st, d = http(LIVE, "GET", "/api/calendar/focus-suggestions")
        report["cross_extra"]["calendar_focus_suggestions"] = {
            "status": st,
            "keys": list(d.keys())[:10] if isinstance(d, dict) else [],
        }

        # Journal enc cancel already proven; confirm More menu still works
        await go("journal", 1500)
        enc = await page.evaluate(
            """() => {
          const more=document.querySelector('#journalView details.bujo-more-menu');
          if(more) more.open=true;
          return {
            exportEnc: !!document.getElementById('journalExportEncBtn'),
            importEnc: !!document.getElementById('journalImportEncBtn'),
            moreOpen: !!more?.open
          };
        }"""
        )
        report["controls_deep"]["journal_enc_controls"] = enc

        await browser.close()

    st, d = http(LIVE, "POST", "/api/integrity/scan?trigger=tier3cc-deep", timeout=60)
    report["integrity"] = {
        "status": d.get("status"),
        "overall": (d.get("score") or {}).get("overall"),
        "clean": d.get("clean"),
        "counts": d.get("counts"),
    }
    st, d = http(LIVE, "GET", "/api/activity/inbox?limit=50")
    items = d.get("items") or d.get("events") or d.get("notifications") or []
    kinds = {}
    for it in items:
        k = it.get("kind") or it.get("type") or "unknown"
        kinds[k] = kinds.get(k, 0) + 1
    report["activity"] = {
        "unread": d.get("unread"),
        "kinds": kinds,
        "sample": [
            {
                "kind": (it.get("kind") or it.get("type")),
                "ownerVisible": it.get("ownerVisible"),
                "title": (it.get("title") or it.get("message") or "")[:80],
            }
            for it in items[:10]
        ],
    }

    # Patch domain_proof vision status
    proof_path = OUT / "domain_proof.json"
    if proof_path.exists():
        proof = json.loads(proof_path.read_text(encoding="utf-8"))
        proof["rooms"]["vision"] = {
            **proof.get("rooms", {}).get("vision", {}),
            "snap": report["vision"].get("snap"),
            "after_refresh": report["vision"].get("after_refresh"),
            "status": report["vision"]["status"],
            "note": "Prior fail was false positive matching ~1500MB as 500; corrected with word-boundary detector",
            "jeff_attended": [
                "Camera capture / real image OCR — JEFF-ATTENDED — FINAL RESIDENCY REQUIRED"
            ],
        }
        proof["deep"] = {
            "isol_deep": report["isol_deep"],
            "docs_rag": report["docs_rag"],
            "vision_api": report["vision_api"],
            "controls_deep": report["controls_deep"],
            "leave_return": report["leave_return"],
            "cross_extra": report["cross_extra"],
        }
        proof["integrity"] = report["integrity"]
        proof["activity"] = report["activity"]
        proof_path.write_text(json.dumps(proof, indent=2), encoding="utf-8")

    (OUT / "deep_proof.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("VISION", report["vision"]["status"], report["vision"].get("snap"))
    print("ISOL", json.dumps(isol, indent=2)[:2500])
    print("DOCS", report["docs_rag"])
    print("VISION_API", report["vision_api"])
    print("integrity", report["integrity"])
    print("leave", report["leave_return"])
    print("controls", {k: v for k, v in report["controls_deep"].items()})


if __name__ == "__main__":
    asyncio.run(main())
