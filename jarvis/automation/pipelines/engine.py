"""Pipeline DAG execution engine — registry actions, dry-run, timeouts, retries."""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections.abc import Callable
from typing import Any

from jarvis.automation.pipelines.actions import describe_action, execute_action
from jarvis.automation.pipelines.storage import get_pipeline, record_usage

log = logging.getLogger("jarvis.automation.pipelines.engine")


def _eval_when(expr: str, variables: dict[str, Any]) -> bool:
    if not (expr or "").strip():
        return True
    e = expr.strip()
    if e.startswith("vars."):
        key = e[5:].split()[0]
        return bool(variables.get(key))
    if "==" in e:
        left, right = [x.strip() for x in e.split("==", 1)]
        lv = (
            variables.get(left.replace("vars.", ""))
            if left.startswith("vars.")
            else left.strip("'\"")
        )
        rv = right.strip().strip("'\"")
        if rv in ("true", "True"):
            rv = True
        if rv in ("false", "False"):
            rv = False
        return str(lv) == str(rv)
    return True


def explain_pipeline(pipeline_id: str) -> dict[str, Any]:
    wf = get_pipeline(pipeline_id)
    if not wf:
        return {"ok": False, "error": "not_found"}
    steps_out = []
    for s in wf.get("steps") or []:
        meta = describe_action(str(s.get("action") or ""))
        steps_out.append(
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "action": s.get("action"),
                "when": s.get("when") or "",
                "retries": s.get("retries") or 0,
                "timeout_sec": s.get("timeout_sec"),
                "on_success": s.get("on_success") or [],
                "on_failure": s.get("on_failure") or [],
                "action_meta": {
                    "name": meta.get("name"),
                    "description": meta.get("description"),
                    "permissions": meta.get("permissions"),
                    "ai_explain": meta.get("ai_explain"),
                    "estimated_duration_sec": meta.get("estimated_duration_sec"),
                    "confirmation": meta.get("confirmation"),
                    "experimental": meta.get("experimental"),
                },
            }
        )
    return {
        "ok": True,
        "id": wf["id"],
        "name": wf["name"],
        "version": wf.get("version"),
        "description": wf.get("description") or "",
        "documentation": wf.get("documentation") or "",
        "tags": wf.get("tags") or [],
        "entry": wf.get("entry"),
        "variables": wf.get("variables") or {},
        "steps": steps_out,
        "summary": (
            f"Pipeline **{wf['name']}** has {len(steps_out)} steps starting at `{wf.get('entry')}`. "
            f"{wf.get('description') or ''}"
        ).strip(),
    }


def validate_pipeline(wf: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    steps = {s["id"]: s for s in (wf.get("steps") or []) if s.get("id")}
    if not steps:
        errors.append("Pipeline has no steps")
    entry = wf.get("entry")
    if entry and entry not in steps:
        errors.append(f"Entry step '{entry}' missing")
    for sid, s in steps.items():
        if not s.get("action"):
            errors.append(f"Step {sid} has no action")
        for edge in ("next", "on_success", "on_failure"):
            for nxt in s.get(edge) or []:
                if nxt not in steps:
                    warnings.append(f"Step {sid} {edge} → missing '{nxt}'")
        meta = describe_action(str(s.get("action") or ""))
        if meta.get("unknown"):
            errors.append(f"Step {sid}: unknown action {s.get('action')}")
        if meta.get("experimental"):
            warnings.append(f"Step {sid}: experimental action {s.get('action')}")
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def run_pipeline(
    pipeline_id: str,
    *,
    variables: dict[str, Any] | None = None,
    dry_run: bool = False,
    approve_experimental: bool = False,
    from_step: str | None = None,
    emit_bridges: bool = True,
    trigger: str = "manual",
    correlation_id: str | None = None,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    wf = get_pipeline(pipeline_id)
    if not wf:
        return {"ok": False, "error": "not_found", "status": "failed"}

    validation = validate_pipeline(wf)
    if not validation["ok"] and not dry_run:
        return {
            "ok": False,
            "error": "; ".join(validation["errors"]),
            "status": "failed",
            "validation": validation,
        }

    steps = {s["id"]: s for s in wf["steps"]}
    vars_ = dict(wf.get("variables") or {})
    if variables:
        vars_.update(variables)

    run_id = uuid.uuid4().hex[:12]
    correlation_id = correlation_id or uuid.uuid4().hex[:12]
    log_rows: list[dict[str, Any]] = []
    visited: set[str] = set()
    started = time.time()
    current = from_step or wf.get("entry") or (wf["steps"][0]["id"] if wf["steps"] else "")
    status = "running"
    job_id = None
    cancelled = False

    if emit_bridges:
        try:
            from jarvis.automation.pipelines.jobs import start_job

            job_id = start_job(
                run_id=run_id,
                pipeline_id=pipeline_id,
                name=wf["name"],
                dry_run=dry_run,
                correlation_id=correlation_id,
            )
        except Exception as exc:
            log.debug("job bridge: %s", exc)

    def progress(payload: dict[str, Any]) -> None:
        if on_progress:
            try:
                on_progress(payload)
            except Exception:
                pass
        if job_id:
            try:
                from jarvis.automation.pipelines.jobs import update_job

                update_job(job_id, **payload)
            except Exception:
                pass

    progress(
        {
            "status": "running" if not dry_run else "dry_run",
            "pct": 0,
            "message": f"{'Dry-run' if dry_run else 'Running'} {wf['name']}",
            "current_step": current,
        }
    )

    total = max(1, len(steps))
    while current:
        if cancel_check and cancel_check():
            cancelled = True
            status = "cancelled"
            log_rows.append({"step": current, "ok": False, "cancelled": True, "error": "cancelled"})
            break
        if current in visited:
            log_rows.append({"step": current, "ok": False, "error": "cycle detected"})
            status = "failed"
            break
        visited.add(current)
        step = steps.get(current)
        if not step:
            log_rows.append({"step": current, "ok": False, "error": "missing step"})
            status = "failed"
            break

        progress(
            {
                "status": "running" if not dry_run else "dry_run",
                "pct": int(100 * len(visited) / total),
                "message": f"Step: {step.get('name') or current}",
                "current_step": current,
                "log_len": len(log_rows),
            }
        )

        if not _eval_when(str(step.get("when") or ""), vars_):
            log_rows.append(
                {
                    "step": step["id"],
                    "name": step.get("name"),
                    "ok": True,
                    "skipped": True,
                    "reason": "when",
                    "action": step.get("action"),
                }
            )
            nxt = (step.get("next") or step.get("on_success") or [None])[0]
            current = nxt
            continue

        attempt = 0
        result: dict[str, Any] = {"ok": False}
        timeout = step.get("timeout_sec")
        max_attempts = int(step.get("retries") or 0) + 1

        while attempt < max_attempts:
            attempt += 1
            try:
                if timeout and float(timeout) > 0 and not dry_run:
                    result = _run_with_timeout(
                        lambda: execute_action(
                            str(step["action"]),
                            dict(step.get("params") or {}),
                            vars_,
                            dry_run=dry_run,
                            approve_experimental=approve_experimental,
                        ),
                        float(timeout),
                    )
                else:
                    result = execute_action(
                        str(step["action"]),
                        dict(step.get("params") or {}),
                        vars_,
                        dry_run=dry_run,
                        approve_experimental=approve_experimental,
                    )
            except Exception as exc:
                result = {"ok": False, "error": str(exc)}

            if result.get("ok") or result.get("dry_run"):
                break
            if result.get("permission_required"):
                break
            if attempt < max_attempts:
                time.sleep(float(step.get("retry_delay_sec") or 0.5))
                log_rows.append(
                    {
                        "step": step["id"],
                        "name": step.get("name"),
                        "ok": False,
                        "retry": True,
                        "attempt": attempt,
                        "error": result.get("error"),
                    }
                )

        row = {
            "step": step["id"],
            "name": step.get("name"),
            "action": step.get("action"),
            "ok": bool(result.get("ok") or result.get("dry_run")),
            "attempts": attempt,
            "dry_run": bool(dry_run or result.get("dry_run")),
            "skipped": bool(result.get("skipped")),
            "permission_required": bool(result.get("permission_required")),
            "result": {k: v for k, v in result.items() if k not in ("variables",)},
            "timeout_sec": timeout,
        }
        if result.get("error"):
            row["error"] = result.get("error")
        log_rows.append(row)

        if result.get("permission_required"):
            status = "permission_required"
            break

        if row["ok"]:
            nxt_list = step.get("on_success") or step.get("next") or []
        else:
            nxt_list = step.get("on_failure") or []
            if not nxt_list:
                status = "failed"
                break
        current = nxt_list[0] if nxt_list else None

    elapsed_ms = int((time.time() - started) * 1000)
    if cancelled:
        status = "cancelled"
    elif status in ("permission_required", "failed"):
        pass  # keep status set in loop
    elif status == "running":
        failed_rows = [
            r for r in log_rows if not r.get("ok") and not r.get("skipped") and not r.get("retry")
        ]
        if dry_run:
            status = "dry_run"
        elif not failed_rows:
            status = "succeeded"
        elif current is None:
            # Walk finished (including via on_failure edges)
            status = "partial_success"
        else:
            status = "failed"

    ok = status in ("succeeded", "dry_run", "partial_success")
    payload = {
        "ok": ok,
        "status": status,
        "run_id": run_id,
        "correlation_id": correlation_id,
        "workflow_id": wf["id"],
        "pipeline_id": wf["id"],
        "name": wf["name"],
        "version": wf.get("version"),
        "variables": vars_,
        "log": log_rows,
        "elapsed_ms": elapsed_ms,
        "dry_run": dry_run,
        "trigger": trigger,
        "job_id": job_id,
        "validation": validation,
        "from_step": from_step,
        "success_summary": _summarize(log_rows, ok=True),
        "failure_summary": _summarize(log_rows, ok=False),
    }

    # Persist run history
    try:
        from jarvis.automation.pipelines.runs import record_pipeline_run

        record_pipeline_run(payload)
    except Exception as exc:
        log.debug("run history: %s", exc)

    if not dry_run and status == "succeeded":
        try:
            record_usage(pipeline_id)
        except Exception:
            pass

    if emit_bridges:
        try:
            from jarvis.automation.activity_bridge import publish_run_event

            pub = publish_run_event(
                kind="workflow_dag",
                name=wf["name"],
                status=status,
                target_id=wf["id"],
                why=payload.get("failure_summary") or payload.get("success_summary") or status,
                what_changed=payload.get("success_summary") if ok else None,
                what_did_not=payload.get("failure_summary") if not ok else None,
                dry_run=dry_run,
                executed=not dry_run and status not in ("cancelled", "permission_required"),
                detail={
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "job_id": job_id,
                    "elapsed_ms": elapsed_ms,
                    "deep_link_run": f"automation:pipeline-run:{run_id}",
                },
            )
            payload["activity"] = pub.get("activity")
            payload["history_run"] = pub.get("run")
            if payload.get("activity") and isinstance(payload["activity"], dict):
                meta = payload["activity"].setdefault("metadata", {})
                meta["pipelineRunId"] = run_id
                meta["jobId"] = job_id
                meta["correlationId"] = correlation_id
                payload["activity"]["deepLink"] = "automation"
        except Exception as exc:
            log.debug("activity: %s", exc)

        if job_id:
            try:
                from jarvis.automation.pipelines.jobs import finish_job

                finish_job(job_id, status=status, result=payload)
            except Exception:
                pass

    progress(
        {
            "status": status,
            "pct": 100 if status != "running" else 99,
            "message": status,
            "done": True,
        }
    )
    return payload


def _summarize(log_rows: list[dict[str, Any]], *, ok: bool) -> str:
    parts = []
    for r in log_rows:
        is_ok = bool(r.get("ok") or r.get("skipped"))
        if ok and is_ok:
            parts.append(
                f"{r.get('name') or r.get('step')}: ok" + (" (skipped)" if r.get("skipped") else "")
            )
        if not ok and not is_ok:
            parts.append(f"{r.get('name') or r.get('step')}: {r.get('error') or 'failed'}")
    return "; ".join(parts[:12])


def _run_with_timeout(fn: Callable[[], dict[str, Any]], timeout_sec: float) -> dict[str, Any]:
    box: dict[str, Any] = {}

    def target():
        try:
            box["result"] = fn()
        except Exception as exc:
            box["result"] = {"ok": False, "error": str(exc)}

    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join(timeout=timeout_sec)
    if t.is_alive():
        return {"ok": False, "timeout": True, "error": f"step timed out after {timeout_sec}s"}
    return box.get("result") or {"ok": False, "error": "no result"}
