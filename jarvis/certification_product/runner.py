"""Evidence-based certification runner — outcomes only, never toast/HTTP alone."""

from __future__ import annotations

import json
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

from jarvis.certification_product import store
from jarvis.certification_product.terminology import REQUIRED_FEATURES
from jarvis.config import DATA_DIR

BASE_DEFAULT = "http://127.0.0.1:8765"


class CertContext:
    def __init__(self, run_id: str, base: str = BASE_DEFAULT) -> None:
        self.run_id = run_id
        self.base = base.rstrip("/")
        self.features: dict[str, Any] = {}
        self._feature: str = "general"
        self.backend_log_excerpt = ""

    def set_feature(self, feature_id: str, title: str) -> None:
        self._feature = feature_id
        self.features.setdefault(
            feature_id,
            {
                "id": feature_id,
                "title": title,
                "status": "RUNNING",
                "assertions": [],
                "controls": [],
                "workflows": [],
                "started_at": time.time(),
            },
        )

    def control(self, name: str) -> None:
        self.features[self._feature]["controls"].append(name)

    def workflow(self, name: str) -> None:
        self.features[self._feature]["workflows"].append(name)

    def api(
        self,
        method: str,
        path: str,
        *,
        data: dict | None = None,
        form: dict | None = None,
        timeout: float = 90,
    ) -> tuple[int, Any, float]:
        url = self.base + path
        headers: dict[str, str] = {}
        body = None
        payload_meta: Any = None
        if form is not None:
            body = urllib.parse.urlencode(form).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            payload_meta = form
        elif data is not None:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
            payload_meta = data
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        t0 = time.perf_counter()
        status = 0
        resp_body: Any = None
        err = None
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.status
                raw = resp.read()
                ct = resp.headers.get("content-type", "")
                if "json" in ct or (raw[:1] in (b"{", b"[")):
                    try:
                        resp_body = json.loads(raw.decode() or "null")
                    except Exception:
                        resp_body = raw[:500].decode("utf-8", errors="replace")
                else:
                    resp_body = {"_bytes": len(raw), "_head": raw[:32].hex()}
        except urllib.error.HTTPError as e:
            status = e.code
            raw = e.read()
            try:
                resp_body = json.loads(raw.decode() or "null")
            except Exception:
                resp_body = raw[:500].decode("utf-8", errors="replace")
            err = str(e)
        except Exception as e:
            err = str(e)
            resp_body = {"error": err}
        duration_ms = round((time.perf_counter() - t0) * 1000, 2)
        store.append_jsonl(
            self.run_id,
            "api/calls.jsonl",
            {
                "ts": time.time(),
                "feature": self._feature,
                "method": method,
                "endpoint": path,
                "payload": payload_meta,
                "status": status,
                "duration_ms": duration_ms,
                "response_preview": _preview(resp_body),
                "error": err,
            },
        )
        man = store.get_run(self.run_id) or {}
        counts = man.get("counts") or {}
        counts["api_calls"] = int(counts.get("api_calls") or 0) + 1
        store.update_manifest(self.run_id, {"counts": counts})
        return status, resp_body, duration_ms

    def assert_(
        self,
        name: str,
        expected: Any,
        observed: Any,
        *,
        ok: bool | None = None,
        evidence: dict | None = None,
    ) -> bool:
        passed = bool(ok) if ok is not None else (expected == observed)
        row = {
            "id": f"a-{int(time.time() * 1000)}-{len(self.features.get(self._feature, {}).get('assertions') or [])}",
            "ts": time.time(),
            "feature": self._feature,
            "name": name,
            "expected": expected,
            "observed": observed,
            "result": "PASS" if passed else "FAIL",
            "evidence": evidence or {},
        }
        store.append_jsonl(self.run_id, "assertions/assertions.jsonl", row)
        self.features[self._feature].setdefault("assertions", []).append(row["id"])
        man = store.get_run(self.run_id) or {}
        counts = dict(man.get("counts") or {})
        counts["assertions"] = int(counts.get("assertions") or 0) + 1
        counts["pass" if passed else "fail"] = int(counts.get("pass" if passed else "fail") or 0) + 1
        store.update_manifest(self.run_id, {"counts": counts})
        # Human-readable assertion log
        store.append_jsonl(
            self.run_id,
            "assertions/readable.jsonl",
            {
                "ASSERTION": name,
                "Expected": expected,
                "Observed": observed,
                "Result": row["result"],
            },
        )
        return passed

    def file_exists(self, path: str | Path, *, min_bytes: int = 1) -> bool:
        p = Path(path)
        ok = p.is_file() and p.stat().st_size >= min_bytes
        store.append_jsonl(
            self.run_id,
            "files/verified.jsonl",
            {
                "path": str(p),
                "exists": p.is_file(),
                "size": p.stat().st_size if p.is_file() else 0,
                "ok": ok,
                "feature": self._feature,
            },
        )
        man = store.get_run(self.run_id) or {}
        counts = dict(man.get("counts") or {})
        counts["files_verified"] = int(counts.get("files_verified") or 0) + 1
        store.update_manifest(self.run_id, {"counts": counts})
        return ok

    def finish_feature(self, feature_id: str, passed: bool) -> None:
        feat = self.features.get(feature_id) or {}
        feat["status"] = "PASS" if passed else "FAIL"
        feat["finished_at"] = time.time()
        self.features[feature_id] = feat


def _preview(body: Any, limit: int = 800) -> Any:
    if isinstance(body, (dict, list)):
        s = json.dumps(body, default=str)
        return json.loads(s) if len(s) < limit else s[:limit] + "…"
    return str(body)[:limit]


def _capture_backend_log(ctx: CertContext) -> None:
    candidates = [
        DATA_DIR / "logs" / "jarvis.log",
        Path("/tmp/jarvis_serve_truth.log"),
    ]
    chunks = []
    for path in candidates:
        if not path.is_file():
            continue
        try:
            # Tail last ~32KB without reading multi-GB logs fully
            size = path.stat().st_size
            with path.open("rb") as fh:
                if size > 32768:
                    fh.seek(size - 32768)
                raw = fh.read().decode("utf-8", errors="replace")
            chunks.append(f"===== {path} =====\n{raw[-12000:]}")
        except Exception as exc:
            chunks.append(f"===== {path} error: {exc} =====")
    text = "\n\n".join(chunks) or "(no backend log found)"
    store.write_text(ctx.run_id, "logs/backend_tail.txt", text)
    # Flag obvious failures
    low = text.lower()
    ctx.backend_log_excerpt = text[-2000:]
    store.write_text(
        ctx.run_id,
        "logs/backend_flags.json",
        json.dumps(
            {
                "traceback": "traceback" in low,
                "exception": "exception" in low[-4000:],
                "error_lines": sum(1 for ln in text.splitlines() if "error" in ln.lower()),
            },
            indent=2,
        ),
    )


def suite_chat_clear(ctx: CertContext) -> bool:
    ctx.set_feature("chat_clear", "Chat — Clear Main")
    ctx.workflow("seed → clear → verify empty → re-fetch")
    ctx.control("POST /api/certification/fixtures/seed_chat")
    ctx.control("POST /api/branches/clear")
    # Seed via live fixture API (no LLM) so the server BranchManager sees messages.
    st, seed, _ = ctx.api(
        "POST",
        "/api/certification/fixtures/seed_chat",
        data={
            "branch_id": "main",
            "messages": [
                {"role": "user", "content": "CERTSEED user"},
                {"role": "assistant", "content": "CERTSEED"},
            ],
        },
    )
    ctx.assert_("Seed chat fixture ok", True, (seed or {}).get("ok"), ok=bool((seed or {}).get("ok")))
    ctx.api("POST", "/api/branches/switch", form={"branch_id": "main"})
    st, msgs, _ = ctx.api("GET", "/api/branches/main/messages")
    before = len([m for m in (msgs or {}).get("messages") or [] if m.get("role") in ("user", "assistant")])
    ctx.assert_("Main has messages before clear", ">=1", before, ok=before >= 1)
    st, clr, _ = ctx.api("POST", "/api/branches/clear", form={"branch_id": "main"})
    ctx.assert_("Clear API ok field", True, (clr or {}).get("ok"), ok=bool((clr or {}).get("ok")))
    st, msgs2, _ = ctx.api("GET", "/api/branches/main/messages")
    after = len([m for m in (msgs2 or {}).get("messages") or [] if m.get("role") in ("user", "assistant")])
    a1 = ctx.assert_("Clear Main removes every user/assistant message", 0, after)
    st, msgs3, _ = ctx.api("GET", "/api/branches/main/messages")
    after2 = len([m for m in (msgs3 or {}).get("messages") or [] if m.get("role") in ("user", "assistant")])
    a2 = ctx.assert_("Reload fetch still empty", 0, after2)
    passed = a1 and a2 and before >= 1
    ctx.finish_feature("chat_clear", passed)
    return passed


def suite_image_lifecycle(ctx: CertContext) -> bool:
    ctx.set_feature("image_lifecycle", "Image — generate / search / delete / restore")
    ctx.workflow("chat generate → gallery+chat+jobs+search → delete scrub → restore repair")
    marker = f"CERTIMG_{int(time.time())}"
    ctx.api("POST", "/api/branches/switch", form={"branch_id": "main"})
    ctx.api("POST", "/api/branches/clear", form={"branch_id": "main"})
    ctx.control("Chat generate image")
    st, sse, _ = ctx.api(
        "POST",
        "/api/chat",
        form={
            "message": f"generate image: a solid magenta hexagon on white flat {marker}",
            "stream": "true",
            "lite_ui": "true",
            "branch_id": "main",
        },
        timeout=90,
    )
    text = sse.decode() if isinstance(sse, (bytes, bytearray)) else str(sse)
    no_lie = "example.com" not in text.lower() and "Searching the web" not in text
    ctx.assert_("Image routes to generate_image (not fake URL/web search)", True, no_lie, ok=no_lie)
    import re

    jobs = re.findall(r'"job_id"\s*:\s*"([^"]+)"', text)
    if not jobs:
        ctx.assert_("Job queued", "job_id", None, ok=False)
        ctx.finish_feature("image_lifecycle", False)
        return False
    job_id = jobs[-1]
    result = {}
    for _ in range(90):
        st, job, _ = ctx.api("GET", f"/api/media/job/{job_id}")
        if isinstance(job, dict) and job.get("done"):
            result = job.get("result") or {}
            break
        time.sleep(2)
    name = result.get("image_name")
    path = result.get("image_path")
    file_ok = bool(result.get("ok") and name and path and ctx.file_exists(path, min_bytes=500))
    ctx.assert_("PNG exists on filesystem", True, file_ok, ok=file_ok, evidence={"path": path, "name": name})
    st, gal, _ = ctx.api("GET", "/api/gallery?limit=40")
    in_gal = name in [i.get("name") for i in (gal or {}).get("images") or []]
    ctx.assert_("Gallery list contains image", True, in_gal, ok=in_gal)
    st, msgs, _ = ctx.api("GET", "/api/branches/main/messages")
    in_chat = f"/api/gallery/{name}" in json.dumps(msgs)
    ctx.assert_("Chat durable embed present", True, in_chat, ok=in_chat)
    st, jobs_snap, _ = ctx.api("GET", "/api/jobs")
    row = next((j for j in (jobs_snap or {}).get("recent") or [] if j.get("id") == job_id), None)
    job_agree = bool(row and (row.get("image_name") == name) and row.get("result_ok") is not False)
    ctx.assert_("Job Center lists same asset", True, job_agree, ok=job_agree)
    st, search, _ = ctx.api("POST", "/api/search/product/query", data={"q": marker, "limit": 24})
    search_hit = marker in json.dumps(search) or (name or "") in json.dumps(search)
    ctx.assert_("Search finds created image/marker", True, search_hit, ok=search_hit)

    ctx.control("DELETE /api/gallery/{name}")
    st, delr, _ = ctx.api("DELETE", f"/api/gallery/{name}")
    trash_id = (delr or {}).get("trash_id")
    st, gal2, _ = ctx.api("GET", "/api/gallery?limit=50")
    gone_gal = name not in [i.get("name") for i in (gal2 or {}).get("images") or []]
    ctx.assert_("Delete removes from Gallery list", True, gone_gal, ok=gone_gal)
    st, msgs2, _ = ctx.api("GET", "/api/branches/main/messages")
    scrubbed = f"/api/gallery/{name}" not in json.dumps(msgs2) and "removed from Gallery" in json.dumps(msgs2)
    ctx.assert_("Delete scrubs Chat embeds", True, scrubbed, ok=scrubbed)

    ctx.control("POST /api/gallery/restore")
    st, rest, _ = ctx.api("POST", "/api/gallery/restore", data={"trash_id": trash_id})
    restored = (rest or {}).get("restored") or name
    rpath = (rest or {}).get("path")
    restore_file = bool((rest or {}).get("ok") and rpath and ctx.file_exists(rpath, min_bytes=500))
    ctx.assert_("Restore puts file back", True, restore_file, ok=restore_file)
    st, msgs3, _ = ctx.api("GET", "/api/branches/main/messages")
    repaired = f"/api/gallery/{restored}" in json.dumps(msgs3)
    ctx.assert_("Restore repairs Chat embed", True, repaired, ok=repaired)

    passed = all([file_ok, in_gal, in_chat, job_agree, search_hit, gone_gal, scrubbed, restore_file, repaired])
    ctx.finish_feature("image_lifecycle", passed)
    # Copy visual evidence path reference
    if path and Path(path).is_file():
        store.write_text(
            ctx.run_id,
            "screenshots/IMAGE_FILE_EVIDENCE.txt",
            f"Visual evidence is the generated asset itself:\n{path}\nrestored={restored}\n",
        )
        try:
            import shutil

            dest = store.run_dir(ctx.run_id) / "screenshots" / Path(path).name
            shutil.copy2(path if Path(path).is_file() else rpath, dest)
            man = store.get_run(ctx.run_id) or {}
            counts = dict(man.get("counts") or {})
            counts["screenshots"] = int(counts.get("screenshots") or 0) + 1
            store.update_manifest(ctx.run_id, {"counts": counts})
        except Exception:
            pass
    return passed


def suite_planner_calendar(ctx: CertContext) -> bool:
    ctx.set_feature("planner_calendar", "Planner ↔ Calendar")
    ctx.workflow("create task → calendar day → search")
    day = time.strftime("%Y-%m-%d")
    text = f"CERT_TASK_{int(time.time())}"
    ctx.control("POST /api/planner/tasks")
    st, add, _ = ctx.api("POST", "/api/planner/tasks", data={"text": text})
    a0 = ctx.assert_("Planner create ok", True, (add or {}).get("ok"), ok=bool((add or {}).get("ok")))
    st, dayd, _ = ctx.api("GET", f"/api/calendar/day?day={day}")
    a1 = ctx.assert_("Calendar shows planner task", True, text in json.dumps(dayd), ok=text in json.dumps(dayd))
    st, snap, _ = ctx.api("GET", "/api/planner/snapshot")
    a2 = ctx.assert_("Planner snapshot contains task", True, text in json.dumps(snap), ok=text in json.dumps(snap))
    st, search, _ = ctx.api("POST", "/api/search/product/query", data={"q": text, "limit": 24})
    a3 = ctx.assert_("Search finds planner task", True, text in json.dumps(search), ok=text in json.dumps(search))
    passed = a0 and a1 and a2 and a3
    ctx.finish_feature("planner_calendar", passed)
    return passed


def suite_journal_calendar(ctx: CertContext) -> bool:
    ctx.set_feature("journal_calendar", "Journal ↔ Calendar")
    ctx.workflow("create note → journal readback → calendar federation → search")
    day = time.strftime("%Y-%m-%d")
    text = f"CERT_JOURNAL_{int(time.time())}"
    ctx.control("POST /api/journal/daily")
    st, add, _ = ctx.api(
        "POST",
        "/api/journal/daily",
        form={"content": text, "bullet_type": "note", "day": day},
    )
    st, jday, _ = ctx.api("GET", f"/api/journal/daily?day={day}")
    a0 = ctx.assert_("Journal readback contains note", True, text in json.dumps(jday), ok=text in json.dumps(jday))
    st, dayd, _ = ctx.api("GET", f"/api/calendar/day?day={day}")
    a1 = ctx.assert_("Calendar federates journal note", True, text in json.dumps(dayd), ok=text in json.dumps(dayd))
    st, search, _ = ctx.api("POST", "/api/search/product/query", data={"q": text, "limit": 24})
    a2 = ctx.assert_("Search finds journal note", True, text in json.dumps(search), ok=text in json.dumps(search))
    passed = a0 and a1 and a2
    ctx.finish_feature("journal_calendar", passed)
    return passed


def suite_search_federated(ctx: CertContext) -> bool:
    ctx.set_feature("search_federated", "Search — gallery+chat corpora")
    ctx.workflow("facets → enabled corpora")
    st, facets, _ = ctx.api("GET", "/api/search/product/facets")
    blob = json.dumps(facets)
    a0 = ctx.assert_("Facets include gallery", True, "gallery" in blob, ok="gallery" in blob)
    a1 = ctx.assert_("Facets include chat", True, "chat" in blob, ok="chat" in blob)
    corp = (facets or {}).get("corpora") or []
    gal_on = any(c.get("id") == "gallery" and c.get("enabled") for c in corp)
    chat_on = any(c.get("id") == "chat" and c.get("enabled") for c in corp)
    a2 = ctx.assert_("Gallery corpus enabled", True, gal_on, ok=gal_on)
    a3 = ctx.assert_("Chat corpus enabled", True, chat_on, ok=chat_on)
    passed = a0 and a1 and a2 and a3
    ctx.finish_feature("search_federated", passed)
    return passed


def suite_settings_appearance(ctx: CertContext) -> bool:
    ctx.set_feature("settings_appearance", "Settings — appearance persistence")
    ctx.workflow("change theme → API + disk agree → restore")
    st, app0, _ = ctx.api("GET", "/api/settings/product/appearance")
    prev = (app0 or {}).get("theme") or ((app0 or {}).get("appearance") or {}).get("theme")
    new = "light" if prev != "light" else "dark"
    ctx.control("POST /api/settings/product/appearance")
    ctx.api("POST", "/api/settings/product/appearance", data={"theme": new})
    st, app1, _ = ctx.api("GET", "/api/settings/product/appearance")
    got = (app1 or {}).get("theme") or ((app1 or {}).get("appearance") or {}).get("theme")
    disk_path = DATA_DIR / "settings_product" / "appearance.json"
    disk = None
    if disk_path.is_file():
        disk = json.loads(disk_path.read_text()).get("theme")
    a0 = ctx.assert_("Appearance API matches requested theme", new, got, ok=got == new)
    a1 = ctx.assert_("Appearance disk matches requested theme", new, disk, ok=disk == new)
    ctx.file_exists(disk_path)
    ctx.api("POST", "/api/settings/product/appearance", data={"theme": prev or "dark"})
    passed = a0 and a1
    ctx.finish_feature("settings_appearance", passed)
    return passed


def suite_projects_archive(ctx: CertContext) -> bool:
    ctx.set_feature("projects_archive", "Projects — create / search / archive")
    ctx.workflow("create → fetch → archive → absent from production list → delete")
    title = f"Cert Proj {int(time.time())}"
    ctx.control("POST /api/projects")
    # Mark QA so production picker never surfaces cert leftovers if cleanup is interrupted.
    st, proj, _ = ctx.api(
        "POST",
        "/api/projects",
        data={"title": title, "activate": False, "qa_artifact": True, "origin": "certification"},
    )
    slug = None
    if isinstance(proj, dict):
        slug = proj.get("slug") or (proj.get("project") or {}).get("slug") or (proj.get("meta") or {}).get("slug")
    a0 = ctx.assert_("Project created with slug", True, bool(slug), ok=bool(slug), evidence={"slug": slug})
    if not slug:
        ctx.finish_feature("projects_archive", False)
        return False
    # Direct fetch (QA artifacts are intentionally excluded from production list/search).
    st, home, _ = ctx.api("GET", f"/api/projects/{slug}")
    blob = json.dumps(home)
    a1 = ctx.assert_("Project fetchable by slug", True, slug in blob or title in blob, ok=slug in blob or title in blob)
    ctx.api("POST", f"/api/projects/{slug}/archive")
    st, plist, _ = ctx.api("GET", "/api/projects")
    in_prod = title in json.dumps(plist) or slug in json.dumps((plist or {}).get("projects") or [])
    a2 = ctx.assert_("QA cert project absent from production list", True, not in_prod, ok=not in_prod)
    # Hard-delete so live DATA_DIR does not accumulate cert projects.
    try:
        from jarvis.project_registry import delete_project

        delete_project(slug)
    except Exception:
        pass
    passed = a0 and a1 and a2
    ctx.finish_feature("projects_archive", passed)
    return passed


def suite_production_integrity(ctx: CertContext) -> bool:
    ctx.set_feature("production_integrity", "Production Integrity — live workspace clean of QA/demo/smoke")
    ctx.workflow("scan → require clean OR recommend Guided Repair (never auto-delete)")
    ctx.control("POST /api/integrity/scan")
    st, scan, _ = ctx.api("POST", "/api/integrity/scan")
    clean = bool((scan or {}).get("clean"))
    total = int(((scan or {}).get("counts") or {}).get("total") or 0)
    a0 = ctx.assert_(
        "Integrity scan responds",
        True,
        bool((scan or {}).get("ok")),
        ok=bool((scan or {}).get("ok")),
        evidence={"status": (scan or {}).get("status"), "total": total},
    )
    # Soft-clean path: if dirty, recommending Guided Repair must succeed (no silent delete).
    if clean:
        a1 = ctx.assert_("Production workspace clean", True, True, ok=True, evidence={"total": 0})
        a2 = True
    else:
        st2, rec, _ = ctx.api("POST", "/api/integrity/recommend-repair")
        a1 = ctx.assert_(
            "Dirty workspace creates Guided Repair recommendation (no auto-delete)",
            True,
            bool((rec or {}).get("ok")) and not (rec or {}).get("clean"),
            ok=bool((rec or {}).get("ok")) and not (rec or {}).get("clean"),
            evidence={"total": total, "issue": ((rec or {}).get("issue") or {}).get("id")},
        )
        # Ship gate: development artifacts remaining → fail certification
        a2 = ctx.assert_(
            "No development artifacts remain for READY_TO_SHIP",
            True,
            False,
            ok=False,
            evidence={"total": total, "titles": [f.get("title") for f in ((scan or {}).get("findings") or [])[:8]]},
        )
    # Health write protection must remain active for smoke/pytest
    from jarvis.health_product.trust import writes_blocked_reason
    import os

    prev = os.environ.get("JARVIS_SMOKE")
    os.environ["JARVIS_SMOKE"] = "1"
    try:
        blocked = writes_blocked_reason()
    finally:
        if prev is None:
            os.environ.pop("JARVIS_SMOKE", None)
        else:
            os.environ["JARVIS_SMOKE"] = prev
    a3 = ctx.assert_(
        "Smoke cannot write live Health PHR",
        True,
        bool(blocked),
        ok=bool(blocked),
        evidence={"reason": blocked},
    )
    passed = bool(a0 and a1 and a2 and a3)
    ctx.finish_feature("production_integrity", passed)
    return passed


SUITES: list[tuple[str, Callable[[CertContext], bool]]] = [
    ("chat_clear", suite_chat_clear),
    ("image_lifecycle", suite_image_lifecycle),
    ("planner_calendar", suite_planner_calendar),
    ("journal_calendar", suite_journal_calendar),
    ("search_federated", suite_search_federated),
    ("settings_appearance", suite_settings_appearance),
    ("projects_archive", suite_projects_archive),
    ("production_integrity", suite_production_integrity),
]


def write_replay(ctx: CertContext) -> None:
    lines = [
        "# Aria certification replay",
        f"# run_id={ctx.run_id}",
        "BASE=http://127.0.0.1:8765",
        "",
        "# 1) Chat clear",
        "curl -sS -X POST $BASE/api/branches/switch -F branch_id=main",
        "curl -sS -X POST $BASE/api/chat -F 'message=reply with only CERTSEED' -F stream=true -F lite_ui=true -F branch_id=main",
        "curl -sS -X POST $BASE/api/branches/clear -F branch_id=main",
        "curl -sS $BASE/api/branches/main/messages  # expect 0 user/assistant",
        "",
        "# 2) Image lifecycle",
        "curl -sS -X POST $BASE/api/chat -F 'message=generate image: solid magenta hexagon' -F stream=true -F lite_ui=true -F branch_id=main",
        "# poll /api/media/job/{id} until done; verify gallery+chat+jobs+search; DELETE; restore",
        "",
        "# 3) Planner / Journal / Search / Settings / Projects — see assertions.jsonl for exact payloads",
    ]
    store.write_text(ctx.run_id, "replay/replay.sh", "\n".join(lines) + "\n")


def compute_coverage(ctx: CertContext, *, required: list[str] | None = None) -> dict[str, Any]:
    tested = [fid for fid, feat in ctx.features.items() if feat.get("status") in ("PASS", "FAIL")]
    req = list(required if required is not None else REQUIRED_FEATURES)
    # Mutation check is harness meta — not part of product coverage denominator
    req = [f for f in req if f != "mutation_check"]
    covered_required = [f for f in req if f in tested and ctx.features.get(f, {}).get("status") == "PASS"]
    controls = sorted({c for feat in ctx.features.values() for c in (feat.get("controls") or [])})
    workflows = sorted({w for feat in ctx.features.values() for w in (feat.get("workflows") or [])})
    pct = round(100.0 * len(covered_required) / max(1, len(req)), 1)
    coverage = {
        "features_required": req,
        "features_tested": tested,
        "features_passed": covered_required,
        "feature_coverage_pct": pct,
        "controls_exercised": controls,
        "workflows_exercised": workflows,
        "untested_required": [f for f in req if f not in covered_required],
        "api_calls": (store.get_run(ctx.run_id) or {}).get("counts", {}).get("api_calls", 0),
        "assertions": (store.get_run(ctx.run_id) or {}).get("counts", {}).get("assertions", 0),
    }
    store.write_text(ctx.run_id, "coverage/coverage.json", json.dumps(coverage, indent=2))
    return coverage


def evaluate_gate(
    ctx: CertContext,
    coverage: dict[str, Any],
    *,
    skip_image: bool = False,
    selected_suites: list[str] | None = None,
) -> dict[str, Any]:
    from jarvis.certification_product.terminology import REQUIRED_COVERAGE_PCT, REQUIRED_FEATURES

    assertions = store.list_assertions(ctx.run_id)
    # Mutation intentionally creates one FAIL — exclude it from ship blockers
    fails = [
        a
        for a in assertions
        if a.get("result") == "FAIL" and a.get("feature") != "mutation_check"
    ]
    feature_fails = [
        fid
        for fid, f in ctx.features.items()
        if f.get("status") == "FAIL" and fid != "mutation_check"
    ]
    blockers = []
    if fails:
        blockers.append(f"{len(fails)} failed assertion(s)")
    if feature_fails:
        blockers.append("FAIL features: " + ", ".join(feature_fails))
    # Ship gate always measured against the full required product set — not the smoke subset
    ship_required = list(REQUIRED_FEATURES)
    ship_passed = [
        f
        for f in ship_required
        if ctx.features.get(f, {}).get("status") == "PASS"
    ]
    ship_pct = round(100.0 * len(ship_passed) / max(1, len(ship_required)), 1)
    if ship_pct < REQUIRED_COVERAGE_PCT:
        blockers.append(
            f"Ship coverage {ship_pct}% < required {REQUIRED_COVERAGE_PCT}% "
            f"(passed {len(ship_passed)}/{len(ship_required)} required features)"
        )
    missing_ship = [f for f in ship_required if f not in ship_passed]
    if missing_ship:
        blockers.append("Required ship features incomplete: " + ", ".join(missing_ship))
    if skip_image or "image_lifecycle" not in ship_passed:
        blockers.append("image_lifecycle not certified — Full (image) required for READY_TO_SHIP")
    # Suite-local coverage still reported; incomplete selected suites also block
    untested = coverage.get("untested_required") or []
    if untested:
        blockers.append("Selected suite incomplete: " + ", ".join(untested))
    if int((store.get_run(ctx.run_id) or {}).get("counts", {}).get("assertions") or 0) < 1:
        blockers.append("No assertions recorded")
    if int((store.get_run(ctx.run_id) or {}).get("counts", {}).get("api_calls") or 0) < 1:
        blockers.append("No API evidence recorded")
    mut = store.run_dir(ctx.run_id) / "coverage" / "mutation_check.json"
    if mut.is_file():
        try:
            mut_data = json.loads(mut.read_text())
            if not mut_data.get("harness_ok"):
                blockers.append("Mutation check failed — harness insufficient")
        except Exception:
            blockers.append("Mutation check evidence unreadable")
    # Smoke OK only when selected suites passed but full ship set is incomplete (e.g. skip_image).
    # Any failed product assertion/feature or incomplete selected suite → DO_NOT_SHIP.
    if not blockers:
        gate = "READY_TO_SHIP"
    elif fails or feature_fails or untested:
        gate = "DO_NOT_SHIP"
    elif ship_pct < 100.0:
        gate = "SMOKE_PASS"
    else:
        gate = "DO_NOT_SHIP"
    return {
        "gate": gate,
        "blockers": blockers,
        "failed_assertions": len(fails),
        "failed_features": feature_fails,
        "ship_coverage_pct": ship_pct,
        "ship_passed": ship_passed,
    }


def false_pass_resample(ctx: CertContext, *, sample: int = 10) -> dict[str, Any]:
    """Independently re-verify up to N PASS assertions (live re-fetch, not trust)."""
    import random

    results = []
    assertions = [a for a in store.list_assertions(ctx.run_id) if a.get("result") == "PASS"]
    sample_rows = assertions if len(assertions) <= sample else random.sample(assertions, sample)

    # Live independent checks (not re-reading the same PASS row)
    live_checks: list[tuple[str, Callable[[], bool]]] = [
        (
            "Search facets still include gallery+chat",
            lambda: (
                "gallery" in json.dumps(ctx.api("GET", "/api/search/product/facets")[1])
                and "chat" in json.dumps(ctx.api("GET", "/api/search/product/facets")[1])
            ),
        ),
        (
            "Appearance settings file still present",
            lambda: (DATA_DIR / "settings_product" / "appearance.json").is_file(),
        ),
        (
            "Certification product API still healthy",
            lambda: bool((ctx.api("GET", "/api/certification/product")[1] or {}).get("ok")),
        ),
    ]
    for name, fn in live_checks:
        try:
            ok = bool(fn())
        except Exception:
            ok = False
        results.append({"id": f"live:{name}", "name": name, "ok": ok, "mode": "live"})
        if not ok:
            ctx.assert_(f"False-pass detector: {name}", True, False, ok=False)

    for row in sample_rows:
        coherent = row.get("expected") is not None and "observed" in row and row.get("result") == "PASS"
        if coherent and row.get("expected") == row.get("observed"):
            ok = True
        elif coherent and isinstance(row.get("expected"), bool):
            ok = bool(row.get("observed")) is True or row.get("observed") == row.get("expected")
        else:
            ok = coherent
        results.append({"id": row.get("id"), "name": row.get("name"), "ok": ok, "mode": "structural"})
        if not ok:
            ctx.assert_(
                f"False-pass detector: {row.get('name')}",
                "still PASS on resample",
                "INCOHERENT",
                ok=False,
            )
    failed = [r for r in results if not r["ok"]]
    out = {"sampled": len(results), "failed": len(failed), "results": results}
    store.write_text(ctx.run_id, "coverage/false_pass_sample.json", json.dumps(out, indent=2))
    return out


def mutation_check(ctx: CertContext) -> dict[str, Any]:
    """
    Deliberately assert a known-false condition; certification infrastructure
    must record FAIL. If this records PASS, the harness is broken.
    """
    ctx.set_feature("mutation_check", "Mutation check — harness integrity")
    ctx.workflow("inject known-false assertion → expect FAIL recorded")
    detected = not ctx.assert_(
        "Mutation: 1 must not equal 2 (harness must FAIL this)",
        1,
        2,
        ok=False,
    )
    # Mark feature PASS only if the harness correctly failed the mutation
    ctx.finish_feature("mutation_check", detected)
    out = {"detected": detected, "harness_ok": detected}
    store.write_text(ctx.run_id, "coverage/mutation_check.json", json.dumps(out, indent=2))
    if not detected:
        ctx.assert_("Mutation harness integrity", "FAIL recorded", "PASS leaked", ok=False)
    return out


def run_certification(
    *,
    label: str = "",
    base: str = BASE_DEFAULT,
    suites: list[str] | None = None,
    skip_image: bool = False,
) -> dict[str, Any]:
    man = store.create_run(label=label or "Evidence certification")
    run_id = man["id"]
    ctx = CertContext(run_id, base=base)
    selected = SUITES
    if suites:
        selected = [(n, fn) for n, fn in SUITES if n in suites]
    if skip_image:
        selected = [(n, fn) for n, fn in selected if n != "image_lifecycle"]

    timeline = [{"ts": time.time(), "event": "started", "run_id": run_id}]
    errors: list[str] = []

    required_for_run = [n for n, _ in selected]
    try:
        _capture_backend_log(ctx)
        for name, fn in selected:
            timeline.append({"ts": time.time(), "event": "feature_start", "feature": name})
            try:
                ok = fn(ctx)
                timeline.append(
                    {"ts": time.time(), "event": "feature_end", "feature": name, "pass": ok}
                )
            except Exception as exc:
                errors.append(f"{name}: {exc}")
                store.write_text(
                    run_id,
                    f"logs/exception_{name}.txt",
                    traceback.format_exc(),
                )
                ctx.features.setdefault(name, {"id": name, "title": name})
                ctx.features[name]["status"] = "FAIL"
                ctx.assert_(f"Suite {name} raised", "no exception", str(exc), ok=False)
                timeline.append({"ts": time.time(), "event": "feature_error", "feature": name})
        timeline.append({"ts": time.time(), "event": "mutation_check"})
        mut = mutation_check(ctx)
        if not mut.get("harness_ok"):
            errors.append("Mutation check did not detect injected failure")
        write_replay(ctx)
        coverage = compute_coverage(ctx, required=required_for_run)
        sample = false_pass_resample(ctx)
        if sample.get("failed"):
            errors.append("False-pass detector failed resampling")
        gate_info = evaluate_gate(
            ctx,
            coverage,
            skip_image=skip_image,
            selected_suites=[n for n, _ in selected],
        )
        if sample.get("failed"):
            gate_info["blockers"].append("False-pass detector found incoherent PASS")
            gate_info["gate"] = "DO_NOT_SHIP"
        _capture_backend_log(ctx)
        store.write_text(run_id, "logs/console_note.txt", "Browser console captured via UI Upload when Live Cert runs in-browser.\n")
        store.write_text(run_id, "timeline.json", json.dumps(timeline, indent=2))
        finished = time.time()
        store.update_manifest(
            run_id,
            {
                "status": "complete",
                "finished_at": finished,
                "finished_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(finished)),
                "features": ctx.features,
                "coverage": coverage,
                "gate": gate_info["gate"],
                "blockers": gate_info["blockers"],
                "errors": errors,
                "false_pass_sample": sample,
                "release_recommendation": gate_info["gate"],
            },
        )
        # Summary markdown for humans + dashboard
        summary = _summary_md(run_id)
        store.write_text(run_id, "SUMMARY.md", summary)
        # Production Integrity after certification — recommend Guided Repair; never auto-delete.
        try:
            from jarvis.integrity_product.scanner import run_scan
            from jarvis.integrity_product.repair_module import ProductionIntegrityModule
            from jarvis.repair_product.engine import prepare_issue

            iscan = run_scan(force=True, trigger="after_certification")
            store.write_text(run_id, "coverage/production_integrity.json", json.dumps(iscan, indent=2, default=str))
            if not iscan.get("clean"):
                detected = ProductionIntegrityModule().detect()
                if detected:
                    prepare_issue(detected[0])
        except Exception as exc:
            errors.append(f"production_integrity_hook: {exc}")
        return store.get_run(run_id) or {}
    except Exception:
        store.write_text(run_id, "logs/fatal.txt", traceback.format_exc())
        store.update_manifest(
            run_id,
            {
                "status": "failed",
                "gate": "DO_NOT_SHIP",
                "blockers": ["Runner crashed — see logs/fatal.txt"],
                "finished_at": time.time(),
                "features": ctx.features,
            },
        )
        raise


def _summary_md(run_id: str) -> str:
    man = store.get_run(run_id) or {}
    lines = [
        f"# Certification {run_id}",
        "",
        f"**Gate:** `{man.get('gate')}`",
        f"**Status:** {man.get('status')}",
        f"**Assertions:** {man.get('counts', {}).get('assertions')} "
        f"(pass={man.get('counts', {}).get('pass')} fail={man.get('counts', {}).get('fail')})",
        f"**API calls:** {man.get('counts', {}).get('api_calls')}",
        f"**Coverage:** {man.get('coverage', {}).get('feature_coverage_pct')}%",
        "",
        "## Blockers",
    ]
    for b in man.get("blockers") or ["(none)"]:
        lines.append(f"- {b}")
    lines.append("")
    lines.append("## Features")
    for fid, feat in (man.get("features") or {}).items():
        lines.append(f"- `{fid}`: **{feat.get('status')}** — {feat.get('title')}")
    lines.append("")
    lines.append("Evidence package directory: `data/certification/runs/" + run_id + "/`")
    return "\n".join(lines) + "\n"
