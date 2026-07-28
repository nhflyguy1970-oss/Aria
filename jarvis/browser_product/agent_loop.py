"""DOM / VLM agent loop against the live Playwright page."""

from __future__ import annotations

import logging
from typing import Any, Callable

log = logging.getLogger("jarvis.browser.loop")


def run_loop(
    goal: str,
    *,
    mode: str = "auto",
    max_steps: int = 10,
    assistant=None,
    pause_check: Callable[[], bool] | None = None,
    on_step_screenshot: Callable[[str], dict] | None = None,
) -> dict[str, Any]:
    max_steps = max(1, min(int(max_steps or 10), 20))
    mode = (mode or "auto").lower()
    steps_out: list[dict[str, Any]] = []

    use_vlm = mode == "vlm"
    use_dom = mode in ("auto", "dom")

    for i in range(max_steps):
        if pause_check and pause_check():
            return {
                "ok": False,
                "message": "Stopped: agent paused or takeover active",
                "steps": steps_out,
                "paused": True,
                "recovery": "Click Resume to continue, or Stop to end",
            }

        action_result: dict[str, Any]
        if use_vlm or (mode == "auto" and i > 0 and not use_dom):
            action_result = _vlm_step(goal, assistant=assistant)
            if not action_result.get("ok") and use_dom:
                action_result = _dom_step(goal)
        else:
            action_result = _dom_step(goal)
            if not action_result.get("ok") and mode == "auto":
                action_result = _vlm_step(goal, assistant=assistant)

        steps_out.append({"step": i + 1, **action_result})
        if on_step_screenshot:
            try:
                on_step_screenshot(f"step{i+1}")
            except Exception:
                pass

        if action_result.get("done"):
            return {
                "ok": True,
                "message": action_result.get("summary") or f"Completed in {i+1} steps",
                "steps": steps_out,
            }
        if action_result.get("failed") or (
            not action_result.get("ok") and action_result.get("terminal")
        ):
            return {
                "ok": False,
                "message": action_result.get("reason")
                or action_result.get("message")
                or action_result.get("error")
                or "Agent failed",
                "steps": steps_out,
                "recovery": "Adjust the goal, Takeover manually, or try DOM-only mode",
            }
        if not action_result.get("ok"):
            # soft failure — continue unless last step
            if i == max_steps - 1:
                return {
                    "ok": False,
                    "message": action_result.get("message")
                    or action_result.get("error")
                    or "Agent could not complete the goal",
                    "steps": steps_out,
                    "recovery": "Try a clearer goal or Takeover",
                }

    return {
        "ok": False,
        "message": f"Reached max steps ({max_steps}) without done",
        "steps": steps_out,
        "recovery": "Increase max_steps or refine the goal",
    }


def _dom_step(goal: str) -> dict[str, Any]:
    from jarvis.browser_dom_agent import dom_plan_step, execute_dom_action, get_page_snapshot

    snap = get_page_snapshot()
    if not snap.get("ok"):
        return {
            "ok": False,
            "error": snap.get("error") or "No snapshot",
            "terminal": True,
            "mode": "dom",
        }
    plan = dom_plan_step(goal, snap)
    if not plan.get("ok"):
        return {"ok": False, "error": plan.get("error") or "DOM plan failed", "mode": "dom"}
    action = plan.get("action") or {}
    executed = execute_dom_action(action)
    executed["mode"] = "dom"
    executed["action"] = action
    if executed.get("done") or executed.get("failed"):
        return executed
    return executed


def _vlm_step(goal: str, *, assistant=None) -> dict[str, Any]:
    from jarvis.browser_product.screenshots import capture
    from jarvis.browser_vlm import vlm_click_at, vlm_plan_click

    shot = capture(label="vlm", reason="vlm_plan")
    if not shot.get("ok"):
        return {"ok": False, "error": shot.get("error") or "Screenshot required for VLM", "mode": "vlm"}
    plan = vlm_plan_click(shot["path"], goal, assistant=assistant)
    if not plan.get("ok"):
        return {"ok": False, "error": plan.get("error") or "VLM plan failed", "mode": "vlm"}
    action = plan.get("plan") or {}
    kind = (action.get("action") or "").lower()
    if kind == "done":
        return {"ok": True, "done": True, "summary": action.get("summary") or "", "mode": "vlm"}
    if kind == "fail":
        return {"ok": False, "failed": True, "reason": action.get("reason") or "", "mode": "vlm"}
    if kind == "click":
        try:
            x, y = int(action["x"]), int(action["y"])
        except Exception:
            return {"ok": False, "error": "VLM click missing coordinates", "mode": "vlm"}
        clicked = vlm_click_at(x, y)
        clicked["mode"] = "vlm"
        clicked["action"] = action
        return clicked
    return {"ok": False, "error": f"Unknown VLM action: {kind}", "mode": "vlm"}
