"""Preference correction UX (B12) — distinguish correction from new observation.

Builds on B11 PreferencePolicyGate. Correction phrases mark lineage explicitly
while still committing through encode (immutable Experiences).
"""

from __future__ import annotations

import re
from typing import Any, TYPE_CHECKING

from acm.authority.preference_edit import (
    _canonical_text,
    _find_active,
    _normalize_key,
    apply_preference_change,
    preview_preference_change,
    propose_preference_change,
)

if TYPE_CHECKING:
    from acm.api.engine import CognitiveEngine

SCHEMA = "acm.preference.correction.v1"

_CORRECTION = re.compile(
    r"^\s*(?:actually|no,?\s+wait|i\s+meant|correction:?|rather,?)\s*[,:]?\s*"
    r"(?:my\s+)?(?:favorite\s+)?(?P<noun>[\w\s]+?)\s+is\s+(?P<value>.+?)\s*\.?\s*$",
    re.I,
)
_CORRECTION_SHORT = re.compile(
    r"^\s*(?:actually|i\s+meant|correction:?)\s*[,:]?\s*(?P<value>[A-Za-z][\w\s-]*)\s*\.?\s*$",
    re.I,
)


def parse_preference_correction(text: str, *, default_key: str = "favorite_color") -> dict[str, Any] | None:
    """Parse correction utterance into key/value or None."""
    body = (text or "").strip()
    if not body:
        return None
    m = _CORRECTION.match(body)
    if m:
        noun = " ".join(m.group("noun").strip().split())
        key = _normalize_key(noun if "favorite" in noun.lower() else f"favorite_{noun}")
        return {
            "key": key,
            "value": m.group("value").strip().rstrip("."),
            "phrase": "correction",
        }
    m2 = _CORRECTION_SHORT.match(body)
    if m2:
        return {
            "key": _normalize_key(default_key),
            "value": m2.group("value").strip().rstrip("."),
            "phrase": "correction_short",
        }
    return None


def preview_preference_correction(
    engine: CognitiveEngine,
    text: str,
    *,
    default_key: str = "favorite_color",
) -> dict[str, Any]:
    parsed = parse_preference_correction(text, default_key=default_key)
    if parsed is None:
        return {
            "schema": SCHEMA,
            "status": "unrecognized",
            "invents_experiences": False,
            "store_write": False,
        }
    preview = preview_preference_change(
        engine, key=parsed["key"], value=parsed["value"], op="replace"
    )
    preview.update(
        {
            "schema": SCHEMA,
            "status": "preview",
            "is_correction": True,
            "phrase": parsed["phrase"],
            "explanation": (
                f"The user corrected the prior value from '{preview['previous']}' "
                f"to '{preview['proposed']}'."
                if preview.get("previous")
                else f"The user stated a corrected preference '{preview['proposed']}'."
            ),
        }
    )
    return preview


def apply_preference_correction(
    engine: CognitiveEngine,
    text: str,
    *,
    default_key: str = "favorite_color",
    assent: bool = True,
) -> dict[str, Any]:
    """Apply a correction utterance with explicit correction lineage metadata."""
    preview = preview_preference_correction(engine, text, default_key=default_key)
    if preview.get("status") != "preview":
        return preview
    if not assent:
        prop = propose_preference_change(
            engine,
            key=preview["key"],
            value=preview["proposed"],
            op="replace",
            reason="preference_correction",
        )
        prop["is_correction"] = True
        prop["explanation"] = preview.get("explanation")
        return prop
    result = apply_preference_change(
        engine,
        key=preview["key"],
        value=preview["proposed"],
        op="replace",
        assent=True,
    )
    # Side-channel correction lineage (Experiences are frozen/immutable).
    lineage = {
        "preference_correction": True,
        "corrected_from": str(preview.get("previous") or ""),
        "corrected_to": str(preview.get("proposed") or ""),
        "key": preview["key"],
        "experience_id": result.get("experience_id"),
        "explanation": preview.get("explanation"),
    }
    store = getattr(engine, "_preference_corrections", None)
    if not isinstance(store, dict):
        engine._preference_corrections = {}
        store = engine._preference_corrections
    if result.get("experience_id"):
        store[str(result["experience_id"])] = lineage
    result.update(
        {
            "schema": SCHEMA,
            "is_correction": True,
            "explanation": preview.get("explanation"),
            "previous": preview.get("previous"),
            "proposed": preview.get("proposed"),
            "correction_lineage": lineage,
        }
    )
    return result
