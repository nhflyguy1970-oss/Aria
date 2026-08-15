#!/usr/bin/env python3
"""3C-D retest after repairs: WhatsNew dismiss, Video abort, Search UI, Video ok."""
from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright

LIVE = "http://127.0.0.1:8765"
OUT = Path(__file__).resolve().parent


def http(method, path, data=None, headers=None, timeout=45):
    body = None
    hdrs = dict(headers or {})
    if data is not None:
        body = json.dumps(data).encode()
        hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(LIVE + path, data=body, headers=hdrs, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}"), round((time.perf_counter() - t0) * 1000, 1)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw.decode() or "{}")
        except Exception:
            payload = {}
        return e.code, payload, round((time.perf_counter() - t0) * 1000, 1)
    except Exception as e:
        return None, {"error": str(e)}, round((time.perf_counter() - t0) * 1000, 1)


async def main():
    report = {"repairs": [], "search": {}, "video": {}, "whatsnew": {}, "rapid_video": {}, "integrity": {}, "isolation": {}}

    # API search POST (owner path)
    for q, key in [("Adams", "fly"), ("warranty", "docs")]:
        st, d, ms = http("POST", "/api/search/product/query", {"query": q, "mode": "browse", "limit": 24})
        results = d.get("results") or []
        report["search"][f"api_{key}"] = {
            "ms": ms,
            "n": len(results),
            "ok": st == 200 and len(results) > 0,
            "sample": [(r.get("source"), (r.get("title") or "")[:48]) for r in results[:4]],
        }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 960})
        await page.goto(LIVE + "/?workspace=1", wait_until="domcontentloaded", timeout=120000)
        await page.wait_for_function(
            "() => !!(window.AriaFrontDoorCatalog && window.AriaWorkspaceRegistry)",
            timeout=60000,
        )

        # Proper WhatsNew dismiss using exported API / version
        wn = await page.evaluate(
            """() => {
          const ver = window.AriaDiscoverability?.WHATS_NEW_VERSION || '2026.07.29-global-ux';
          try {
            const k='aria_ui_prefs_v1';
            const p=JSON.parse(localStorage.getItem(k)||'{}');
            p.whatsNewSeen = ver;
            localStorage.setItem(k, JSON.stringify(p));
          } catch(_){}
          window.dismissWhatsNew?.();
          document.getElementById('whatsNewModal')?.classList.add('hidden');
          return {
            hasDismiss: typeof window.dismissWhatsNew === 'function',
            version: window.AriaDiscoverability?.WHATS_NEW_VERSION || null,
            hidden: document.getElementById('whatsNewModal')?.classList.contains('hidden')
          };
        }"""
        )
        report["whatsnew"] = wn
        await page.wait_for_timeout(1500)  # past auto-open timer
        wn2 = await page.evaluate(
            """() => ({
          stillHidden: document.getElementById('whatsNewModal')?.classList.contains('hidden'),
          blocking: !document.getElementById('whatsNewModal')?.classList.contains('hidden')
        })"""
        )
        report["whatsnew"]["after_timer"] = wn2

        # Esc path: open then Esc
        await page.evaluate("() => window.openWhatsNew?.(true)")
        await page.wait_for_timeout(200)
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(200)
        esc = await page.evaluate(
            """() => ({
          hidden: document.getElementById('whatsNewModal')?.classList.contains('hidden'),
          seen: (JSON.parse(localStorage.getItem('aria_ui_prefs_v1')||'{}').whatsNewSeen || '')
        })"""
        )
        report["whatsnew"]["esc"] = esc

        # Video
        await page.evaluate("() => window.AriaFrontDoorCatalog.goRoom('video')")
        await page.wait_for_timeout(2000)
        video = await page.evaluate(
            """() => {
          const t = document.getElementById('videoView')?.innerText || '';
          return {
            room: document.body.dataset.room,
            btns: document.querySelectorAll('#videoView button').length,
            couldnt: /Couldn.?t load videos/i.test(t),
            failedToLoad: /Failed to load videos/i.test(t),
            emptyOk: /No videos yet/i.test(t),
            head: t.replace(/\\s+/g,' ').trim().slice(0,280)
          };
        }"""
        )
        report["video"]["enter"] = video

        # Rapid leave/enter video should not paint abort error
        for _ in range(6):
            await page.evaluate("() => window.AriaFrontDoorCatalog.goRoom('video')")
            await page.wait_for_timeout(60)
            await page.evaluate("() => window.AriaFrontDoorCatalog.goRoom('home')")
            await page.wait_for_timeout(60)
        await page.evaluate("() => window.AriaFrontDoorCatalog.goRoom('video')")
        await page.wait_for_timeout(1500)
        report["rapid_video"] = await page.evaluate(
            """() => {
          const t = document.getElementById('videoView')?.innerText || '';
          return {
            room: document.body.dataset.room,
            couldnt: /Couldn.?t load videos/i.test(t),
            failedToLoad: /Failed to load videos/i.test(t),
            emptyOk: /No videos yet|Video Studio|Generate/i.test(t)
          };
        }"""
        )

        # Search UI Adams + warranty with force click if needed
        await page.evaluate("() => window.AriaFrontDoorCatalog.goRoom('search')")
        await page.wait_for_timeout(1200)
        await page.evaluate(
            """() => [...document.querySelectorAll('#searchFacetBar button')]
              .find(b=>/everything|all/i.test(b.textContent||''))?.click()"""
        )

        async def run_search(q):
            await page.fill("#searchHomeInput", q)
            t0 = time.perf_counter()
            await page.evaluate("() => document.getElementById('searchHomeRunBtn')?.click()")
            # wait for non-empty result items (not the empty placeholder alone with 0 results)
            data = None
            for _ in range(80):
                data = await page.evaluate(
                    """() => {
                      const items = [...document.querySelectorAll('#searchResultsList li.search-result-item')];
                      const empty = !!document.querySelector('#searchResultsList li.search-empty');
                      const status = document.getElementById('searchResultsStatus')?.textContent || '';
                      return {
                        n: items.length,
                        empty,
                        status,
                        titles: items.slice(0,5).map(el => (el.innerText||'').slice(0,100)),
                        searching: /Searching/i.test(status)
                      };
                    }"""
                )
                if data["n"] > 0 or (data["empty"] and not data["searching"] and "No matches" in (data["status"] or "")):
                    break
                await page.wait_for_timeout(100)
            ms = round((time.perf_counter() - t0) * 1000, 1)
            # open first result if any
            dest = None
            if data and data["n"] > 0:
                await page.evaluate(
                    """() => {
                      document.querySelector('#searchResultsList li.search-result-item')?.click();
                      document.getElementById('searchOpenResultBtn')?.click();
                    }"""
                )
                await page.wait_for_timeout(900)
                dest = await page.evaluate("() => ({ room: document.body.dataset.room, hash: location.hash })")
                await page.evaluate("() => window.AriaFrontDoorCatalog.goRoom('search')")
                await page.wait_for_timeout(600)
            return {"ms": ms, "ui": data, "dest": dest}

        report["search"]["ui_fly"] = await run_search("Adams")
        report["search"]["ui_docs"] = await run_search("warranty")

        await browser.close()

    st, d, ms = http("POST", "/api/integrity/scan?trigger=tier3cd-retest", timeout=90)
    report["integrity"] = {"status": d.get("status"), "overall": (d.get("score") or {}).get("overall"), "clean": d.get("clean"), "ms": ms}
    report["isolation"]["qa"] = http("POST", "/api/planner/tasks", {"text": "ARIA-QA"}, {"X-Aria-QA-Run": "e2e"})[0]
    report["isolation"]["test_shaped"] = http("POST", "/api/planner/tasks", {"text": "ARIA-REPAIR-E2E-PLAN-PHASE3CD"})[0]

    (OUT / "retest_after_repair.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2)[:5000])


if __name__ == "__main__":
    asyncio.run(main())
