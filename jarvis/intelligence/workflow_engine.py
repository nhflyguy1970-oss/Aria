"""Reusable workflow DAG engine — steps, conditions, retries, logging."""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis.intelligence.workflow")

WORKFLOW_DIR = DATA_DIR / "workflows"


@dataclass
class WorkflowStep:
    id: str
    name: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    next: list[str] = field(default_factory=list)  # unconditional next
    on_success: list[str] = field(default_factory=list)
    on_failure: list[str] = field(default_factory=list)
    retries: int = 0
    retry_delay_sec: float = 0.5
    when: str = ""  # optional expression: "vars.x == true"


@dataclass
class WorkflowDef:
    id: str
    name: str
    version: int = 1
    steps: list[WorkflowStep] = field(default_factory=list)
    entry: str = ""
    variables: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


TEMPLATES: dict[str, dict[str, Any]] = {
    "morning_routine": {
        "name": "Morning Routine",
        "tags": ["daily"],
        "entry": "brief",
        "steps": [
            {"id": "brief", "name": "Briefing", "action": "builtin:log", "params": {"msg": "morning"}, "on_success": ["memory"]},
            {"id": "memory", "name": "Consolidate memory", "action": "memory_consolidate", "on_success": ["health"]},
            {"id": "health", "name": "Health check", "action": "builtin:log", "params": {"msg": "health ok"}},
        ],
    },
    "doc_ingest": {
        "name": "Document Ingest Pipeline",
        "tags": ["documents"],
        "entry": "index",
        "steps": [
            {"id": "index", "name": "Reindex documents", "action": "documents_reindex", "on_success": ["graph"]},
            {"id": "graph", "name": "Update knowledge graph", "action": "graph_ingest_note", "params": {"text": "Document library refreshed"}},
        ],
    },
}


def _step_from_dict(d: dict[str, Any]) -> WorkflowStep:
    return WorkflowStep(
        id=str(d["id"]),
        name=str(d.get("name") or d["id"]),
        action=str(d.get("action") or ""),
        params=dict(d.get("params") or {}),
        next=list(d.get("next") or []),
        on_success=list(d.get("on_success") or []),
        on_failure=list(d.get("on_failure") or []),
        retries=int(d.get("retries") or 0),
        retry_delay_sec=float(d.get("retry_delay_sec") or 0.5),
        when=str(d.get("when") or ""),
    )


def workflow_from_template(template_id: str, *, name: str | None = None) -> WorkflowDef:
    tpl = TEMPLATES.get(template_id)
    if not tpl:
        raise KeyError(template_id)
    wid = uuid.uuid4().hex[:10]
    steps = [_step_from_dict(s) for s in tpl["steps"]]
    return WorkflowDef(
        id=wid,
        name=name or str(tpl["name"]),
        steps=steps,
        entry=str(tpl.get("entry") or steps[0].id),
        tags=list(tpl.get("tags") or []),
    )


def save_workflow(wf: WorkflowDef) -> Path:
    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    path = WORKFLOW_DIR / f"{wf.id}.json"
    payload = {
        "id": wf.id,
        "name": wf.name,
        "version": wf.version,
        "entry": wf.entry,
        "variables": wf.variables,
        "tags": wf.tags,
        "steps": [asdict(s) for s in wf.steps],
    }
    try:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(path)
    except Exception:
        pass
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_workflow(workflow_id: str) -> WorkflowDef:
    path = WORKFLOW_DIR / f"{workflow_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return WorkflowDef(
        id=data["id"],
        name=data.get("name") or data["id"],
        version=int(data.get("version") or 1),
        entry=data.get("entry") or "",
        variables=dict(data.get("variables") or {}),
        tags=list(data.get("tags") or []),
        steps=[_step_from_dict(s) for s in data.get("steps") or []],
    )


def list_workflows() -> list[dict[str, Any]]:
    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for p in sorted(WORKFLOW_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            out.append(
                {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "version": data.get("version"),
                    "tags": data.get("tags") or [],
                    "path": str(p),
                }
            )
        except Exception:
            continue
    return out


def _eval_when(expr: str, variables: dict[str, Any]) -> bool:
    if not expr.strip():
        return True
    # Extremely small safe evaluator: "vars.key" truthiness or == comparisons
    e = expr.strip()
    if e.startswith("vars."):
        key = e[5:].split()[0]
        return bool(variables.get(key))
    if "==" in e:
        left, right = [x.strip() for x in e.split("==", 1)]
        lv = variables.get(left.replace("vars.", "")) if left.startswith("vars.") else left.strip("'\"")
        rv = right.strip().strip("'\"")
        if rv in ("true", "True"):
            rv = True
        if rv in ("false", "False"):
            rv = False
        return str(lv) == str(rv)
    return True


def _builtin(action: str, params: dict[str, Any], variables: dict[str, Any]) -> dict[str, Any]:
    if action == "builtin:log":
        msg = params.get("msg") or params.get("message") or ""
        log.info("workflow log: %s", msg)
        return {"ok": True, "message": str(msg)}
    if action == "builtin:set":
        for k, v in params.items():
            variables[k] = v
        return {"ok": True, "variables": dict(variables)}
    if action == "builtin:fail":
        return {"ok": False, "error": params.get("error") or "forced failure"}
    if action == "memory_consolidate":
        from jarvis.intelligence.memory_platform import consolidate_memories

        return consolidate_memories()
    if action == "documents_reindex":
        try:
            from jarvis import documents_rag

            documents_rag.build_index(force=True)
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
    if action == "graph_ingest_note":
        from jarvis.intelligence.knowledge_graph import ingest_text

        return ingest_text(
            str(params.get("text") or "workflow note"),
            namespace=str(params.get("namespace") or "default"),
            source="automation",
            confidence=0.6,
            explicit=True,
        )
    return {"ok": False, "error": f"unknown action {action}"}


def run_workflow(
    workflow_id: str,
    *,
    variables: dict[str, Any] | None = None,
    action_runner: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    wf = load_workflow(workflow_id)
    steps = {s.id: s for s in wf.steps}
    vars_ = dict(wf.variables)
    if variables:
        vars_.update(variables)
    current = wf.entry or (wf.steps[0].id if wf.steps else "")
    run_id = uuid.uuid4().hex[:12]
    log_rows: list[dict[str, Any]] = []
    visited: set[str] = set()
    started = time.time()

    while current:
        if current in visited:
            log_rows.append({"step": current, "ok": False, "error": "cycle detected"})
            break
        visited.add(current)
        step = steps.get(current)
        if not step:
            log_rows.append({"step": current, "ok": False, "error": "missing step"})
            break
        if not _eval_when(step.when, vars_):
            log_rows.append({"step": current, "ok": True, "skipped": True, "reason": "when"})
            nxt = (step.next or step.on_success or [None])[0]
            current = nxt
            continue

        attempt = 0
        result: dict[str, Any] = {"ok": False}
        while attempt <= step.retries:
            attempt += 1
            try:
                if action_runner and not step.action.startswith("builtin:"):
                    result = action_runner(step.action, {**step.params, **{"variables": vars_}})
                else:
                    result = _builtin(step.action, step.params, vars_)
            except Exception as exc:
                result = {"ok": False, "error": str(exc)}
            if result.get("ok"):
                break
            if attempt <= step.retries:
                time.sleep(step.retry_delay_sec)

        log_rows.append(
            {
                "step": step.id,
                "name": step.name,
                "ok": bool(result.get("ok")),
                "attempts": attempt,
                "result": {k: v for k, v in result.items() if k != "variables"},
            }
        )
        if result.get("ok"):
            nxt_list = step.on_success or step.next
        else:
            nxt_list = step.on_failure or []
            if not nxt_list:
                break
        current = nxt_list[0] if nxt_list else None

    ok = all(r.get("ok") or r.get("skipped") for r in log_rows) and bool(log_rows)
    return {
        "ok": ok,
        "run_id": run_id,
        "workflow_id": wf.id,
        "name": wf.name,
        "version": wf.version,
        "variables": vars_,
        "log": log_rows,
        "elapsed_ms": int((time.time() - started) * 1000),
    }
