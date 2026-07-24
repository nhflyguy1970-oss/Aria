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
| God-app.js split | Architecture | app.js (~5.9k after extract) | INTENTIONALLY DEFERRED | Partial: `modal_chrome.js` extracted; further slices staged |
| Orphan `jarvis/api.py` | Dead code | Voice API duplicate | REMOVED | Live routes live in `extensions/voice/api.py` |
| Palette model switching | Models | Command palette Models group | FIXED & CERTIFIED | Reads `#chatModelSelect` options |
| Memory hit deep-link | Search / Memory | Palette Results → memory list | FIXED & CERTIFIED | Search + scroll/flash when id matches |
| Comfy full generate soak | Gallery | ComfyUI | INTENTIONALLY DEFERRED | Needs GPU long-run |
| HA live scenes | Smart home | HA | INTENTIONALLY DEFERRED | HA often down on workstation |
| Long-duration leak profile | Performance | Runtime | INTENTIONALLY DEFERRED | Hours soak not yet run this wave |
| Multi-monitor docking | Desktop | Native window | INTENTIONALLY DEFERRED | Needs native multi-display session |
| Command palette content search | Discoverability | Palette | FIXED & CERTIFIED | Superseded by federated Results group |

Inventory detail: `docs/ARIA_GUI_INVENTORY_V2.md`

Expand this matrix as each subsystem completes deep certification.

## Wave resume (2026-07-24)
- FIXED & CERTIFIED: calendar↔journal/planner deep-links; module chips navigate+preferred_module; MC Dashboard→overview; projects create uses API slug; stop/cancel/memory/palette/security/journal-stats toasts; orphan browser.js removed; async backup + theme persist.
- INTENTIONALLY DEFERRED: full app.js god-file split; long-duration soak; multi-monitor; Comfy/HA/voice deep soaks; complete per-control matrix.
- Verdict: **NO** — continue highest-priority silent-fail / discoverability / AI-workflow work.
