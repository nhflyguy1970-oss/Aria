"""Route CAD requests to build123d, OpenSCAD, or Meshy."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jarvis.engineering import build123d_runner, cad_store, openscad_runner
from jarvis.engineering.cad_verify import verify_stl
from jarvis.p3_flags import cad_enabled, meshy_cad_enabled


def pick_backend(prompt: str | None, *, prefer: str = "auto") -> str:
    p = (prefer or "auto").strip().lower()
    if p in ("build123d", "openscad", "meshy"):
        return p
    text = (prompt or "").lower()
    organic = bool(re.search(r"\b(sculpt|organic|character|figurine|creature|artistic|meshy)\b", text))
    if organic and meshy_cad_enabled():
        try:
            from jarvis.meshy_client import meshy_available

            if meshy_available():
                return "meshy"
        except Exception:
            pass
    if build123d_runner.build123d_available():
        return "build123d"
    if openscad_runner.openscad_available():
        return "openscad"
    if meshy_cad_enabled():
        try:
            from jarvis.meshy_client import meshy_available

            if meshy_available():
                return "meshy"
        except Exception:
            pass
    return "openscad"


def _generate_meshy(prompt: str, stl_path: str | Path) -> dict[str, Any]:
    from jarvis.meshy_client import text_to_3d_preview

    stl_path = Path(stl_path)
    stl_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        data, fmt, meta = text_to_3d_preview(prompt)
        if (fmt or "").lower() != "stl":
            return {"ok": False, "error": f"Meshy returned {fmt}, expected STL"}
        stl_path.write_bytes(data)
        return {"ok": True, "path": str(stl_path), "backend": "meshy", "meta": meta}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _generate_build123d(
    prompt: str,
    script_path: str | Path,
    stl_path: str | Path,
    *,
    prior_script: str = "",
) -> dict[str, Any]:
    import jarvis.llm as llm

    script_path = Path(script_path)
    stl_path = Path(stl_path)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    system = (
        "You write build123d Python only. End with export_stl(part, r'__OUT__'). "
        "Use millimeters. No markdown."
    )
    user = prompt
    try:
        from jarvis.engineering.cad_teaching import patterns_context_for_prompt

        ctx = patterns_context_for_prompt(prompt)
        if ctx:
            user = f"{ctx}\n\n{user}"
    except Exception:
        pass
    if prior_script:
        user = f"Edit this build123d script:\n{prior_script[:8000]}\n\nChange: {prompt}"
    try:
        raw = llm.ask_with_system(
            llm.coder_model(),
            system,
            user,
            options={"temperature": 0.2, "num_predict": 2500},
        )
        text = openscad_runner._strip_code(raw).replace("__OUT__", str(stl_path).replace("\\", "\\\\"))
        script_path.write_text(text, encoding="utf-8")
        return build123d_runner.run_script_file(script_path, stl_path)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def generate_cad(
    prompt: str | None,
    *,
    backend: str = "auto",
    edit: bool = False,
    model_id: str = "",
) -> dict[str, Any]:
    if not cad_enabled():
        return {"ok": False, "error": "CAD disabled (JARVIS_CAD=0)"}
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "error": "Describe the part to design"}

    prior_scad = ""
    prior_script = ""
    if edit:
        last = cad_store.load_last_script()
        if last.get("backend") == "openscad":
            prior_scad = str(last.get("content") or "")
        elif last.get("backend") == "build123d":
            prior_script = str(last.get("content") or "")
        if model_id:
            m = cad_store.get_model(model_id)
            if m and m.get("scad_path"):
                try:
                    prior_scad = Path(m["scad_path"]).read_text(encoding="utf-8")
                except OSError:
                    pass

    mid = (model_id or "").strip() or cad_store.new_model_id()
    paths = cad_store.paths_for_model(mid)
    chosen = pick_backend(prompt, prefer=backend)

    if chosen == "meshy":
        result = _generate_meshy(prompt, paths["stl"])
    elif chosen == "build123d":
        result = _generate_build123d(prompt, paths["script"], paths["stl"], prior_script=prior_script)
    else:
        result = openscad_runner.prompt_to_stl(
            prompt, paths["scad"], paths["stl"], prior_scad=prior_scad
        )

    if not result.get("ok"):
        return result

    stl_file = Path(result.get("path") or paths["stl"])
    verify = verify_stl(stl_file)
    if not verify.get("ok"):
        return {"ok": False, "error": "STL verification failed", "verify": verify}

    if chosen == "openscad" and paths["scad"].is_file():
        cad_store.save_last_script(
            backend="openscad",
            content=paths["scad"].read_text(encoding="utf-8"),
            model_id=mid,
            prompt=prompt,
        )
    elif chosen == "build123d" and paths["script"].is_file():
        cad_store.save_last_script(
            backend="build123d",
            content=paths["script"].read_text(encoding="utf-8"),
            model_id=mid,
            prompt=prompt,
        )

    row = cad_store.register_model(
        prompt=prompt,
        backend=chosen,
        stl_path=result["path"],
        scad_path=str(paths["scad"]) if paths["scad"].is_file() else "",
        script_path=str(paths["script"]) if paths["script"].is_file() else "",
        verify=verify,
        model_id=mid,
    )
    return {
        "ok": True,
        "model": row,
        "backend": chosen,
        "stl_path": result["path"],
        "verify": verify,
        "message": f"CAD ready ({chosen}) — {verify.get('triangles', '?')} triangles",
    }
