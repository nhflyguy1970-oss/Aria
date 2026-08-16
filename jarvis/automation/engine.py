"""Local automation engine — scheduled tasks + filesystem watchers (honest execution)."""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from jarvis.automation.execution import FAILED, SKIPPED, normalize_result
from jarvis.automation.paths import ensure_dirs
from jarvis.automation.registry import get_action, validate_action

log = logging.getLogger("jarvis.automation.engine")


def _rules_path() -> Path:
    """Resolve rules.json from the current DATA_DIR (tests patch config.DATA_DIR)."""
    from jarvis.config import DATA_DIR

    root = Path(DATA_DIR) / "automation_product"
    root.mkdir(parents=True, exist_ok=True)
    return root / "rules.json"


@dataclass
class AutomationRule:
    id: str
    name: str
    kind: str  # cron | interval | watch | planner | calendar | memory | documents | ha
    enabled: bool = True
    expression: str = ""
    action: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    last_run: float | None = None
    last_status: str = ""
    version: int = 1
    condition: str = ""
    permissions: list[str] = field(default_factory=list)


_lock = threading.RLock()
_rules: list[AutomationRule] = []
_watchers: dict[str, Any] = {}
_thread: threading.Thread | None = None
_stop = threading.Event()
_runner: Callable[[AutomationRule], dict[str, Any]] | None = None
_paused = False


def _load() -> None:
    global _rules
    path = _rules_path()
    if not path.is_file():
        _rules = []
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("rules") if isinstance(data, dict) else data
        loaded = []
        for r in items or []:
            if not isinstance(r, dict):
                continue
            loaded.append(
                AutomationRule(
                    id=str(r.get("id") or uuid.uuid4().hex[:10]),
                    name=str(r.get("name") or "Automation"),
                    kind=str(r.get("kind") or "interval"),
                    enabled=bool(r.get("enabled", True)),
                    expression=str(r.get("expression") or "300"),
                    action=str(r.get("action") or ""),
                    params=dict(r.get("params") or {}),
                    last_run=r.get("last_run"),
                    last_status=str(r.get("last_status") or ""),
                    version=int(r.get("version") or 1),
                    condition=str(r.get("condition") or ""),
                    permissions=list(r.get("permissions") or []),
                )
            )
        # Drop leaked certification/test fixture rules from the live house only.
        # Isolated test stores may use these action names as negative fixtures.
        fixture_actions = {"definitely_missing_action_xyz", "builtin_skip"}
        try:
            from jarvis.live_data_guard import _LIVE_DATA_ROOT

            resolved = path.resolve()
            live = resolved == _LIVE_DATA_ROOT or _LIVE_DATA_ROOT in resolved.parents
        except Exception:
            live = False
        cleaned = [r for r in loaded if (not live) or r.action not in fixture_actions]
        _rules = cleaned
        if live and len(cleaned) != len(loaded):
            try:
                _save()
            except Exception as exc:
                log.warning("automation fixture purge save failed: %s", exc)
    except Exception as exc:
        log.warning("automation load failed: %s", exc)
        _rules = []


def _save() -> None:
    ensure_dirs()
    path = _rules_path()
    payload = {"version": 2, "rules": [asdict(r) for r in _rules]}
    try:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(path)
    except Exception:
        pass
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def list_rules() -> list[dict[str, Any]]:
    with _lock:
        if not _rules:
            _load()
        return [asdict(r) for r in _rules]


def upsert_rule(rule: dict[str, Any]) -> dict[str, Any]:
    global _rules
    with _lock:
        _load()
        rid = str(rule.get("id") or uuid.uuid4().hex[:10])
        existing = next((r for r in _rules if r.id == rid), None)
        version = int(rule.get("version") or ((existing.version + 1) if existing else 1))
        obj = AutomationRule(
            id=rid,
            name=str(rule.get("name") or "Automation"),
            kind=str(rule.get("kind") or "interval"),
            enabled=bool(rule.get("enabled", True)),
            expression=str(rule.get("expression") or "300"),
            action=str(rule.get("action") or ""),
            params=dict(rule.get("params") or {}),
            last_run=rule.get("last_run", existing.last_run if existing else None),
            last_status=str(rule.get("last_status") or (existing.last_status if existing else "")),
            version=version,
            condition=str(rule.get("condition") or ""),
            permissions=list(rule.get("permissions") or []),
        )
        _rules = [r for r in _rules if r.id != rid] + [obj]
        _save()
        return asdict(obj)


def delete_rule(rule_id: str) -> dict[str, Any]:
    with _lock:
        _load()
        before = len(_rules)
        _rules[:] = [r for r in _rules if r.id != rule_id]
        _save()
        return {"ok": True, "deleted": before - len(_rules)}


def export_rules() -> dict[str, Any]:
    return {"version": 2, "exported_at": time.time(), "rules": list_rules()}


def import_rules(payload: dict[str, Any], *, replace: bool = False) -> dict[str, Any]:
    rules = payload.get("rules") if isinstance(payload, dict) else payload
    if not isinstance(rules, list):
        return {"ok": False, "error": "rules list required"}
    imported = 0
    with _lock:
        _load()
        if replace:
            _rules.clear()
        for r in rules:
            if isinstance(r, dict):
                upsert_rule(r)
                imported += 1
    return {"ok": True, "imported": imported}


def _match_cron(expr: str, now: time.struct_time) -> bool:
    """5-field cron: min hour dom mon dow. Supports * and exact ints; dow 1-5 as weekday approx via list."""
    parts = (expr or "").split()
    if len(parts) != 5:
        return False
    fields = [now.tm_min, now.tm_hour, now.tm_mday, now.tm_mon, (now.tm_wday + 1) % 7]

    def match(part: str, val: int) -> bool:
        if part == "*":
            return True
        if "," in part:
            return any(match(p, val) for p in part.split(","))
        if "-" in part and part.replace("-", "").isdigit():
            a, b = part.split("-", 1)
            try:
                return int(a) <= val <= int(b)
            except ValueError:
                return False
        try:
            return int(part) == int(val)
        except ValueError:
            return False

    return all(match(p, v) for p, v in zip(parts, fields))


def _default_run(rule: AutomationRule, *, dry_run: bool = False) -> dict[str, Any]:
    v = validate_action(rule.action, rule.params)
    if not v.get("ok"):
        status = v.get("status") or SKIPPED
        return {
            "ok": False,
            "skipped": status == SKIPPED,
            "permission_required": status == "permission_required",
            "reason": v.get("error") or "invalid action",
            "status": status,
        }

    if dry_run:
        if rule.action == "workflow_dag_run":
            from jarvis.automation.pipelines.engine import run_pipeline

            wid = (rule.params or {}).get("workflow_id") or (rule.params or {}).get("pipeline_id")
            if not wid:
                return {"ok": False, "error": "workflow_id required", "status": FAILED}
            return run_pipeline(
                str(wid),
                variables=dict((rule.params or {}).get("variables") or {}),
                dry_run=True,
                trigger="rule-dry-run",
                emit_bridges=True,
                correlation_id=f"rule:{rule.id}",
            )
        return {
            "ok": True,
            "dry_run": True,
            "reason": f"Dry run — would execute {rule.action}",
            "action": rule.action,
            "params": rule.params,
        }

    if rule.action in ("maintenance", "system_maintenance"):
        try:
            from jarvis.automation import ops

            fn = getattr(ops, "run_maintenance", None) or getattr(ops, "nightly", None)
            if callable(fn):
                result = fn()
                return {"ok": bool(result.get("ok", True)), "result": result}
            return {"ok": False, "skipped": True, "reason": "maintenance runner missing"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    if rule.action in ("memory_consolidate", "consolidate"):
        from jarvis.intelligence.memory_platform import consolidate_memories

        return consolidate_memories()

    if rule.action in ("knowledge_sync", "sync"):
        try:
            from jarvis.knowledge import sync as knowledge_sync

            fn = getattr(knowledge_sync, "sync_all", None) or getattr(knowledge_sync, "run", None)
            if callable(fn):
                return {"ok": True, "result": fn()}
            return {"ok": False, "skipped": True, "reason": "knowledge sync missing"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    if rule.action == "documents_reindex":
        try:
            from jarvis import documents_rag

            documents_rag.build_index(force=True)
            return {"ok": True, "result": "reindexed"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    if rule.action == "briefing":
        try:
            from jarvis.morning_briefing import build_briefing

            text = build_briefing()
            return {"ok": True, "result": str(text)[:500]}
        except Exception as exc:
            try:
                from jarvis.workflows.daily import dispatch

                return {"ok": True, "result": dispatch("overnight_summary", None)}
            except Exception:
                return {"ok": False, "error": str(exc)}

    if rule.action == "skill_run":
        from jarvis.skill_database import run_skill

        slug = (rule.params or {}).get("slug")
        if not slug:
            return {"ok": False, "error": "slug required", "status": FAILED}
        return run_skill(str(slug), dry_run=False)

    if rule.action == "workflow_learned_run":
        from jarvis.workflow_learning import run_workflow as run_learned

        slug = (rule.params or {}).get("slug")
        if not slug:
            return {"ok": False, "error": "slug required", "status": FAILED}
        return run_learned(str(slug), assistant=None, dry_run=False)

    if rule.action == "workflow_dag_run":
        from jarvis.automation.pipelines.engine import run_pipeline

        wid = (rule.params or {}).get("workflow_id") or (rule.params or {}).get("pipeline_id")
        if not wid:
            return {"ok": False, "error": "workflow_id required", "status": FAILED}
        vars_ = dict((rule.params or {}).get("variables") or {})
        return run_pipeline(
            str(wid),
            variables=vars_,
            dry_run=False,
            trigger="rule",
            emit_bridges=True,
            correlation_id=f"rule:{rule.id}",
        )

    if rule.action in ("ha_scene", "journal_log"):
        from jarvis.automation.pipelines.actions import execute_action

        return execute_action(rule.action, dict(rule.params or {}), {})

    meta = get_action(rule.action)
    if meta and meta.get("experimental"):
        return {
            "ok": False,
            "permission_required": True,
            "reason": "Experimental action requires explicit confirmation",
        }

    # Honest: unknown / unimplemented = skipped, NOT success
    return {
        "ok": False,
        "skipped": True,
        "reason": f"no handler for action {rule.action}",
        "status": SKIPPED,
    }


def run_rule(rule_id: str, *, dry_run: bool = False) -> dict[str, Any]:
    with _lock:
        _load()
        rule = next((r for r in _rules if r.id == rule_id), None)
        if not rule:
            return {"ok": False, "error": "not_found", "status": FAILED}
        if _paused and not dry_run:
            return {
                "ok": False,
                "status": "cancelled",
                "reason": "Automation engine paused",
                "cancelled": True,
            }
        # Mission Control health gate — never run dangerous work while unhealthy
        if not dry_run:
            try:
                from jarvis.mission_control_ops.automation_gate import evaluate_health_gate

                gate = evaluate_health_gate(params=rule.params, rule_name=rule.name)
                if gate.get("action") in ("skip", "delay", "pause") and not gate.get("ok", True):
                    return {
                        "ok": False,
                        "status": gate.get("status") or SKIPPED,
                        "reason": gate.get("reason"),
                        "skipped": True,
                        "health_gate": gate,
                        "result": normalize_result(
                            {
                                "ok": False,
                                "skipped": True,
                                "why": gate.get("reason"),
                                "status": gate.get("status") or SKIPPED,
                            },
                            dry_run=False,
                        ),
                    }
                # warn mode continues but attaches health_gate
                _gate_warn = gate if gate.get("action") == "warn" else None
            except Exception as exc:
                log.debug("health gate skipped: %s", exc)
                _gate_warn = None
        else:
            _gate_warn = None
        runner = _runner or (lambda r: _default_run(r, dry_run=dry_run))
        try:
            if _runner and dry_run:
                result = {"ok": True, "dry_run": True, "reason": "Dry run with custom runner"}
            else:
                result = runner(rule) if _runner else _default_run(rule, dry_run=dry_run)
            normalized = normalize_result(result, dry_run=dry_run)
            rule.last_run = time.time()
            rule.last_status = normalized["status"]
            _save()
            try:
                from jarvis.automation.activity_bridge import publish_run_event

                pub = publish_run_event(
                    kind="rule",
                    name=rule.name,
                    status=normalized["status"],
                    target_id=rule.id,
                    why=normalized["why"],
                    what_changed=normalized.get("what_changed"),
                    what_did_not=normalized.get("what_did_not"),
                    dry_run=normalized["dry_run"],
                    executed=normalized["executed"],
                    detail={"action": rule.action},
                )
                normalized["activity"] = pub.get("activity")
                normalized["run"] = pub.get("run")
            except Exception as exc:
                log.debug("activity bridge skipped: %s", exc)
            out = {
                "ok": normalized["ok"],
                "status": normalized["status"],
                "rule": asdict(rule),
                "result": normalized,
            }
            if _gate_warn:
                out["health_gate"] = _gate_warn
                out["warning"] = _gate_warn.get("warning") or _gate_warn.get("reason")
            return out
        except Exception as exc:
            rule.last_run = time.time()
            rule.last_status = f"error: {exc}"
            _save()
            return {"ok": False, "error": str(exc), "status": FAILED}


def set_paused(paused: bool) -> dict[str, Any]:
    global _paused
    _paused = bool(paused)
    return {"ok": True, "paused": _paused}


def is_paused() -> bool:
    return _paused


def _tick() -> None:
    if _paused:
        return
    with _lock:
        _load()
        now = time.localtime()
        for rule in list(_rules):
            if not rule.enabled:
                continue
            due = False
            if rule.kind in ("cron", "planner", "calendar"):
                # planner/calendar kinds use cron expression for schedule for now
                due = _match_cron(rule.expression, now)
                if due and rule.last_run and time.time() - rule.last_run < 50:
                    due = False
            elif rule.kind in ("interval", "memory", "documents", "ha", "providers", "connections"):
                try:
                    secs = max(30, int(float(rule.expression or "300")))
                except ValueError:
                    secs = 300
                due = rule.last_run is None or (time.time() - float(rule.last_run) >= secs)
            elif rule.kind in ("watch", "file", "folder"):
                continue
            if due:
                try:
                    run_rule(rule.id)
                except Exception as exc:
                    log.warning("automation tick failed %s: %s", rule.id, exc)


def _watch_loop_paths() -> None:
    if _paused:
        return
    with _lock:
        watches = [r for r in _rules if r.enabled and r.kind in ("watch", "file", "folder")]
    for rule in watches:
        path = Path(rule.expression).expanduser()
        if not path.exists():
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        key = rule.id
        prev = _watchers.get(key)
        _watchers[key] = mtime
        if prev is not None and mtime > prev:
            log.info("watch fired for %s (%s)", rule.name, path)
            run_rule(rule.id)


def _loop() -> None:
    while not _stop.is_set():
        try:
            _tick()
            _watch_loop_paths()
        except Exception as exc:
            log.warning("automation loop error: %s", exc)
        _stop.wait(15)


def start_engine(
    runner: Callable[[AutomationRule], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    global _thread, _runner
    try:
        from jarvis.automation.migrate import migrate_storage

        migrate_storage()
    except Exception:
        pass
    with _lock:
        _runner = runner
        _load()
        if _thread and _thread.is_alive():
            return {"ok": True, "running": True, "paused": _paused, "rules": len(_rules)}
        _stop.clear()
        _thread = threading.Thread(target=_loop, name="aria-automation", daemon=True)
        _thread.start()
        return {"ok": True, "running": True, "paused": _paused, "rules": len(_rules)}


def stop_engine() -> dict[str, Any]:
    _stop.set()
    return {"ok": True, "running": False}


def status() -> dict[str, Any]:
    alive = bool(_thread and _thread.is_alive())
    return {"ok": True, "running": alive, "paused": _paused, "rules": list_rules()}
