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
| God-app.js split | Architecture | app.js (~3035 after extracts) | INTENTIONALLY DEFERRED | Partial: many panels extracted; crop/webcam/chat stream remain |
| Skip-to-content | A11y | Body skip-link → #mainContent | FIXED & CERTIFIED | Focusable skip target |
| Cross-system Memory↔Journal/Projects | Cross-system | Memory toolbar | FIXED & CERTIFIED | Bidirectional with Projects |
| Cross-system Gallery↔Maker/Fly tying | Cross-system | Gallery / Maker / Fly tying | FIXED & CERTIFIED | Nav shortcuts |
| Cross-system Gallery↔Video↔Meme | Cross-system | Gallery / Video / Meme headers | FIXED & CERTIFIED | Bidirectional media studio links |
| Cross-system Audio↔Voice | Cross-system | Audio / Voice headers | FIXED & CERTIFIED | Studio ↔ settings |
| Cross-system Planner↔Calendar↔Journal | Cross-system | Planner / Calendar toolbars | FIXED & CERTIFIED | Header shortcuts + journal deep-links |
| Cross-system Documents↔Memory/Calendar | Cross-system | Documents toolbar | FIXED & CERTIFIED | ICS wizard toasts |
| Free VRAM module | System | free_vram.js | FIXED & CERTIFIED | Extracted from app.js |
| Vision settings module | Vision | vision_settings.js | FIXED & CERTIFIED | Extracted from app.js |
| Audio status in health module | System | health.mjs renderAudioStatus | FIXED & CERTIFIED | Extracted from app.js |
| Audio advanced feedback | Audio | Detect/diarize/live/PTT | FIXED & CERTIFIED | Toasts on fail/success |
| Palette checklist / meme / storyboard | Discoverability | Command palette | FIXED & CERTIFIED | First-flight + media focus actions |
| Crop/compare/webcam extract | Architecture | app.js attachments | FIXED & CERTIFIED | crop_webcam.js + jarvisAttach bridge; compare preview remains in app.js |
| Comfy full generate soak | Gallery | ComfyUI | INTENTIONALLY DEFERRED | Needs GPU long-run |
| HA live scenes | Smart home | HA | INTENTIONALLY DEFERRED | HA often down on workstation |
| Long-duration leak profile | Performance | Runtime | INTENTIONALLY DEFERRED | Hours soak not yet run this wave |
| Multi-monitor docking | Desktop | Native window | INTENTIONALLY DEFERRED | Needs native multi-display session |
| Command palette content search | Discoverability | Palette | FIXED & CERTIFIED | Superseded by federated Results group |
| Exhaustive per-control matrix | QA | All controls | INTENTIONALLY DEFERRED | Seed + regression tests; full matrix ongoing |

Inventory detail: `docs/ARIA_GUI_INVENTORY_V2.md`

Expand this matrix as each subsystem completes deep certification.

## Wave resume (2026-07-24 late)
- FIXED & CERTIFIED: …/attachment_compare/media_jobs/coding_jobs/**media_urls** extracts; empty-state CTAs (+Projects/Fly videos/Memory/MC recs/Gallery/Meme); act:compare-images + act:resume-media-jobs; coding cancel + poll failure toasts. `app.js` ~**2241** lines.
- INTENTIONALLY DEFERRED: chat/stream/sendMessage still in app.js (core pipeline); proposal/diff helpers still coupled; long-duration soak; multi-monitor; Comfy/HA/voice deep soaks; exhaustive per-control matrix.
- Verdict: **NO** — continue highest-priority silent-fail / extracts / soaks.

**Next priorities:** chat-stream/sendMessage extract; coding proposal/diff extract; long-duration memory-leak soak; multi-monitor native; Comfy/HA deep soaks; per-control matrix completion.

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

## Change log
- 2026-07-24: app.js ~3035; free_vram + vision_settings + cross-links Gallery/Maker/Fly tying; audio_advanced toasts; matrix refreshed.
- 2026-07-24: app.js ~3382 lines after media/coding/models/uncensored/startup/wakeword/chat_branches extracts; boot fixed (lastEditorFile); ship verdict still NO.
- 2026-07-24: wakeword_chat extract; HA/upgrade toasts; app boot lastEditorFile fix.
- 2026-07-24: Fix lastEditorFile window binding (app boot); startup_overlay + models/uncensored extracts.
- 2026-07-24: models_panel extract; modelsToggle wired.
- 2026-07-24: coding_panel + media_lightbox extracts; palette Cloud Live/git/models/LSP; branch/personality/uncensored/face/audio cancel feedback.

- 2026-07-24: media_lightbox extract; gallery ✎ → inpaint modal; models/git/cloud-live/VRAM/actions/fly-init friction ships.
