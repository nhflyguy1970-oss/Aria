# ARIA — Exhaustive Functional Verification

**Campaign status: WAITING FOR JEFF — STOPPED**  
**Journal encrypted import:** NOT PROVEN  
**Production incident:** Journal wipe via misconfigured isol (`DATA_DIR` ≠ `JARVIS_DATA_DIR`) — **restored from backup** — Jeff must ACK  
**Do not issue certification. Do not begin Owner Residency.**

Evidence: `docs/evidence/exhaustive_functional_verification/`  
Incident: `PRODUCTION_JOURNAL_WIPE_INCIDENT.json`  
Format defect: `journal_enc_format_defect.json`

---

## 1. What Phase 3C-D actually proved

| Claim area | Evidence-backed verdict |
| --- | --- |
| 34 Rooms exist in live registry | **ACTUALLY PROVEN** (`house_proof.json` registry total 34, unique 34) |
| Front Door → Room identity (`dataset.room`) | **ACTUALLY PROVEN** for all 34 (cold+warm enter) |
| Room “usable” heuristic (buttons/text present) | **SURFACE ONLY** — not end-to-end capability proof |
| Warm API regression targets | **PARTIALLY PROVEN** (planner/projects/repair/connections/audit/docs keyword/mission warm) |
| Search → Fly / Documents (after repairs) | **PARTIALLY PROVEN** (later retests; not full Search product matrix) |
| Chat Tools | **SURFACE ONLY** — input/send/stop + registry count; **no Tool execution** |
| Cross-Room product links (15) | **PARTIALLY PROVEN** — navigation destination only |
| Rapid nav / soak stability | **PARTIALLY PROVEN** — enter/leave identity; little real interaction |
| `REPAIRED — AWAITING FINAL CERTIFICATION` for all 34 as *complete functional* proof | **NOT PROVEN** — label was integration/surface status, not exhaustive control/workflow proof |
| Persistence / restart / forms / mutations in 3C-D | **NOT PROVEN** for most Rooms in 3C-D evidence |
| Credential workflows | **JEFF-ATTENDED / NOT PROVEN** (explicitly deferred) |

---

## 2. What 3C-D did NOT prove

- Every meaningful control driven
- Every owner workflow end-to-end (input → execute → visible result → state → persist)
- Forms submitted with verified persistence
- Restart verification
- Hardware workflows
- Credential workflows
- Chat Tool execution matrix
- Exhaustive per-Room capability certification

---

## 3. Why the previous ~five-minute run was insufficient

| Metric | Actual (evidence) |
| --- | --- |
| House proof wall-clock | **~91 seconds** (`run_house_proof.py` terminal elapsed_ms 91249) |
| Retest wall-clock | **~30 seconds** |
| What it did per Room | `goRoom` → measure `identity_ms` / `usable_ms` (often **7–30 ms**) |
| Soak elapsed for ~35 enters | **~804 ms** total (~23 ms/Room) — identity only |
| Rapid nav | 34 Rooms with **~80 ms** sleeps — no workflow exercise |
| Controls clicked (documented) | **NOT PROVEN** — no per-control exercise log |
| Forms submitted | **NOT PROVEN** in house proof |
| State mutations | **NOT PROVEN** in 3C-D soak |
| Persistence checks | **NOT PROVEN** for most Rooms |

A Room can “enter” in 10 ms and still have broken primary workflows. Route/identity speed ≠ functional verification.

**Conclusion:** Treating that run as exhaustive functional testing of 34 Rooms is **not credible**.

---

## 4. This campaign’s progress (before credential stop)

### Enumeration
All **34 Rooms** control inventories captured (`control_inventory.json` / `campaign_state.json`).

Honest caveat: some native Rooms (health/mission/home/providers/audio) still show inflated control counts — root scoping imperfect; those counts are **not** trusted as exact until re-scoped. Furnished Rooms (documents/planner/search/journal/etc.) look plausible.

### Partial exercise (pre-gate)
Ungated/partial control clicks occurred for multiple Rooms (chat, flytying, documents, planner, gallery, search, memory, maker, settings, …). Status for those: **PARTIALLY PROVEN** only — UI clicks observed, **not** full create/save/persist workflows.

### Mutations
No production Journal/Planner/Health/etc. test writes in this stop package. Isol server prepared on `:8768` for later disposable mutations after resume.

---


## 5. Journal More-menu defect — REPAIRED

(See prior evidence `journal_more_menu_repair.json`.)

---

## 6. Journal encrypted export — JEFF-ATTENDED — PROVEN

Prior gate closed with Jeff attestation + live POST 200 OK.

---

## 7. Encrypted import format investigation — RESULTS

**ROOM:** Journal  
**CAPABILITY:** Encrypted Import  
**SYMPTOM:** Owner file rejected as "Not a Jarvis encrypted journal file."  
**OWNER FILE:** `/home/jeff/Downloads/jarvis-journal-encrypted-2026-08-08.json`  
**STATUS:** **BLOCKED — FORMAT/IMPORT DEFECT** (investigated; contract not diverged)

### What export produces

| Field | Value |
| --- | --- |
| format | `jarvis-journal-v1` |
| salt | hex string (16 bytes) |
| ciphertext | base64 Fernet token |
| KDF | PBKDF2-HMAC-SHA256, 200000 iterations, dklen 32 |
| filename | `jarvis-journal-encrypted-YYYY-MM-DD.json` |
| location | Browser download (Blob), not server disk |

Code: `encrypt_export` ← `POST /api/journal/export/encrypted` ← Journal More → Export encrypted

### What import expects

Same envelope. UI sends `{export, password, merge}`. Validator error **"Not a Jarvis encrypted journal file"** is raised when the decrypt-root object lacks `format==jarvis-journal-v1` (after normalize).

### Exact mismatch

| | |
| --- | --- |
| EXPORT PRODUCES | `{format, salt, ciphertext}` with format `jarvis-journal-v1` |
| IMPORT EXPECTS | same |
| OWNER FILE ON DISK | **matches** (proven) |
| OWNER UI WITH THAT FILE | posts correct body; response is **Wrong password or corrupt file** (format accepted) |
| FORMAT ERROR | decrypt-root is **not** the envelope (e.g. unencrypted `jarvis-journal-*.json` in Downloads) |

**Critical answer:** **F** — not A/C/E for the Aug 8 encrypted files. Formats have not diverged; Aug 8 remains importable. The format error means the server did not receive a `jarvis-journal-v1` envelope at decrypt-root.

### Repairs applied

1. `normalize_encrypted_envelope` — unwrap accidental `{ok, export}`; plain-journal honest error  
2. Export UI validates envelope before download; password field type  
3. Import UI: Replace-all second confirm + `confirm_wipe`  
4. Unit tests + **safe** isol round-trip (`JARVIS_DATA_DIR=/tmp/aria-exhaustive-isol-v2`)

Aug 8 owner exports: **compatible** (wrong password ≠ format error).

---

## 8. PRODUCTION INCIDENT — Journal wipe during isol misconfig

**Cause:** Isol was started with `DATA_DIR=/tmp/...` but `jarvis.config` reads **`JARVIS_DATA_DIR`**. Isol round-trip (including `confirm_wipe` cleanup) wrote to **live** `data/journal/`.

**Action taken:** Quarantined wiped file; restored from `bullet_journal.backup-20260812T171036Z.json` (92 daily / 6 weekly / 5 habits). Undo history sidecar was emptied by the wipe and could not be fully recovered.

**Integrity after restore:** clean / 100

**Jeff must acknowledge** Journal content before import is retried.

Evidence: `PRODUCTION_JOURNAL_WIPE_INCIDENT.json`

---

## 9–11. STOP

Exhaustive verification is **STOPPED**.

Do **not** continue past Journal encrypted import.  
Do **not** mark import JEFF-ATTENDED / passed / skipped.

**WAITING FOR JEFF**

1. Confirm Journal looks correct after restore  
2. Then retry: Journal → More → Import encrypted → select `jarvis-journal-encrypted-*.json` → password in Aria  
3. Reply when import actually succeeds **and** Journal content was ACK'd

---

## Journal encryption design (read-only investigation)

Evidence: `docs/evidence/exhaustive_functional_verification/journal_encryption_design_readonly.json`

| Question | Answer |
| --- | --- |
| Persistent Journal encryption password configured? | **No** |
| Export encrypted password model | **Ephemeral per export** — prompt “Export password (min 4 characters)”; not loaded from settings; no confirm-password step; not stored |
| Import encrypted password model | Password used when **that specific file** was exported |
| Separate Journal encryption settings UI? | **No** (optional `JARVIS_JOURNAL_AT_REST_PASSWORD` env for on-disk `.enc` — **unset** here; no `.enc` file) |
| Aug 8 files structurally valid? | **Yes** — `format=jarvis-journal-v1`, salt, ciphertext |
| Can validate without decrypt? | **Yes** |
| “Not a Jarvis encrypted journal file” | **Format/envelope stage** (before password decrypt) — not proof of a wrong owner password |
| Complete import without knowing export-time password? | **No** for that file |

**STOP.** Do not ask Jeff to guess a password. Exhaustive verification remains stopped.

---

## Owner Security Vault architecture (pause)

Document: `docs/ARIA_OWNER_SECURITY_VAULT_ARCHITECTURE.md`  
Checkpoint: `docs/evidence/exhaustive_functional_verification/EXHAUSTIVE_CHECKPOINT.json`

Architecture is **documented only** — not implemented.  
Aug 8 encrypted exports remain valid and unrecovered.  
Do not ask Jeff to guess passwords.  
Resume exhaustive verification from the Journal encrypted import checkpoint after architecture review / Journal workflow resolution — **not** from Room 1.

