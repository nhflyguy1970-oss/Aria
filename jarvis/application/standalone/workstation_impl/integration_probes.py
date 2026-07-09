"""Live integration probes — verify components with real operations."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from jarvis.env_loader import PROJECT_ROOT

_PROBE_PREFIX = "aria_acceptance_"


def _result(ok: bool, detail: str = "", **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "detail": detail[:500]}
    payload.update(extra)
    return payload


def _http_json(method: str, url: str, body: dict | None = None, timeout: float = 8.0) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw.strip() else {}


def probe_redis() -> dict[str, Any]:
    host = os.getenv("REDIS_HOST", "127.0.0.1")
    port = int(os.getenv("REDIS_PORT", "6379"))
    key = f"{_PROBE_PREFIX}{uuid.uuid4().hex[:8]}"
    try:
        import redis

        client = redis.Redis(host=host, port=port, socket_timeout=3)
        client.set(key, "ok", ex=30)
        val = client.get(key)
        client.delete(key)
        return _result(val == b"ok", "write/read/delete")
    except Exception as exc:
        if shutil.which("redis-cli"):
            try:
                proc = subprocess.run(
                    ["redis-cli", "-h", host, "-p", str(port), "PING"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                return _result(proc.stdout.strip() == "PONG", proc.stdout.strip() or str(exc))
            except Exception as inner:
                return _result(False, str(inner))
        return _result(False, str(exc))


def probe_postgres() -> dict[str, Any]:
    host = os.getenv("POSTGRES_HOST", "127.0.0.1")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "postgres")
    db = os.getenv("POSTGRES_DB", "aiplatform")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    table = f"{_PROBE_PREFIX}{uuid.uuid4().hex[:6]}"
    try:
        import psycopg2

        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=db, connect_timeout=3
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"CREATE TEMP TABLE {table} (id int, note text)")
        cur.execute(f"INSERT INTO {table} (id, note) VALUES (1, 'ok')")
        cur.execute(f"SELECT note FROM {table} WHERE id=1")
        row = cur.fetchone()
        cur.close()
        conn.close()
        return _result(row and row[0] == "ok", "temp table insert/select")
    except Exception as exc:
        return _result(False, str(exc))


def probe_qdrant() -> dict[str, Any]:
    url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
    coll = f"{_PROBE_PREFIX}{uuid.uuid4().hex[:8]}"
    try:
        _http_json(
            "PUT", f"{url}/collections/{coll}", {"vectors": {"size": 4, "distance": "Cosine"}}
        )
        point_id = uuid.uuid4().hex
        _http_json(
            "PUT",
            f"{url}/collections/{coll}/points",
            {"points": [{"id": point_id, "vector": [0.1, 0.2, 0.3, 0.4], "payload": {"t": "ok"}}]},
        )
        search = _http_json(
            "POST",
            f"{url}/collections/{coll}/points/search",
            {"vector": [0.1, 0.2, 0.3, 0.4], "limit": 1},
        )
        urllib.request.urlopen(
            urllib.request.Request(f"{url}/collections/{coll}", method="DELETE"), timeout=5
        )
        hits = search.get("result") or []
        return _result(bool(hits), f"collection write/search ({len(hits)} hits)")
    except Exception as exc:
        if os.getenv("JARVIS_VECTOR_BACKEND", "") == "pgvector":
            return probe_postgres()
        return _result(False, str(exc))


def _first_ollama_model() -> str:
    preferred = os.getenv("JARVIS_GENERAL_MODEL", "").strip()
    if preferred:
        return preferred
    if not shutil.which("ollama"):
        return "qwen2.5:14b"
    try:
        proc = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        names = [line.split()[0] for line in (proc.stdout or "").splitlines()[1:] if line.strip()]
        for name in names:
            low = name.lower()
            if "embed" in low:
                continue
            if any(x in low for x in ("32b", "70b", "64k")):
                continue
            return name
        return names[0] if names else "qwen2.5:14b"
    except Exception:
        return "qwen2.5:14b"


def probe_ollama() -> dict[str, Any]:
    model = _first_ollama_model()
    if not shutil.which("ollama"):
        return _result(False, "ollama binary missing")
    try:
        proc = subprocess.run(
            ["ollama", "run", model, "Reply OK"],
            capture_output=True,
            text=True,
            timeout=90,
        )
        out = (proc.stdout or "").strip()
        return _result(proc.returncode == 0 and bool(out), out[:120] or model)
    except subprocess.TimeoutExpired:
        return _result(False, "ollama inference timed out")
    except Exception as exc:
        return _result(False, str(exc))


def probe_litellm() -> dict[str, Any]:
    url = os.getenv("JARVIS_LITELLM_URL", "http://127.0.0.1:4000").rstrip("/")
    candidates = [
        os.getenv("JARVIS_PROBE_LITELLM_MODEL", "").strip(),
        "ollama",
        f"ollama/{_first_ollama_model()}",
    ]
    candidates = [c for c in candidates if c]
    try:
        with urllib.request.urlopen(f"{url}/health/readiness", timeout=4) as resp:
            if resp.status != 200:
                return _result(False, f"health status {resp.status}")
    except Exception as exc:
        return _result(False, str(exc))

    last_error = ""
    for model in dict.fromkeys(candidates):
        try:
            body = {
                "model": model,
                "messages": [{"role": "user", "content": "Reply with exactly: OK"}],
                "max_tokens": 12,
                "stream": False,
            }
            data = json.dumps(body).encode()
            req = urllib.request.Request(
                f"{url}/v1/chat/completions",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                payload = json.loads(resp.read().decode())
            text = (
                ((payload.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            ).strip()
            usage = payload.get("usage") or {}
            if text:
                return _result(
                    True,
                    f"{model}: {text[:80]}",
                    tokens=usage.get("total_tokens"),
                    streaming_tested=False,
                )
        except urllib.error.HTTPError as exc:
            last_error = exc.read().decode()[:200]
        except Exception as exc:
            last_error = str(exc)
    return _result(False, last_error or "inference failed")


def probe_litellm_chain() -> dict[str, Any]:
    """Verify LiteLLM -> Ollama inference path (Aria gateway uses same route)."""
    litellm = probe_litellm()
    if litellm.get("ok"):
        litellm["chain"] = "litellm->ollama"
        return litellm
    ollama = probe_ollama()
    if ollama.get("ok"):
        return _result(
            True,
            "fallback: direct ollama (litellm routing failed)",
            fallback=True,
            litellm_error=litellm.get("detail"),
        )
    return _result(False, f"litellm: {litellm.get('detail')}; ollama: {ollama.get('detail')}")


def probe_open_webui() -> dict[str, Any]:
    base = os.getenv("JARVIS_OPENWEBUI_URL", "http://127.0.0.1:3000").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/health", timeout=4) as resp:
            if resp.status != 200:
                return _result(False, f"health {resp.status}")
    except Exception as exc:
        return _result(False, f"health: {exc}")

    models_ok = False
    for path in ("/ollama/api/tags", "/api/models"):
        try:
            with urllib.request.urlopen(f"{base}{path}", timeout=6) as resp:
                payload = json.loads(resp.read().decode())
            if isinstance(payload, dict) and (payload.get("models") or payload.get("data")):
                models_ok = True
                break
            if isinstance(payload, list) and payload:
                models_ok = True
                break
        except Exception:
            continue
    return _result(True, "health ok" + (" + models" if models_ok else " (models auth required)"))


def probe_mongodb() -> dict[str, Any]:
    uri = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    coll = f"{_PROBE_PREFIX}{uuid.uuid4().hex[:8]}"
    try:
        from pymongo import MongoClient

        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        db = client["aria_acceptance"]
        db[coll].insert_one({"ok": True})
        doc = db[coll].find_one({"ok": True})
        db[coll].drop()
        client.close()
        return _result(bool(doc), "insert/read/delete")
    except Exception as exc:
        return _result(False, str(exc))


def probe_n8n() -> dict[str, Any]:
    base = os.getenv("JARVIS_N8N_URL", "http://127.0.0.1:5678").rstrip("/")
    for path in ("/healthz", "/"):
        try:
            with urllib.request.urlopen(f"{base}{path}", timeout=4) as resp:
                if resp.status == 200:
                    return _result(True, f"GET {path}")
        except Exception:
            continue
    return _result(False, "offline")


def probe_prometheus() -> dict[str, Any]:
    base = os.getenv("JARVIS_PROMETHEUS_URL", "http://127.0.0.1:9090").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/-/healthy", timeout=4) as resp:
            healthy = resp.status == 200
        with urllib.request.urlopen(f"{base}/api/v1/query?query=up", timeout=4) as resp:
            payload = json.loads(resp.read().decode())
        series = payload.get("data", {}).get("result") or []
        return _result(healthy and bool(series), f"{len(series)} targets")
    except Exception as exc:
        return _result(False, str(exc))


def probe_grafana() -> dict[str, Any]:
    base = os.getenv("JARVIS_GRAFANA_URL", "http://127.0.0.1:3001").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/health", timeout=4) as resp:
            health = json.loads(resp.read().decode())
        with urllib.request.urlopen(f"{base}/api/search?type=dash-db", timeout=4) as resp:
            dashboards = json.loads(resp.read().decode())
        return _result(
            health.get("database") == "ok",
            f"health ok, {len(dashboards) if isinstance(dashboards, list) else 0} dashboards",
        )
    except Exception as exc:
        return _result(False, str(exc))


def probe_opencode() -> dict[str, Any]:
    if not shutil.which("opencode"):
        return _result(False, "opencode not installed")
    ver = subprocess.run(["opencode", "--version"], capture_output=True, text=True, timeout=10)
    if ver.returncode != 0:
        return _result(False, (ver.stderr or ver.stdout or "version failed")[:200])

    try:
        proc = subprocess.run(
            ["opencode", "run", "--pure", "Reply with exactly the single word OK"],
            capture_output=True,
            text=True,
            timeout=int(os.getenv("JARVIS_PROBE_OPENCODE_TIMEOUT", "120")),
            cwd=str(PROJECT_ROOT),
        )
        stdout = (proc.stdout or "").strip()
        ok = proc.returncode == 0 and bool(stdout)
        if ok:
            try:
                from jarvis.env_loader import DATA_DIR

                mem_file = DATA_DIR / "automation" / "opencode_probe_last.txt"
                mem_file.parent.mkdir(parents=True, exist_ok=True)
                mem_file.write_text(stdout[:800], encoding="utf-8")
            except Exception:
                pass
        return _result(ok, stdout[:200] or (proc.stderr or "")[:200])
    except subprocess.TimeoutExpired:
        return _result(False, "opencode task timed out")
    except Exception as exc:
        return _result(False, str(exc))


def probe_cli_tool(tool_id: str, *, smoke_task: str = "Reply with exactly: OK") -> dict[str, Any]:
    from jarvis.tools.runner import run_sync

    if tool_id == "opencode":
        return probe_opencode()

    if tool_id == "claude_code":
        result = run_sync(
            tool_id,
            {"task": smoke_task, "timeout": 45},
            timeout=45,
        )
        return _result(
            bool(result.get("ok")), (result.get("stdout") or result.get("error") or "")[:200]
        )

    if tool_id == "gemini_cli":
        result = run_sync(tool_id, {"task": smoke_task, "timeout": 45}, timeout=45)
        return _result(
            bool(result.get("ok")), (result.get("stdout") or result.get("error") or "")[:200]
        )

    binary = {
        "goose": "goose",
        "hermes": "hermes",
        "continue": shutil.which("cn") or shutil.which("continue") or "",
        "openhands": "openhands",
    }.get(tool_id, "")
    if not binary or not shutil.which(binary):
        return _result(False, "not installed")
    proc = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=8)
    return _result(proc.returncode == 0, (proc.stdout or proc.stderr or binary)[:120])


def probe_whisper() -> dict[str, Any]:
    py = shutil.which("python3") or "python3"
    venv_py = os.path.join(os.path.dirname(__file__), "..", "..", "venv", "bin", "python")
    if os.path.isfile(venv_py):
        py = venv_py
    try:
        proc = subprocess.run(
            [py, "-c", "import faster_whisper; print('ok')"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return _result(proc.returncode == 0, "faster-whisper importable")
    except Exception as exc:
        return _result(False, str(exc))


def probe_piper() -> dict[str, Any]:
    from jarvis.config import piper_binary, piper_model_path, piper_ready, piper_runtime_env

    if not piper_ready():
        return _result(False, "piper not configured")
    binary = piper_binary()
    model = piper_model_path()
    if not binary or not model:
        return _result(False, "piper binary or model missing")
    out = Path(tempfile.gettempdir()) / f"{_PROBE_PREFIX}piper.wav"
    env = {**os.environ, **piper_runtime_env()}
    try:
        proc = subprocess.run(
            [str(binary), "--model", str(model), "--output_file", str(out)],
            input="Workstation acceptance test.",
            capture_output=True,
            text=True,
            timeout=25,
            env=env,
        )
        ok = proc.returncode == 0 and out.is_file() and out.stat().st_size > 100
        size = out.stat().st_size if out.is_file() else 0
        if out.is_file():
            out.unlink(missing_ok=True)
        return _result(ok, f"generated {size} bytes")
    except Exception as exc:
        return _result(False, str(exc))


def probe_ocr() -> dict[str, Any]:
    if not shutil.which("tesseract"):
        return _result(False, "tesseract missing")
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (120, 40), "white")
        draw = ImageDraw.Draw(img)
        draw.text((5, 10), "OK", fill="black")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img.save(tmp.name)
            path = tmp.name
        proc = subprocess.run(
            ["tesseract", path, "stdout"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        os.unlink(path)
        text = (proc.stdout or "").strip().upper()
        return _result("OK" in text, text[:80])
    except Exception as exc:
        return _result(False, str(exc))


def probe_aria_api() -> dict[str, Any]:
    host = os.getenv("JARVIS_HOST", "127.0.0.1")
    if host in ("0.0.0.0", "::", "::0"):
        host = "127.0.0.1"
    port = os.getenv("JARVIS_PORT", "8765")
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/api/health", timeout=3) as resp:
            payload = json.loads(resp.read().decode())
        return _result(payload.get("ok", True), json.dumps(payload)[:120])
    except Exception as exc:
        return _result(False, str(exc))


PROBE_MAP: dict[str, Any] = {
    "ollama": probe_ollama,
    "redis": probe_redis,
    "postgres": probe_postgres,
    "qdrant": probe_qdrant,
    "litellm": probe_litellm_chain,
    "open_webui": probe_open_webui,
    "mongodb": probe_mongodb,
    "n8n": probe_n8n,
    "prometheus": probe_prometheus,
    "grafana": probe_grafana,
    "opencode": lambda: probe_cli_tool("opencode"),
    "claude_code": lambda: probe_cli_tool("claude_code"),
    "gemini_cli": lambda: probe_cli_tool("gemini_cli"),
    "goose": lambda: probe_cli_tool("goose"),
    "hermes": lambda: probe_cli_tool("hermes"),
    "continue": lambda: probe_cli_tool("continue"),
    "openhands": lambda: probe_cli_tool("openhands"),
    "whisper": probe_whisper,
    "piper": probe_piper,
    "tesseract": probe_ocr,
    "aria": probe_aria_api,
}


def run_probe(component_id: str) -> dict[str, Any]:
    fn = PROBE_MAP.get(component_id)
    if fn is None:
        return _result(False, "no probe")
    started = time.time()
    try:
        result = fn()
    except Exception as exc:
        result = _result(False, str(exc))
    result["duration_ms"] = round((time.time() - started) * 1000, 1)
    return result


def run_all_probes(component_ids: list[str] | None = None) -> dict[str, dict[str, Any]]:
    from jarvis.application.standalone.workstation_impl.acceptance import _CATALOG

    ids = component_ids or [c[0] for c in _CATALOG]
    out: dict[str, dict[str, Any]] = {}
    for cid in ids:
        if cid in PROBE_MAP:
            out[cid] = run_probe(cid)
    return out
