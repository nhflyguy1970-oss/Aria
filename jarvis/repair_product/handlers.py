"""Chat/NL handlers for Guided Repair."""

from __future__ import annotations

from typing import Any


def _ok(payload: dict) -> dict:
    return payload


def repair_home(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.repair_product.engine import home_payload

    return _ok(home_payload())


def repair_scan(_assistant, _params: dict, _message: str) -> dict:
    from jarvis.repair_product.engine import scan_issues

    scan = scan_issues(force=True)
    issues = scan.get("issues") or []
    if not issues:
        return _ok({**scan, "message": "No repairable issues detected right now.\n\n_" + scan.get("disclaimer", "") + "_"})
    lines = ["**Guided Repair — issues found**", ""]
    for i in issues[:8]:
        conf = int(round(float(i.get("confidence") or 0) * 100))
        lines.append(f"• {i.get('title')} — {conf}% confidence — state={i.get('state')}")
    lines += ["", "Open Mission Control → Recovery to review plans, or say **repair <issue>**.", "", f"_{scan.get('disclaimer')}_"]
    return _ok({**scan, "message": "\n".join(lines), "open_view": "workstation"})


def repair_plan(_assistant, params: dict, message: str) -> dict:
    from jarvis.repair_product.engine import plan_from_event

    text = str(params.get("text") or message or "")
    return _ok(plan_from_event(text=text))
