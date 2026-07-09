# Platform Data Cutover

Safe switch from legacy Jarvis data paths to AI-Platform authoritative storage.

## Modes

| Mode | Reads | Writes |
|------|-------|--------|
| `dual_write` (default) | Legacy | Legacy + platform mirror |
| `platform_authoritative` | Platform | Legacy + platform mirror |

Legacy data is **never deleted**. Rollback restores legacy reads immediately.

## Pre-cutover checklist

1. Platform infrastructure attached (`JARVIS_PLATFORM_ATTACHED=1`)
2. Memory, semantic memory, and knowledge retrieval adapters attached
3. `verify_readiness()` reports `ready: true` with zero blockers
4. Memory backfill completed (`backfill_memory` or enable with `force_backfill`)
5. Memory parity matches (`legacy_count == mirrored`)
6. Namespace bridging complete for required namespaces
7. Zero verification failures across memory, semantic, and knowledge metrics

## Commands

```bash
# Check status
python -m jarvis.workstation  # or GUI /api/platform/cutover

# Dry-run backfill
python -c "from jarvis.platform_cutover import backfill_memory; print(backfill_memory(dry_run=True))"

# Enable (blocked until verification passes)
python -c "from jarvis.platform_cutover import enable_platform_authoritative; print(enable_platform_authoritative())"

# Rollback
python -c "from jarvis.platform_cutover import rollback_to_legacy; print(rollback_to_legacy())"
```

## Startup hydration

On daemon, tray, and `main.py` startup, `apply_cutover_state_on_startup()` reads
`data/platform/cutover.json`. When mode is `platform_authoritative`, it sets
`JARVIS_PLATFORM_DATA_AUTHORITATIVE=1` before platform attachment so path
resolution uses platform storage.

## Rollback drill

1. Note current mode: `status()["mode"]`
2. Run `rollback_to_legacy()`
3. Confirm `current_mode()` is `dual_write`
4. Confirm `JARVIS_DATA_DIR` points at legacy path
5. Restart Aria and verify chat/memory still work
6. Re-enable only after `verify_readiness()` is green

## Environment

| Variable | Purpose |
|----------|---------|
| `JARVIS_PLATFORM_DATA_AUTHORITATIVE` | Force authoritative mode |
| `JARVIS_LEGACY_DATA_DIR` | Legacy jarvis data root |
| `JARVIS_PLATFORM_DATA_DIR` | Platform application data root |
| `JARVIS_DISABLE_PLATFORM_ATTACHMENT` | Kill switch — blocks cutover |
