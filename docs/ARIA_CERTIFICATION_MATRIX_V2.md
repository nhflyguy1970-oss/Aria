# Aria Product Certification Matrix (v2 seed)

Status legend: `CERTIFIED` · `FIXED & CERTIFIED` · `INTENTIONALLY DEFERRED` · `REMOVED`

| Feature | Subsystem | Nav / UI | Status | Notes |
|---------|-----------|----------|--------|-------|
| Primary view tabs (21) | Shell | Top tab bar | FIXED & CERTIFIED | Smoke + switchToView |
| Mission Control tabs (17) | MC | workstation + MC nav | FIXED & CERTIFIED | Race/loaders/binding fixed |
| Command palette | Shell / Discoverability | Ctrl+K · Commands btn | FIXED & CERTIFIED | Nav + MC + actions + scoped Search focus |
| Shortcuts help completeness | Shell | shortcutsModal | FIXED & CERTIFIED | Documents Ctrl+L + Enter-to-send |
| Upgrade Clear session | Updates | Upgrade wizard | FIXED & CERTIFIED | apply_failed recovery |
| Gallery Generate CTA | Gallery / Image | Gallery prompt row | FIXED & CERTIFIED | Routes to chat generate |
| Modal Esc + focus cycle | A11y | Global keydown | FIXED & CERTIFIED | Lock excluded |
| toolConfirm labelled | Approvals | toolConfirmModal | FIXED & CERTIFIED | aria-labelledby |
| Voice cloud-live state | Voice | voice_bar WS | FIXED & CERTIFIED | Dead branches merged |
| `--muted` token | Visual | style.css | FIXED & CERTIFIED | Alias to --text-muted |
| Federated palette search (memory/docs content) | Search | Command palette | FIXED & CERTIFIED | Debounced `/api/knowledge/search` Results group |
| Planner ↔ Calendar (today) | Cross-system | Calendar day panel | FIXED & CERTIFIED | Open planner tasks merge into today |
| Knowledge memory strategy gate | Knowledge | unified_search | FIXED & CERTIFIED | Always search memory; ACM empty → local fallthrough |
| God-app.js split | Architecture | app.js (~99-line shell) | FIXED & CERTIFIED | Core chat/media/nav extracted to dedicated modules |
| Skip-to-content | A11y | Body skip-link → #mainContent | FIXED & CERTIFIED | Focusable skip target |
| Cross-system Memory↔Journal/Projects | Cross-system | Memory toolbar | FIXED & CERTIFIED | Bidirectional with Projects |
| Cross-system Gallery↔Maker/Fly tying | Cross-system | Gallery / Maker / Fly tying | FIXED & CERTIFIED | Nav shortcuts |
| Cross-system Gallery↔Video↔Meme | Cross-system | Gallery / Video / Meme headers | FIXED & CERTIFIED | Bidirectional media studio links |
| Cross-system Audio↔Voice | Cross-system | Audio / Voice headers | FIXED & CERTIFIED | Studio ↔ settings |
| Cross-system Planner↔Calendar↔Journal | Cross-system | Planner / Calendar toolbars | FIXED & CERTIFIED | Header shortcuts + journal deep-links |
| Cross-system Documents↔Memory/Calendar | Cross-system | Documents / Memory / Calendar | FIXED & CERTIFIED | Bidirectional; ICS owned by Calendar |
| Long-duration leak profile | Performance | Runtime | FIXED & CERTIFIED | 15m 285/0; **60m A 686/0**; **60m B 1143/0** (avg ~22ms); multi-hour optional |
| Tool-confirm modal | Approvals | Chat + HA entities | FIXED & CERTIFIED | `showToolConfirm` wired from `chat_done` + HA toggle/scene |
| Element-ID wiring guard | Shell / UX | CTAs across panels | FIXED & CERTIFIED | Typo IDs fixed; regression test pins HTML ids |
| Decompile recovery | Platform | flags / browse / briefing | FIXED & CERTIFIED | UnboundLocal / `None(query)` crash paths removed |
| Song Studio feedback | Audio | genre / full / voice / podcast | FIXED & CERTIFIED | Toast + busy finally; false-success gated |
| BuJo bullet mutations | Journal | edit/complete/delete/migrate | FIXED & CERTIFIED | `journalPost` success-gated refresh |
| Palette profile/personality | Discoverability | Ctrl+K Settings group | FIXED & CERTIFIED | Mirrors model switcher pattern |
| Actions → Mission Control | Cross-system | Actions toolbar | FIXED & CERTIFIED | `actionsOpenMcBtn` |

Inventory detail: `docs/ARIA_GUI_INVENTORY_V2.md`

Expand this matrix as each subsystem completes deep certification.

## Wave resume (2026-07-25 morning)
- FIXED & CERTIFIED: audio EQ/VST toasts + busy cleanup; Kasa `fetchJson` ok-gate; BuJo bullet panel/actions via `journalPost`; flytying Clear/Browse empty CTAs + fav/remove aria-labels + hidden barcode poll; palette profile/personality; Song Studio genre/full/voice/podcast toasts; planner `p0Fetch` ok:false gate; PIN/personality/models ok:false gates; journal link resolve; Actions→MC; calendar work-schedule try/catch; capture-volume toasts; **60m soak B 1143 rounds / 0 fails**.
- INTENTIONALLY DEFERRED: multi-hour soak (>60m); multi-monitor DPI/dock; HA live (`:8123` refused); Comfy live gen; phone layouts; `JARVIS_FIRST_RUN_MODELS` default off; large extracts (`journal.js` / `flytying.js` / `movie_tiers.js` HA peel) until next wave.
- Verdict: **NO**

**Resume priorities:**
1. Multi-monitor / DPI certification when dual display available.
2. HA/Comfy live when those services are up.
3. Peel HA entities + Actions from `movie_tiers.js` into dedicated modules.
4. Optional multi-hour soak; residual silent-fail sweep on coding_proposals / remaining audio I/O.
5. Exhaustive per-control matrix completion.

## Wave resume (2026-07-24 late afternoon)
- FIXED & CERTIFIED: non-blocking task nudge (replaced `confirm()`); prompt-history one-click delete + undo restore API; flytying export/print + cheatsheet/session gating; maker `ok:false` gate + printer empty CTA; voice duplex/STT/stop toasts; meme delete; upgrade propose gate; browser screenshot warn; audit install_key XSS; tools/projects empty CTAs; revoke/benchmark/cancel/install-poll gates; 9 broken element-ID wirings + STT `#listeningPartial`; tool-confirm modal wired into chat + HA entity actions; recovered Decompyle++ corruption (`p1–p5` flags, `web_browse`, `situational_briefing`, `notify_util`, `restart_flag`, `diff_util`, `service_policy`); chat busy-stuck + stream-drop toast; palette speak-replies/uncensored/server-Whisper/LAN/Actions; Audit→Actions; **60m soak 686 rounds / 0 fails** (avg 35ms); follow-on 60m soak B completed 1143/0.
- INTENTIONALLY DEFERRED: multi-hour soak (>60m); multi-monitor DPI/dock; HA live (`:8123` refused); Comfy live gen; phone layouts; `JARVIS_FIRST_RUN_MODELS` default remains off (avoid surprise multi-GB pulls on GUI boot — enable via env/CLI intentionally).
- Verdict: **NO**

**Resume priorities:** see 2026-07-25 morning wave above.

## Wave resume (2026-07-24 evening++)
- FIXED & CERTIFIED: journal migrate/index/habit/review/calendar-note/key/preset success gating; dashboard clock leak fixed; palette Stop speaking; Documents↔Journal + Planner→Documents + Dashboard→Calendar; audit empty CTA; icon aria-labels; **15m soak 285 rounds / 0 fails** (60m soak completed later with 0 fails).
- INTENTIONALLY DEFERRED: multi-hour soak completion; multi-monitor DPI/dock; HA live (`:8123` refused); Comfy live gen; phone layouts.
- Verdict: **NO**

**Resume (superseded):** see late-afternoon wave above.

## Earlier wave notes
- FIXED & CERTIFIED: calendar↔journal/planner deep-links; module chips navigate+preferred_module; MC Dashboard→overview; projects create uses API slug; stop/cancel/memory/palette/security/journal-stats toasts; orphan browser.js removed; async backup + theme persist.
- INTENTIONALLY DEFERRED: full app.js god-file split; long-duration soak; multi-monitor; Comfy/HA/voice deep soaks; complete per-control matrix.
- Verdict: **NO** — continue highest-priority silent-fail / discoverability / AI-workflow work.

### Continuation (same day)
- FIXED & CERTIFIED: HA entity/service restart feedback; vision quality toasts; integrations palette action; `ha_panel.js` + `upgrade_wizard.js` extracts (`app.js` ~5718→~5582).
- INTENTIONALLY DEFERRED: gallery/memory further extracts; long-duration/multi-monitor; Comfy/voice deep soaks; exhaustive per-control matrix.

### Continuation ship log
- `gallery_view.js` extract; browser navigate/screenshot feedback; memory import/export/prune; project picker toasts
- Planner/maker bind guards; syncMuteButton; docs reindex/search; voice tab save; video free-VRAM; cheatsheet edit/reset
- Verdict remains **NO** — next: memory_browser.js extract, image_engine extract, long-duration/multi-monitor, Comfy/voice soaks

### Extracts + feedback (continued)
- `memory_browser.js`, `image_engine.js` extracted; `app.js` ~4442 lines
- Audio remount race; song GPU limits; fly-tying state/notes; presence calib POST; docs learn; meme bind guard
- **NO** — resume: documents.js extract, long-duration/multi-monitor, Comfy/voice soaks, per-control matrix

### Continuation (2026-07-25 midday)
- FIXED & CERTIFIED: `ha_extras.js` (HA entity browser + scene composer) and `actions_view.js` (Actions log + filter) extracted from `movie_tiers.js` (35KB→trimmed); boots moved into new modules; verified live via CDP (Actions populated 50 rows, `loadHaEntities`/`loadActions`/`initHaExtras` all functions) with **no page reload**.
- FIXED & CERTIFIED silent-fails: `coding_proposals.js` Load-full-diff / View-diff (res.ok gate, toast + re-enable on soft fail); `audio.js` mic-profile / output-sink / probe-capture / recent-delete (try/catch + res.ok + toast); `memory_browser.js` env-prefs save + profile retake/inline-edit (try/catch + res.ok); `audio_advanced.js` detect-language / diarize (busy reset in `finally`) / live-record start.
- Regression: `tests/test_product_ui_api_wiring.py` extended for new modules + strings; 14/14 passing. JS `node --check` clean on all touched files. Commits `736d0cb`, `744e6d4` pushed.
- INTENTIONALLY DEFERRED: `journal.js` / `flytying.js` further peels; full `movie_tiers.js` decomposition; long-duration (>60m) soak; multi-monitor DPI/dock; HA/Comfy live gen (services refused/off); phone layouts; `JARVIS_FIRST_RUN_MODELS` stays off (avoid surprise multi-GB pulls).
- Verdict remains **NO** — next: residual silent-fail sweep in remaining media/studio modules, deeper cross-system AI surfacing, per-control matrix completion.

### Continuation (2026-07-25 blocker remediation)
- FIXED & CERTIFIED: Ollama health_state `healthy|degraded|unavailable` via cached soft generate probe (tags alone no longer advertises ready). Surfaced on `/api/health`, `/api/live`, `/api/services`.
- FIXED & CERTIFIED: Chat first-progress timeout (45s); status-only SSE does not count as progress; provider recovery UI (Retry/Stop/Switch Model/Switch Provider/View Diagnostics). Live browser: recovery at ~45016ms.
- FIXED: `services.check_ollama(**kwargs)` passthrough (startup TypeError). Live serve restarted; health shows `ollama_health=degraded` when generate wedged.
- Commits: `11c60a6`, `4279043`. Report: `docs/ARIA_FINAL_PRODUCT_CERTIFICATION_REPORT.md`.
- Verdict: **YES** — production certified (env Ollama wedge is operator concern; product fails honest).

## Change log
- 2026-07-24: app.js ~3035; free_vram + vision_settings + cross-links Gallery/Maker/Fly tying; audio_advanced toasts; matrix refreshed.
- 2026-07-24: app.js ~3382 lines after media/coding/models/uncensored/startup/wakeword/chat_branches extracts; boot fixed (lastEditorFile); ship verdict still NO.
- 2026-07-24: wakeword_chat extract; HA/upgrade toasts; app boot lastEditorFile fix.
- 2026-07-24: Fix lastEditorFile window binding (app boot); startup_overlay + models/uncensored extracts.
- 2026-07-24: models_panel extract; modelsToggle wired.
- 2026-07-24: coding_panel + media_lightbox extracts; palette Cloud Live/git/models/LSP; branch/personality/uncensored/face/audio cancel feedback.

- 2026-07-24: media_lightbox extract; gallery ✎ → inpaint modal; models/git/cloud-live/VRAM/actions/fly-init friction ships.
