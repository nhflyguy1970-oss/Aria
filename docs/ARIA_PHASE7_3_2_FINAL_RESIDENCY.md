# ARIA Phase 7.3.2 — Final Residency Defect Repair

**Date:** 2026-08-08  
**Nature:** Repair only verified engineering defects E1–E4 from Phase 7.3.1. No feature work. No unrelated refactor.  
**Entry:** `http://127.0.0.1:8765/?workspace=1`  
**Evidence dir:** `/tmp/aria-residency/c732/`

---

## Final question

> **If Jeff begins living in Aria today, is there any remaining known engineering reason he cannot use Aria as his permanent daily workspace?**

### Answer: **No**

There is no remaining known engineering reason. Final Owner Residency Certification is issued with **no remaining known engineering blockers**.

Phase 7.2 (non-credential house) and Phase 7.3.1 (credential defect discovery) stand. This phase closed E1–E4 with live Living Workspace re-verification.

---

## Defects repaired

### E1 — Invisible `ariaPrompt` / `ariaConfirm`

**Cause:** Dialogs lived under `#ariaLegacyShell`, which is `display: none` (0×0) in Living Workspace while `showModal()` still trapped the UI.

**Repair:** Host `#ariaPromptDialog`, `#ariaConfirmDialog`, and `#chatNewDialog` on `document.body`; `aria_dialogs.js` reparents if needed; CSS centers with `position: fixed; inset: 0; z-index: 10000`; journal import guarded against double-`change` cancel.

**Re-verify:** Journal encrypted export/import — owner-visible centered prompts; merge confirm; toast “Encrypted journal imported”. Health Restore — prompt open, title “Restore backup”, centered (~416×168). Evidence: `e1_prompt_visible.*`, `e1_import_ok.json`, `e1_health_restore_prompt.json`.

### E2 — Lock Now lockout

**Cause:** Lock Now / `jarvisShowLock` / `POST /api/security/lock` ignored `lock_capable` when PIN lock was off or unset.

**Repair:** UI and API refuse lock when not capable; lock screen will not show; toast explains PIN lock must be enabled and configured first. Unlock accepts `session || session_token`.

**Re-verify:** Lock Now → toast “PIN lock is off…”, `#lockScreen` stays `display: none`. Evidence: `e2_lock_now.json`.

### E3 — Home Automation routing

**Cause:** Front Door Home Automation mapped to `presence` instead of the HA product surface.

**Repair:** Dedicated `#homeAutomationView` / room `home_automation`; Presence is its own room; catalog, furnish, registry, tools, and smarthome home updated.

**Re-verify:** Room `home_automation`, chrome “Home Automation”, HA status Connected, Presence separate. Evidence: `e3_home_auto2.json`, `e3_presence_separate.json`.

### E4 — Living Chat Git stall

**Cause:** Orchestration did not route owner `gh …` speak to `coding_run_command`, and sandboxed runs (firejail `--private` / `--net=none`) broke authenticated `gh`.

**Repair:** Pre-NLU route for `gh api/auth/pr/…` → `coding_run_command`; allowlist `gh ` and run unsandboxed so host auth works.

**Re-verify:** Living Chat completed `gh api user -q .login` → `Command … — OK` + `nhflyguy1970-oss`, busy cleared. Evidence: `e4_live_ok.json`.

---

## Regression + smoke

| Workflow | Result |
|----------|--------|
| E1 password dialogs (Journal + Health restore) | Pass — visible, centered, interactive |
| E1 credential complete (encrypted import) | Pass |
| E2 Lock Now with PIN off | Pass — refuses; no lockout |
| E3 Home Automation room | Pass — HA UI, Connected |
| E4 Living Chat authenticated `gh` | Pass |
| Integrity | Score **100 · ready** (`final_integrity.json`) |
| Concise Living Workspace smoke | Integrity + HA + repaired credential/lock/git paths above |

Browser real-site login and Uncensored vault password were **not** claimed as daily defects in 7.3.1 (no owner credentials / intentional vault password in residency). They remain optional owner-supplied scenarios, not engineering blockers from this repair set.

---

## Certification status

| Gate | Status |
|------|--------|
| Phase 7.2 Owner Residency (non-credential house) | Stands |
| Phase 7.3.1 Credential Owner Residency (defect discovery) | Complete — E1–E4 recorded |
| Phase 7.3.2 Final Residency Defect Repair | **Complete** |
| Final Owner Residency — **no remaining known engineering blockers** | **Issued** |

**Signed answer:** **No** — Jeff can use Aria as his permanent daily workspace with no remaining known engineering blockers from the Phase 7.3 credential residency defects.
