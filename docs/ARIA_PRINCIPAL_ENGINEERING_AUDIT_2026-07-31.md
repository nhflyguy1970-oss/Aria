# ARIA Principal Engineering Audit

**Date:** 2026-07-31  
**Role:** Hostile principal engineer (inherited-codebase review)  
**Host:** live GUI `http://127.0.0.1:8765`  
**Stance:** Previous certifications are evidence, not proof. Prior work is assumed flawed until re-proven.

---

## 1. Executive Summary

Aria is a **capable personal workstation megaproduct** wrapped in a **corporate product taxonomy**. It is not yet a coherent production architecture.

What works: rich local AI surface area (chat, media, planner/calendar/journal federation, search, HA, jobs), and recent truth/consistency repairs that genuinely closed some toast-driven lies.

What fails the principal bar:

1. **Architecture is dual-stack sprawl** — flat `jarvis/*.py` god modules + 16 `*_product` facades + extensions + AI-Platform dual-write, without retiring the previous layer.
2. **Certification minting `READY_TO_SHIP` was dishonest** — seven HTTP smoke suites at a 60% bar (now hardened; smoke can no longer ship).
3. **False success still existed after “truth” work** — verify-on-failure → empty, journal HTTP-200-only, automation pause blind toasts, Focus `ok:true` when HA failed, gallery trash/restore without outcome checks.
4. **Security is LAN-trust by default** — API key optional; webhook/tool/HA surfaces reachable from private IPs; document path fallback could read arbitrary files (repaired); video restriction check failed open (repaired).
5. **UX is a feature museum** — 31 views, duplicated nav (Maker/Mission Control/Integrations in sidebar and tabs), 166 alerts noise, Ollama “degraded” vs “Ready” contradiction on the same screen.

**Ship recommendation: DO NOT SHIP as a release.** Treat as a strong private workstation beta. Continue deleting dual stacks and killing toast-driven success before any “READY TO SHIP” claim.

---

## 2–10. Grades (A–F)

| Area | Grade | Rationale |
|------|-------|-----------|
| **2. Overall Architecture** | **D+** | Product veneer over flat god monolith; dual_write cutover forever; ~455 routes in two files; competing routers. |
| **3. Code Quality** | **C-** | Real domain skill in places; copy-paste bridges; swallowed `except: pass` on product registration; mega files (server 3933, router 2267, assistant 2152). |
| **4. User Experience** | **C** | Powerful when you know it; overwhelming tab sprawl; success/status contradictions; Activity/Notifications feel unfinished. |
| **5. Reliability** | **C-** | Persistence exists but multi-truth stores; event-loop blocking; dual-write activity; restore/chat embed debt still listed in prior docs. |
| **6. Performance** | **D+** | Sync PIL on gallery list; full JSON indexes in RAM (~91MB code_index); sync tools up to 600s on ASGI loop; branch JSON full rewrite. |
| **7. Maintainability** | **D** | New engineer cannot find a single owner for memory, notifications, HA, or fly tying. Naming is cosplay. |
| **8. AI/LLM Architecture** | **C** | Works locally; `router` + `nlu` + FunctionGemma + capability_routing compete; image routing was previously lying (partially fixed). |
| **9. Product Integration** | **C+** | Planner↔Calendar↔Journal↔Search federation improved; Activity/Notifications/Settings still multi-home. |
| **10. Security** | **D** | Auth off by default; LAN bypass; webhook secret surface; home-rooted FS tools; restricted video fail-open (fixed this audit). |

---

## 11. Technical Debt Assessment

**Severity: Critical structural debt.**

| Debt class | Scale | Cost if ignored |
|------------|------:|-----------------|
| Flat root god modules | ~287 `.py`, ~66k LOC | Every feature touches `assistant`/`router`/`extra_routes` |
| Dual product/legacy stacks | flytying×3, HA×3, browser×3, voice×2 | Every bug fixed twice or once in the wrong place |
| Bridge factory | ~58 `*_bridge.py` | Noise without shared kernel |
| Persistence swamp | 6 SQLite DBs + N JSON owners | Drift is the default |
| SPA megapage | index.html ~3450, CSS ~6911, 130 JS | Untestable frontend growth |
| Cert / audit / acceptance theater | 3+ ship narratives | Operators get contradictory greens |
| Platform `dual_write` default | cutover never finishes | Permanent consistency tax |

---

## 12. Everything that should be redesigned

1. **Intent pipeline** — one router (kill parallel NLU / FunctionGemma / table private imports).
2. **HTTP composition** — FastAPI routers per domain; delete mega `extra_routes` / split `server.py`.
3. **Activity + Notifications** — one durable bus; delete localStorage-as-inbox-of-record.
4. **Settings** — one schema + migrations; settings_product either writes truth or is links-only.
5. **Memory** — one API / one durable store (sqlite *or* platform, not both forever).
6. **Frontend** — modular views + build step; stop growing a single HTML shell.
7. **Platform cutover** — finish migration or roll back; ban `dual_write` as steady state.
8. **Auth model** — explicit trust zones (loopback vs LAN vs remote); no silent LAN bypass.

---

## 13. Everything that should be simplified

- Fold `provider_health` into Integrations.
- Fold `layouts_product` into shell/settings.
- Fold coding “home” into jobs + engineering behaviors.
- One gallery/media library path (image/video/meme share lifecycle semantics).
- Certification dashboard as **report viewer**, with pytest/e2e as authority — or reverse, but not both claiming ship.

---

## 14. Everything that should be removed

- Clone `mission_bridge` / empty `status_bus` / boilerplate voice bridges after a shared kernel exists.
- Conflicting `docs/ARIA_*CERTIFICATION*.md` pile that disagree on ship.
- Legacy HA / flytying / browser stacks once product path is authoritative (pick one).
- `except Exception: pass` on product route registration (fail loud at startup).
- Default `READY_TO_SHIP` from smoke runs (done this audit).

---

## 15. Everything that should be modernized

- Async-offload heavy gallery/PIL/reindex/audit/HA list_states.
- Bounded indexes (sqlite/FTS) instead of multi‑MB JSON blobs in RAM.
- Structured logging with correlation IDs across chat → job → gallery → search.
- Frontend test harness for outcome verification (not click-cert theater).
- Rate-limit GC; tool-run artifact pruning.

---

## 16. Every bug discovered (this audit)

### Critical / High

| ID | Bug | Evidence |
|----|-----|----------|
| B1 | Clear/Clear Main treated verify failure/`{}` as empty → false “cleared” | `chat_controls.js`, `chat_branches.js` |
| B2 | Journal `journalPost` treated HTTP 200 as success ignoring `body.ok===false` | `journal.js` |
| B3 | Automation pause/resume toasted success without reading response | `command_catalog.js` |
| B4 | Focus/Pomodoro returned `ok:true` when HA Focus failed | `planner_services.py` + `planner.js` |
| B5 | Theme toast before remote persist; silent `.catch` | `theme.js` |
| B6 | Gallery trash/restore toasted without list/GET outcome check | `gallery_view.js` |
| B7 | Certification smoke could mint `READY_TO_SHIP` at 60% without image suite | `terminology.py`, prior run `20260731_111514_*` |
| B8 | Document preview/learn fell back to raw filesystem path | `document_services.py` |
| B9 | Restricted video check `except: pass` then served file | `extra_routes.py` video_gallery_file |
| B10 | Activity dismiss/read is localStorage-only (multi-client drift) | `activity_store.js`; OneTruth residual |
| B11 | Dual-write notifications: server fail still `ok:true` locally | `notifications.js` |
| B12 | Auth optional + LAN treated as local → dangerous APIs exposed on LAN | `auth.py`, `network_guard.py` |
| B13 | Sync cert deadlocked ASGI event loop (HTTP self-calls) | observed hung run; fixed earlier via `asyncio.to_thread` |
| B14 | Product route registration failures swallowed → silent 404 | `extra_routes.py` |

### Medium / UX

| ID | Issue |
|----|-------|
| U1 | 31 views + duplicated sidebar/tab destinations — feature museum |
| U2 | Footer “Ollama degraded” vs header “Ready” on same screen |
| U3 | 166 alerts — alert fatigue, not actionable ops |
| U4 | Vision warm log shows chat model warmed twice |
| U5 | Activity “complete” race before gallery asset verify (`chat_done.js`) |
| U6 | Storyboard/inpaint/video queue toasted as success before job outcome |
| U7 | Calendar NL “Scheduled” without asserting day item identity |
| U8 | Open Chat tab may need reload after gallery restore embeds |
| U9 | `cert_runner.js` default PASS / chrome clicks ≠ outcomes |

---

## 17. Every repair performed (this audit)

| Repair | Root cause addressed | Proof |
|--------|----------------------|-------|
| Clear verify fail-closed | B1 — missing/invalid verify ≠ empty | Code: require `verify.ok` + `Array.isArray(messages)` |
| Journal honors `body.ok===false` | B2 | Code in `journalPost` |
| Automation pause/resume checks `res`/`data.ok` | B3 | Code in `command_catalog.js` |
| Focus returns `ha_ok`/`complete`/`warnings`; UI warns | B4 | Live API: `ha_ok:false`, `complete:false` with HA warnings |
| Theme persist failure surfaces warn toast | B5 | Code in `theme.js` |
| Gallery trash verifies list absence; restore verifies GET | B6 | Code in `gallery_view.js` |
| Cert gate: 100% ship set; skip_image → not READY; `SMOKE_PASS` | B7 | Live sync: `GATE SMOKE_PASS`, blockers list image_lifecycle; tests pass |
| Document preview/learn no raw-path fallback | B8 | Code uses resolve-only |
| Video restriction fail-closed | B9 | `except` returns 403 |
| Cache-bust static assets for repairs | — | `index.html` `?v=*-audit` |

**Tests:** `tests/test_certification_product.py` — 4 passed (includes `skip_image` cannot READY_TO_SHIP).

**Live cert after harden:** run labeled `Principal audit smoke` → **`SMOKE_PASS`**, blockers include incomplete `image_lifecycle`. Previous optimistic READY from skip_image is invalidated.

---

## 18. Architectural improvements made

- Certification ship gate now measures **full `REQUIRED_FEATURES`**, not smoke subset.
- Introduced honest **`SMOKE_PASS`** vs **`READY_TO_SHIP`**.
- Focus API now exposes partial-success semantics instead of a single lying `ok`.

*(Larger redesigns listed in §12–15 are recommended, not executed — they require multi-week cutovers.)*

---

## 19. UX improvements made

- Focus toast distinguishes timer-started vs scene-failed.
- Theme/automation/gallery/journal/clear no longer celebrate unverified success.

---

## 20. Performance improvements made

None in this pass (identified only). Highest ROI next: offload gallery PIL + reindex; bound JSON indexes.

---

## 21. Reliability improvements made

- Fail-closed clear verify and video restriction.
- Certification no longer green-lights incomplete ship sets.
- Document path confinement tightened.

---

## 22. Remaining issues (not fixed this pass)

1. Activity inbox still localStorage-authoritative (B10).
2. Notification dual-write / duplicate “ready” events (B11).
3. Auth-off-by-default / LAN bypass (B12) — product decision required.
4. Dual stacks (flytying/HA/browser/voice) still present.
5. God files `server.py` / `extra_routes.py` / `assistant.py` / `router.py` untouched.
6. Image lifecycle still required for READY_TO_SHIP — full cert not re-run in this audit (Comfy slow).
7. Process restart verification still not automated in certification.
8. Python/JS code coverage not measured by certification.
9. Alert noise (166) and provider health contradiction (U2).
10. Chat restore-embed open-tab refresh debt (U8).
11. `import_folder` / home-rooted coding FS still broad.
12. Swallowed product registration exceptions (B14).

---

## 23. Honest inheritance assessment

**If I inherited this codebase today, I would keep Aria’s product *intent* and much of the domain code, but I would not keep this architecture as-is.**

I would:

1. Freeze new `*_product` packages until one dual stack is deleted per sprint.
2. Split HTTP into domain routers; make registration fail loud.
3. Choose one memory store, one notification bus, one settings schema.
4. Demote certification to evidence viewer until e2e covers restart + media + auth.
5. Turn on auth for non-loopback by default before any LAN “ship” claim.

Aria is **impressive as a personal AI workstation**. It is **not yet an exceptional engineered product**. The gap is not missing features — it is **too many parallel truths**, **optimistic gates**, and **UI that celebrates intent instead of outcome**.

Loyalty here is to making Aria exceptional — not to preserving the factory that grew around it.

---

## Appendix A — Audit method

- Architecture exploration of `jarvis/` products, gods, bridges, cutover.
- Hostile false-success scan of static JS + backend Focus/journal/automation paths.
- Security/performance skim (auth, documents, gallery/video, indexes, ASGI blocking).
- Live dogfood: Cert dashboard, Chat shell, Focus API, clear seed/clear, smoke certification.
- Prior cert docs treated as claims and contradicted where evidence failed.

## Appendix B — Key evidence artifacts

- Smoke cert gate proof: `SMOKE_PASS` with image_lifecycle blockers (2026-07-31 principal audit run).
- Focus partial success: `ha_ok: false`, `complete: false`, warnings populated.
- Clear API: seed → clear → `remaining 0`.
- Unit: `tests/test_certification_product.py` (4 passed).

## Appendix C — Grades summary strip

`Architecture D+ · Code C- · UX C · Reliability C- · Performance D+ · Maintainability D · AI/LLM C · Integration C+ · Security D · Overall: do not ship`
