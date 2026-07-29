"""Product bridges — Search retrieves; products own behavior."""

from __future__ import annotations

from typing import Any


def voice_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "bridge": "voice",
        "note": "Voice speaks queries into run_search; Search does not own STT/TTS.",
        "entry": "POST /api/search/product/query",
        "demo": "Say: search everything for warranty PDF",
    }


def vision_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "bridge": "vision",
        "note": "Vision may supply a text query or similarity hint; Gallery owns image similarity.",
        "experimental": "vision_similarity via Gallery product when opt-in gallery corpus is enabled.",
    }


def planner_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "bridge": "planner",
        "note": "Planner owns tasks; Search retrieves task titles/notes via planner facet.",
        "facet": "planner",
    }


def automation_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "bridge": "automation",
        "note": "Automation owns workflows; Search retrieves names/descriptions via automation facet.",
        "facet": "automation",
    }


def calendar_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "bridge": "calendar",
        "note": "Calendar owns schedule; Search retrieves work blocks and events via calendar facet.",
        "facet": "calendar",
    }


def documents_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "bridge": "documents",
        "note": "Documents owns library + RAG index; Search retrieves via documents facet.",
        "facet": "documents",
    }


def memory_bridge() -> dict[str, Any]:
    return {
        "ok": True,
        "bridge": "memory",
        "note": "Memory/ACM owns stores; Search retrieves via memory facet (always in default federation).",
        "facet": "memory",
    }
