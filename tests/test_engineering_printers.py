"""Engineering printer profile and Bambu handoff tests."""

from __future__ import annotations

from pathlib import Path


def test_printer_models_list():
    from jarvis.engineering.printer_profiles import get_model, list_models

    models = list_models()
    ids = {m["id"] for m in models}
    assert "bambu_a1" in ids
    assert "bambu_a1_mini" in ids
    assert "creality_ender3_v3_ke" in ids
    assert get_model("a1_mini")["id"] == "bambu_a1_mini"


def test_bambu_handoff(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.engineering.bambu_handoff.HANDOFF_ROOT", tmp_path)
    from jarvis.engineering.bambu_handoff import handoff_gcode, printer_status

    gcode = tmp_path / "part.gcode"
    gcode.write_text("G28\n", encoding="utf-8")
    printer = {"id": "bambu-a1-mini", "name": "A1 Mini", "model": "bambu_a1_mini", "backend": "bambu_handoff"}
    result = handoff_gcode(printer, gcode)
    assert result["ok"] is True
    assert (tmp_path / "bambu-a1-mini" / "latest.gcode").is_file()
    st = printer_status(printer)
    assert st["ok"] is True
    assert st["state"] == "handoff"
    assert st["mode"] == "no_lan"


def test_add_preset_bambu(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.engineering.printer_store.STORE", tmp_path / "printers.json")
    from jarvis.engineering.printer_store import add_preset_printer, get_printer

    row = add_preset_printer("bambu_a1", name="Shop A1")
    assert row["backend"] == "bambu_handoff"
    assert row["model"] == "bambu_a1"
    assert get_printer(row["id"])["name"] == "Shop A1"


def test_add_preset_creality_requires_host(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.engineering.printer_store.STORE", tmp_path / "printers.json")
    from jarvis.engineering.printer_store import add_preset_printer
    import pytest

    with pytest.raises(ValueError):
        add_preset_printer("creality_ender3_v3_ke")
    row = add_preset_printer("creality_ender3_v3_ke", host="192.168.1.88", name="KE")
    assert row["host"] == "http://192.168.1.88:7125"
    assert row["backend"] == "moonraker"


def test_printer_client_routes_bambu():
    from jarvis.engineering.printer_client import printer_status

    st = printer_status({"id": "x", "model": "bambu_a1", "backend": "bambu_handoff", "name": "A1"})
    assert st["state"] == "handoff"


def test_slicer_detect_env_override(monkeypatch):
    from jarvis.engineering import slicer

    monkeypatch.setenv("JARVIS_ORCASLICER_PATH", "/fake/orcaslicer")
    found = slicer.detect_slicers()
    assert any(s["path"] == "/fake/orcaslicer" for s in found)


def test_slicer_detect_flathub_orca_id(monkeypatch):
    from jarvis.engineering import slicer

    monkeypatch.delenv("JARVIS_ORCASLICER_PATH", raising=False)
    monkeypatch.setattr(slicer.shutil, "which", lambda _n: None)
    monkeypatch.setattr(slicer.glob, "glob", lambda _p: [])

    def fake_run(cmd, **_kwargs):
        class P:
            returncode = 0 if cmd[:3] == ["flatpak", "info", "com.orcaslicer.OrcaSlicer"] else 1
            stdout = ""
            stderr = ""

        return P()

    monkeypatch.setattr(slicer.subprocess, "run", fake_run)
    found = slicer.detect_slicers()
    assert any(s["path"] == "flatpak run --command=orca-slicer com.orcaslicer.OrcaSlicer" for s in found)


def test_bambu_checklist_no_bed_required(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.engineering.printer_store.STORE", tmp_path / "printers.json")
    from jarvis.engineering.print_jobs import pre_print_checklist
    from jarvis.engineering.printer_store import add_preset_printer

    add_preset_printer("bambu_a1_mini", name="Mini")
    chk = pre_print_checklist(bed_confirmed=False, filament_confirmed=False)
    names = [c["name"] for c in chk["checks"]]
    assert "Bambu handoff" in names
    assert "Bed clear" not in names


def test_mislabelled_moonraker_bambu_uses_handoff(tmp_path, monkeypatch):
    from jarvis.engineering.printer_client import effective_backend, start_print_job

    monkeypatch.setattr("jarvis.engineering.bambu_handoff.HANDOFF_ROOT", tmp_path / "handoff")
    gcode = tmp_path / "plate_1.gcode"
    gcode.write_text("G28\n", encoding="utf-8")
    printer = {
        "id": "printer-2",
        "name": "Printer 2",
        "host": "http://10.0.0.0.187:7125",
        "backend": "moonraker",
        "model": "bambu_a1",
    }
    assert effective_backend(printer) == "bambu_handoff"
    result = start_print_job(printer, gcode)
    assert result["ok"] is True
    assert (tmp_path / "handoff" / "printer-2" / "latest.gcode").is_file()


def test_add_printer_bambu_ignores_moonraker_default(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.engineering.printer_store.STORE", tmp_path / "printers.json")
    from jarvis.engineering.printer_store import add_printer

    row = add_printer(name="Printer 2", host="http://10.0.0.0.187:7125", backend="moonraker", model="bambu_a1")
    assert row["backend"] == "bambu_handoff"
    assert row["model"] == "bambu_a1"


def test_enqueue_print_bambu_handoff(tmp_path, monkeypatch):
    monkeypatch.setattr("jarvis.engineering.printer_store.STORE", tmp_path / "printers.json")
    monkeypatch.setattr("jarvis.engineering.print_jobs.STATE_FILE", tmp_path / "jobs.json")
    monkeypatch.setattr("jarvis.engineering.bambu_handoff.HANDOFF_ROOT", tmp_path / "handoff")
    monkeypatch.setattr(
        "jarvis.engineering.slicer.slicer_status",
        lambda: {"slicers": [{"id": "orca", "label": "OrcaSlicer"}]},
    )
    from jarvis.engineering import print_jobs
    from jarvis.engineering.printer_store import add_preset_printer

    print_jobs._jobs = {}
    add_preset_printer("bambu_a1", name="Shop A1")
    gcode = tmp_path / "plate_1.gcode"
    gcode.write_text("G28\n", encoding="utf-8")
    out = print_jobs.enqueue_print(gcode, bed_confirmed=False, filament_confirmed=False)
    assert out["ok"] is True
    assert out["status"] == "handoff"
    assert "Bambu Studio" in (out.get("message") or "")
    assert (tmp_path / "handoff" / "shop-a1" / "latest.gcode").is_file()
