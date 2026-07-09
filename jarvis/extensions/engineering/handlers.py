"""Physical engineering handlers — CAD, slicing, and printer status."""

from __future__ import annotations

from jarvis.handlers.registry import register_action
from jarvis.response import err, ok


@register_action("cad_status", module="engineering", description="CAD toolchain status", info=True)
def cad_status_action(assistant, params: dict, message: str) -> dict:
    from jarvis.engineering.cad_deps import cad_status

    status = cad_status()
    lines = [
        f"**CAD enabled:** {status.get('cad_enabled', True)}",
        f"**OpenSCAD:** {status.get('openscad') or 'not found'}",
        f"**build123d:** {'yes' if status.get('build123d') else 'no'}",
        f"**Meshy:** {'yes' if status.get('meshy') else 'no'}",
    ]
    return ok("\n".join(lines), module="engineering", status=status)


@register_action("generate_cad", module="engineering", description="Generate CAD from description")
def generate_cad_action(assistant, params: dict, message: str) -> dict:
    from jarvis.engineering.cad_router import generate_cad

    prompt = (params.get("prompt") or message or "").strip()
    result = generate_cad(
        prompt,
        backend=str(params.get("backend") or "auto"),
        edit=bool(params.get("edit")),
        model_id=str(params.get("model_id") or ""),
    )
    if not result.get("ok"):
        return err(result.get("error") or "CAD generation failed.", module="engineering")
    return ok(result.get("message") or "CAD model ready.", module="engineering", **result)


@register_action("iterate_cad", module="engineering", description="Iterate current CAD design")
def iterate_cad_action(assistant, params: dict, message: str) -> dict:
    from jarvis.engineering.cad_router import generate_cad

    prompt = (params.get("prompt") or message or "").strip()
    result = generate_cad(
        prompt,
        backend=str(params.get("backend") or "auto"),
        edit=True,
        model_id=str(params.get("model_id") or ""),
    )
    if not result.get("ok"):
        return err(result.get("error") or "CAD iteration failed.", module="engineering")
    return ok(result.get("message") or "CAD updated.", module="engineering", **result)


@register_action("slice_stl", module="engineering", description="Slice STL to G-code")
def slice_stl_action(assistant, params: dict, message: str) -> dict:
    from jarvis.engineering import cad_store
    from jarvis.engineering.slicer import slice_stl

    stl = params.get("stl") or params.get("path") or ""
    if not stl:
        last = cad_store.load_last_script()
        model_id = last.get("model_id") or ""
        if model_id:
            paths = cad_store.paths_for_model(model_id)
            stl = str(paths.get("stl") or "")
    if not stl:
        return err("No STL to slice — generate a CAD model first.", module="engineering")
    result = slice_stl(stl, slicer_id=str(params.get("slicer") or ""))
    if not result.get("ok"):
        return err(result.get("error") or "Slicing failed.", module="engineering")
    return ok(result.get("message") or "G-code ready.", module="engineering", **result)


@register_action("printer_status", module="engineering", description="3D printer status", info=True)
def printer_status_action(assistant, params: dict, message: str) -> dict:
    from jarvis.engineering.printer_client import printer_status
    from jarvis.engineering.printer_store import get_printer, list_printers

    printer_id = str(params.get("printer_id") or params.get("printer") or "")
    printer = get_printer(printer_id) if printer_id else None
    if printer is None:
        printers = list_printers()
        printer = printers[0] if printers else None
    if printer is None:
        return ok("No printers configured.", module="engineering")
    status = printer_status(printer)
    name = printer.get("name") or printer.get("id") or "printer"
    state = status.get("state") or ("ok" if status.get("ok") else "unknown")
    return ok(f"**{name}** — {state}", module="engineering", printer=status)


@register_action("teach_cad", module="engineering", description="Teach CAD pattern or rule")
def teach_cad_action(assistant, params: dict, message: str) -> dict:
    from jarvis.engineering.cad_teaching import parse_teach_cad, record_pattern

    parsed = parse_teach_cad(message)
    if not parsed:
        return err("Say **teach cad:** followed by a pattern or rule.", module="engineering")
    entry = record_pattern(parsed["text"], kind=parsed.get("kind") or "pattern")
    return ok(f"Stored CAD {entry.get('kind', 'pattern')}.", module="engineering", pattern=entry)
