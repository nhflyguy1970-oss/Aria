"""Aria ↔ ACM thin translation façade (M1 Shadow · M3 Primary · M4 Sole SoT).

Blueprint: docs/acm_integration/MEMORY_API_MAPPING.md · REMOVAL_PLAN.md

Rules:
- M4: ARIA_ACM_PRIMARY defaults **on** — ACM is Aria's sole cognitive SoT.
- Legacy MemoryStore writes redirect to ACM when authoritative.
- DualWrite cognitive authority retired (M4b).
- ARIA_ACM_ROLLBACK forces legacy façades only during the M4 rollback window.
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
    "primary_encode": 0,
    "primary_recall": 0,
    "primary_cool": 0,
    "primary_revise": 0,
    "legacy_writes_while_primary": 0,
    "legacy_fallback_reads": 0,
}
_METRICS_SAMPLES_CAP = 500
_ENGINE: Any = None
_LAST_COMPARE: dict[str, Any] | None = None
_LAST_PRIMARY: dict[str, Any] | None = None


def _env_bool(name: str, default: str = "0") -> bool:
    raw = os.getenv(name, default).strip().lower()
    return raw not in ("0", "false", "no", "off", "")


def shadow_enabled() -> bool:
    """ARIA_ACM_SHADOW — M1–M2 parallel measure (default off)."""
    return _env_bool("ARIA_ACM_SHADOW", "0")


def primary_enabled() -> bool:
    """ARIA_ACM_PRIMARY — ACM production authority (M4 default on).

    Default ``1`` after M4. Set ``0`` only with explicit ``ARIA_ACM_ROLLBACK``
    emergency window (legacy forensic façades) — reintroducing legacy as
    product primary requires DECISION_LOG re-certification (Rule 6).
    """
    return _env_bool("ARIA_ACM_PRIMARY", "1")


def rollback_enabled() -> bool:
    """ARIA_ACM_ROLLBACK — force legacy façade (M4 rollback window only)."""
    return _env_bool("ARIA_ACM_ROLLBACK", "0")


def legacy_read_fallback_enabled() -> bool:
    """Optional legacy read when ACM returns empty (M3); default off after M4."""
    return _env_bool("ARIA_ACM_LEGACY_READ_FALLBACK", "0")


def redirect_legacy_write_to_acm(
    content: str,
    *,
    entry_type: str = "fact",
    tags: list[str] | None = None,
    namespace: str | None = None,
) -> dict[str, Any] | None:
    """M4: MemoryStore.add sinks → Cap Bus/ACM when ACM is authoritative.

    Returns host-shaped entry when redirected; ``None`` → caller may write
    legacy (ROLLBACK / PRIMARY=0 forensic window only).
    """
    if not acm_is_authoritative():
        return None
    # Import manager lazily to avoid cycle at module import time.
    from aria_core import memory_manager

    return memory_manager.remember(content, entry_type=entry_type, tags=tags, namespace=namespace)


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
    """True only when PRIMARY and not ROLLBACK."""
    return authoritative_route() == "acm"


def acm_is_authoritative() -> bool:
    return authoritative_route() == "acm"


def note_legacy_write_while_primary() -> None:
    """SUP-02 observability — must stay 0 when PRIMARY (except ROLLBACK)."""
    _bump("legacy_writes_while_primary")


def note_legacy_fallback_read() -> None:
    _bump("legacy_fallback_reads")


def last_primary_op() -> dict[str, Any] | None:
    return dict(_LAST_PRIMARY) if _LAST_PRIMARY else None


def _bump(key: str, n: int = 1) -> None:
    _METRICS[key] = int(_METRICS.get(key, 0)) + n


def _record_ms(ms: float) -> None:
    samples: list[float] = _METRICS["shadow_ms_samples"]
    samples.append(float(ms))
    if len(samples) > _METRICS_SAMPLES_CAP:
        del samples[: len(samples) - _METRICS_SAMPLES_CAP]


def reset_for_tests() -> None:
    """Clear engine singleton and metrics (tests only)."""
    global _ENGINE, _LAST_COMPARE, _LAST_PRIMARY
    _ENGINE = None
    _LAST_COMPARE = None
    _LAST_PRIMARY = None
    for k in list(_METRICS.keys()):
        if k == "shadow_ms_samples":
            _METRICS[k] = []
        else:
            _METRICS[k] = 0


def _legacy_cleanup_marker(path: str) -> Path:
    return Path(path).with_name(Path(path).name + ".d047_cleanup.json")


def legacy_cleanup_report() -> dict[str, Any] | None:
    """Report of the one-time D047 cleanup for the current store, if it ran."""
    import json

    marker = _legacy_cleanup_marker(persist_path())
    if not marker.is_file():
        return None
    try:
        return json.loads(marker.read_text(encoding="utf-8"))
    except Exception:
        return None


def _maybe_run_legacy_cleanup(engine: Any, path: str) -> None:
    """D047 upgrade path — run the legacy contamination cleanup once per pin.

    The migration itself is idempotent and a no-op on clean graphs. The marker
    records which embedded ACM version performed the migration; a store
    migrated by an older pin (e.g. v0.20.0, whose classifier missed live
    backtick tool wrappers) is re-migrated exactly once by the newer pin.
    """
    import json
    import time as _time

    from aria_acm.acm import __version__ as _acm_version

    marker = _legacy_cleanup_marker(path)
    if marker.is_file():
        try:
            recorded = json.loads(marker.read_text(encoding="utf-8"))
        except Exception:
            recorded = {}
        if recorded.get("acm_version") == _acm_version:
            return
    try:
        report = engine.cleanup_legacy_contamination()
        marker.write_text(
            json.dumps(
                {
                    "completed": _time.time(),
                    "acm_version": _acm_version,
                    "persist_path": path,
                    "report": report,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        _bump("d047_cleanup_runs")
    except Exception:
        # Never block engine startup; the next start retries the migration.
        _bump("d047_cleanup_errors")


def get_engine() -> Any:
    """Lazy CognitiveEngine from vendored aria_acm (never site-packages preferred via path)."""
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    from aria_acm.acm.api.engine import CognitiveEngine

    path = persist_path()
    _ENGINE = CognitiveEngine(
        agent_id=os.getenv("ARIA_ACM_AGENT_ID", "aria").strip() or "aria",
        persist_path=path,
        auto_persist=auto_persist_enabled(),
    )
    _maybe_run_legacy_cleanup(_ENGINE, path)
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
        from aria_acm.acm.provenance import TRUSTED_USER_TEACHING

        engine = get_engine()
        out = engine.encode(
            content,
            kind=kind,
            pin=True,  # measurement durability; Attention may otherwise skip
            context_tags=tuple(dict.fromkeys(context_tags)) or None,
            # D046: host memory writes carry user knowledge supplied through
            # Aria's memory API — declare the trusted user source explicitly.
            provenance=TRUSTED_USER_TEACHING,
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
        "authoritative": "legacy" if authoritative_route() == "rollback" else authoritative_route(),
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
        "primary_encode": int(_METRICS.get("primary_encode", 0)),
        "primary_recall": int(_METRICS.get("primary_recall", 0)),
        "primary_cool": int(_METRICS.get("primary_cool", 0)),
        "primary_revise": int(_METRICS.get("primary_revise", 0)),
        "legacy_writes_while_primary": int(_METRICS.get("legacy_writes_while_primary", 0)),
        "legacy_fallback_reads": int(_METRICS.get("legacy_fallback_reads", 0)),
        "legacy_read_fallback": legacy_read_fallback_enabled(),
        "note": "M1 Shadow / M3 Primary metrics — no memory contents",
        "harvest": _harvest_panel(),
    }


def _harvest_panel() -> dict[str, Any]:
    try:
        from aria_core.acm_harvest import last_harvest_report

        last = last_harvest_report()
        if not last:
            return {"last_report": None, "note": "No M2 harvest run in this process"}
        # Drop content-bearing fields; mapping count only
        return {
            "last_report": {
                k: last[k]
                for k in (
                    "ok",
                    "imported",
                    "skipped_existing",
                    "encode_failures",
                    "completeness_rate",
                    "identity_assented",
                    "journal_imported",
                    "preference_imported",
                    "project_imported",
                    "authoritative",
                    "duration_ms",
                )
                if k in last
            }
        }
    except Exception as exc:
        return {"error": type(exc).__name__}


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


def shadow_search_after_legacy(
    query: str, legacy_hits: list[dict[str, Any]]
) -> dict[str, Any] | None:
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


def _set_last_primary(**fields: Any) -> dict[str, Any]:
    global _LAST_PRIMARY
    _LAST_PRIMARY = {
        "authoritative": "acm",
        "user_visible_changed": True,
        **fields,
    }
    return dict(_LAST_PRIMARY)


def primary_remember(
    content: str,
    *,
    entry_type: str = "fact",
    tags: list[str] | None = None,
    namespace: str | None = None,
) -> dict[str, Any]:
    """Authoritative ACM encode → host-shaped entry (M3). No MemoryStore write."""
    from aria_acm.acm.context.frame import ContextFrame
    from aria_acm.acm.provenance import TRUSTED_USER_TEACHING

    t0 = time.perf_counter()
    engine = get_engine()
    engine.context = ContextFrame()
    kind = "preference" if entry_type == "preference" else "experience"
    if entry_type == "identity" or (namespace == "profile" and "identity" in (tags or [])):
        kind = "identity"
    context_tags: list[str] = [str(t) for t in (tags or []) if t]
    if namespace:
        context_tags.append(f"ns:{namespace}")
    context_tags.append(f"legacy_type:{entry_type}")
    out = engine.encode(
        content,
        kind=kind,
        pin=True,
        context_tags=tuple(dict.fromkeys(context_tags)) or None,
        # D046: authoritative host remember() carries user-supplied knowledge.
        provenance=TRUSTED_USER_TEACHING,
    )
    ms = (time.perf_counter() - t0) * 1000.0
    _record_ms(ms)
    _bump("primary_encode")
    exp_id = str(out.get("experience_id") or "")
    host = {
        "id": exp_id or str(out.get("concept_id") or ""),
        "content": content,
        "type": entry_type,
        "namespace": namespace or "default",
        "tags": list(tags or []),
        "source": "acm",
        "encoded": bool(out.get("encoded") or exp_id),
        "attention": out.get("attention"),
        "concept_id": out.get("concept_id"),
    }
    _set_last_primary(acm_verb="encode", duration_ms=round(ms, 3), experience_id=exp_id)
    return host


def primary_classify_request(text: str) -> dict[str, Any]:
    """Cognitive Intent Classification — ownership before speech (D039)."""
    engine = get_engine()
    return engine.classify_request(text)


def primary_route_request(text: str) -> dict[str, Any]:
    """Classify + determine cognitive organ ownership (D039). No reconstruction."""
    engine = get_engine()
    decision = engine.route_request(text)
    ownership = (decision.get("ownership") or {}) if isinstance(decision, dict) else {}
    classification = (decision.get("classification") or {}) if isinstance(decision, dict) else {}
    _set_last_primary(
        acm_verb="route_request",
        intent=classification.get("intent"),
        is_memory_request=classification.get("is_memory_request"),
        primary_organ=ownership.get("primary_organ"),
        uncertain=bool(classification.get("uncertain") or ownership.get("uncertain")),
    )
    return decision


def primary_dispatch_request(text: str) -> dict[str, Any]:
    """End-to-end cognitive dispatch via ACM (D040). Aria does not dispatch."""
    engine = get_engine()
    outcome = engine.dispatch_request(text)
    record = (outcome.get("record") or {}) if isinstance(outcome, dict) else {}
    decision = (outcome.get("decision") or {}) if isinstance(outcome, dict) else {}
    classification = (decision.get("classification") or {}) if isinstance(decision, dict) else {}
    _set_last_primary(
        acm_verb="dispatch_request",
        intent=record.get("intent") or classification.get("intent"),
        is_memory_request=classification.get("is_memory_request"),
        primary_organ=record.get("primary_organ"),
        terminated_at=record.get("terminated_at"),
        supporting_organs=record.get("supporting_organs"),
        uncertain=bool(record.get("uncertain") or classification.get("uncertain")),
    )
    return outcome


def _memory_request_for_search(query: str) -> str:
    """Translate host search cue → ACM memory-request text (façade only)."""
    text = (query or "").strip()
    if not text:
        return "What do you remember about me?"
    lowered = text.lower()
    if lowered in ("about me", "me"):
        return "What do you remember about me?"
    classification = primary_classify_request(text)
    if classification.get("is_memory_request"):
        return text
    return f"What do you remember about {text}?"


def primary_cognitive_respond(request: str) -> dict[str, Any]:
    """classify → route → dispatch → organ terminate → CognitiveMemoryResult."""
    import logging
    import os

    t0 = time.perf_counter()
    # Temporary DEBUG: confirm Teaching Recognition executes on live conversation.
    _teach_log = logging.getLogger("aria.teaching_recognition")
    _teach_debug = os.getenv("ARIA_TEACHING_DEBUG", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )
    teaching_meta: dict[str, Any] = {}
    try:
        from aria_acm.acm.authority.teaching import detect_teaching

        detected = detect_teaching(request)
        teaching_meta = {
            "teaching": bool(detected.is_teaching),
            "reason": detected.reason,
            "facts": [
                {"kind": f.kind.value, "property": f.property, "value": f.value}
                for f in detected.facts
            ],
        }
        if _teach_debug:
            msg_in = f"[TeachingRecognition] Input: {(request or '')[:240]}"
            msg_flag = (
                f"[TeachingRecognition] teaching={detected.is_teaching} reason={detected.reason}"
            )
            _teach_log.warning(msg_in)
            _teach_log.warning(msg_flag)
            print(msg_in, flush=True)
            print(msg_flag, flush=True)
            if detected.is_teaching:
                dispatch_msg = "[TeachingRecognition] Dispatching to EncodeAuthority"
                _teach_log.warning(dispatch_msg)
                print(dispatch_msg, flush=True)
    except Exception as exc:
        teaching_meta = {"teaching": False, "reason": f"detect_failed:{type(exc).__name__}"}
        if _teach_debug:
            fail = f"[TeachingRecognition] detect_failed: {type(exc).__name__}"
            _teach_log.warning(fail)
            print(fail, flush=True)

    # Explicit ownership + dispatch steps (D039 · D040). ACM owns execution.
    route = primary_route_request(request)
    ownership = (route.get("ownership") or {}) if isinstance(route, dict) else {}
    dispatched = primary_dispatch_request(request)
    record = (dispatched.get("record") or {}) if isinstance(dispatched, dict) else {}
    engine = get_engine()
    result = engine.cognitive_respond(request)
    ms = (time.perf_counter() - t0) * 1000.0
    _record_ms(ms)
    _bump("primary_recall")
    diag = (result.get("diagnostics") or {}) if isinstance(result, dict) else {}
    path = list(result.get("reasoning_path") or [])
    teach_steps = [p for p in path if str(p).startswith("teaching_")]
    if _teach_debug and teach_steps:
        done = f"[TeachingRecognition] pipeline={teach_steps}"
        _teach_log.warning(done)
        print(done, flush=True)
    _set_last_primary(
        acm_verb="cognitive_respond",
        duration_ms=round(ms, 3),
        cognitive_status=result.get("status"),
        is_memory_request=result.get("is_memory_request"),
        intent=result.get("intent") or ownership.get("intent"),
        primary_organ=diag.get("primary_organ") or ownership.get("primary_organ"),
        terminated_at=diag.get("terminated_at") or record.get("terminated_at"),
        supporting_organs=diag.get("supporting_organs") or record.get("supporting_organs"),
        confidence=result.get("confidence"),
        provenance=result.get("provenance") or diag.get("provenance"),
        reconstruction_path=diag.get("reconstruction_path") or diag.get("path"),
        dispatch_path=diag.get("dispatch_path")
        or [
            "classify_request",
            "route_request",
            "dispatch_request",
            diag.get("terminated_at") or ownership.get("primary_organ"),
        ],
        uncertain=bool(
            diag.get("uncertain") or (route.get("classification") or {}).get("uncertain")
        ),
        teaching_recognition=teaching_meta,
        teaching_pipeline=teach_steps,
    )
    return result


def primary_cognitive_speak(request: str) -> dict[str, Any]:
    """Full path: classify → route → dispatch → respond → faithful speak."""
    result = primary_cognitive_respond(request)
    speech = ""
    if result.get("is_memory_request"):
        speech = get_engine().speak_cognitive_result(result)
    return {
        "result": result,
        "speech": speech,
        "diagnostics": result.get("diagnostics") or {},
        "route": last_primary_op(),
    }


def cognitive_result_to_hits(
    result: dict[str, Any],
    *,
    speech: str = "",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Map CognitiveMemoryResult → host-shaped hits (faithful, never invented)."""
    if not isinstance(result, dict) or not result.get("is_memory_request"):
        return []
    text = (speech or str(result.get("memory") or "")).strip()
    if not text:
        return []
    raw = result.get("organ_payload") or {}
    if isinstance(raw, dict):
        raw_view = raw.get("raw") or {}
    else:
        raw_view = {}
    hit_id = ""
    if isinstance(raw_view, dict):
        hit_id = str(
            raw_view.get("experience_id")
            or raw_view.get("primary_concept_id")
            or raw_view.get("concept_id")
            or ""
        )
    hits = [
        {
            "id": hit_id,
            "content": text,
            "type": "fact",
            "score": result.get("confidence"),
            "source": "acm",
            "ambiguous": result.get("ambiguous"),
            "cognitive_status": result.get("status"),
            "intent": result.get("intent"),
            "provenance": result.get("provenance"),
            "uncertainty": result.get("uncertainty"),
            "explanation_class": result.get("explanation_class"),
        }
    ]
    return hits[:limit]


def primary_search(
    query: str,
    *,
    limit: int = 10,
    namespace: str | None = None,
) -> list[dict[str, Any]]:
    """Authoritative ACM recall → host-shaped hit list via Memory Authority (M0C)."""
    if namespace:
        get_engine().set_context(f"ns:{namespace}")
    request = _memory_request_for_search(query)
    cog = primary_cognitive_speak(request)
    hits = cognitive_result_to_hits(cog["result"], speech=cog["speech"], limit=limit)
    _set_last_primary(
        acm_verb="cognitive_respond",
        hit_count=len(hits),
        ambiguous=(cog["result"] or {}).get("ambiguous"),
        cognitive_status=(cog["result"] or {}).get("status"),
    )
    return hits


def primary_get(entry_id: str) -> dict[str, Any] | None:
    engine = get_engine()
    exp = engine.store.experiences.get(entry_id)
    if exp is not None:
        pub = engine.experiences.public_view(exp)
        return {
            "id": exp.id,
            "content": exp.summary,
            "type": "fact",
            "source": "acm",
            "tags": list(exp.context_tags),
            "public": pub,
        }
    concept = engine.store.concepts.get(entry_id)
    if concept is not None:
        return {
            "id": concept.id,
            "content": concept.labels[0] if concept.labels else concept.id,
            "type": "fact",
            "source": "acm",
        }
    return None


def primary_forget(
    *,
    entry_id: str | None = None,
    query: str | None = None,
) -> dict[str, Any]:
    """Soft forget via cool_memory (never hard-delete Experiences)."""
    engine = get_engine()
    concept_id = entry_id
    if entry_id and entry_id in engine.store.experiences:
        exp = engine.store.experiences[entry_id]
        concept_id = exp.concept_ids[0] if exp.concept_ids else None
    if not concept_id and query:
        view = engine.what_do_i_remember(query)
        concept_id = str((view or {}).get("primary_concept_id") or "") or None
    if not concept_id:
        return {"ok": False, "cooled": False, "deleted": False, "reason": "no_concept"}
    t0 = time.perf_counter()
    out = engine.cool_memory(str(concept_id), steps=1)
    ms = (time.perf_counter() - t0) * 1000.0
    _record_ms(ms)
    _bump("primary_cool")
    _set_last_primary(acm_verb="cool", duration_ms=round(ms, 3), concept_id=concept_id)
    return {
        "ok": bool(out.get("cooled")),
        "cooled": bool(out.get("cooled")),
        "deleted": False,
        "experiences_unchanged": out.get("experiences_unchanged", True),
        "id": concept_id,
    }


def primary_correct(
    *,
    experience_id: str | None = None,
    query: str | None = None,
    text: str,
) -> dict[str, Any]:
    """revise_experience — immutable lineage correction."""
    engine = get_engine()
    eid = experience_id
    if not eid and query:
        # encode new correction revises best match if we can locate prior
        view = engine.what_do_i_remember(query)
        eid = str((view or {}).get("experience_id") or "") or None
        if not eid:
            # fall through: encode as pinned preference/fact without revise link
            host = primary_remember(text, entry_type="fact", tags=["correction"])
            return {"ok": bool(host.get("encoded")), "entry": host, "revised": False}
    if not eid:
        host = primary_remember(text, entry_type="fact", tags=["correction"])
        return {"ok": bool(host.get("encoded")), "entry": host, "revised": False}
    from aria_acm.acm.provenance import TRUSTED_USER_CORRECTION

    t0 = time.perf_counter()
    out = engine.revise_experience(str(eid), text, provenance=TRUSTED_USER_CORRECTION)
    ms = (time.perf_counter() - t0) * 1000.0
    _record_ms(ms)
    _bump("primary_revise")
    new_id = str(out.get("experience_id") or "")
    host = {
        "id": new_id,
        "content": text,
        "type": "fact",
        "source": "acm",
        "revises_id": eid,
    }
    _set_last_primary(acm_verb="revise", duration_ms=round(ms, 3), experience_id=new_id)
    return {"ok": bool(out.get("encoded") or new_id), "entry": host, "revised": True}


def primary_context_fragments(message: str, *, limit: int = 5) -> list[str]:
    """Prompt fragments from Memory Authority — no CoT / no prompts leaked."""
    cog = primary_cognitive_speak(message)
    result = cog["result"]
    parts: list[str] = []
    if isinstance(result, dict) and result.get("is_memory_request"):
        speech = str(cog.get("speech") or "").strip()
        mem = str(result.get("memory") or "").strip()
        intent = str(result.get("intent") or "")
        if intent in ("identity", "assistant_identity", "user_identity") and mem:
            parts.append(f"Identity:\n- {mem[:500]}")
        elif speech:
            parts.append(f"Relevant memories:\n- {speech[:800]}")
        elif mem:
            parts.append(f"Relevant memories:\n- {mem[:800]}")
    _set_last_primary(acm_verb="cognitive_respond", context_parts=len(parts[:limit]))
    return parts[:limit]


def system_prompt_from_acm(*, max_chars: int = 2200) -> str:
    """Stable user/assistant context for system prompt — ACM only."""
    if not acm_is_authoritative():
        return ""
    parts: list[str] = ["Persistent cognitive context (ACM):"]
    try:
        who = primary_cognitive_speak("Who are you?")
        speech = str(who.get("speech") or "").strip()
        if speech and not speech.lower().startswith("i don't"):
            parts.append(f"- Assistant: {speech[:400]}")
    except Exception:
        pass
    try:
        user = primary_cognitive_speak("Who am I?")
        speech = str(user.get("speech") or "").strip()
        if speech and "don't currently know" not in speech.lower():
            parts.append(f"- User: {speech[:500]}")
    except Exception:
        pass
    try:
        prefs = primary_cognitive_speak("What are my preferences?")
        speech = str(prefs.get("speech") or "").strip()
        if speech and "don't currently know" not in speech.lower():
            parts.append(f"- Preferences: {speech[:500]}")
    except Exception:
        pass
    try:
        goals = primary_cognitive_speak("What is our long-term goal?")
        speech = str(goals.get("speech") or "").strip()
        if speech and "don't currently know" not in speech.lower():
            parts.append(f"- Goals: {speech[:400]}")
    except Exception:
        pass
    if len(parts) <= 1:
        return ""
    block = "\n".join(parts)
    if len(block) > max_chars:
        block = block[: max_chars - 3] + "..."
    return block


def project_list_entries(
    entry_type: str | None = None,
    *,
    namespace: str | None = None,
    query: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """Host-shaped ACM projection for list_entries façades (not legacy SoT)."""
    if not acm_is_authoritative():
        return []
    engine = get_engine()
    out: list[dict[str, Any]] = []
    q = (query or "").strip().lower()
    ns = (namespace or "").strip()
    for exp in engine.store.experiences.values():
        tags = list(getattr(exp, "context_tags", ()) or [])
        content = str(getattr(exp, "summary", "") or "")
        entry_ns = "default"
        for t in tags:
            if str(t).startswith("ns:"):
                entry_ns = str(t)[3:]
                break
        etype = "fact"
        for t in tags:
            if str(t).startswith("legacy_type:"):
                etype = str(t).split(":", 1)[1]
                break
        if entry_type and etype != entry_type:
            continue
        if ns and entry_ns != ns:
            continue
        if q and q not in content.lower() and not any(q in str(t).lower() for t in tags):
            continue
        out.append(
            {
                "id": exp.id,
                "content": content,
                "type": etype,
                "namespace": entry_ns,
                "tags": tags,
                "source": "acm",
                "timestamp": getattr(exp, "t_encoded", None) or getattr(exp, "timestamp", None),
            }
        )
        if len(out) >= limit:
            break
    if len(out) < limit:
        for concept in engine.store.concepts.values():
            label = concept.labels[0] if getattr(concept, "labels", None) else concept.id
            if entry_type and entry_type not in ("fact", "concept"):
                continue
            if q and q not in str(label).lower():
                continue
            out.append(
                {
                    "id": concept.id,
                    "content": str(label),
                    "type": "fact",
                    "namespace": ns or "default",
                    "tags": ["concept"],
                    "source": "acm",
                }
            )
            if len(out) >= limit:
                break
    _set_last_primary(acm_verb="project_list", hit_count=len(out))
    return out


def project_search(
    query: str, *, limit: int = 10, namespace: str | None = None
) -> list[dict[str, Any]]:
    """Authoritative ACM search for MemoryStore.search façades."""
    return primary_search(query, limit=limit, namespace=namespace)


def acm_similar_exists(content: str, threshold: float = 0.88) -> bool:
    """Soft duplicate check against ACM (authoritative path)."""
    if not acm_is_authoritative() or not (content or "").strip():
        return False
    hits = primary_search(content.strip()[:200], limit=3)
    if not hits:
        return False
    needle = content.strip().lower()
    for h in hits:
        blob = str(h.get("content") or "").strip().lower()
        if not blob:
            continue
        if blob == needle or needle in blob or blob in needle:
            return True
        score = h.get("score")
        try:
            if score is not None and float(score) >= threshold:
                return True
        except (TypeError, ValueError):
            pass
    return False


def acm_dashboard(*, limit: int = 100) -> dict[str, Any]:
    """Mission Control ACM Cognitive Dashboard payload (no legacy SoT)."""
    engine = get_engine()
    exps = list(engine.store.experiences.values())
    concepts = list(engine.store.concepts.values())
    goals = list(engine.store.active_goals())
    assocs = (
        list(engine.store.associations.values()) if hasattr(engine.store, "associations") else []
    )
    last = last_primary_op() or {}
    obs = panel_observables()

    def _sample_events(n: int = 20) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for exp in exps[-n:]:
            rows.append(
                {
                    "id": exp.id,
                    "kind": "experience",
                    "organ": "experiences",
                    # ids/flags only — never memory body contents in MC payload
                }
            )
        return rows[-n:]

    who: dict[str, Any] = {}
    try:
        who = engine.who_am_i() if hasattr(engine, "who_am_i") else {}
    except Exception:
        who = {}

    return {
        "ok": True,
        "title": "ACM Cognitive Dashboard",
        "owner": "aria_acm",
        "version": "acm-cognitive-dashboard.v1",
        "implementation": "embedded ACM (aria_acm)",
        "provider": "aria_core.acm_bridge → CognitiveEngine",
        "authoritative": "acm",
        "cognitive_model": "D038+D039+D040",
        "identity": {
            "answer": (who.get("answer") or "")[:300] if isinstance(who, dict) else "",
            "confidence": who.get("confidence") if isinstance(who, dict) else None,
            "agent_id": getattr(engine, "agent_id", "aria"),
        },
        "experiences": {"count": len(exps)},
        "concepts": {"count": len(concepts)},
        "associations": {"count": len(assocs)},
        "goals": {
            "active_count": len(goals),
            "titles": [g.title for g in goals[:8]],
        },
        "organs": {
            "identity": True,
            "remembering": True,
            "learning": True,
            "reflection": True,
            "associations": True,
            "concepts": True,
            "goals": True,
            "confidence": True,
            "attention": True,
            "accessibility": True,
            "dispatch": True,
        },
        "dispatch": {
            "last_intent": last.get("intent"),
            "last_primary_organ": last.get("primary_organ"),
            "last_terminated_at": last.get("terminated_at"),
            "last_verb": last.get("acm_verb"),
            "supporting_organs": last.get("supporting_organs") or [],
        },
        "confidence": {
            "note": "Per-result confidence on CognitiveMemoryResult",
            "last_status": last.get("cognitive_status"),
        },
        "uncertainty": {"policy": "unknown remains unknown; speak faithful templates"},
        "provenance": {"policy": "experience provenance via Memory Authority gates"},
        "memory_health": {
            "ok": True,
            "cognitive_store_reachable": True,
            "persist_path_set": bool(persist_path()),
            "experience_count": len(exps),
            "concept_count": len(concepts),
            "active_goals": len(goals),
        },
        "cognitive_health": {
            "ok": True,
            "authoritative": "acm",
            "primary_default_on": True,
            "rollback": rollback_enabled(),
        },
        "cognitive_activity": {
            "primary_encode": obs.get("primary_encode"),
            "primary_recall": obs.get("primary_recall"),
            "primary_cool": obs.get("primary_cool"),
            "primary_revise": obs.get("primary_revise"),
        },
        "organ_activity": obs,
        "recent_cognitive_events": _sample_events(min(limit, 40)),
        "reconstruction_metrics": {
            "primary_recall": obs.get("primary_recall"),
            "shadow_p95_ms": obs.get("shadow_p95_ms"),
        },
        "memory_growth": {"experiences": len(exps), "concepts": len(concepts)},
        "learning_progress": {"note": "via Learning organ adaptations"},
        "reflection_history": {"note": "via Reflection organ outcomes"},
        # Compatibility keys for existing Mission Control Memory tab layout
        "entry_count": len(exps),
        "active_facts": len(exps),
        "superseded_facts": 0,
        "health": {"ok": True, "store_reachable": True},
        "history": [],  # contents never in MC; use recent_cognitive_events (ids only)
        "statistics": {
            "entry_count": len(exps),
            "provider": "aria_acm",
            "experiences": len(exps),
            "concepts": len(concepts),
            "goals": len(goals),
        },
        "counters": {
            "reads": int(obs.get("primary_recall") or 0),
            "writes": int(obs.get("primary_encode") or 0),
            "searches": int(obs.get("primary_recall") or 0),
        },
        "reads": int(obs.get("primary_recall") or 0),
        "writes": int(obs.get("primary_encode") or 0),
        "searches": int(obs.get("primary_recall") or 0),
        "shadow": obs,
        "consumers": [
            "capability_bus",
            "cognitive_orchestrator",
            "mission_control",
            "conversation",
        ],
        "note": (
            "ACM Cognitive Dashboard — embedded ACM is the sole cognitive SoT. "
            "Legacy MemoryStore is not cognitive authority."
        ),
        "legacy_disconnected": True,
    }
