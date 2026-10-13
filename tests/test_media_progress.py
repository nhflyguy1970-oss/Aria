"""Image RAM reservation sized by checkpoint; real progress for image/video jobs."""
from __future__ import annotations

import json
import sys
import threading
import types

from jarvis import comfyui, media_jobs


def test_ram_need_follows_the_models_the_workflow_loads(monkeypatch, tmp_path):
    (tmp_path / "models" / "checkpoints").mkdir(parents=True)
    (tmp_path / "models" / "checkpoints" / "sdxl.safetensors").write_bytes(b"\0" * (6 * 1048576))
    monkeypatch.setattr(comfyui, "COMFY_ROOT", tmp_path)
    wf = {"4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sdxl.safetensors"}}}
    assert comfyui.workflow_ram_mib(wf) == 6 + comfyui.RAM_OVERHEAD_MIB
    assert comfyui.workflow_ram_mib({"1": {"inputs": {"ckpt_name": "missing.safetensors"}}}) is None


def test_ram_need_is_capped_at_the_flux_default(monkeypatch, tmp_path):
    from jarvis.gpu_scheduler import IMAGE_PROFILE

    (tmp_path / "models" / "diffusion_models").mkdir(parents=True)
    big = tmp_path / "models" / "diffusion_models" / "flux.safetensors"
    with open(big, "wb") as fh:
        fh.truncate(20 * 1024 * 1048576)  # sparse 20 GiB
    monkeypatch.setattr(comfyui, "COMFY_ROOT", tmp_path)
    wf = {"1": {"inputs": {"unet_name": "flux.safetensors"}}}
    assert comfyui.workflow_ram_mib(wf) == IMAGE_PROFILE["ram_mib"]


def test_smaller_checkpoint_admits_with_less_free_ram(monkeypatch):
    from jarvis import gpu_scheduler as gs

    gs.reset_for_tests()
    monkeypatch.setattr(gs, "cuda", lambda: {"ok": True, "temp_c": 50, "free_mib": 12000})
    monkeypatch.setattr(gs, "amd", lambda: {"ok": True, "temp_c": 40, "free_mib": 7000})
    monkeypatch.setattr(gs, "host_available_mib", lambda: 21000)  # < 24 GiB Flux need
    monkeypatch.setattr(gs, "ftr_busy", lambda eps: [])
    monkeypatch.setattr(gs, "_get_json", lambda url, timeout=2.0: {"models": []})
    monkeypatch.setattr(gs, "_post_json", lambda url, body, timeout=30.0: {})
    monkeypatch.setattr(gs, "RAM_SETTLE_S", 0.2)
    monkeypatch.setattr(gs, "RELEASE_SETTLE_S", 0)
    with gs.admit_image(label="lustify", ram_mib=8664):  # 12 GiB reserve + 8.5 GiB = 20.5 GiB
        pass
    try:
        with gs.admit_image(label="flux"):
            raise AssertionError("Flux-sized default should not fit in 21000 MiB")
    except gs.GpuUnavailable as exc:
        assert "host RAM" in exc.reason
    gs.reset_for_tests()


def _fake_job(monkeypatch):
    jid = "job-progress-test"
    with media_jobs._lock:
        media_jobs._jobs[jid] = {"id": jid, "pct": 5, "message": "Running…", "done": False}
    monkeypatch.setattr(media_jobs._tls, "job_id", jid, raising=False)
    return jid


def test_report_progress_is_monotonic_and_bounded(monkeypatch):
    jid = _fake_job(monkeypatch)
    media_jobs.report_progress(40, "Generating — step 12/30")
    media_jobs.report_progress(20, "late event")
    assert media_jobs._jobs[jid]["pct"] == 40
    media_jobs.report_progress(150)
    assert media_jobs._jobs[jid]["pct"] == 99  # 100 only when the job is really done
    media_jobs._jobs[jid]["done"] = True
    media_jobs.report_progress(10, "after done")
    assert media_jobs._jobs[jid]["message"] != "after done"
    media_jobs._jobs.pop(jid, None)


def test_comfy_step_events_drive_the_job_bar(monkeypatch):
    jid = _fake_job(monkeypatch)
    stop = threading.Event()
    events = [
        json.dumps({"type": "execution_start", "data": {}}),
        b"\x00binary-preview",
        json.dumps({"type": "progress", "data": {"value": 15, "max": 30}}),
        json.dumps({"type": "progress", "data": {"value": 30, "max": 30}}),
    ]

    class FakeWS:
        def settimeout(self, t):
            pass

        def recv(self):
            if events:
                return events.pop(0)
            stop.set()
            raise fake.WebSocketTimeoutException()

        def close(self):
            pass

    fake = types.SimpleNamespace(create_connection=lambda url, timeout=5: FakeWS(),
                                 WebSocketTimeoutException=type("T", (Exception,), {}))
    monkeypatch.setitem(sys.modules, "websocket", fake)
    seen = []
    real = media_jobs.report_progress
    monkeypatch.setattr(media_jobs, "report_progress",
                        lambda pct, message=None, job_id=None: (seen.append((int(pct), message)),
                                                                real(pct, message, job_id=job_id)))
    comfyui._listen_progress("client", jid, stop)
    assert seen[0] == (10, "Loading model…")
    assert seen[1] == (53, "Generating — step 15/30")
    assert seen[2] == (95, "Decoding and saving…")
    assert media_jobs._jobs[jid]["pct"] == 95
    media_jobs._jobs.pop(jid, None)
