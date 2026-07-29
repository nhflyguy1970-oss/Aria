"""First-class tying sessions."""

from __future__ import annotations

import json
import time
import uuid
from copy import deepcopy
from typing import Any

from jarvis.config import DATA_DIR

SESSIONS_FILE = DATA_DIR / "flytying_product" / "sessions.json"

_STATUSES = ("active", "paused", "completed")


def _empty_store() -> dict[str, Any]:
    return {"sessions": [], "active_id": ""}


def _load() -> dict[str, Any]:
    if SESSIONS_FILE.is_file():
        try:
            data = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data.setdefault("sessions", [])
                data.setdefault("active_id", "")
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return _empty_store()


def _save(store: dict[str, Any]) -> None:
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_FILE.write_text(json.dumps(store, indent=2), encoding="utf-8")


def _find(store: dict[str, Any], session_id: str) -> dict[str, Any] | None:
    for s in store.get("sessions") or []:
        if isinstance(s, dict) and s.get("id") == session_id:
            return s
    return None


def list_sessions(*, limit: int = 50) -> list[dict[str, Any]]:
    store = _load()
    rows = [deepcopy(s) for s in (store.get("sessions") or []) if isinstance(s, dict)]
    rows.reverse()
    return rows[: max(1, min(limit, 200))]


def get_session(session_id: str = "") -> dict[str, Any] | None:
    store = _load()
    sid = (session_id or store.get("active_id") or "").strip()
    if not sid:
        return None
    row = _find(store, sid)
    return deepcopy(row) if row else None


def active_session() -> dict[str, Any] | None:
    return get_session("")


def start_session(
    *,
    recipe_id: str = "",
    recipe_name: str = "",
    notes: str = "",
    materials_checklist: list[Any] | None = None,
) -> dict[str, Any]:
    store = _load()
    # Pause any other active session
    for s in store.get("sessions") or []:
        if isinstance(s, dict) and s.get("status") == "active":
            s["status"] = "paused"
            s["updated_at"] = time.time()

    steps: list[str] = []
    mats_check = list(materials_checklist or [])
    rid = (recipe_id or "").strip()
    rname = (recipe_name or "").strip()
    if rid or rname:
        try:
            from jarvis.flytying import bridge

            row = bridge.get_recipe(rid or rname)
            if row:
                rname = rname or str(row.get("name") or row.get("fly_name") or "")
                rid = rid or str(row.get("recipe_id") or row.get("id") or "")
                raw_steps = row.get("steps") or []
                steps = [str(s) for s in raw_steps if str(s).strip()]
                if not mats_check:
                    mats_check = [{"text": str(m), "done": False} for m in (row.get("materials") or [])[:40]]
        except Exception:
            pass

    session = {
        "id": uuid.uuid4().hex[:12],
        "status": "active",
        "recipe_id": rid,
        "recipe_name": rname,
        "step_idx": 0,
        "steps": steps,
        "notes": notes or "",
        "timer_started": time.time(),
        "timer_paused_total": 0.0,
        "paused_at": None,
        "materials_checklist": mats_check,
        "photos": [],
        "mistakes": [],
        "created_at": time.time(),
        "updated_at": time.time(),
        "completed_at": None,
    }
    sessions = list(store.get("sessions") or [])
    sessions.append(session)
    store["sessions"] = sessions
    store["active_id"] = session["id"]
    _save(store)
    try:
        from jarvis.flytying_product.history import add_entry
        from jarvis.config import is_uncensored

        add_entry(
            {
                "kind": "session",
                "session_id": session["id"],
                "recipe_id": session["recipe_id"],
                "recipe_name": session["recipe_name"],
                "summary": f"Started session: {session['recipe_name'] or session['recipe_id'] or 'untitled'}",
                "source": "sessions",
                "uncensored_origin": bool(is_uncensored()),
            }
        )
    except Exception:
        pass
    try:
        from jarvis.flytying_product.status_bus import set_flytying_state

        set_flytying_state("session", detail=session.get("recipe_name") or session["id"])
    except Exception:
        pass
    return deepcopy(session)


def _mutate(session_id: str, mutator) -> dict[str, Any]:
    store = _load()
    sid = (session_id or store.get("active_id") or "").strip()
    row = _find(store, sid) if sid else None
    if not row:
        raise ValueError("session_not_found")
    mutator(row)
    row["updated_at"] = time.time()
    store["active_id"] = row["id"] if row.get("status") != "completed" else (store.get("active_id") or "")
    if row.get("status") == "completed" and store.get("active_id") == row["id"]:
        store["active_id"] = ""
    _save(store)
    return deepcopy(row)


def pause_session(session_id: str = "") -> dict[str, Any]:
    def _m(row: dict[str, Any]) -> None:
        if row.get("status") != "active":
            return
        row["status"] = "paused"
        row["paused_at"] = time.time()

    out = _mutate(session_id, _m)
    try:
        from jarvis.flytying_product.status_bus import set_flytying_state

        set_flytying_state("idle", detail="session_paused")
    except Exception:
        pass
    return out


def resume_session(session_id: str = "") -> dict[str, Any]:
    def _m(row: dict[str, Any]) -> None:
        if row.get("status") == "completed":
            return
        paused_at = row.get("paused_at")
        if paused_at:
            try:
                row["timer_paused_total"] = float(row.get("timer_paused_total") or 0) + (
                    time.time() - float(paused_at)
                )
            except (TypeError, ValueError):
                pass
        row["paused_at"] = None
        row["status"] = "active"
        if not row.get("timer_started"):
            row["timer_started"] = time.time()

    out = _mutate(session_id, _m)
    store = _load()
    store["active_id"] = out["id"]
    # Ensure only one active
    for s in store.get("sessions") or []:
        if isinstance(s, dict) and s.get("id") != out["id"] and s.get("status") == "active":
            s["status"] = "paused"
    _save(store)
    try:
        from jarvis.flytying_product.status_bus import set_flytying_state

        set_flytying_state("session", detail=out.get("recipe_name") or out["id"])
    except Exception:
        pass
    return get_session(out["id"]) or out


def next_step(session_id: str = "", *, max_steps: int | None = None) -> dict[str, Any]:
    def _m(row: dict[str, Any]) -> None:
        steps = row.get("steps") or []
        limit = max_steps if max_steps is not None else len(steps)
        idx = int(row.get("step_idx") or 0) + 1
        if limit:
            idx = min(idx, max(0, int(limit) - 1))
        row["step_idx"] = max(0, idx)

    out = _mutate(session_id, _m)
    return _with_step_text(out)


def prev_step(session_id: str = "") -> dict[str, Any]:
    def _m(row: dict[str, Any]) -> None:
        row["step_idx"] = max(0, int(row.get("step_idx") or 0) - 1)

    out = _mutate(session_id, _m)
    return _with_step_text(out)


def _with_step_text(session: dict[str, Any]) -> dict[str, Any]:
    steps = session.get("steps") or []
    idx = int(session.get("step_idx") or 0)
    text = str(steps[idx]) if 0 <= idx < len(steps) else ""
    session = dict(session)
    session["step_text"] = text
    session["message"] = text or f"Step {idx + 1}"
    session["ok"] = True
    return session


def update_session(session_id: str = "", patch: dict[str, Any] | None = None) -> dict[str, Any]:
    patch = dict(patch or {})

    def _m(row: dict[str, Any]) -> None:
        for key in (
            "recipe_id",
            "recipe_name",
            "notes",
            "materials_checklist",
            "photos",
            "mistakes",
            "step_idx",
        ):
            if key in patch and patch[key] is not None:
                row[key] = patch[key]
        if "add_photo" in patch and patch["add_photo"]:
            photos = list(row.get("photos") or [])
            photos.append(patch["add_photo"])
            row["photos"] = photos
        if "add_mistake" in patch and patch["add_mistake"]:
            mistakes = list(row.get("mistakes") or [])
            mistakes.append(patch["add_mistake"])
            row["mistakes"] = mistakes

    return _mutate(session_id, _m)


def complete_session(session_id: str = "") -> dict[str, Any]:
    def _m(row: dict[str, Any]) -> None:
        row["status"] = "completed"
        row["completed_at"] = time.time()
        row["paused_at"] = None

    out = _mutate(session_id, _m)
    try:
        from jarvis.flytying_product.history import add_entry
        from jarvis.config import is_uncensored

        add_entry(
            {
                "kind": "session",
                "session_id": out["id"],
                "recipe_id": out.get("recipe_id") or "",
                "recipe_name": out.get("recipe_name") or "",
                "summary": f"Completed session: {out.get('recipe_name') or out.get('recipe_id') or out['id']}",
                "detail": out.get("notes") or "",
                "source": "sessions",
                "uncensored_origin": bool(is_uncensored()),
                "meta": {"step_idx": out.get("step_idx"), "mistakes": out.get("mistakes") or []},
            }
        )
    except Exception:
        pass
    try:
        from jarvis.flytying_product.status_bus import set_flytying_state

        set_flytying_state("idle", detail="session_completed")
    except Exception:
        pass
    return out
