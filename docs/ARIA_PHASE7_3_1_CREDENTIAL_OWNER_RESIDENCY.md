# ARIA Phase 7.3.1 — Credential Owner Residency

**Date:** 2026-08-08  
**Nature:** Living Workspace owner scenarios only — no feature work, no code changes.  
**Entry:** `http://127.0.0.1:8765/?workspace=1` (LAN gate also via `http://10.0.0.235:8765/?workspace=1`)  
**Evidence dir:** `/tmp/aria-residency/c731/`

---

## Final question

> **If Jeff begins living in Aria today, is there any remaining known engineering reason he cannot use Aria as his permanent daily workspace?**

### Answer: **Yes**

There are remaining known engineering reasons. Final Owner Residency Certification with **no remaining known validation gaps is not issued**.

Phase 7.2 remains valid for non-credential house use. This phase closes the credential validation gap with live evidence and surfaces product defects that block natural owner credential workflows in Living Workspace.

---

## Remaining known engineering issues

### E1 — `ariaPrompt` / `ariaConfirm` invisible and trapping in Living Workspace (blocker)

- `#ariaPromptDialog` and `#ariaConfirmDialog` live under `#ariaLegacyShell` / `#mainContent`.
- In Living Workspace, `#ariaLegacyShell` is `display: none` (0×0).
- `showModal()` still marks the dialog `:modal`, but geometry is **0×0** (`ownerCanSee: false`).
- Accessibility snapshot collapses to **`(no interactive elements)`** while the invisible modal is open — owner cannot see, type, Cancel, or Escape productively.
- **Blocks natural completion of:** Journal encrypted export/import passwords, Health backup restore password, and any other Living Workspace flow that uses `ariaPrompt` / `ariaConfirm`.

Evidence: `restore_prompt_geometry.json`, `dialog_hosts.json`, `health_restore_prompt_owner_view.png`, Journal import attempts.

### E2 — “Lock now” lockout when PIN lock is not configured (blocker for Security)

- Security panel correctly shows: `PIN lock off (set JARVIS_PIN_LOCK=1)`.
- Live API: `pin_lock_enabled=false`, `pin_configured=false`, `lock_capable=false`.
- Clicking **Lock now** still calls `jarvisShowLock()`, which clears session and shows the body-level lock screen.
- Owner is then prompted for a PIN that does not exist; Unlock cannot succeed.
- Full page reopen did not clear the overlay in residency; recovery required applying the same rule `checkLock()` uses (`!pin_lock_enabled || !pin_configured` → hide).
- `POST /api/security/lock` returned `ok: true, locked: true` even though lock is not capable.

Evidence: `security_panel.json`, `after_lock_now.png`, `after_lock_now.json`, `lock_after_reload.json`.

### E3 — Home Automation room does not surface Home Assistant credential/control UI

- Front Door **Home Automation** resolves to `viewId: "presence"` (camera / gestures / face enroll).
- Room chrome title is **Presence**; no HA token, test, entities, or scenes in the Living Workspace surface.
- HA is configured and connected at the product/API layer (`token_set`, `connected`), but the owner cannot complete HA credential verify → real device task → leave/return from the Home Automation room under residency law.

Evidence: `ha_room.json`, `ha_home.png`, routing in `priority3_rooms.js` (`home_automation` → `presence`).

### E4 — Living Chat did not complete an authenticated GitHub (`gh`) task in this residency

- Host `gh auth status` is valid (`nhflyguy1970-oss`, scopes include `repo`).
- Coding → LSP & Git shows remote-aware summary (`main...origin/main`).
- Owner chat request to run `gh api user` remained stuck busy with the prompt still in the composer (screenshot `gh_auth_task2.png`); Stop was required. No authenticated login string returned in the Living Chat transcript.

This is an incomplete credential workflow for Git-from-Aria, not proof that host `gh` is broken.

---

## Scenario evidence (what completed / what did not)

| Scenario | Auth | Work completed | Persist / leave-return | Restart | Cancel / retry | Owner-visible UI | Integrity |
|----------|------|----------------|------------------------|---------|----------------|------------------|-----------|
| **Morning · Journal enc export** | Password entered only via DOM on **invisible** `ariaPrompt` | Encrypted file written (`format/salt/ciphertext`, 113013 bytes, no plaintext marker) | Left to Chat, returned to Journal | N/A | Cancel OK; short password rejected with toast | **Fail (E1)** — owner cannot see prompt | 100 later |
| **Morning · Journal enc import** | Blocked for natural owner entry (E1) | Not completed under residency law | — | — | Wrong-password path inconclusive under invisible modal | **Fail (E1)** | — |
| **Health · enc backup create** | Inline password form (visible) | Backup row created (`ok`, Verify/Restore) | Leave Chat → return Backups: row persisted | N/A | Empty Create blocked by `required` | **Pass** | — |
| **Health · restore** | `ariaPrompt` opened (“Restore backup”) | **Not completable by owner** — 0×0 modal + a11y trap | — | — | Cancel only via DOM recovery | **Fail (E1)** | — |
| **Health · PIN step-up** | N/A in daily driver | Step-up off unless `JARVIS_PIN_LOCK` / explicit health step-up | — | — | — | N/A (not in daily config) | — |
| **Security · PIN / lock** | PIN lock **off** in serve env | Panel readable; Lock now caused **lockout (E2)** | Reload did not clear lock overlay | Not verified (lockout) | Unlock impossible without PIN | Lock screen visible; setup path mis-gated | — |
| **Trusted devices** | Depends on working PIN unlock | Empty state only | — | — | — | Incomplete | — |
| **Providers · Gemini / OpenAI / HF** | Keys already set | Gemini: “Gemini API authenticated”; OpenAI: “OpenAI API authenticated”; HF: presence check; Test configured: “Tests complete” | Leave → return: still CONFIGURED | Not restarted this phase | Clear not exercised | **Pass** (inline Integrations UI) | — |
| **Cloud Live** | Gemini key | Security panel: `Cloud live: ready (gemini_live)` | — | — | — | Partial (status only; no live session exercise) | — |
| **LAN API key (C12)** | Key entered in body-level modal on `10.0.0.235` | Modal dismissed; opened Integrity on LAN — Score 100 | Modal stayed dismissed after room change | N/A | Cancel then re-auth | **Pass** | 100 |
| **Home Assistant** | Token already set (API) | Living Home Automation room ≠ HA UI (E3) | — | — | — | **Fail (E3)** for room workflow | — |
| **Git (`gh`)** | Host auth OK | Coding Git summary OK; Living Chat authenticated op **not** completed (E4) | — | — | Stop after busy stall | Incomplete | — |
| **Browser site login** | — | Browser room live (Playwright running); history = Example Domain only | — | — | — | **Not run** — no owner site credentials supplied | — |
| **Uncensored password** | — | Body-level modal exists (not in legacy shell) | — | — | — | **Not run** — would leave a new owner password in vault | — |

Integrity at end of credential residency probes: **Score 100 · ready** (`integrity.json`, LAN `lan_work.json`).

---

## Daily-driver credential inventory (what Jeff actually has configured)

Observed live (flags/previews only; secrets not copied into this doc):

- Gemini, OpenAI, Hugging Face, Ollama, LiteLLM — configured  
- Home Assistant — configured + connected (API)  
- Aria Host API key — required; LAN gate active off-localhost  
- `gh` — logged in on host  
- PIN lock — **not** enabled in serve environment  
- Anthropic / OpenRouter / Meshy / SearXNG — not set (not claimed as daily credentials)

---

## What this is not

- Not a claim that encrypted journal/health crypto is broken on the server (export ciphertext and health backup create succeeded when UI could submit).
- Not a recommendation to “force” `JARVIS_PIN_LOCK=1` for certification theater.
- Not feature work — defects are recorded for a follow-on repair → re-verify cycle under residency law.

---

## Certification status

| Gate | Status |
|------|--------|
| Phase 7.2 Owner Residency (non-credential house) | Still stands |
| Phase 7.3 credential audit (gap identified) | Superseded by 7.3.1 living evidence |
| Phase 7.3.1 Credential Owner Residency — **no remaining known validation gaps** | **Not issued** (E1–E4 recorded) |
| Phase 7.3.2 Final Residency Defect Repair | See `docs/ARIA_PHASE7_3_2_FINAL_RESIDENCY.md` — E1–E4 repaired and re-verified; Final Owner Residency issued |

**Signed answer (7.3.1 only):** **Yes** — at discovery time, Jeff could not yet treat Aria as a permanent daily workspace for every credential-protected capability, because of **E1–E4** above. Those defects were repaired and certified under Phase 7.3.2.
