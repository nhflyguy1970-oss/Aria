# Problem Report — M1 ACM v0.25.0 Promotion

**Milestone:** M1  
**Status:** Resolved (package promotion)  
**Date:** 2026-07-19

## Summary

Controlled promotion of certified standalone ACM **v0.25.0** (episodic
autobiographical memory) into Aria `aria_acm/`. Episodic teaching and temporal
reconstruction ship **only** as the unchanged ACM package. No Aria host
episodic cognition and no integration-layer changes in this promotion.

## Source pin

| Field | Value |
|-------|-------|
| Tag | `v0.25.0` |
| Commit | `d71a6af77dab578fd85ace14e241a72df3ce59a1` |
| Local copy | `aria-acm-v0.25.0-1` |
| Certification | ACM `docs/EPISODIC_MEMORY_CERTIFICATION.md` |

## Explicitly not implemented in Aria

- Aria NLU / runtime routing special-cases for episodic statements or queries
- New Cap Bus / Core memory bridges for episodic cognition
- Any redesign of Memory Authority or Teaching Recognition

Live conversational validation of episodic cues through Aria NLU may require a
follow-on integration milestone; cognitive authority remains the promoted ACM.

## Gates

- `tests/test_aria_acm_m1_episodic.py` — vendored ACM episodic certification via bridge
- Prior M0L / M0K / Shadow M1 gates remain green
