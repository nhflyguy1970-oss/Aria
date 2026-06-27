"""Git REST API routes (GUI sidebar / tooling)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

    from jarvis.assistant import JarvisAssistant


def register_routes(app: FastAPI, assistant: JarvisAssistant) -> None:
    from jarvis import git_util

    @app.get("/api/git/status")
    def git_status_api():
        return {"status": git_util.status()}

    @app.get("/api/git/diff")
    def git_diff_api(file: str = ""):
        return {"diff": git_util.diff(file=file or None)}

    @app.get("/api/git/log")
    def git_log_api(limit: int = 10):
        return {"log": git_util.log_oneline(limit=limit)}
