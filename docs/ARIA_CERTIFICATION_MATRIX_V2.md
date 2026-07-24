# Aria Product Certification Matrix (v2 seed)

Status legend: `CERTIFIED` · `FIXED & CERTIFIED` · `INTENTIONALLY DEFERRED` · `REMOVED`

| Feature | Subsystem | Nav / UI | Status | Notes |
|---------|-----------|----------|--------|-------|
| Primary view tabs (21) | Shell | Top tab bar | FIXED & CERTIFIED | Smoke + switchToView |
| Mission Control tabs (17) | MC | workstation + MC nav | FIXED & CERTIFIED | Race/loaders/binding fixed |
| Command palette | Shell / Discoverability | Ctrl+K · Commands btn | FIXED & CERTIFIED | Nav + MC + actions; recent localStorage |
| Upgrade Clear session | Updates | Upgrade wizard | FIXED & CERTIFIED | apply_failed recovery |
| Gallery Generate CTA | Gallery / Image | Gallery prompt row | FIXED & CERTIFIED | Routes to chat generate |
| Modal Esc + focus cycle | A11y | Global keydown | FIXED & CERTIFIED | Lock excluded |
| toolConfirm labelled | Approvals | toolConfirmModal | FIXED & CERTIFIED | aria-labelledby |
| Voice cloud-live state | Voice | voice_bar WS | FIXED & CERTIFIED | Dead branches merged |
| `--muted` token | Visual | style.css | FIXED & CERTIFIED | Alias to --text-muted |
| Federated palette search (memory/docs) | Search | Command palette | INTENTIONALLY DEFERRED | Stage after action palette cert |
| God-app.js split | Architecture | app.js | INTENTIONALLY DEFERRED | High risk; staged modules already exist |
| Comfy full generate soak | Gallery | ComfyUI | INTENTIONALLY DEFERRED | Needs GPU long-run |
| HA live scenes | Smart home | HA | INTENTIONALLY DEFERRED | HA often down on workstation |
| Long-duration leak profile | Performance | Runtime | INTENTIONALLY DEFERRED | Hours soak not yet run this wave |
| Multi-monitor docking | Desktop | Native window | INTENTIONALLY DEFERRED | Needs native multi-display session |
| Command palette content search | Discoverability | Palette | INTENTIONALLY DEFERRED | P2 competitive gap |

Expand this matrix as each subsystem completes deep certification.
