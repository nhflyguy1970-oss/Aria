# Aria ACM Import Plan — Vendored Copy

**Status:** M0 IMPLEMENTED — design decisions remain **locked**  
**Policy:** ACM SUPREMACY RULES · Independent copy (not shared library)  
**Baseline pin:** ACM `v0.16.0` · commit `6f6d0f89d0af35b018c2a781a38748d21e303ae0` · harvested `source_version` `0.16.0`  
**Local copy:** `aria-acm-v0.16.0-1` · see `aria_acm/VERSION.json`

---

## Goal

Import a **complete certified ACM source tree** into Aria so runtime cognition never depends on `/media/jeff/AI/ACM` or PyPI auto-updates.

---

## Locked layout

```text
jarvis/
  aria_acm/                         # Aria Cognitive Memory (vendored ACM)
    __init__.py                     # re-exports / package marker
    VERSION.json                    # source tag, commit, copy date, sha256
    LICENSE                         # Apache-2.0 (preserved from ACM)
    NOTICE                          # attribution (see below)
    acm/                            # literal package copy from ACM repo `acm/`
      (all organs — see include list)
  aria_core/
    acm_bridge.py                   # NEW later: thin façades only (not part of import)
```

**Rejected alternatives:** `jarvis/vendor/acm/`, `aria/acm/`, installing `aria-cognitive-memory` from PyPI for cognition.

### Python namespace (locked)

```python
from aria_acm.acm.api.engine import CognitiveEngine
from aria_acm.acm import …  # optional convenience
```

Packaging: add `aria_acm` to Aria package discovery (`setuptools`/`hatch` packages).  
Ensure `sys.path` / editable install resolves **vendored** `aria_acm` first.  
CI gate: importlib finds module file under `jarvis/aria_acm/` — fail if site-packages ACM wins.

---

## Exact copy — INCLUDE

From pinned ACM commit, copy these paths into `jarvis/aria_acm/`:

### Required (runtime cognition)

| Source (ACM repo) | Destination |
|-------------------|-------------|
| `acm/` (entire package, all `.py`) | `aria_acm/acm/` |
| `LICENSE` | `aria_acm/LICENSE` |
| `acm/_version.py` | preserved inside package |

**`acm/` tree includes (~83 Python modules), all copied:**

`activation/`, `adapters/` (in-package protocol only), `analogy/`, `api/`, `associations/`, `attention/`, `certification/` (harness helpers used by ValidationHarness), `concepts/`, `confidence/`, `context/`, `core/`, `experiences/`, `forgetting/`, `goals/`, `identity/`, `learning/`, `multimodal/`, `observability/`, `persistence/`, `plugins/`, `prediction/`, `provenance/`, `recombination/`, `reconciliation/`, `reconsolidation/`, `reflection/`, `remembering/`, `simulation/`, `sleep/`, `types/`, `validation/`, `working/`, plus package `__init__.py` and `_version.py`.

### Required provenance files (Aria-authored at copy time)

| File | Content |
|------|---------|
| `aria_acm/VERSION.json` | see schema below |
| `aria_acm/NOTICE` | attribution block |
| `aria_acm/__init__.py` | package marker; may document import path |

### Optional (Phase M0 test harness inside Aria)

| Source | Destination | When |
|--------|-------------|------|
| Selected ACM `tests/` subsets | `tests/aria_acm/` or `aria_acm/upstream_tests/` | After M0 packaging green |
| ACM `docs/API.md` excerpt | `aria_acm/docs/` | Operator reference |

---

## Exact copy — EXCLUDE

| Path | Why |
|------|-----|
| `aria_memory_adapter/` (repo root) | Reference only; Aria builds `aria_core/acm_bridge.py` |
| `.git/` | Independence |
| ACM `.github/` / CI workflows | Aria owns CI |
| `benchmarks/` | Promote later if needed |
| `examples/` | Reference in standalone ACM |
| ACM root `docs/` wholesale | Keep pointer; avoid doc drift as authority |
| `scripts/` release-only | Unless Aria CI needs a certify script (promote later) |
| `__pycache__/`, `.venv/`, build artifacts | Never |
| Standalone ACM `pyproject.toml` as installable dependency | Do **not** add pip dep; harvest version fields into `VERSION.json` only |

---

## VERSION.json schema

```json
{
  "aria_acm_local_version": "aria-acm-v0.14.0-1",
  "source_project": "aria-cognitive-memory",
  "source_version": "0.14.1",
  "source_tag": "v0.14.0",
  "source_commit": "454dcb90a352a3f1daa44aa95ff7b2801994f4e3",
  "source_repo": "/media/jeff/AI/ACM",
  "copy_date": "YYYY-MM-DD",
  "tree_sha256": "<sha256 of sorted file contents under aria_acm/acm/>",
  "license": "Apache-2.0",
  "certification_ref": "ACM docs/ACM_CERTIFIED_v1.md"
}
```

Environment mirror (optional ops): `ARIA_ACM_SOURCE_TAG`, `ARIA_ACM_SOURCE_COMMIT`, `ARIA_ACM_COPY_DATE`.

---

## Build / packaging integration

1. Discover package `aria_acm` in Aria `pyproject.toml` / setuptools `packages`.  
2. **Do not** list `aria-cognitive-memory` as a cognition dependency.  
3. CI job `test_aria_acm_import_authority`: assert `CognitiveEngine.__module__` file path contains `aria_acm`.  
4. Optional: vendored unit smoke (`CognitiveEngine()` construct + encode/remember round-trip in tmp store).

---

## Configuration (runtime — design)

| Setting | Meaning | Default by phase |
|---------|---------|------------------|
| `ARIA_ACM_PERSIST_PATH` | Durable CognitiveStore path under `JARVIS_DATA_DIR` | `acm/cognitive.db` |
| `ARIA_ACM_AUTO_PERSIST` | Flush policy | on |
| `ARIA_ACM_SHADOW` | M1–M2 parallel measure | off until M1 |
| `ARIA_ACM_PRIMARY` | M3+ ACM authoritative | false until M3 |
| `ARIA_ACM_ROLLBACK` | Force legacy façade | false; **pre-M4 only** |

Legacy `JARVIS_MEMORY_BACKEND` / memory DB paths remain until M4 retirement.  
Flags must never encode permanent dual cognitive authority (Rule 1).

---

## Copyright / attribution

Preserve Apache-2.0 headers on all copied source files. Root `NOTICE`:

> Aria Cognitive Memory (`jarvis/aria_acm`) is an independent copy of ACM (Aria Cognitive Memory engine), derived from the certified standalone ACM repository (Apache-2.0). Modifications inside Aria do not update the standalone project unless explicitly contributed upstream. Automatic synchronization is forbidden. Standalone ACM remains the research and reference implementation.

---

## Promotion workflow (post-import)

1. Improve cognition in **standalone ACM**.  
2. Certify (ACM certification suite).  
3. Explicit Aria PR: replace/patch files under `aria_acm/acm/` from tagged source; update `VERSION.json`.  
4. Re-run Aria integration gates ([`INTEGRATION_TEST_PLAN.md`](INTEGRATION_TEST_PLAN.md)).  

Never `pip install -U aria-cognitive-memory` as the cognition update path.

---

## Copy procedure (operator — design only)

1. Verify ACM checkout at pinned commit; run ACM certification smoke.  
2. `rsync -a --delete` (or equivalent) `ACM/acm/` → `jarvis/aria_acm/acm/`.  
3. Copy `LICENSE`; write `NOTICE` + `VERSION.json` with tree hash.  
4. Verify no `aria_memory_adapter` under `aria_acm/`.  
5. Run packaging discovery + import-authority CI check.  

No Aria memory cutover in this step (Phase M0 only).
