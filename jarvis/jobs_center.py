"""Unified view of background work across media, coding, audio, and ComfyUI settings."""

from __future__ import annotations

import time
from typing import Any


def _sanitize_job(job: dict, *, queue: str) -> dict:
    from pathlib import Path

    out = {
        "id": job.get("id"),
        "queue": queue,
        "label": job.get("label") or job.get("kind") or queue,
        "pct": job.get("pct", 0),
        "message": job.get("message", ""),
        "done": bool(job.get("done")),
        "error": job.get("error") or "",
        "started": job.get("started", 0),
        "cancelled": bool(job.get("cancelled")),
    }
    if job.get("kind"):
        out["kind"] = job["kind"]
    if job.get("done") and job.get("result"):
        res = job["result"]
        if isinstance(res, dict):
            out["result_ok"] = res.get("ok")
            out["ok"] = res.get("ok")
            out["result_message"] = (res.get("message") or "")[:200]
            if res.get("proposal_id"):
                out["proposal_id"] = res["proposal_id"]
            if res.get("type"):
                out["result_type"] = res["type"]
            # Outcome fields required for Chat/Gallery to show the real asset
            for key in (
                "image_path",
                "image_name",
                "output_path",
                "image_paths",
                "video_path",
                "audio_path",
            ):
                if res.get(key):
                    out[key] = res[key]
                    out.setdefault("result", {})
                    if isinstance(out["result"], dict):
                        out["result"][key] = res[key]
            # Consistency: never advertise Complete when the asset file is gone
            asset_paths = []
            for key in ("image_path", "video_path", "audio_path", "output_path"):
                p = res.get(key) or out.get(key)
                if p:
                    asset_paths.append(str(p))
            iname = res.get("image_name") or out.get("image_name")
            if iname and not asset_paths:
                from jarvis.config import DATA_DIR

                asset_paths.append(str(DATA_DIR / "generated" / Path(str(iname)).name))
            missing = False
            for p in asset_paths:
                try:
                    if not Path(p).is_file():
                        missing = True
                        break
                except Exception:
                    missing = True
                    break
            if missing and queue == "media" and res.get("ok"):
                out["result_ok"] = False
                out["ok"] = False
                out["asset_missing"] = True
                msg = (
                    f"Asset missing on disk ({Path(asset_paths[0]).name if asset_paths else 'unknown'}). "
                    "Not shown as Complete."
                )
                out["error"] = msg
                out["message"] = msg
                out["result_message"] = msg
            elif res.get("ok") and res.get("image_path") and not missing:
                out["result"] = {
                    "ok": True,
                    "message": out.get("result_message") or res.get("message") or "",
                    "type": res.get("type") or "image_result",
                    "image_path": res.get("image_path"),
                    "image_name": res.get("image_name"),
                    "output_path": res.get("output_path") or res.get("image_path"),
                    "module": res.get("module") or "image",
                }
    if queue == "coding":
        try:
            from jarvis.coding_product.job_links import enrich_coding_job

            enriched = enrich_coding_job({**job, **out})
            out["deep_links"] = enriched.get("deep_links")
            if enriched.get("proposal_id"):
                out["proposal_id"] = enriched["proposal_id"]
        except Exception:
            pass
    return out


def snapshot(*, recent_limit: int = 12) -> dict[str, Any]:
    from jarvis.coding_jobs import job_stats as coding_stats
    from jarvis.coding_jobs import list_recent as coding_recent
    from jarvis.media_jobs import busy_state
    from jarvis.media_jobs import job_stats as media_stats
    from jarvis.media_jobs import list_recent as media_recent

    media = media_stats()
    coding = coding_stats()
    audio: dict[str, Any] = {"busy": False, "active_count": 0}
    try:
        from jarvis.audio_progress import job_stats as audio_stats

        audio = audio_stats()
    except Exception:
        pass

    comfy: dict[str, Any] = {}
    try:
        from jarvis.metrics import snapshot as metrics_snap

        comfy = metrics_snap().get("comfyui_settings_jobs") or {}
    except Exception:
        pass

    recent: list[dict] = []
    for job in media_recent(recent_limit):
        recent.append(_sanitize_job(job, queue="media"))
    for job in coding_recent(recent_limit):
        recent.append(_sanitize_job(job, queue="coding"))
    try:
        from jarvis.audio_progress import list_recent as audio_recent

        for job in audio_recent(recent_limit):
            recent.append(_sanitize_job(job, queue="audio"))
    except Exception:
        pass

    recent.sort(key=lambda j: j.get("started") or 0, reverse=True)
    recent = recent[:recent_limit]

    agent_jobs: list[dict] = []
    agent_busy = False
    try:
        from jarvis.jobs.checkpointed import list_jobs

        for job in list_jobs()[:5]:
            done = job.status in ("completed", "failed", "cancelled")
            if not done:
                agent_busy = True
            agent_jobs.append(
                {
                    "id": job.id,
                    "queue": "agent",
                    "label": job.goal[:80],
                    "pct": int(job.progress * 100),
                    "message": job.message,
                    "done": done,
                    "error": job.message if job.status == "failed" else "",
                    "started": job.created_at,
                    "kind": job.kind,
                    "status": job.status,
                    "run_id": (job.checkpoint or {}).get("run_id"),
                }
            )
            recent.append(agent_jobs[-1])
    except Exception:
        pass

    specialist_jobs: list[dict] = []
    specialist_busy = False
    try:
        from jarvis.specialists.jobs import busy as team_busy
        from jarvis.specialists.jobs import list_jobs as list_team_jobs

        specialist_busy = bool(team_busy())
        for job in list_team_jobs(limit=8):
            row = {
                "id": job.get("id"),
                "queue": "specialists",
                "label": job.get("label") or "Specialist Team",
                "pct": job.get("pct", 0),
                "message": job.get("message") or "",
                "done": bool(job.get("done")),
                "error": job.get("error") or "",
                "started": job.get("started", 0),
                "kind": "specialist_team",
                "status": job.get("status"),
                "run_id": job.get("run_id"),
                "cancelled": bool(job.get("cancelled")),
            }
            specialist_jobs.append(row)
            recent.append(row)
    except Exception:
        pass

    automation_jobs: list[dict] = []
    automation_busy = False
    try:
        from jarvis.automation.pipelines.jobs import busy as pipe_busy
        from jarvis.automation.pipelines.jobs import list_jobs as list_pipe_jobs

        automation_busy = bool(pipe_busy())
        for job in list_pipe_jobs(limit=8):
            row = {
                "id": job.get("id"),
                "queue": "automation",
                "label": job.get("label") or "Pipeline",
                "pct": job.get("pct", 0),
                "message": job.get("message") or "",
                "done": bool(job.get("done")),
                "error": job.get("error") or "",
                "started": job.get("started", 0),
                "kind": "pipeline",
                "status": job.get("status"),
                "pipeline_id": job.get("pipeline_id"),
                "run_id": job.get("run_id"),
                "cancelled": bool(job.get("cancelled")),
            }
            automation_jobs.append(row)
            recent.append(row)
    except Exception:
        pass

    any_busy = bool(
        media.get("busy")
        or media.get("pending", 0) > 0
        or coding.get("busy")
        or coding.get("pending", 0) > 0
        or audio.get("busy")
        or audio.get("active_count", 0) > 0
        or automation_busy
        or agent_busy
        or specialist_busy
    )

    recent.sort(key=lambda j: j.get("started") or 0, reverse=True)

    return {
        "ok": True,
        "ts": time.time(),
        "any_busy": any_busy,
        "media": {**busy_state(), **media},
        "coding": coding,
        "audio": audio,
        "comfyui_settings_jobs": comfy,
        "agent_jobs": agent_jobs,
        "specialist_jobs": specialist_jobs,
        "automation_jobs": automation_jobs,
        "recent": recent[:recent_limit],
    }
