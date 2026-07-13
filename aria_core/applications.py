"""Aria Core — Applications (delegates to ApplicationHost)."""

from __future__ import annotations

from typing import Any

from aria_core.ownership import module_ownership

OWNER = module_ownership("applications")


def get_host_module() -> Any:
    from jarvis.application import host

    return host


def application_ids() -> list[str]:
    """Known application ids (static Phase 2 list + live discovery when possible)."""
    ids = ["aria", "aria-uncensored", "flytying", "housefly"]
    try:
        from aiplatform.applications.host import discover_and_attach

        hosts = discover_and_attach() or []
        for host in hosts:
            hid = host.get("id")
            if hid and hid not in ids:
                ids.append(str(hid))
    except Exception:
        pass
    return ids


def attach_aria_if_present() -> bool:
    try:
        from jarvis.application.host import attach_if_present

        return bool(attach_if_present())
    except Exception:
        return False
