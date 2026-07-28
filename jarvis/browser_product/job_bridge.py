"""Job Center bridge for long browser tasks."""

from __future__ import annotations

from typing import Any


def submit_browser_task(
    goal: str,
    *,
    url: str = "",
    mode: str = "auto",
    max_steps: int = 10,
    allow_risky: bool = False,
    assistant=None,
) -> dict[str, Any]:
    """Enqueue a browser agent run via coding-style job queue when available."""
    try:
        from jarvis.coding_jobs import submit

        def work():
            from jarvis import browser_agent as ba

            if url:
                nav = ba.navigate(url, allow_risky=allow_risky)
                if not nav.get("ok"):
                    return nav
            return ba.run_agent_task(
                goal, mode=mode, max_steps=max_steps, assistant=assistant
            )

        job_id = submit(f"Browser: {goal[:60]}", work)
        return {
            "ok": True,
            "pending": True,
            "job_id": job_id,
            "queue": "coding",  # shared worker pool; labeled Browser
            "message": "Browser task queued in Job Center",
            "deep_link": "jobs",
        }
    except Exception as exc:
        # Fail closed to sync path rather than fake queue success
        from jarvis import browser_agent as ba

        if url:
            nav = ba.navigate(url, allow_risky=allow_risky)
            if not nav.get("ok"):
                return nav
        result = ba.run_agent_task(goal, mode=mode, max_steps=max_steps, assistant=assistant)
        result["job_fallback"] = str(exc)
        return result
