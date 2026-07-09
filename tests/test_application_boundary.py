"""Boundary tests — Aria standalone vs platform attach."""

from __future__ import annotations


def test_aria_host_register():
    from jarvis.application.host import AriaApplicationHost

    host = AriaApplicationHost()
    reg = host.register()
    assert reg.app_id == "aria"
    assert "aria" in reg.component_ids


def test_workstation_shim_imports():
    import jarvis.workstation as ws

    assert hasattr(ws, "main")


def test_standalone_impl_available():
    from jarvis.application.standalone.workstation_impl import acceptance

    assert acceptance._CATALOG
