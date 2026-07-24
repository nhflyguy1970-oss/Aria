"""Engineering lab HTTP API."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse


def register_routes(app, assistant) -> None:
    def _cad_payload():
        from jarvis.engineering.cad_deps import cad_status

        payload = {"ok": True, **cad_status()}
        try:
            from jarvis.engineering.slicer import slicer_status

            payload["slicer"] = slicer_status()
        except Exception:
            payload["slicer"] = {}
        return payload

    @app.get("/api/engineering/cad/status")
    @app.get("/api/engineering/cad_status")
    def engineering_cad_status():
        return _cad_payload()

    @app.get("/api/engineering/models")
    def engineering_models():
        from jarvis.engineering_3d import engineering_lab_status, list_models as list_3d_models

        payload: dict = {"ok": True, **engineering_lab_status(), "models": list_3d_models()}
        try:
            from jarvis.engineering.cad_store import list_models as list_cad_models

            seen = {m.get("id") for m in payload["models"]}
            for row in list_cad_models():
                mid = row.get("id")
                if mid and mid not in seen:
                    payload["models"].append(row)
                    seen.add(mid)
        except Exception:
            pass
        return payload

    @app.post("/api/engineering/design")
    async def engineering_legacy_design(request: Request):
        from jarvis.engineering_3d import design_and_render

        body = await request.json()
        result = design_and_render(
            str(body.get("prompt") or ""),
            engine=str(body.get("engine") or "openscad"),
        )
        if not result.get("ok"):
            return JSONResponse(status_code=400, content=result)
        return result

    @app.post("/api/engineering/edit")
    async def engineering_legacy_edit(request: Request):
        from jarvis.engineering_3d import edit_and_render

        body = await request.json()
        model_id = str(body.get("model_id") or "").strip()
        prompt = str(body.get("prompt") or "").strip()
        if not model_id or not prompt:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "message": "model_id and prompt required"},
            )
        result = edit_and_render(model_id, prompt)
        if not result.get("ok"):
            return JSONResponse(status_code=400, content=result)
        return result

    @app.post("/api/engineering/render")
    async def engineering_legacy_render(request: Request):
        from jarvis.engineering_3d import render_stl

        body = await request.json()
        model_id = str(body.get("model_id") or "").strip()
        if not model_id:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "message": "model_id required"},
            )
        ok, msg, _rel = render_stl(model_id)
        if not ok:
            return JSONResponse(status_code=500, content={"ok": False, "message": msg})
        return {
            "ok": True,
            "message": msg,
            "stl_url": f"/api/engineering/stl/{model_id}",
        }

    @app.get("/api/engineering/print-advice/{model_id}")
    def engineering_print_advice(model_id: str):
        from jarvis.engineering_3d import print_advice

        result = print_advice(model_id)
        if not result.get("ok"):
            return JSONResponse(status_code=404, content=result)
        return result

    @app.get("/api/engineering/stl/{model_id}")
    def engineering_legacy_stl(model_id: str):
        from jarvis.engineering_3d import ENGINEERING_DIR, get_model

        m = get_model(model_id)
        if not m:
            return JSONResponse(status_code=404, content={"ok": False, "message": "not found"})
        path = Path(str(m.get("stl_path") or ""))
        if not path.is_file():
            path = ENGINEERING_DIR / f"{model_id}.stl"
        if not path.is_file():
            return JSONResponse(status_code=404, content={"ok": False, "message": "STL missing"})
        return FileResponse(path, media_type="model/stl", filename=f"{model_id}.stl")

    @app.get("/api/engineering/scad/{model_id}")
    def engineering_legacy_scad(model_id: str):
        from jarvis.engineering_3d import ENGINEERING_DIR, get_model

        m = get_model(model_id)
        if not m:
            return JSONResponse(status_code=404, content={"ok": False, "message": "not found"})
        path = Path(str(m.get("scad_path") or ""))
        if not path.is_file():
            path = ENGINEERING_DIR / f"{model_id}.scad"
        if not path.is_file():
            return JSONResponse(status_code=404, content={"ok": False, "message": "SCAD missing"})
        return FileResponse(
            path,
            media_type="application/octet-stream",
            filename=f"{model_id}.scad",
        )

    @app.post("/api/engineering/hello-cube")
    @app.post("/api/engineering/hello_cube")
    def engineering_hello_cube():
        from jarvis.engineering.build123d_runner import build123d_available, hello_cube
        from jarvis.engineering.cad_store import paths_for_model, register_model
        from jarvis.engineering.cad_verify import verify_stl
        from jarvis.engineering.openscad_runner import openscad_available, render_scad

        mid = uuid.uuid4().hex[:10]
        paths = paths_for_model(mid)
        backend = ""
        result: dict
        if build123d_available():
            result = hello_cube(paths["stl"])
            backend = "build123d"
        elif openscad_available():
            paths["scad"].write_text("cube(10);\n", encoding="utf-8")
            result = render_scad(paths["scad"], paths["stl"])
            backend = "openscad"
        else:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "message": "Install build123d or OpenSCAD"},
            )
        if not result.get("ok"):
            return JSONResponse(status_code=500, content=result)
        verify = verify_stl(str(paths["stl"]))
        row = register_model(
            prompt="10mm hello cube",
            name="Hello cube",
            backend=backend,
            stl_path=str(paths["stl"]),
            verify=verify,
            model_id=mid,
        )
        return {"ok": True, "model": row, "verify": verify}

    @app.get("/api/engineering/models/{model_id}/stl")
    def engineering_model_stl(model_id: str):
        from jarvis.engineering.cad_store import get_model

        m = get_model(model_id)
        if not m:
            return JSONResponse(status_code=404, content={"ok": False, "message": "not found"})
        path = Path(str(m.get("stl_path") or ""))
        if not path.is_file():
            return JSONResponse(status_code=404, content={"ok": False, "message": "STL missing"})
        return FileResponse(path, media_type="model/stl", filename=path.name)

    @app.get("/api/engineering/printers")
    def engineering_printers():
        from jarvis.engineering.printer_store import list_printers

        return {"ok": True, "printers": list_printers()}

    @app.get("/api/engineering/printer-models")
    def engineering_printer_models():
        from jarvis.engineering.printer_profiles import list_models

        return {"ok": True, "models": list_models()}

    @app.get("/api/engineering/print/checklist")
    def engineering_print_checklist():
        from jarvis.engineering.print_jobs import pre_print_checklist

        return {"ok": True, **pre_print_checklist()}

    @app.get("/api/engineering/print/jobs")
    def engineering_print_jobs():
        from jarvis.engineering.print_jobs import list_jobs

        return {"ok": True, "jobs": list_jobs()}

    @app.post("/api/engineering/generate")
    async def engineering_generate(request: Request):
        from jarvis.engineering.cad_router import generate_cad

        body = await request.json()
        prompt = str(body.get("prompt") or "").strip()
        if not prompt:
            return JSONResponse(status_code=400, content={"ok": False, "message": "prompt required"})
        return generate_cad(
            prompt,
            backend=str(body.get("backend") or "auto"),
            edit=bool(body.get("edit")),
            model_id=str(body.get("model_id") or ""),
        )

    @app.post("/api/engineering/slice")
    async def engineering_slice(request: Request):
        body = await request.json()
        stl = str(body.get("stl_path") or "").strip()
        mid = str(body.get("model_id") or "").strip()
        if mid and not stl:
            from jarvis.engineering.cad_store import get_model

            m = get_model(mid)
            stl = str((m or {}).get("stl_path") or "")
        if not stl:
            return JSONResponse(
                status_code=400,
                content={"ok": False, "message": "model_id or stl_path required"},
            )
        try:
            from jarvis.engineering.slicer import slice_stl

            return slice_stl(stl, slicer_id=str(body.get("slicer") or ""))
        except Exception as exc:
            return JSONResponse(status_code=500, content={"ok": False, "message": str(exc)})

    @app.post("/api/engineering/printers")
    async def engineering_add_printer(request: Request):
        from jarvis.engineering.printer_store import add_printer

        body = await request.json()
        try:
            row = add_printer(
                name=str(body.get("name") or "Printer"),
                host=str(body.get("host") or ""),
                backend=str(body.get("backend") or "moonraker"),
                port=int(body.get("port") or 0),
                api_key=str(body.get("api_key") or ""),
                model=str(body.get("model") or body.get("model_id") or ""),
            )
        except ValueError as exc:
            return JSONResponse(status_code=400, content={"ok": False, "message": str(exc)})
        return {"ok": True, "printer": row}

    @app.post("/api/engineering/printers/discover")
    def engineering_discover_printers():
        from jarvis.engineering.printer_store import discover_mdns

        return {"ok": True, "printers": discover_mdns()}

    @app.get("/api/engineering/printer/status")
    def engineering_printer_status(printer_id: str = ""):
        from jarvis.engineering.printer_store import get_printer, list_printers

        p = get_printer(printer_id)
        if not p:
            printers = list_printers()
            p = printers[0] if printers else None
        if not p:
            return {"ok": False, "message": "No printer configured"}
        try:
            from jarvis.engineering.moonraker_client import printer_status

            return {"ok": True, "printer": p, **printer_status(p["host"], api_key=p.get("api_key") or "")}
        except Exception as exc:
            return {"ok": False, "printer": p, "message": str(exc)}

    @app.post("/api/engineering/print")
    async def engineering_print(request: Request):
        from jarvis.engineering.print_jobs import enqueue_print

        body = await request.json()
        gcode = str(body.get("gcode_path") or "").strip()
        if not gcode:
            return JSONResponse(status_code=400, content={"ok": False, "message": "gcode_path required"})
        return enqueue_print(
            gcode,
            printer_id=str(body.get("printer_id") or ""),
            bed_confirmed=bool(body.get("bed_confirmed")),
            filament_confirmed=bool(body.get("filament_confirmed")),
        )

    @app.post("/api/engineering/models/clear")
    def engineering_models_clear():
        from jarvis.engineering.cad_store import clear_gallery

        return clear_gallery(delete_files=False)

    @app.get("/api/engineering/printers/discover")
    def engineering_discover_printers():
        from jarvis.engineering.printer_store import discover_mdns

        return {"ok": True, "printers": discover_mdns()}

    @app.get("/api/engineering/printers/{printer_id}/status")
    def engineering_printer_status(printer_id: str):
        from jarvis.engineering.printer_client import printer_status
        from jarvis.engineering.printer_store import get_printer

        p = get_printer(printer_id)
        if not p:
            return {"ok": False, "message": "No printer configured"}
        try:
            st = printer_status(p)
            return {"ok": True, "status": st, "printer": p}
        except Exception as exc:
            return {"ok": False, "message": str(exc), "printer": p}

    @app.get("/api/engineering/models/{model_id}/dimensions")
    def engineering_model_dimensions(model_id: str):
        from jarvis.engineering.cad_store import get_model
        from jarvis.engineering.cad_verify import stl_dimensions

        m = get_model(model_id)
        if not m:
            return JSONResponse(status_code=404, content={"ok": False, "message": "not found"})
        path = str(m.get("stl_path") or "")
        if not path:
            return JSONResponse(status_code=404, content={"ok": False, "message": "no STL"})
        return stl_dimensions(path)

    @app.get("/api/engineering/usb/ports")
    def engineering_usb_ports():
        from jarvis.engineering.usb_printer import list_serial_ports, serial_available

        return {"ok": True, "serial": serial_available(), "ports": list_serial_ports()}

