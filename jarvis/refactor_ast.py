"""AST-based Python refactor tools — rename, extract function, move module."""

from __future__ import annotations

import ast
import re
import shutil
from pathlib import Path

from jarvis import fs
from jarvis.config import PROJECT_ROOT, SKIP_DIRS


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def rename_python_symbol(path: Path, old: str, new: str, *, dry_run: bool = False) -> dict:
    """AST-aware rename within a single Python file."""
    if not path.exists() or path.suffix != ".py":
        return {"error": "Not a Python file", "changed": False}
    if old == new or not old.isidentifier() or not new.isidentifier():
        return {"error": "Invalid symbol names", "changed": False}

    source = _read(path)
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}", "changed": False}

    class Renamer(ast.NodeTransformer):
        def visit_Name(self, node: ast.Name) -> ast.Name:
            if node.id == old:
                return ast.copy_location(ast.Name(id=new, ctx=node.ctx), node)
            return node

        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
            if node.name == old:
                node.name = new
            self.generic_visit(node)
            return node

        def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
            if node.name == old:
                node.name = new
            self.generic_visit(node)
            return node

        def visit_arg(self, node: ast.arg) -> ast.arg:
            if node.arg == old:
                node.arg = new
            return node

    new_tree = Renamer().visit(tree)
    ast.fix_missing_locations(new_tree)
    try:
        new_source = ast.unparse(new_tree)
    except Exception as e:
        return {"error": str(e), "changed": False}

    if new_source == source:
        return {"changed": False, "path": str(path), "message": "Symbol not found"}

    rel = str(path)
    try:
        from jarvis.config import PROJECT_ROOT
        rel = str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        pass

    if dry_run:
        return {"changed": True, "path": rel, "code": new_source, "dry_run": True}

    fs.backup_file(str(path), base=path.parent)
    _write(path, new_source + ("\n" if not new_source.endswith("\n") else ""))
    return {"changed": True, "path": rel, "old": old, "new": new}


def extract_function(
    path: Path,
    start_line: int,
    end_line: int,
    func_name: str,
    *,
    dry_run: bool = False,
) -> dict:
    """Extract lines [start_line, end_line] into a new function; replace with call."""
    if not path.exists() or path.suffix != ".py":
        return {"error": "Not a Python file"}
    if not func_name.isidentifier():
        return {"error": "Invalid function name"}

    lines = _read(path).splitlines()
    if start_line < 1 or end_line > len(lines) or start_line > end_line:
        return {"error": f"Invalid line range 1-{len(lines)}"}

    body_lines = lines[start_line - 1 : end_line]
    indent = ""
    for ch in body_lines[0]:
        if ch in " \t":
            indent += ch
        else:
            break

    # Detect existing indent in body
    dedented = []
    for line in body_lines:
        if line.startswith(indent):
            dedented.append(line[len(indent):] if len(line) > len(indent) else "")
        else:
            dedented.append(line)

    func_indent = indent[:-4] if len(indent) >= 4 else ""
    func_def = [f"{func_indent}def {func_name}():"]
    has_body = False
    for line in dedented:
        if line.strip():
            func_def.append(f"{func_indent}    {line}")
            has_body = True
        else:
            func_def.append("")
    if not has_body:
        func_def.append(f"{func_indent}    pass")

    call_line = f"{indent}{func_name}()"
    new_lines = lines[: start_line - 1] + [call_line] + lines[end_line:]

    insert_at = 0
    for i, line in enumerate(new_lines):
        s = line.strip()
        if s and not s.startswith("#") and not s.startswith(("import ", "from ", '"""', "'''")):
            insert_at = i
            break
    final = new_lines[:insert_at] + func_def + [""] + new_lines[insert_at:]

    new_source = "\n".join(final) + "\n"
    rel = str(path)
    try:
        from jarvis.config import PROJECT_ROOT
        rel = str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        pass
    if dry_run:
        return {"changed": True, "path": rel, "code": new_source, "dry_run": True}

    fs.backup_file(str(path), base=path.parent)
    _write(path, new_source)
    return {"changed": True, "path": rel, "function": func_name, "lines": [start_line, end_line]}


def rename_python_symbol_project(
    symbol: str,
    new_name: str,
    root: Path | None = None,
    *,
    dry_run: bool = False,
) -> dict:
    """AST-aware rename across all Python files in project."""
    root = root or PROJECT_ROOT
    changed: list[dict] = []
    for dirpath, dirnames, filenames in __import__("os").walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            if fs._is_blocked(Path(filename)):
                continue
            path = Path(dirpath) / filename
            result = rename_python_symbol(path, symbol, new_name, dry_run=dry_run)
            if result.get("changed"):
                rel = str(path.relative_to(root))
                changed.append({"path": rel, "dry_run": dry_run})
    return {
        "symbol": symbol,
        "new_name": new_name,
        "files_changed": len(changed),
        "changed": changed,
    }


def preview_rename_python_symbol_project(
    symbol: str,
    new_name: str,
    root: Path | None = None,
) -> dict:
    """Return proposal file items for a project-wide Python rename."""
    root = root or PROJECT_ROOT
    files: list[dict] = []
    for dirpath, dirnames, filenames in __import__("os").walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            if fs._is_blocked(Path(filename)):
                continue
            path = Path(dirpath) / filename
            result = rename_python_symbol(path, symbol, new_name, dry_run=True)
            if result.get("changed") and result.get("code"):
                files.append({"path": result["path"], "code": result["code"]})
    return {
        "symbol": symbol,
        "new_name": new_name,
        "files": files,
        "files_changed": len(files),
    }


def preview_move_module(from_path: Path, to_path: Path, root: Path | None = None) -> dict:
    """Return proposal file items for moving a module and updating imports."""
    root = root or PROJECT_ROOT
    from_path = from_path.resolve()
    to_path = to_path.resolve()

    if not from_path.exists():
        return {"error": f"Source not found: {from_path}"}

    try:
        from_mod = from_path.relative_to(root).with_suffix("").as_posix().replace("/", ".")
        to_mod = to_path.relative_to(root).with_suffix("").as_posix().replace("/", ".")
        from_rel = from_path.relative_to(root).as_posix()
        to_rel = to_path.relative_to(root).as_posix()
    except ValueError:
        return {"error": "Paths must be under project root"}

    files: list[dict] = [{"path": to_rel, "code": _read(from_path)}]
    if from_rel != to_rel:
        files.append({"path": from_rel, "delete": True})

    for dirpath, dirnames, filenames in __import__("os").walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            fp = Path(dirpath) / filename
            if fp.resolve() == from_path.resolve():
                continue
            try:
                content = _read(fp)
            except OSError:
                continue
            original = content
            content = re.sub(rf"\bimport\s+{re.escape(from_mod)}\b", f"import {to_mod}", content)
            content = re.sub(
                rf"\bfrom\s+{re.escape(from_mod)}\s+import\b",
                f"from {to_mod} import",
                content,
            )
            if content != original:
                rel = fp.relative_to(root).as_posix()
                files.append({"path": rel, "code": content})

    return {
        "from": from_rel,
        "to": to_rel,
        "files": files,
        "imports_updated": max(0, len(files) - 2),
    }


def move_module(from_path: Path, to_path: Path, root: Path | None = None, *, dry_run: bool = False) -> dict:
    """Move a Python module and update imports across the project."""
    root = root or PROJECT_ROOT
    from_path = from_path.resolve()
    to_path = to_path.resolve()

    if not from_path.exists():
        return {"error": f"Source not found: {from_path}"}

    try:
        from_mod = from_path.relative_to(root).with_suffix("").as_posix().replace("/", ".")
        to_mod = to_path.relative_to(root).with_suffix("").as_posix().replace("/", ".")
    except ValueError:
        return {"error": "Paths must be under project root"}

    from_import = from_mod
    to_import = to_mod
    # Also handle `from jarvis.foo import bar` style partial paths
    from_mod.split(".")
    to_mod.split(".")

    updated_files: list[str] = []
    if not dry_run:
        to_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(from_path), str(to_path))

    for dirpath, dirnames, filenames in __import__("os").walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            fp = Path(dirpath) / filename
            try:
                content = _read(fp)
            except OSError:
                continue
            original = content
            # Replace full module paths
            content = re.sub(rf"\bimport\s+{re.escape(from_import)}\b", f"import {to_import}", content)
            content = re.sub(
                rf"\bfrom\s+{re.escape(from_import)}\s+import\b",
                f"from {to_import} import",
                content,
            )
            if content != original:
                rel = str(fp.relative_to(root))
                if not dry_run:
                    fs.backup_file(rel, base=root)
                    _write(fp, content)
                updated_files.append(rel)

    return {
        "from": str(from_path.relative_to(root)),
        "to": str(to_path.relative_to(root)),
        "imports_updated": len(updated_files),
        "files": updated_files[:30],
        "dry_run": dry_run,
    }
