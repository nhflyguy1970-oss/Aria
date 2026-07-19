# M0L Certification — Memory Explanation & Personal Summary

**Status:** CERTIFIED · FROZEN  
**Date:** 2026-07-19  
**Milestone:** M0L

---

## Certification record

| Check | Status | Pin |
|-------|--------|-----|
| Standalone ACM | **PASS** | `v0.24.0` · commit `3c3bdbc0b1e7566da7922df422c72578e5550df5` |
| Promotion verification | **PASS** | Aria vendored `aria-acm-v0.24.0-1` matches certified ACM (bootstrap `__init__.py` only) |
| Bridge verification | **PASS** | `acm_bridge.primary_cognitive_speak` returns certified ACM speech |
| Live Aria validation | **PASS** | Conversational path: teaching → explanation → evidence → about-me |
| Regression suite | **PASS** | ACM M0L gates · Aria `tests/test_aria_acm_m0l.py` · evidence routing · CI |

### Commits

| Role | Commit |
|------|--------|
| Standalone ACM | `3c3bdbc0b1e7566da7922df422c72578e5550df5` |
| Aria M0L promotion | `adc722f8afaeb3e25ff9d425d9c46e13aa83f771` |
| Aria evidence routing (integration) | `7343faaf6dde8381e24f7e7ecb0f4c325f29a38e` |
| Aria M0L certification record (this freeze) | tag `m0l-certified` |

### Tags

| Repo | Tag |
|------|-----|
| Standalone ACM | `v0.24.0` |
| Aria | `m0l-certified` |

---

## Certified capabilities

- Teaching Recognition (declarative encode through Memory Authority)
- Multi-domain memory (favorite color / food / fish isolated)
- Memory updates with retirement of prior values
- Lineage preserved across updates
- Evidence reconstruction (`Show me the evidence.` → active/retired versions)
- Explanation (why favorite / why not active / what replaced / why active)
- Active-only personal summary (`What do you know about me?`)
- Promotion fidelity verification (Aria loads certified ACM v0.24.0)
- Aria routing validation (explanation, about-me, evidence → `memory_about_user`; never Mission Control / `memory_search` for these cues)

---

## Freeze

**M0L is frozen.** No additional feature work on this milestone.

Any future cognitive or integration change starts a **new milestone** under the pipeline:

Standalone ACM → Develop → Certify → Release → Promote unchanged → Aria → Integration validation.

---

## References

- `docs/acm_integration/PROBLEM_REPORT_M0L.md`
- Aria decision **A021** (promotion) · evidence routing commit `7343faa`
- Standalone ACM CHANGELOG `[0.24.0]`
