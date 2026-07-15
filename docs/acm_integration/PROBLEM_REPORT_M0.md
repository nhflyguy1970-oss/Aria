# Problem Report — M0 Implementation

**ID:** PR-M0-001  
**Date:** 2026-07-15  
**Milestone:** M0  
**Severity:** Documentation mismatch (non-blocking for M0)  
**Status:** Resolved by harvest-from-pin (Import Plan § VERSION.json / copy procedure)

## Conflict

The approved Import Plan schema example listed:

- `source_version`: `0.14.1`

while the locked pin (same document) is:

- tag `v0.14.0`
- commit `454dcb90a352a3f1daa44aa95ff7b2801994f4e3`

At that commit, ACM `pyproject.toml` and `acm/_version.py` both report **`0.14.0`**. The `0.14.1` value existed only on an uncommitted ACM working tree at blueprint draft time.

## Resolution applied (no redesign)

M0 `aria_acm/VERSION.json` **harvests** `source_version` from the pinned commit → `0.14.0`. Commit hash and tag remain the authority. No alternate ACM revision was selected.

## Second note (implementation necessity, Import Plan allowed)

Literal nested copy under `aria_acm/acm/` retains absolute `from acm.*` imports. Aria adds a minimal bootstrap in vendored `acm/__init__.py` registering `sys.modules["acm"]` to the nested package so imports resolve without site-packages or the standalone repo. Documented in `aria_acm/NOTICE`. Blueprint import path `from aria_acm.acm.api.engine import CognitiveEngine` is preserved.

No architectural redesign. No M1+ work.
