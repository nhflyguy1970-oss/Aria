# Testing Checklist

## Automated (run before every push)

```bash
cd /media/jeff/AI/jarvis && ./scripts/ci-local.sh
cd /media/jeff/AI/AI-Platform && ./scripts/ci-local.sh
```

Target: **all tests pass**, ruff clean.

## Workstation acceptance

```bash
cd /media/jeff/AI/jarvis
./workstation acceptance
```

| Metric | Target |
|--------|--------|
| Daily-required | 100% |
| Integration | 100% |
| Production readiness | ≥ 99% |
| Overall passed | YES |

## End-to-end validation

```bash
cd /media/jeff/AI/jarvis
./scripts/e2e-validate-workstation.sh
```

Covers: clean stop → start → infra → Aria API → real chat → acceptance → clean stop.

## Failure injection

```bash
cd /media/jeff/AI/jarvis
./scripts/failure-inject-workstation.sh
```

Injects: Redis, PostgreSQL, LiteLLM, Qdrant, Ollama, Aria stop, cache corruption, full recovery, platform rollback.

Optional network block: `FAILURE_INJECT_NETWORK=1 ./scripts/failure-inject-workstation.sh`

## Platform cutover (server must be running)

```bash
curl -X POST http://127.0.0.1:8765/api/platform/cutover/verify
```

Expect: `"ready": true`, `"mode": "dual_write"`.

## Live integration probes

Included in acceptance. Individual probes live in `jarvis/application/standalone/workstation_impl/integration_probes.py`.

Timeout: `JARVIS_PROBE_TIMEOUT` (default 60s).

## Manual power-user smoke (Phase 2)

- [ ] Chat in Aria GUI
- [ ] Knowledge / memory recall in chat
- [ ] Git status via tool or OpenCode
- [ ] Whisper / Piper from GUI (if used)
- [ ] `./workstation backup` creates archive
- [ ] Double-click desktop icon → greeting

## Skipped tests policy

Only skip tests that are genuinely obsolete or require hardware Jeff does not have. Never skip production-critical paths: memory, acceptance, repair, cutover, probes.
