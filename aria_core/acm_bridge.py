"""Aria ↔ ACM thin translation façade (M1 Shadow).

Blueprint: docs/acm_integration/MEMORY_API_MAPPING.md · ARIA_ACM_IMPORT_PLAN.md

Rules (M1):
- Authoritative cognition remains **legacy** MemoryStore.
- When ARIA_ACM_SHADOW is on, dual-call vendored ACM for measurement only.
- Never serve ACM answers to users while authoritative_route() == \"legacy\".
- Do not reimplement ACM organs. Do not modify aria_acm cognition.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any

# Process counters (ids/counts only — never memory contents)
_METRICS: dict[str, Any] = {
    "shadow_calls": 0,
    "shadow_agree": 0,
    "shadow_disagree": 0,
    "shadow_errors": 0,
    "shadow_encode": 0,
    "shadow_recall": 0,
    "shadow_ms_samples": [],  # capped list of ACM-side ms
}
_METRICS_SAMPLES_CAP = 500
_ENGINE: Any = None
_LAST_COMPARE: dict[str, Any] | None = None


def _env_bool(name: str, default: str = "0") -> bool:
    raw = os.getenv(name, default).strip().lower()
    return raw not in ("0", "false", "no", "off", "")


def shadow_enabled() -> bool:
    """ARIA_ACM_SHADOW — M1–M2 parallel measure (default off)."""
    return _env_bool("ARIA_ACM_SHADOW", "0")


def primary_enabled() -> bool:
    """ARIA_ACM_PRIMARY — must stay false until M3."""
    return _env_bool("ARIA_ACM_PRIMARY", "0")


def rollback_enabled() -> bool:
    """ARIA_ACM_ROLLBACK — force legacy façade (pre-M4)."""
    return _env_bool("ARIA_ACM_ROLLBACK", "0")


def auto_persist_enabled() -> bool:
    return _env_bool("ARIA_ACM_AUTO_PERSIST", "1")


def persist_path() -> str:
    override = os.getenv("ARIA_ACM_PERSIST_PATH", "").strip()
    if override:
        return override
    try:
        from jarvis.config import DATA_DIR

        path = Path(DATA_DIR) / "acm" / "cognitive.db"
    except Exception:
        path = Path("data") / "acm" / "cognitive.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


def authoritative_route() -> str:
    """Return legacy | acm | rollback per blueprint flag precedence."""
    if rollback_enabled():
        return "rollback"
    if primary_enabled():
        return "acm"
    return "legacy"


def user_visible_uses_acm() -> bool:
    """M1: always False unless PRIMARY (forbidden until M3)."""
    return authoritative_route() == "acm"


def _bump(key: str, n: int = 1) -> None:
    _METRICS[key] = int(_METRICS.get(key, 0)) + n


def _record_ms(ms: float) -> None:
    samples: list[float] = _METRICS["shadow_ms_samples"]
    samples.append(float(ms))
    if len(samples) > _METRICS_SAMPLES_CAP:
        del samples[: len(samples) - _METRICS_SAMPLES_CAP]


def reset_for_tests() -> None:
    """Clear engine singleton and metrics (tests only)."""
    global _ENGINE, _LAST_COMPARE
    _ENGINE = None
    _LAST_COMPARE = None
    for k in list(_METRICS.keys()):
        if k == "shadow_ms_samples":
            _METRICS[k] = []
        else:
            _METRICS[k] = 0


def get_engine() -> Any:
    """Lazy CognitiveEngine from vendored aria_acm (never site-packages preferred via path)."""
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    from aria_acm.acm.api.engine import CognitiveEngine

    _ENGINE = CognitiveEngine(
        agent_id=os.getenv("ARIA_ACM_AGENT_ID", "aria").strip() or "aria",
        persist_path=persist_path(),
        auto_persist=auto_persist_enabled(),
    )
    return _ENGINE


def normalize_answer(text: str) -> str:
    """Shadow answer normalizer (INTEGRATION_TEST_PLAN)."""
    s = (text or "").strip().lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # synonym booleans
    if s in ("y", "yeah", "yep", "true"):
        s = "yes"
    if s in ("n", "nope", "false"):
        s = "no"
    return s


def _legacy_answer_text(legacy: Any) -> str:
    if legacy is None:
        return ""
    if isinstance(legacy, str):
        return legacy
    if isinstance(legacy, dict):
        for key in ("content", "answer", "text", "summary"):
            if legacy.get(key):
                return str(legacy[key])
        return str(legacy.get("id") or "")
    if isinstance(legacy, list):
        parts: list[str] = []
        for item in legacy[:5]:
            if isinstance(item, dict) and item.get("content"):
                parts.append(str(item["content"]))
            else:
                parts.append(str(item))
        return " ".join(parts)
    return str(legacy)


def _acm_answer_text(acm_view: Any) -> str:
    if acm_view is None:
        return ""
    if isinstance(acm_view, str):
        return acm_view
    if isinstance(acm_view, dict):
        for key in ("answer", "text", "summary", "content"):
            if acm_view.get(key):
                return str(acm_view[key])
        # RememberResult-like public fields
        return str(acm_view.get("primary_label") or "")
    return str(acm_view)


def shadow_compare(legacy_answer: Any, acm_answer: Any) -> dict[str, Any]:
    """Compare normalized answers — ids/flags only in returned metrics."""
    global _LAST_COMPARE
    leg = normalize_answer(_legacy_answer_text(legacy_answer))
    acm = normalize_answer(_acm_answer_text(acm_answer))
    if not leg and not acm:
        agree = True
    elif not leg or not acm:
        agree = False
    else:
        # Slot-ish: token overlap or substring either way
        agree = leg == acm or leg in acm or acm in leg
        if not agree:
            leg_toks = set(leg.split())
            acm_toks = set(acm.split())
            if leg_toks and acm_toks:
                overlap = len(leg_toks & acm_toks) / max(1, len(leg_toks))
                agree = overlap >= 0.5
    if agree:
        _bump("shadow_agree")
    else:
        _bump("shadow_disagree")
    result = {
        "agree": agree,
        "authoritative": authoritative_route() if authoritative_route() != "rollback" else "legacy",
        "user_visible_changed": False,  # M1 invariant when route != acm
        "legacy_len": len(leg),
        "acm_len": len(acm),
    }
    _LAST_COMPARE = dict(result)
    return result


def last_shadow_compare() -> dict[str, Any] | None:
    return dict(_LAST_COMPARE) if _LAST_COMPARE else None


def encode_from_host(payload: dict[str, Any]) -> dict[str, Any]:
    """Translate host remember payload → CognitiveEngine.encode (measurement)."""
    content = str(payload.get("content") or payload.get("text") or "")
    entry_type = str(payload.get("entry_type") or payload.get("type") or "fact")
    tags = list(payload.get("tags") or [])
    namespace = payload.get("namespace")
    kind = "preference" if entry_type == "preference" else "experience"
    if entry_type in ("identity",) or (namespace == "profile" and "identity" in tags):
        kind = "identity"
    context_tags: list[str] = [str(t) for t in tags if t]
    if namespace:
        context_tags.append(f"ns:{namespace}")
    context_tags.append(f"legacy_type:{entry_type}")
    t0 = time.perf_counter()
    try:
        engine = get_engine()
        out = engine.encode(
            content,
            kind=kind,
            pin=True,  # measurement durability; Attention may otherwise skip
            context_tags=tuple(dict.fromkeys(context_tags)) or None,
        )
        ms = (time.perf_counter() - t0) * 1000.0
        _record_ms(ms)
        _bump("shadow_calls")
        _bump("shadow_encode")
        return {
            "ok": bool(out.get("encoded") or out.get("experience_id")),
            "acm_verb": "encode",
            "duration_ms": round(ms, 3),
            "encoded": out.get("encoded"),
            "experience_id": out.get("experience_id"),
            "attention": out.get("attention"),
            "reason": out.get("reason"),
        }
    except Exception as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        _record_ms(ms)
        _bump("shadow_calls")
        _bump("shadow_errors")
        return {
            "ok": False,
            "acm_verb": "encode",
            "duration_ms": round(ms, 3),
            "error": type(exc).__name__,
        }


def recall_from_host(cue: str, *, mode: str = "remember") -> dict[str, Any]:
    """Translate host recall/search → what_do_i_remember / remember."""
    t0 = time.perf_counter()
    try:
        engine = get_engine()
        if mode == "engine_remember":
            view = engine.remember(cue)
            # RememberResult dataclass-ish
            if hasattr(view, "__dict__"):
                payload = {
                    "answer": getattr(view, "answer", None)
                    or getattr(view, "text", None)
                    or str(view),
                    "confidence": getattr(view, "confidence", None),
                    "ambiguous": getattr(view, "ambiguous", None),
                }
            elif isinstance(view, dict):
                payload = view
            else:
                payload = {"answer": str(view)}
        else:
            payload = engine.what_do_i_remember(cue)
        ms = (time.perf_counter() - t0) * 1000.0
        _record_ms(ms)
        _bump("shadow_calls")
        _bump("shadow_recall")
        return {
            "ok": True,
            "acm_verb": "remember",
            "duration_ms": round(ms, 3),
            "view": payload if isinstance(payload, dict) else {"answer": str(payload)},
        }
    except Exception as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        _record_ms(ms)
        _bump("shadow_calls")
        _bump("shadow_errors")
        return {
            "ok": False,
            "acm_verb": "remember",
            "duration_ms": round(ms, 3),
            "error": type(exc).__name__,
            "view": {},
        }


def panel_observables() -> dict[str, Any]:
    """Mission Control shadow block — counts/flags only, no contents."""
    samples: list[float] = list(_METRICS.get("shadow_ms_samples") or [])
    agree = int(_METRICS.get("shadow_agree", 0))
    disagree = int(_METRICS.get("shadow_disagree", 0))
    compared = agree + disagree
    rate = round(agree / compared, 4) if compared else None
    p95 = None
    if samples:
        ordered = sorted(samples)
        idx = min(len(ordered) - 1, max(0, int(0.95 * (len(ordered) - 1))))
        p95 = round(ordered[idx], 3)
    return {
        "shadow_enabled": shadow_enabled(),
        "authoritative": "legacy"
        if authoritative_route() == "rollback"
        else authoritative_route(),
        "user_visible_changed": user_visible_uses_acm(),
        "shadow_calls": int(_METRICS.get("shadow_calls", 0)),
        "shadow_encode": int(_METRICS.get("shadow_encode", 0)),
        "shadow_recall": int(_METRICS.get("shadow_recall", 0)),
        "shadow_agree": agree,
        "shadow_disagree": disagree,
        "shadow_errors": int(_METRICS.get("shadow_errors", 0)),
        "agreement_rate": rate,
        "shadow_p95_ms": p95,
        "shadow_samples": len(samples),
        "persist_path_set": bool(persist_path()),
        "note": "M1 Shadow metrics — no memory contents",
    }


def shadow_remember_after_legacy(content: str, **kwargs: Any) -> dict[str, Any] | None:
    """Best-effort ACM encode after legacy remember. Never changes return path."""
    if not shadow_enabled() or user_visible_uses_acm():
        return None
    return encode_from_host(
        {
            "content": content,
            "entry_type": kwargs.get("entry_type", "fact"),
            "tags": kwargs.get("tags"),
            "namespace": kwargs.get("namespace"),
        }
    )


def shadow_search_after_legacy(query: str, legacy_hits: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Best-effort ACM recall + compare after legacy search. Legacy hits unchanged."""
    if not shadow_enabled() or user_visible_uses_acm():
        return None
    acm = recall_from_host(query)
    view = acm.get("view") or {}
    cmp = shadow_compare(legacy_hits, view)
    return {
        "acm_verb": acm.get("acm_verb"),
        "duration_ms": acm.get("duration_ms"),
        "ok": acm.get("ok"),
        "shadow_agree": cmp.get("agree"),
        "authoritative": cmp.get("authoritative"),
        "user_visible_changed": False,
        "error": acm.get("error"),
    }
