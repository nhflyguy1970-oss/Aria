# Release Readiness

**Status:** RELEASE CANDIDATE 1 (RC1)  
**Date:** 2026-07-10  
**Production Readiness Score:** **99.2%** (last acceptance)

## Executive summary

The AI Workstation is ready for Jeff to use as a daily local-first AI environment. RC1 adds measured benchmarks, release checklist, packaging recommendation, standalone Mission Control observability tabs (Routing, Timeline, Intent Analytics), and synchronized user documentation. Core path — power on, Aria chat, NLU routing, Mission Control observability, memory, knowledge, repair, acceptance — is complete and tested.

## RC1 deliverables

| Artifact | Location |
|----------|----------|
| Release checklist | AI-Platform `docs/RELEASE_RC1_CHECKLIST.md` |
| User guide | AI-Platform `docs/USER_GUIDE.md` |
| Benchmark harness | AI-Platform `scripts/benchmark_rc1.py` |
| Endurance sampler | AI-Platform `scripts/endurance_rc1.py` |
| Packaging recommendation | AI-Platform `docs/PACKAGING_RECOMMENDATION.md` |

## Scores (latest acceptance)

| Metric | Score |
|--------|-------|
| Daily-required | 100% |
| Integration | 100% |
| Production readiness | 99.2% |
| Overall passed | YES |

## What is ready

- Desktop start: `./workstation start` / AI Workstation icon
- Aria standalone + platform attach
- NLU routing v1.0 with confidence bands and classifier placement
- Mission Control: Routing Inspector, Event Timeline, Intent Analytics
- Reference Engine (documentation lookup)
- Cutover verify: `ready: true` in `dual_write` mode
- Repair, backup/restore, acceptance, report
- CI: Aria ~239 tests, Platform ~738 tests — green on `main`

## What is intentionally deferred

| Item | Recommendation |
|------|----------------|
| Platform-authoritative mode | Stay in compatibility mode until 2+ weeks RC1 dogfooding |
| Debian/AppImage packaging | See packaging recommendation — installer script for RC1 |
| 8h/24h/48h endurance sign-off | Run `scripts/endurance_rc1.py`; mark checklist when complete |
| Optional apps (Continue, OpenHands, etc.) | Not installed; no action needed |

## Failure injection (2026-07-09)

21/25 checks passed on first full run. Failures addressed in prior release. Re-run: `./scripts/failure-inject-workstation.sh`

## Hardware

- NVIDIA RTX 3060 12GB
- 62GB RAM
- Ollama: 40 models installed
- ComfyUI: GPU mode available

## Recommendation

**Use RC1 daily.** Run `./workstation acceptance` weekly, archive `benchmark_rc1.py` output before tagging, and `./workstation backup` before major updates.

Do **not** enable platform-authoritative mode until RC1 checklist is signed off.
