"""Reviewed promotion of an agent's verified changes into a real project.

A coding plan's approval covers *running the agent in a disposable clone*.
Moving its changes into the project is a separate decision with its own
single-use approval, bound to the exact patch and the destination's state:

 1. capture  — the run's patch (``git diff --binary`` against the clone's
               base) and a manifest: per file, base and new content hashes
 2. check    — protected/credential/data paths, migrations, deletions,
               binaries, symlinks, size; boundary-violating runs are refused
 3. verify   — apply the patch to a *fresh* clone of the destination's
               current HEAD and run the project's tests there, sandboxed
 4. present  — files, diffstat, test results, risks, destination
 5. approve  — owner only; nonce bound to patch hash + destination HEAD
 6. preflight— branch/HEAD unchanged, no uncommitted changes in any touched
               file, ``git apply --check`` clean
 7. recovery — exact copies of every touched file (or its absence)
 8. apply    — ``git apply`` (atomic, no 3-way: a conflict aborts everything)
 9. verify   — every file matches the manifest; tests re-run read-only;
               any failure restores the recovery point automatically
10. record   — receipt, continuity outcome, and the rollback procedure

Never: commit, push, restart a service, run a migration, or touch a file
whose working copy differs from the commit the patch was verified against.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from jarvis.coding_agents import contract, runs, workspace
from jarvis.config import DATA_DIR

ROOT = DATA_DIR / "coding_agents"
APPROVAL_TTL_S = 30 * 60
MAX_PATCH_BYTES = 2_000_000

# Proposed → approved → applying → applied | rolled_back | failed; or rejected / expired / blocked.
PROPOSED, APPROVED, APPLYING, APPLIED = "proposed", "approved", "applying", "applied"
ROLLED_BACK, FAILED, REJECTED, EXPIRED, BLOCKED = "rolled_back", "failed", "rejected", "expired", "blocked"
REVERTED = "reverted"

# Paths a promotion may never write, in any project (in addition to the
# project's own protected paths).
DENY = [
    (r"(^|/)\.git(/|$)", "git internals"),
    (r"(^|/)\.env($|\.)|(^|/)[^/]*\.env$", "environment/credential file"),
    (r"(^|/)(secrets?|credentials?)(/|\.|$)|(^|/)[^/]*(secret|credential|token|password)[^/]*\.(json|ya?ml|toml|txt)$",
     "credentials"),
    (r"\.(pem|key|p12|pfx|keystore)$|(^|/)id_(rsa|ed25519|ecdsa)", "private key"),
    (r"\.(db|sqlite3?|db-wal|db-shm|sqlite3?-wal|sqlite3?-shm)$", "database file"),
    (r"(^|/)(data|output|backups?)/", "data/output directory"),
    (r"(^|/)(venv|\.venv|node_modules)/", "environment directory"),
    (r"\.service$|\.timer$|(^|/)systemd/", "service unit"),
]
MIGRATION = r"(^|/)(migrations?|alembic)/|\.sql$|(^|/)schema[^/]*\.(py|sql)$"


class PromotionError(RuntimeError):
    pass


def _conn():
    conn = runs._conn()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS promotions (
            id TEXT PRIMARY KEY, run_id TEXT UNIQUE, project TEXT, destination TEXT, branch TEXT,
            dest_head TEXT, patch_path TEXT, patch_sha256 TEXT, manifest TEXT, checks TEXT,
            verification TEXT, status TEXT, nonce TEXT, created_at REAL, approved_at REAL,
            approved_via TEXT, expires_at REAL, applied_at REAL, recovery_dir TEXT, result TEXT,
            allow_unverified INTEGER DEFAULT 0
        );
        """
    )
    if "owner_pid" not in {r[1] for r in conn.execute("PRAGMA table_info(promotions)")}:
        conn.execute("ALTER TABLE promotions ADD COLUMN owner_pid INTEGER DEFAULT 0")
    return conn


def _git(args: list[str], cwd: str | Path, *, input_bytes: bytes | None = None, timeout: int = 120, untrusted: bool = False):
    from jarvis.security.owner.env_boundary import build_subprocess_env

    env = build_subprocess_env(extra={"GIT_TERMINAL_PROMPT": "0", "GIT_SSH_COMMAND": "false", "GIT_OPTIONAL_LOCKS": "0"})
    env.pop("SSH_AUTH_SOCK", None)
    env.pop("GIT_EXTERNAL_DIFF", None)
    if args and args[0] in ("diff", "show"):
        args = [args[0], "--no-ext-diff", "--no-textconv", *args[1:]]
    argv = ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args]
    if untrusted or workspace._inside(Path(cwd), workspace.workspaces_root()):
        argv = workspace.sandbox_argv(argv, str(cwd), network=False)
    return subprocess.run(argv, cwd=str(cwd), input=input_bytes, capture_output=True, timeout=timeout, env=env)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _row(pid: str) -> dict[str, Any] | None:
    with _conn() as conn:
        r = conn.execute("SELECT * FROM promotions WHERE id=?", (pid,)).fetchone()
    if not r:
        return None
    d = dict(r)
    for k in ("manifest", "checks", "verification", "result"):
        d[k] = json.loads(d[k]) if d.get(k) else ({} if k != "manifest" else [])
    return d


def get(pid: str) -> dict[str, Any] | None:
    d = _row(pid)
    if d:
        d.pop("nonce", None)
    return d


def list_promotions(*, status: str = "", project: str = "", limit: int = 50) -> list[dict[str, Any]]:
    recover_interrupted()
    q, args = "SELECT id FROM promotions WHERE 1=1", []
    if status:
        q += " AND status=?"
        args.append(status)
    if project:
        q += " AND project=?"
        args.append(project)
    with _conn() as conn:
        ids = [r["id"] for r in conn.execute(q + " ORDER BY created_at DESC LIMIT ?", (*args, limit)).fetchall()]
    return [p for p in (get(i) for i in ids) if p]


def _update(pid: str, **fields: Any) -> None:
    for k in ("manifest", "checks", "verification", "result"):
        if k in fields and not isinstance(fields[k], str):
            fields[k] = json.dumps(fields[k], default=str)
    with _conn() as conn:
        conn.execute(f"UPDATE promotions SET {', '.join(f'{k}=?' for k in fields)} WHERE id=?", (*fields.values(), pid))


# ---------------------------------------------------------------- 1–4: capture, check, verify, present


def capture(run: dict[str, Any]) -> tuple[bytes, list[dict[str, Any]]]:
    ws, base = run.get("workspace"), run.get("base_commit")
    if not ws or not Path(ws).is_dir() or not base:
        raise PromotionError("the run's workspace is gone; nothing to promote")
    _git(["add", "-A"], ws, untrusted=True)
    patch = _git(["diff", "--cached", "--no-renames", "--binary", "--full-index", base], ws, untrusted=True).stdout
    if not patch.strip():
        raise PromotionError("the run made no changes")
    if len(patch) > MAX_PATCH_BYTES:
        raise PromotionError(f"patch is {len(patch)} bytes; larger than the {MAX_PATCH_BYTES}-byte review limit")
    manifest = []
    raw = _git(["diff", "--cached", "--no-renames", "--raw", "-z", "--no-abbrev", base], ws, untrusted=True).stdout.decode(errors="replace")
    parts = [p for p in raw.split("\0") if p != ""]
    i = 0
    while i < len(parts):
        meta = parts[i].lstrip(":").split()
        status = meta[4] if len(meta) > 4 else "?"
        if status.startswith(("R", "C")):
            src, dst = parts[i + 1], parts[i + 2]
            i += 3
        else:
            src = dst = parts[i + 1]
            i += 2
        new = Path(ws) / dst
        if not workspace._inside(new.parent, Path(ws)) or any(
            parent.is_symlink() for parent in new.parents if parent != Path(ws) and workspace._inside(parent, Path(ws))):
            raise PromotionError("workspace manifest contains a symlink ancestor or escaped path")
        manifest.append({
            "path": dst, "source_path": src, "status": status[0], "old_mode": meta[0], "new_mode": meta[1],
            "base_sha256": _sha(_git(["show", f"{base}:{src}"], ws, untrusted=True).stdout) if status[0] not in ("A",) else None,
            "new_sha256": _sha(new.read_bytes()) if status[0] != "D" and new.is_file() and not new.is_symlink() else None,
            "symlink": new.is_symlink(),
        })
    return patch, manifest


def check(patch: bytes, manifest: list[dict], project: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    blocking, risks = [], []
    status = run.get("status")
    if status == contract.VIOLATION:
        blocking.append(f"the run itself was a boundary violation: {(run.get('result') or {}).get('reason')}")
    if status not in (contract.VERIFIED, contract.UNVERIFIED):
        blocking.append(f"run status is {status!r}; only verified runs (or explicitly accepted unverified ones) can be promoted")
    dest = Path(project["path"]).resolve()
    protected = [Path(p).expanduser() for p in project.get("protected_paths") or []]
    for f in manifest:
        path = f["path"]
        for pattern, why in DENY:
            if re.search(pattern, path, re.I):
                blocking.append(f"{path}: {why}")
        target = (dest / path).resolve()
        for prot in protected:
            prot = prot if prot.is_absolute() else dest / prot
            try:
                target.relative_to(prot.resolve())
                blocking.append(f"{path}: inside protected path {prot}")
            except ValueError:
                pass
        try:
            target.relative_to(dest)
        except ValueError:
            blocking.append(f"{path}: resolves outside the project")
        if f["symlink"] or "120000" in (f["old_mode"], f["new_mode"]):
            blocking.append(f"{path}: symlink")
        if f["new_mode"] == "160000" or f["old_mode"] == "160000":
            blocking.append(f"{path}: submodule")
        if f["status"] == "D":
            risks.append(f"{path}: deleted")
        if f["old_mode"] not in ("000000", f["new_mode"]) and f["status"] != "D":
            risks.append(f"{path}: mode {f['old_mode']} → {f['new_mode']}")
        if re.search(MIGRATION, path, re.I):
            risks.append(f"{path}: looks like a database migration — it will be copied, never run")
    if b"GIT binary patch" in patch:
        risks.append("contains binary changes")
    if len(manifest) > 25:
        risks.append(f"{len(manifest)} files changed")
    return {"blocking": blocking, "risks": risks, "ok": not blocking}


def verify_on_fresh_clone(patch: bytes, project: dict[str, Any], pid: str) -> dict[str, Any]:
    """Apply the patch to a new clone of the destination's current HEAD; run its tests there."""
    ws = workspace.prepare(project["path"], f"verify-{pid}")
    try:
        chk = _git(["apply", "--check", "--whitespace=nowarn", "-"], ws["workspace"], input_bytes=patch)
        if chk.returncode != 0:
            return {"applies": False, "detail": chk.stderr.decode(errors="replace")[-600:], "base": ws["base_commit"]}
        _git(["apply", "--whitespace=nowarn", "-"], ws["workspace"], input_bytes=patch)
        tests = workspace.run_tests(ws["workspace"], project.get("test_command") or "")
        return {"applies": True, "base": ws["base_commit"], "tests": tests, "clone": ws["workspace"]}
    finally:
        pass  # the verification clone is kept for inspection, like run workspaces


def propose(run_id: str, *, allow_unverified: bool = False) -> dict[str, Any]:
    from jarvis.coding_agents import projects

    run = runs.get_run(run_id)
    if not run:
        raise PromotionError("no such run")
    with _conn() as conn:
        existing = conn.execute("SELECT id FROM promotions WHERE run_id=?", (run_id,)).fetchone()
    if existing:
        return get(existing["id"]) or {}
    project = projects.get(run["project"])
    if not project:
        raise PromotionError(f"project {run['project']!r} is not registered")
    patch, manifest = capture(run)
    checks = check(patch, manifest, project, run)
    if run["status"] == contract.UNVERIFIED and not allow_unverified:
        checks["blocking"].append("changes were never verified by tests; promotion needs explicit acceptance of that")
        checks["ok"] = False
    pid = "prm_" + uuid.uuid4().hex[:10]
    pdir = ROOT / "promotions" / pid
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / "change.patch").write_bytes(patch)
    dest = Path(project["path"])
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], dest).stdout.decode().strip()
    head = _git(["rev-parse", "HEAD"], dest).stdout.decode().strip()
    verification = verify_on_fresh_clone(patch, project, pid) if checks["ok"] else {"skipped": "blocked by checks"}
    if checks["ok"] and not verification.get("applies"):
        checks["blocking"].append("the patch does not apply cleanly to the project's current HEAD")
    tests = verification.get("tests") or {}
    if checks["ok"] and not tests.get("ran") and not allow_unverified:
        checks["blocking"].append("verification did not run; verified promotion cannot proceed")
    if checks["ok"] and tests.get("ran") and not tests.get("passed"):
        checks["blocking"].append("the project's tests fail with the patch applied")
    if verification.get("base") and verification["base"] != head:
        checks["blocking"].append("the destination moved while verifying; propose again")
    checks["ok"] = not checks["blocking"]
    row = {
        "id": pid, "run_id": run_id, "project": project["slug"], "destination": str(dest), "branch": branch,
        "dest_head": head, "patch_path": str(pdir / "change.patch"), "patch_sha256": _sha(patch),
        "manifest": json.dumps(manifest), "checks": json.dumps(checks), "verification": json.dumps(verification, default=str),
        "status": PROPOSED if checks["ok"] else BLOCKED, "nonce": secrets.token_urlsafe(16), "created_at": time.time(),
        "approved_at": None, "approved_via": "", "expires_at": None, "applied_at": None, "recovery_dir": "",
        "result": json.dumps({}), "allow_unverified": 1 if allow_unverified else 0,
    }
    with _conn() as conn:
        conn.execute(f"INSERT INTO promotions ({','.join(row)}) VALUES ({','.join('?' * len(row))})", tuple(row.values()))
    _continuity(row["id"], "proposed")
    return get(pid) or {}


def approval_token(pid: str) -> str:
    r = _row(pid)
    return str(r["nonce"]) if r else ""


def summary_text(p: dict[str, Any]) -> str:
    files = ", ".join(f"{m['status']} {m['path']}" for m in p["manifest"][:15])
    tests = (p["verification"] or {}).get("tests") or {}
    t = ("passed" if tests.get("passed") else f"FAILED (exit {tests.get('exit_code')})") if tests.get("ran") \
        else (tests.get("reason") or "not run")
    lines = [
        f"**Promotion {p['id']}** → {p['destination']} (branch `{p['branch']}`, HEAD {p['dest_head'][:10]})",
        f"- From run {p['run_id']}; patch sha256 {p['patch_sha256'][:16]}…",
        f"- Files: {files}",
        f"- Tests on a fresh clone with the patch applied: {t}",
    ]
    if p["checks"].get("risks"):
        lines.append("- Risks: " + "; ".join(p["checks"]["risks"]))
    if p["checks"].get("blocking"):
        lines.append("- **Blocked:** " + "; ".join(p["checks"]["blocking"]))
    if p.get("allow_unverified"):
        lines.append("- **Unverified changes** — accepted as unverified, will be recorded that way")
    lines.append("- Applies to the working tree only: no commit, no push, no service restart, no migration run.")
    return "\n".join(lines)


# ---------------------------------------------------------------- 5–10: approve, preflight, recover, apply, verify


def approve(pid: str, *, token: str, via: str) -> dict[str, Any]:
    r = _row(pid)
    if not r:
        raise PromotionError("no such promotion")
    if not token or not secrets.compare_digest(str(r["nonce"]), str(token)):
        raise PromotionError("approval refused: missing or wrong promotion token")
    if r["status"] != PROPOSED:
        raise PromotionError(f"promotion is {r['status']}, not awaiting approval")
    if _sha(Path(r["patch_path"]).read_bytes()) != r["patch_sha256"]:
        raise PromotionError("the stored patch changed after review")
    now = time.time()
    with _conn() as conn:
        cur = conn.execute("UPDATE promotions SET status=?, approved_at=?, approved_via=?, expires_at=? "
                           "WHERE id=? AND status=?", (APPROVED, now, via, now + APPROVAL_TTL_S, pid, PROPOSED))
        if cur.rowcount != 1:
            raise PromotionError("promotion was approved or changed concurrently")
    _continuity(pid, "approved")
    return get(pid) or {}


def reject(pid: str, *, via: str = "chat") -> None:
    with _conn() as conn:
        conn.execute("UPDATE promotions SET status=?, approved_via=? WHERE id=? AND status IN (?,?)",
                     (REJECTED, via, pid, PROPOSED, APPROVED))
    _continuity(pid, "rejected")


@contextmanager
def _destination_lock(dest: str):
    ROOT.mkdir(parents=True, exist_ok=True)
    lock_path = ROOT / f"dest-{_sha(dest.encode())[:16]}.lock"
    with open(lock_path, "w") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise PromotionError("another promotion into this project is in progress") from exc
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _dirty_paths(dest: Path) -> set[str]:
    out = _git(["status", "--porcelain", "-z", "--untracked-files=all"], dest).stdout.decode(errors="replace")
    paths = set()
    entries = [e for e in out.split("\0") if e]
    i = 0
    while i < len(entries):
        e = entries[i]
        paths.add(e[3:])
        if e[:2].strip().startswith(("R", "C")):
            i += 1
            if i < len(entries):
                paths.add(entries[i])
        i += 1
    return paths


def preflight(p: dict[str, Any]) -> list[str]:
    dest = Path(p["destination"])
    problems = []
    from jarvis.coding_agents import projects

    project = projects.get(p["project"])
    if not project or Path(project["path"]).resolve() != dest.resolve():
        return ["project registration changed since review"]
    problems.extend(check(Path(p["patch_path"]).read_bytes(), p["manifest"], project,
                          runs.get_run(p["run_id"]) or {})["blocking"])
    if not (dest / ".git").exists():
        return ["destination is no longer a git repository"]
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], dest).stdout.decode().strip()
    head = _git(["rev-parse", "HEAD"], dest).stdout.decode().strip()
    if branch != p["branch"]:
        problems.append(f"destination branch changed ({p['branch']} → {branch})")
    if head != p["dest_head"]:
        problems.append(f"destination HEAD moved ({p['dest_head'][:10]} → {head[:10]}) since the patch was verified")
    touched = {m["path"] for m in p["manifest"]} | {m["source_path"] for m in p["manifest"]}
    dirty = touched & _dirty_paths(dest)
    if dirty:
        problems.append("uncommitted changes in files the patch touches (left untouched): " + ", ".join(sorted(dirty)))
    for m in p["manifest"]:
        cur = dest / m["path"]
        if m["status"] == "A" and cur.exists():
            problems.append(f"{m['path']} already exists in the destination")
    chk = _git(["apply", "--check", "--whitespace=nowarn", p["patch_path"]], dest)
    if chk.returncode != 0:
        problems.append("patch no longer applies cleanly: " + chk.stderr.decode(errors="replace")[-300:])
    return problems


def _snapshot(p: dict[str, Any], rdir: Path) -> dict[str, Any]:
    dest = Path(p["destination"])
    files = {}
    for path in sorted({m["path"] for m in p["manifest"]} | {m["source_path"] for m in p["manifest"]}):
        src = dest / path
        if src.is_file():
            target = rdir / "files" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            files[path] = {"existed": True, "sha256": _sha(src.read_bytes()), "mode": src.stat().st_mode}
        else:
            files[path] = {"existed": False}
    snap = {"head": p["dest_head"], "branch": p["branch"], "files": files, "taken_at": time.time()}
    (rdir / "snapshot.json").write_text(json.dumps(snap, indent=1))
    return snap


def _restore(dest: Path, rdir: Path, manifest: list[dict] | None = None) -> list[str]:
    snap = json.loads((rdir / "snapshot.json").read_text())
    reviewed = {m["path"]: m for m in manifest or []}
    # Check every file before restoring any. Tests can outlast an owner's edit;
    # automatic rollback must not overwrite that edit or follow a new symlink.
    for path, info in snap["files"].items():
        target = dest / path
        if target.is_symlink() or not workspace._inside(target, dest):
            raise PromotionError(f"recovery blocked: {path} changed to a symlink or resolves outside the project")
        if manifest is not None:
            current = _sha(target.read_bytes()) if target.is_file() else None
            original = info.get("sha256") if info["existed"] else None
            promoted = (reviewed.get(path) or {}).get("new_sha256")
            if current not in (original, promoted):
                raise PromotionError(f"recovery blocked: {path} changed after the promotion; owner edit left untouched")
    restored = []
    for path, info in snap["files"].items():
        target = dest / path
        if info["existed"]:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(rdir / "files" / path, target)
        elif target.exists():
            target.unlink()
        restored.append(path)
    return restored


def apply(pid: str, *, token: str = "", via: str = "") -> dict[str, Any]:
    """Apply an approved promotion. One approval → at most one application."""
    from jarvis.integration import policy

    r = _row(pid)
    if not r:
        raise PromotionError("no such promotion")
    if r["status"] in (APPLIED, ROLLED_BACK, FAILED, REVERTED):
        return get(pid) or {}  # replay: report, never re-apply
    if reason := policy.refusal("coding"):
        raise PromotionError(reason)
    if token and r["status"] == PROPOSED:
        approve(pid, token=token, via=via or "chat_confirmation")
    now = time.time()
    with _conn() as conn:
        cur = conn.execute("UPDATE promotions SET status=?, owner_pid=? WHERE id=? AND status=? AND expires_at>?",
                           (APPLYING, os.getpid(), pid, APPROVED, now))
        if cur.rowcount != 1:
            state = conn.execute("SELECT status, expires_at FROM promotions WHERE id=?", (pid,)).fetchone()
            if state and state["status"] == APPROVED:
                conn.execute("UPDATE promotions SET status=? WHERE id=?", (EXPIRED, pid))
                raise PromotionError("promotion approval expired; review it again")
            raise PromotionError(f"promotion is not approved (status: {state['status'] if state else 'missing'})")
    p = get(pid) or {}
    dest = Path(p["destination"])
    result: dict[str, Any] = {"steps": []}
    _owned.add(pid)
    try:
        with _destination_lock(str(dest.resolve())):
            if _sha(Path(p["patch_path"]).read_bytes()) != p["patch_sha256"]:
                return _end(pid, FAILED, result, "stored patch no longer matches the reviewed hash; nothing applied")
            problems = preflight(p)
            result["steps"].append({"preflight": problems or "ok"})
            if problems:
                return _end(pid, FAILED, result, "destination changed or conflicts; nothing applied: " + "; ".join(problems))
            rdir = ROOT / "promotions" / pid / "recovery"
            rdir.mkdir(parents=True, exist_ok=True)
            _snapshot(p, rdir)
            _update(pid, recovery_dir=str(rdir))
            result["steps"].append({"recovery_point": str(rdir)})
            done = _git(["apply", "--whitespace=nowarn", p["patch_path"]], dest)
            if done.returncode != 0:
                _restore(dest, rdir, p["manifest"])
                return _end(pid, ROLLED_BACK, result, "git apply failed; recovery point restored: "
                            + done.stderr.decode(errors="replace")[-300:])
            mismatches = []
            for m in p["manifest"]:
                f = dest / m["path"]
                if m["status"] == "D":
                    if f.exists():
                        mismatches.append(f"{m['path']} still exists")
                elif m["new_sha256"] and (not f.is_file() or _sha(f.read_bytes()) != m["new_sha256"]):
                    mismatches.append(f"{m['path']} differs from the reviewed content")
            result["steps"].append({"files_match_manifest": not mismatches})
            if mismatches:
                _restore(dest, rdir, p["manifest"])
                return _end(pid, ROLLED_BACK, result, "applied files did not match the review; restored: "
                            + "; ".join(mismatches))
            try:
                tests = run_tests_in_place(str(dest), _project_test_command(p["project"]))
            except (OSError, subprocess.TimeoutExpired) as exc:
                tests = {"ran": False, "passed": False, "error": f"verification unavailable: {exc}"}
            result["tests_after_apply"] = tests
            if tests.get("error") or (tests.get("ran") and not tests.get("passed")) or (not tests.get("ran") and not p["allow_unverified"]):
                _restore(dest, rdir, p["manifest"])
                return _end(pid, ROLLED_BACK, result, "tests failed after applying; recovery point restored")
            result["verified"] = tests.get("passed") is True
            return _end(pid, APPLIED, result, "applied to the working tree"
                        + ("; tests passed in place" if tests.get("passed") else "; no test command — unverified"),
                        applied=True)
    except PromotionError as exc:
        return _end(pid, FAILED, result, str(exc))
    finally:
        _owned.discard(pid)


_owned: set[str] = set()  # promotions this process is applying right now


def recover_interrupted() -> list[str]:
    """A promotion left 'applying' by a dead ARIA process is put back, never re-applied.

    Files that hold the promoted content are restored from the recovery point;
    files matching neither the original nor the promoted content are left alone
    and named. Nothing is applied again.
    """
    with _conn() as conn:
        stuck = [r["id"] for r in conn.execute("SELECT id FROM promotions WHERE status=?", (APPLYING,)).fetchall()]
    recovered = []
    for pid in stuck:
        p = get(pid) or {}
        if pid in _owned or runs._alive(p.get("owner_pid") or 0):
            continue
        try:
            with _destination_lock(str(Path(p.get("destination") or "").resolve())):
                if (get(pid) or {}).get("status") == APPLYING:
                    _recover_promotion(pid, p)
                    recovered.append(pid)
        except PromotionError:
            continue  # a live writer holds the destination lock
    return recovered


def _recover_promotion(pid: str, p: dict[str, Any]) -> None:
    rdir = Path(p.get("recovery_dir") or "")
    dest = Path(p.get("destination") or "")
    result = dict(p.get("result") or {})
    if not (rdir / "snapshot.json").is_file():
        result["reason"] = "ARIA stopped before the recovery point was taken; nothing was applied"
        _update(pid, status=FAILED, result=result)
        return
    snap = json.loads((rdir / "snapshot.json").read_text())
    manifest = {m["path"]: m for m in p.get("manifest") or []}
    restored, foreign = [], []
    for path, info in snap["files"].items():
        f = dest / path
        if f.is_symlink() or not workspace._inside(f, dest):
            foreign.append(path)
            continue
        current = _sha(f.read_bytes()) if f.is_file() else None
        promoted = (manifest.get(path) or {}).get("new_sha256")
        original = info.get("sha256") if info.get("existed") else None
        if current == original:
            continue
        if current == promoted or (promoted is None and current is None):
            if info.get("existed"):
                f.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(rdir / "files" / path, f)
            elif f.exists():
                f.unlink()
            restored.append(path)
        else:
            foreign.append(path)
    result.update(reason="ARIA stopped mid-promotion; restored the recovery point"
                  + (f" (left untouched, changed by someone else: {', '.join(foreign)})" if foreign else ""),
                  restored=restored, interrupted=True)
    _update(pid, status=ROLLED_BACK, result=result)
    _continuity(pid, ROLLED_BACK, result["reason"])



def _project_test_command(slug: str) -> str:
    from jarvis.coding_agents import projects

    return (projects.get(slug) or {}).get("test_command") or ""


def run_tests_in_place(dest: str, command: str, *, timeout: int = 900) -> dict[str, Any]:
    """Tests in the real project, with the project mounted read-only (no network)."""
    from jarvis.security.owner.env_boundary import build_subprocess_env

    if not command.strip():
        return {"ran": False, "reason": "no test command configured"}
    bw = shutil.which("bwrap")
    if not bw:
        return {"ran": False, "reason": "bubblewrap unavailable; not running tests against the real project"}
    argv = workspace.sandbox_argv(["sh", "-c", command], dest, network=False, read_only=True,
                                 readable=workspace.verification_readables(dest, command, in_place=True))
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=build_subprocess_env(),
                              stdin=subprocess.DEVNULL)
        output = (proc.stdout or "") + (proc.stderr or "")
        logs = ROOT / "verification"
        logs.mkdir(parents=True, exist_ok=True)
        log_path = logs / f"tests-{time.time_ns()}.log"
        log_path.write_text(output)
        return {"ran": True, "command": command, "exit_code": proc.returncode, "passed": proc.returncode == 0,
                "output_tail": output[-2000:], "output_log": str(log_path),
                "sandbox": "bwrap: private roots/PID/IPC, project/toolchains read-only, no network"}
    except subprocess.TimeoutExpired:
        return {"ran": True, "command": command, "passed": False, "error": f"timed out after {timeout}s"}
    except OSError as exc:
        return {"ran": False, "command": command, "passed": False, "error": f"verification unavailable: {exc}"}


def _end(pid: str, status: str, result: dict[str, Any], reason: str, *, applied: bool = False) -> dict[str, Any]:
    p = get(pid) or {}
    result["reason"] = reason
    result["rollback"] = rollback_procedure(p) if applied else None
    _update(pid, status=status, result=result, applied_at=time.time() if applied else None)
    _continuity(pid, status, reason)
    return get(pid) or {}


def rollback_procedure(p: dict[str, Any]) -> str:
    return (f"Say \"roll back promotion {p['id']}\" (or POST /api/coding-agents/promotions/{p['id']}/rollback). "
            f"ARIA restores the exact pre-promotion copies from {p.get('recovery_dir') or '<recovery dir>'} — "
            "only if those files are still exactly as promoted; later edits are never overwritten. "
            "Manual: copy files/<path> back over the project, and delete files the snapshot marks as not existing.")


def rollback(pid: str) -> dict[str, Any]:
    p = get(pid)
    if not p:
        raise PromotionError("no such promotion")
    if p["status"] != APPLIED:
        raise PromotionError(f"promotion is {p['status']}; only applied promotions can be rolled back")
    dest = Path(p["destination"])
    rdir = Path(p["recovery_dir"])
    with _destination_lock(str(dest.resolve())):
        edited = []
        for m in p["manifest"]:
            f = dest / m["path"]
            if m["status"] == "D":
                if f.exists():
                    edited.append(m["path"])
            elif m["new_sha256"] and (not f.is_file() or _sha(f.read_bytes()) != m["new_sha256"]):
                edited.append(m["path"])
        if edited:
            raise PromotionError("files changed after the promotion; not overwriting them: " + ", ".join(edited))
        restored = _restore(dest, rdir, p["manifest"])
    result = {**(p.get("result") or {}), "rolled_back_at": time.time(), "restored": restored}
    _update(pid, status=REVERTED, result=result)
    _continuity(pid, REVERTED, "rolled back by the owner")
    return get(pid) or {}


def _continuity(pid: str, status: str, detail: str = "") -> None:
    """Promotion lifecycle in continuity (never ACM)."""
    try:
        from jarvis.continuity import store

        p = get(pid) or {}
        files = ", ".join(m["path"] for m in (p.get("manifest") or [])[:8])
        text = (f"Change promotion {pid} (run {p.get('run_id')}) into {p.get('project')}: {status}"
                + (f" — {detail}" if detail else "") + (f". Files: {files}" if files else ""))
        record_status = {
            "proposed": store.PROPOSED, "approved": store.ACCEPTED, "rejected": store.REJECTED,
            APPLIED: store.DONE, REVERTED: store.SUPERSEDED,
        }.get(status, store.FAILED if status in (FAILED, ROLLED_BACK, BLOCKED, EXPIRED) else store.OPEN)
        store.add_record(
            store.OUTCOME if status in (APPLIED, FAILED, ROLLED_BACK, REVERTED) else store.SUGGESTION,
            text, actor=store.MISSION if status in (APPLIED, FAILED, ROLLED_BACK, REVERTED) else store.ASSISTANT,
            status=record_status, project=p.get("project") or "",
            source_ref=f"coding_promotion:{pid}:{status}",
            verified=status == APPLIED and bool((p.get("result") or {}).get("verified")),
            detail={"promotion_id": pid, "run_id": p.get("run_id"), "status": status},
        )
    except Exception:
        pass
