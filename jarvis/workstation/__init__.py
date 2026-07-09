"""Compatibility shim — workstation implementation lives in AI Platform.

Use:
  - ``workstation`` (AI Platform) for platform workstation lifecycle
  - ``aria`` for standalone Aria lifecycle
"""

from __future__ import annotations


def _use_platform() -> bool:
    try:
        import aiplatform.workstation  # noqa: F401

        return True
    except ImportError:
        return False


def _attach_aria():
    try:
        from jarvis.application.host import attach_if_present

        attach_if_present()
    except Exception:
        pass


if _use_platform():
    _attach_aria()
    from aiplatform.workstation import *  # noqa: F403
    from aiplatform.workstation.cli import main
else:
    from jarvis.application.standalone.workstation_impl import *  # noqa: F403
    from jarvis.application.standalone.workstation_impl.cli import main

__all__ = ["main"]
