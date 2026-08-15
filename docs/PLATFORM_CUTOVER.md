# Platform Mirror Diagnostics

ACM is the permanent authoritative cognitive memory store. The platform cutover
module no longer switches memory authority; it only reports platform mirror and
backfill diagnostics for non-authoritative infrastructure.

## Mode

`status()["mode"]` is always `acm_authoritative` for cognitive memory.
Legacy memory files are forensic vaults only. Platform mirror checks may still
run, but they do not change reads or writes.

## Diagnostic Checklist

1. ACM primary is active (`ARIA_ACM_PRIMARY=1`, no rollback).
2. `status()["authoritative"] == "acm"`.
3. `verify_readiness()` may be used to inspect platform mirror health.
4. `backfill_memory(dry_run=True)` may be used for inventory diagnostics only.
5. Legacy data is never promoted back to cognitive authority.

## Commands

```bash
# Check status
python -m jarvis.workstation  # or GUI /api/platform/cutover

# Dry-run platform mirror inventory
python -c "from jarvis.platform_cutover import backfill_memory; print(backfill_memory(dry_run=True))"

# Compatibility endpoint: reports ACM authority
python -c "from jarvis.platform_cutover import enable_platform_authoritative; print(enable_platform_authoritative())"

# Compatibility endpoint: ACM remains authority
python -c "from jarvis.platform_cutover import rollback_to_legacy; print(rollback_to_legacy())"
```

## Startup hydration

On daemon, tray, and `main.py` startup, `apply_cutover_state_on_startup()` reads
`data/platform/cutover.json` for compatibility, but does not set platform
authority environment variables. Cognitive memory authority is owned by ACM.

## Rollback drill

1. Note current mode: `status()["mode"]`
2. Run `rollback_to_legacy()`
3. Confirm `current_mode()` is still `acm_authoritative`
4. Confirm Memory Home reports `source_of_truth: acm`
5. Restart Aria and verify chat/memory still work

## Environment

| Variable | Purpose |
|----------|---------|
| `JARVIS_LEGACY_DATA_DIR` | Legacy jarvis data root |
| `JARVIS_PLATFORM_DATA_DIR` | Platform application data root |
| `JARVIS_DISABLE_PLATFORM_ATTACHMENT` | Disables platform diagnostics |
