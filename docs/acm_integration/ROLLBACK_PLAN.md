# Rollback Plan — Aria Memory Replacement

**Status:** DESIGN ONLY  
**Goal:** If cutover fails, Aria returns to its **original** memory system with no cognitive data loss.

---

## Preconditions (before any M3)

1. Full backup of legacy MemoryStore (file copy + checksum) → `vault/memory_pre_m3_<date>.*`.  
2. ACM durable snapshot export (`CognitiveEngine.export_snapshot` / `backup`).  
3. Feature flags documented; default still legacy-authoritative until M3.  
4. Rollback runbook rehearsed on staging (`RB-01`–`RB-04` in test plan).  
5. Ops announcement channel identified (operator chat / status note).

---

## Flag locations (design)

| Flag | Storage | Values |
|------|---------|--------|
| `ARIA_ACM_PRIMARY` | env / Aria config | `true`/`false` |
| `ARIA_ACM_SHADOW` | env / config | `true`/`false` |
| `ARIA_ACM_ROLLBACK` | env / config | `true` forces legacy façade **pre-M4** |
| `ARIA_ACM_PERSIST_PATH` | env / config | ACM durable path |
| `JARVIS_MEMORY_BACKEND` | existing | legacy backend until M4 |

Façade `authoritative_route()` precedence: `ROLLBACK` → legacy; else `PRIMARY` → acm; else legacy.

---

## Rollback triggers

- ACM primary recall quality regression: Shadow/UAT agree rate drop **> 10 points** vs last green **or** UAT preference pack **< 90%**.  
- Persistence corruption / failed `verify_persistence`.  
- Identity Policy Gate incidents.  
- Supremacy violation (duplicate cognition / legacy override in production path).  
- Operator decision.

---

## Steps (exact)

### R1 — Immediate traffic rollback (minutes)

1. Set `ARIA_ACM_PRIMARY=false`.  
2. Set `ARIA_ACM_ROLLBACK=true` (façades route Cap Bus / MemoryEngine to **legacy MemoryStore**).  
3. Set `ARIA_ACM_SHADOW=false` **or** keep Shadow read-only for forensics (no user-visible ACM answers).  
4. Verify Cap Bus `recall` returns legacy answers (spot pack).  
5. Announce temporary legacy mode (ops note).  
6. Confirm MC panel `authoritative=legacy`.

### R2 — Persistence isolation

1. Stop ACM auto-persist writers (`ARIA_ACM_AUTO_PERSIST=false` or process flag).  
2. Freeze ACM DB files (copy aside for forensics).  
3. Do **not** delete ACM data automatically.  
4. Do **not** re-enable DualWrite as a new SoT.

### R3 — Data integrity confirmation

1. Checksum-verify legacy backup vs live legacy path.  
2. Spot-check profile / recent facts / preferences.  
3. Confirm Mission Control memory panel using legacy health endpoints.  
4. Record incident: reason, flag states, checksums.

### R4 — Code rollback (if façades broken)

1. Deploy last known-good Aria revision where memory façade was legacy-only (or known-good flag wiring).  
2. Leave `aria_acm/` tree intact unless corruption.  
3. Re-open incident; **no silent reimplementation of ACM organs in Aria**.

### R5 — Resume path

Fix in standalone ACM or façades → promote into `aria_acm/` → re-enter M1 Shadow → re-qualify gates → M3.

---

## Guarantees

| Guarantee | Mechanism |
|-----------|-----------|
| No loss of pre-cutover autobiography | Legacy backup immutable |
| No orphan “half SoT” as authority | Flags force single authority |
| No supremacy regression “fix” | Forbidden to leave dual primary |

---

## After M4 (legacy retired)

Rollback becomes **ACM snapshot restore**:

1. `CognitiveEngine.restore` / `import_snapshot` from known-good backup.  
2. Verify persistence + golden recall pack.  
3. Optional cold legacy vault remains **read-only forensic** — not Cap Bus authority.

Reintroducing legacy as cognitive primary after M4 requires **explicit approval + re-certification** (Supremacy Rule 6) — DECISION_LOG entry mandatory.

---

## Forbidden rollback “fixes”

- Leaving `ARIA_ACM_PRIMARY` false permanently while continuing to evolve Aria CRUD memory (dual cognition).  
- Rebuilding Remembering / Identity / Concepts organs in Aria “temporarily.”  
- Using rollback to bypass ACM and then shipping that path as the product.

Those outcomes force architectural incident under Supremacy Rules 1, 3, 4, 6.
