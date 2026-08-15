# ARIA — Current Runtime Baseline

**Captured:** 2026-08-11 (local)  
**Evidence root:** `/tmp/aria-current-baseline/`  
**NO application code changed during this baseline.**  
**NO git reset / checkout / clean / commit / push.**

---

## Runtime identity

| Field | Value |
|---|---|
| PID | `3255320` |
| Start | Tue Aug 11 18:42:13 2026 |
| Command | `./venv/bin/python -B -u main.py serve` |
| CWD | `/media/jeff/AI/jarvis` |
| Python | `/media/jeff/AI/jarvis/venv/bin/python` → `/usr/bin/python3.12` |
| Venv | `/media/jeff/AI/jarvis/venv` |
| Port | `8765` (sole listener) |
| Health | `ready=true`, `busy=false`, version `3.1.0` |

Previous stale process (for contrast): PID `2884670`, start `17:09:15` — terminated before this baseline.

---

## Git identity

| Field | Value |
|---|---|
| Branch | `main` |
| HEAD | `c325e5576aca62f71a800641ec1cb9652e6bb5cf` |
| Remote relationship | ahead 25 |
| Working tree | **dirty** |
| Changed paths (unique) | **614** |
| Approx churn vs HEAD | **+96,067 / −4,778** |

Snapshots:  
`/tmp/aria-current-baseline/HEAD.txt`, `BRANCH.txt`, `git_status_porcelain.txt`, `worktree/diff_numstat.txt`, `worktree/classification.json`

---

## Worktree classification (all 614 paths)

| Category | Files | ≈ Added | ≈ Removed | What it mostly is |
|---|---:|---:|---:|---|
| APPLICATION_SOURCE | 402 | 49,148 | 4,174 | Real `jarvis/` / `aria_*` Python + GUI static JS/CSS |
| DOCUMENTATION | 121 | 36,178 | 399 | Certification / inventory / architecture markdown (+ some JSON graphs under `docs/architecture/`) |
| TEST_SOURCE | 59 | 3,786 | 200 | `tests/` |
| UNRELATED | 8 | 3,245 | 0 | Cooling-tower CAD + `design/chat_room_v1` mockups |
| GENERATED_TEST_EVIDENCE | 13 | 2,479 | 0 | `docs/_*.json`, `docs/phase1_runtime_spikes/*.json` |
| BUILD_ARTIFACT | 1 | 871 | 0 | `scripts/electron-shell/package-lock.json` |
| UNKNOWN | 8 | 257 | 5 | Electron shell scripts/launchers under `scripts/` |
| CONFIGURATION | 2 | 103 | 0 | `.cursor/rules/*.mdc` |
| CACHE / TEMP / DATA / LOG | 0 | 0 | 0 | None in the dirty set |

**Totals reconcile:** 614 files, +96,067 / −4,778.

### Why the tree looks huge

The +96k lines are **not** primarily cache, databases, or accidental binary dumps.

Dominant contributors:

1. **Application source (~51% of added lines)** — large multi-phase product work already present as uncommitted/dirty modifications under `jarvis/` (Python + `gui/static` JS/CSS).
2. **Documentation (~38%)** — especially giant inventory/closure docs, e.g.:
   - `docs/ARIA_EXPLORATORY_DISCOVERY_INVENTORY.md` (+10,361)
   - `docs/ARIA_UI_CONTROL_INVENTORY.md` (+2,851)
   - `docs/ARIA_EXECUTION_CLOSURE_MATRIX.md` (+2,203)
3. **Tests (~4%)**
4. **Design / CAD unrelated (~3%)**
5. **Generated JSON evidence (~3%)** — phase/cert proof dumps under `docs/_…` and `docs/phase1_runtime_spikes/`

### Should normally be gitignored (but currently tracked/visible)

These 13 paths look like generated evidence and are **not** ignored by current `.gitignore` (`git check-ignore` → none):

- `docs/_first_token_audit_raw.json`
- `docs/_front_door_foyer_proof.json`
- `docs/_front_door_proof.json`
- `docs/_house_integrity_proof.json`
- `docs/_phase5_flagship_proof.json`
- `docs/_phase5_priority1_proof.json`
- `docs/phase1_runtime_spikes/cert_*.json`
- `docs/phase1_runtime_spikes/measure_*.json`
- `docs/phase1_runtime_spikes/*_latest.json`

**Do not delete them in this phase** — record only.

### Application-source breakdown

| Area | File count | ≈ Added | ≈ Removed |
|---|---:|---:|---:|
| Python (`.py`) | 271 | 30,898 | 3,268 |
| Frontend JS/TS | 109 | 13,265 | 659 |
| CSS | 12 | 4,435 | 7 |
| Templates/HTML | 1 | 487 | 234 |
| Orchestration-related | 6 | 2,919 | 360 |
| Research-related | 17 | 1,068 | 121 |
| Memory-related | 17 | 1,470 | 637 |
| Request lifecycle-related | 4 | 882 | 354 |

Representative application paths include: `jarvis/router.py`, `jarvis/orchestration_policy.py`, `jarvis/research_context.py`, `jarvis/nlu/mapping.py`, `jarvis/runtime_routing.py`, `jarvis/behaviors/memory/engine.py`, `jarvis/gui/static/*.js`, `jarvis/health_product/store.py`.

Full classified lists: `/tmp/aria-current-baseline/worktree/cat_*.txt`

---

## Relevant source hashes (disk at baseline)

See `/tmp/aria-current-baseline/runtime/file_hashes.txt` (sha256 + mtime + size) for:

- `jarvis/router.py`
- `jarvis/orchestration_policy.py`
- `jarvis/research_context.py`
- `jarvis/nlu/mapping.py`
- `jarvis/runtime_routing.py`
- `jarvis/research_verification.py`
- `jarvis/conversation_pipeline.py`
- `jarvis/assistant.py`
- `jarvis/behaviors/memory/engine.py`
- `jarvis/web_search.py`
- (and related)

Latest relevant mtimes on disk: **2026-08-11T18:32:06** (after old stale process; **before** PID 3255320 start 18:42:13).

---

## Loaded-module verification (live process)

Direct `sys.modules[…].__file__` introspection from PID 3255320 was **blocked** (`ptrace_scope` / no passwordless sudo gdb; `/proc/PID/mem` permission denied).

| Module | Disk path | Loaded path (live) | Match |
|---|---|---|---|
| `jarvis.router` | `/media/jeff/AI/jarvis/jarvis/router.py` | UNKNOWN (ptrace denied) | UNKNOWN\* |
| `jarvis.orchestration_policy` | `/media/jeff/AI/jarvis/jarvis/orchestration_policy.py` | UNKNOWN | UNKNOWN\* |
| `jarvis.research_context` | `/media/jeff/AI/jarvis/jarvis/research_context.py` | UNKNOWN | UNKNOWN\* |
| `jarvis.nlu.mapping` | `/media/jeff/AI/jarvis/jarvis/nlu/mapping.py` | UNKNOWN | UNKNOWN\* |
| `jarvis.runtime_routing` | `/media/jeff/AI/jarvis/jarvis/runtime_routing.py` | UNKNOWN | UNKNOWN\* |
| `jarvis.research_verification` | `/media/jeff/AI/jarvis/jarvis/research_verification.py` | UNKNOWN | UNKNOWN\* |
| `jarvis.conversation_pipeline` | `/media/jeff/AI/jarvis/jarvis/conversation_pipeline.py` | UNKNOWN | UNKNOWN\* |
| `jarvis.behaviors.memory.engine` | `/media/jeff/AI/jarvis/jarvis/behaviors/memory/engine.py` | UNKNOWN | UNKNOWN\* |
| `jarvis.web_search` | `/media/jeff/AI/jarvis/jarvis/web_search.py` | UNKNOWN | UNKNOWN\* |

\*Supporting evidence that the live server is serving this tree’s post-18:32 behavior (not the 17:09 stale process):

1. Process cwd/exe/cmdline point at `/media/jeff/AI/jarvis` + project venv.
2. Process start **18:42:13 >** latest relevant source mtime **18:32:06**.
3. Fresh same-tree imports resolve `__file__` exactly to those disk paths (`runtime/fresh_import_paths.txt` / JSON).
4. Live behavioral fingerprints from PID 3255320:
   - Ubuntu follow-up → `thinking=research_followup`, `action=web_search`
   - Correction → `thinking=research_correction`
   - Subject change → `thinking=subject_change`
   - Writing status-update note → `action=chat` (not `runtime_*`)

**RUNTIME MATCH (operational):** YES (cwd + start-after-mtime + unique post-repair route fingerprints).  
**RUNTIME MATCH (hard `sys.modules.__file__`):** UNKNOWN (OS ptrace restriction).

---

## Preservation note

This document and `/tmp/aria-current-baseline/**` are forensic records only. The 614-file dirty tree was **not** cleaned, discarded, or committed.
