"""Gather relevant project context before coding edits."""

from __future__ import annotations

import re
from pathlib import Path

from jarvis import fs

_SANDBOX_PREFIX = "data/scripts/"


def _norm_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _is_sandbox_script(path: str) -> bool:
    return _norm_path(path).startswith(_SANDBOX_PREFIX)


def _context_allowed(primary: str, candidate: str) -> bool:
    """Keep sandbox scripts isolated from core jarvis modules in context."""
    if not _is_sandbox_script(primary):
        return True
    return _is_sandbox_script(candidate)


def _module_stem(path: str) -> str:
    p = Path(path)
    if p.stem == "__init__":
        return p.parent.name
    return p.stem


def _import_patterns(module_stem: str, rel_path: str) -> list[str]:
    """Patterns to find files that reference this module."""
    patterns = [module_stem, rel_path.replace("/", ".").removesuffix(".py")]
    if "/" in rel_path:
        parts = rel_path.replace(".py", "").split("/")
        patterns.append(".".join(parts))
        patterns.append(parts[-1])
    return list(dict.fromkeys(p for p in patterns if p))


def _extract_imports(content: str) -> list[str]:
    imports: list[str] = []
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("import "):
            imports.append(s.split()[1].split(".")[0].split(",")[0].strip())
        elif s.startswith("from "):
            parts = s.split()
            if len(parts) >= 2:
                imports.append(parts[1].split(".")[0])
    return imports


def _find_test_files(path: str, base: Path) -> list[str]:
    """Test files that target this source file only — never every test_*.py in the folder."""
    p = Path(path)
    if p.is_absolute():
        try:
            p = p.relative_to(base)
        except ValueError:
            pass
    stem = p.stem
    parent = p.parent
    rel = str(p).replace("\\", "/")
    candidates = [
        parent / f"test_{stem}.py",
        parent / f"{stem}_test.py",
        parent / "tests" / f"test_{stem}.py",
        parent / "tests" / f"{stem}_test.py",
    ]
    if rel.startswith("jarvis/"):
        candidates.extend([
            Path("tests") / f"test_{stem}.py",
            Path("tests") / f"test_{stem.replace('_', '')}.py",
        ])
    found: list[str] = []
    seen: set[str] = set()
    for c in candidates:
        full = base / c
        if not full.exists():
            continue
        try:
            rel_path = str(full.relative_to(base))
        except ValueError:
            rel_path = str(full)
        if rel_path not in seen:
            seen.add(rel_path)
            found.append(rel_path)
    return found


def _resolve_import_to_path(import_name: str, from_path: str, base: Path) -> str | None:
    """Best-effort map import name to a project file."""
    from_dir = Path(from_path).parent
    candidates = [
        from_dir / f"{import_name}.py",
        from_dir / import_name / "__init__.py",
        base / f"{import_name}.py",
        base / import_name / "__init__.py",
        base / "jarvis" / f"{import_name}.py",
        base / "jarvis" / import_name / "__init__.py",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            try:
                return str(c.relative_to(base))
            except ValueError:
                return str(c)
    return None


def gather_context(
    path: str,
    base: Path,
    *,
    task: str = "",
    max_chars: int = 12000,
) -> dict:
    """Build context bundle for a coding task. Returns {primary, related, tests, callers, semantic}."""
    content = fs.read_file(path, base=base)
    if content.startswith("ERROR:"):
        return {"primary": "", "related": [], "tests": [], "callers": [], "semantic": []}

    related: list[dict] = []
    seen: set[str] = {path}

    def add_file(rel: str, reason: str, limit: int = 2500) -> None:
        if rel in seen or not rel:
            return
        if not _context_allowed(path, rel):
            return
        seen.add(rel)
        text = fs.read_file(rel, base=base)
        if text.startswith("ERROR:"):
            return
        related.append({"path": rel, "reason": reason, "content": text[:limit]})

    # Imports used by target file
    for imp in _extract_imports(content)[:12]:
        resolved = _resolve_import_to_path(imp, path, base)
        if resolved:
            add_file(resolved, f"imported by {path}")

    # Callers / references
    stem = _module_stem(path)
    for pattern in _import_patterns(stem, path):
        hits = fs.search_files(pattern, base)
        for hit_path, line_num, _line in hits[:8]:
            try:
                rel = str(Path(hit_path).relative_to(base))
            except ValueError:
                rel = hit_path
            if rel == path or rel in seen:
                continue
            add_file(rel, f"references '{pattern}' (line {line_num})")
            break

    tests = _find_test_files(path, base)
    for t in tests:
        add_file(t, "test file", limit=3000)

    # Semantic hits from code index if available (skip for sandbox scripts — faster, less noise)
    semantic: list[dict] = []
    if task and not _is_sandbox_script(path):
        try:
            from jarvis import code_index
            for hit in code_index.search(task, limit=4):
                src = hit.get("source", "")
                if src and src not in seen and src != path:
                    semantic.append(hit)
                    add_file(src, "semantic match")
        except Exception:
            pass

    # Trim to max_chars
    total = len(content)
    trimmed_related: list[dict] = []
    for item in related:
        chunk_len = len(item["content"]) + len(item["path"]) + 20
        if total + chunk_len > max_chars:
            break
        trimmed_related.append(item)
        total += chunk_len

    return {
        "primary": content,
        "path": path,
        "related": trimmed_related,
        "tests": tests,
        "callers": [r for r in trimmed_related if "references" in r.get("reason", "")],
        "semantic": semantic,
    }


def format_context(ctx: dict) -> str:
    """Format context dict for LLM prompt."""
    parts = [f"FILE: {ctx.get('path', '')}\n{ctx.get('primary', '')}"]
    for item in ctx.get("related", []):
        parts.append(f"\n--- {item['path']} ({item['reason']}) ---\n{item['content']}")
    if ctx.get("tests"):
        parts.append("\nTest files: " + ", ".join(ctx["tests"]))
    return "\n".join(parts)[:14000]


def find_references(symbol: str, base: Path, *, limit: int = 40) -> list[dict]:
    """Grep-based symbol references (not full LSP, but useful for navigation)."""
    if not symbol or len(symbol) < 2:
        return []
    pattern = rf"\b{re.escape(symbol)}\b"
    hits: list[dict] = []
    seen: set[tuple[str, int]] = set()
    for path, line_no, line_text in fs.search_files(symbol, base):
        if not re.search(pattern, line_text):
            continue
        key = (path, line_no)
        if key in seen:
            continue
        seen.add(key)
        hits.append({"path": path, "line": line_no, "text": line_text.strip()[:200]})
        if len(hits) >= limit:
            break
    return hits
