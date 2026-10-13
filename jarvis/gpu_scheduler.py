"""Phase 8 GPU admission: one exclusive heavy RTX 3060 job, a bounded RX 7600 helper lane.

Rules come from the Phase 8 measurements (aria-evaluations/phase8-model-tournament-20261011):

* RTX 3060 (CUDA): ordinary ARIA models share the device; a *heavy* job (the 27B
  specialist or any ComfyUI image job) holds it exclusively. Before a heavy job,
  ARIA's own idle default-Ollama residents are unloaded; afterwards the heavy
  model is unloaded again so the primary returns.
* RX 7600 (Vulkan): a private helper Ollama on 127.0.0.1:11448 runs *small*
  models only (<= the qualified Qwen3.5:4B size, <= 4096 context, short output),
  one request at a time. While a heavy CUDA job runs, small utility requests are
  placed there instead of loading onto the busy RTX — same model, visible placement.
* Every admission keeps >= 2 GiB free on the device used, >= 12 GiB host RAM,
  and refuses or waits (bounded) while a GPU is at or above the 82 C cutoff. A
  running ARIA job is cut off when the cutoff or the host-RAM floor is crossed.
* FTR-owned runtimes are never managed. A heavy job waits while any FTR endpoint
  on that device has a model loaded.

Queues are bounded (fail fast when full) and every wait has a deadline.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


CUTOFF_C = _env_int("JARVIS_GPU_CUTOFF_C", 82)  # validated Phase 8 workload cutoff
RESUME_C = _env_int("JARVIS_GPU_RESUME_C", 78)
IMAGE_START_MAX_C = _env_int("JARVIS_GPU_IMAGE_START_C", 70)  # Phase 8 runner cooled to <=70 C before images
CUDA_RESERVE_MIB = 2048
AMD_RESERVE_MIB = 2048
HOST_RESERVE_MIB = 12288
MAX_WAITING = _env_int("JARVIS_GPU_MAX_WAITING", 8)
SHARED_WAIT_S = _env_int("JARVIS_GPU_SHARED_WAIT_S", 150)
HEAVY_WAIT_S = _env_int("JARVIS_GPU_HEAVY_WAIT_S", 180)
COOL_WAIT_S = _env_int("JARVIS_GPU_COOL_WAIT_S", 120)
HELPER_WAIT_S = 30
MONITOR_INTERVAL_S = 2.0
VRAM_SETTLE_S = 90  # covers a cold start-up warm-up load already in flight
RELEASE_SETTLE_S = 20
STALE_S = 300  # a shared slot with no progress for 5 min is an abandoned stream; reclaim it

DEFAULT_OLLAMA = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
if not DEFAULT_OLLAMA.startswith("http"):
    DEFAULT_OLLAMA = "http://" + DEFAULT_OLLAMA.replace("0.0.0.0", "127.0.0.1")
HELPER_URL = os.getenv("JARVIS_VULKAN_HELPER_URL", "http://127.0.0.1:11448")
HELPER_MAX_BYTES = 3_600_000_000  # qualified helper: Qwen3.5:4B (3.4 GB)
HELPER_MAX_CTX = 4096
HELPER_MAX_PREDICT = 1024
FTR_CUDA = ("http://127.0.0.1:11435", "http://127.0.0.1:11440")
FTR_AMD = ("http://127.0.0.1:11436", "http://127.0.0.1:11441")

# Measured heavy profiles. Ollama options are the qualified placement.
HEAVY_MODELS: dict[str, dict[str, Any]] = {
    "huihui_ai/qwen3.8-abliterated:27b": {
        "options": {"num_gpu": 24, "num_thread": 4},
        "max_ctx": 8192,
        "vram_mib": 7800,   # ~6.1 GiB weights + KV/compute at 8K
        "ram_mib": 17000,   # observed ~16.5 GiB worker RSS
    },
}
IMAGE_PROFILE = {"vram_mib": 9800, "ram_mib": 12288}  # Schnell/Klein under --reserve-vram 2.5
ZIMAGE_VRAM_MIB = 7200  # Z-Image Turbo INT8: ~7.0 GiB observed peak (Phase 8)
# ComfyUI keeps its last model on the GPU after every prompt (4.2-4.6 GB for SDXL/Flux,
# 2026-10-12). Above this, an idle ComfyUI is asked to release it before ARIA needs the RTX.
COMFY_IDLE_FREE_MIB = 1024
# A chat admission checks for ComfyUI residue only when the RTX is this short of free memory.
SHARED_LOW_FREE_MIB = 6144


class GpuUnavailable(RuntimeError):
    """Admission refused; ``reason`` is shown to the owner."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class WorkloadCutoff(GpuUnavailable):
    """A running job crossed the thermal cutoff or host-RAM floor and was stopped."""


# ---------------------------------------------------------------- telemetry


_cache: dict[str, tuple[float, Any]] = {}
_cache_lock = threading.Lock()


def _cached(key: str, ttl: float, fn):
    now = time.monotonic()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < ttl:
            return hit[1]
    value = fn()
    with _cache_lock:
        _cache[key] = (now, value)
    return value


def _cuda_raw() -> dict:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, check=True,
        ).stdout.strip().splitlines()[0]
        temp, used, total = (int(float(x)) for x in out.split(","))
        return {"ok": True, "temp_c": temp, "used_mib": used, "total_mib": total, "free_mib": total - used}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__}


def _amd_card() -> Path | None:
    for card in sorted(Path("/sys/class/drm").glob("card[0-9]*")):
        dev = card / "device"
        try:
            if (dev / "vendor").read_text().strip() == "0x1002" and (dev / "mem_info_vram_total").exists():
                return dev
        except OSError:
            continue
    return None


def _amd_raw() -> dict:
    dev = _amd_card()
    if dev is None:
        return {"ok": False, "error": "no AMD GPU"}
    try:
        total = int((dev / "mem_info_vram_total").read_text()) // 1048576
        used = int((dev / "mem_info_vram_used").read_text()) // 1048576
        temp = None
        for label in dev.glob("hwmon/hwmon*/temp*_label"):
            if label.read_text().strip() == "edge":
                temp = int(Path(str(label)[: -len("_label")] + "_input").read_text()) // 1000
        return {"ok": temp is not None, "temp_c": temp, "used_mib": used, "total_mib": total,
                "free_mib": total - used}
    except (OSError, ValueError) as exc:
        return {"ok": False, "error": type(exc).__name__}


def cuda() -> dict:
    return _cached("cuda", 1.0, _cuda_raw)


def amd() -> dict:
    return _cached("amd", 1.0, _amd_raw)


def host_available_mib() -> int:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError):
        pass
    return 0


def _get_json(url: str, timeout: float = 2.0) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:  # noqa: BLE001
        return None


def _post_json(url: str, body: dict, timeout: float = 30.0) -> dict | None:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode() or "{}"
            return json.loads(raw)
    except Exception:  # noqa: BLE001
        return None


def comfy_resident_mib() -> int:
    """VRAM the main ComfyUI's PyTorch holds (0 when ComfyUI is not running)."""
    from jarvis.comfyui import COMFY_URL

    stats = _get_json(f"{COMFY_URL}/system_stats", timeout=2) or {}
    devices = stats.get("devices") or []
    return int(devices[0].get("torch_vram_total") or 0) // 1048576 if devices else 0


def comfy_queue_empty() -> bool:
    """No prompt running or pending — including ones queued from ComfyUI's own web UI."""
    from jarvis.comfyui import COMFY_URL

    queue = _get_json(f"{COMFY_URL}/queue", timeout=2)
    return queue is not None and not queue.get("queue_running") and not queue.get("queue_pending")


def ftr_busy(endpoints: tuple[str, ...]) -> list[str]:
    """FTR endpoints with a model loaded; ARIA yields to them and never manages them."""
    def probe():
        busy = []
        for url in endpoints:
            ps = _get_json(f"{url}/api/ps", timeout=1.5)
            if ps and ps.get("models"):
                busy.append(url)
        return busy
    return _cached("ftr:" + ",".join(endpoints), 2.0, probe)


def model_size(model: str) -> int:
    def tags():
        data = _get_json(f"{DEFAULT_OLLAMA}/api/tags", timeout=3) or {}
        return {m.get("name"): int(m.get("size") or 0) for m in data.get("models") or []}
    sizes = _cached("tags", 60.0, tags)
    return int(sizes.get(model) or sizes.get(f"{model}:latest") or 0)


def helper_ready() -> bool:
    return _cached("helper", 5.0, lambda: _get_json(f"{HELPER_URL}/api/version", timeout=1.0) is not None)


# ---------------------------------------------------------------- lanes and jobs


@dataclass(eq=False)  # identity: jobs live in a set
class Job:
    kind: str                     # shared | heavy | image | helper
    label: str
    model: str = ""
    host: str | None = None       # Ollama base URL; None = default ARIA Ollama
    options: dict[str, Any] = field(default_factory=dict)
    started: float = field(default_factory=time.time)
    touched: float = field(default_factory=time.monotonic)
    cutoff_reason: str = ""
    _cut: threading.Event = field(default_factory=threading.Event)

    def cut(self, reason: str) -> None:
        if not self._cut.is_set():
            self.cutoff_reason = reason
            self._cut.set()

    @property
    def cut_off(self) -> bool:
        return self._cut.is_set()

    def check(self) -> None:
        self.touched = time.monotonic()  # progress: streams call this per chunk
        if self._cut.is_set():
            raise WorkloadCutoff(self.cutoff_reason)


class _Scheduler:
    def __init__(self) -> None:
        self._cv = threading.Condition()
        self._shared = 0
        self._heavy: Job | None = None
        self._heavy_waiting = 0
        self._waiting = 0
        self._helper_busy = False
        self._active: set[Job] = set()
        self._hold_reason = ""
        self._events: list[dict] = []
        self._monitor: threading.Thread | None = None

    # -- bookkeeping
    def _event(self, name: str, **detail) -> None:
        row = {"ts": round(time.time(), 3), "event": name, **detail}
        self._events = (self._events + [row])[-50:]
        logger.info("gpu_scheduler %s %s", name, detail)

    def _reap_stale(self) -> None:
        """Caller holds the condition. Reclaim shared slots whose stream was abandoned."""
        now = time.monotonic()
        for job in [j for j in self._active if j.kind == "shared" and now - j.touched > STALE_S]:
            self._active.discard(job)
            self._shared = max(0, self._shared - 1)
            self._event("reaped_stale", job=job.label, idle_s=round(now - job.touched))

    def _enter_queue(self) -> None:
        if self._waiting >= MAX_WAITING:
            raise GpuUnavailable(f"GPU queue is full ({MAX_WAITING} waiting); try again shortly")
        self._waiting += 1

    # -- thermal / memory gates
    def _thermal(self, device: str) -> int | None:
        info = cuda() if device == "cuda" else amd()
        return info.get("temp_c") if info.get("ok") else None

    def _wait_cool(self, device: str, *, strict: bool = False, start_max: int | None = None) -> None:
        temp = self._thermal(device)
        if temp is None:
            if strict:  # heavy/image work never runs without the thermal gate
                raise GpuUnavailable("RTX 3060 telemetry unavailable; refusing heavy GPU work without the thermal gate")
            return
        if start_max is not None and start_max < temp < CUTOFF_C and not self._hold_reason:
            # Long image renders start cool so they finish under the cutoff (Phase 8 admission rule).
            deadline = time.monotonic() + COOL_WAIT_S
            self._event("cool_start_wait", device=device, temp_c=temp, target_c=start_max)
            while temp is None or temp > start_max:
                if time.monotonic() > deadline:
                    raise GpuUnavailable(f"RTX 3060 is still warm ({temp}°C > {start_max}°C start limit for "
                                         f"image jobs); try again shortly")
                time.sleep(2)
                _cache.pop("cuda", None)
                temp = self._thermal(device)
            return
        if temp < CUTOFF_C and not (self._hold_reason and device == "cuda"):
            return
        deadline = time.monotonic() + COOL_WAIT_S
        self._event("cooling_hold", device=device, temp_c=temp)
        while time.monotonic() < deadline:
            time.sleep(2)
            temp = self._thermal(device)
            if temp is not None and temp <= RESUME_C:
                if device == "cuda":
                    self._hold_reason = ""
                self._event("cooling_released", device=device, temp_c=temp)
                return
        name = "RTX 3060" if device == "cuda" else "RX 7600"
        raise GpuUnavailable(f"{name} is cooling ({temp}°C ≥ {CUTOFF_C}°C cutoff); try again shortly")

    # -- monitor: cutoff for running ARIA jobs
    def _ensure_monitor(self) -> None:
        if self._monitor and self._monitor.is_alive():
            return
        self._monitor = threading.Thread(target=self._watch, name="gpu-thermal-monitor", daemon=True)
        self._monitor.start()

    def _watch(self) -> None:
        while True:
            try:
                if not self._watch_once():
                    return
            except Exception:  # noqa: BLE001 — the safety monitor must outlive any single bad sample
                logger.exception("gpu_scheduler monitor sample failed")
            time.sleep(MONITOR_INTERVAL_S)

    def _watch_once(self) -> bool:
        with self._cv:
            jobs = list(self._active)
        if not jobs:
            return False
        reasons: dict[str, str] = {}
        ct = cuda()
        if ct.get("ok") and ct["temp_c"] >= CUTOFF_C:
            reasons["cuda"] = f"RTX 3060 reached {ct['temp_c']}°C (cutoff {CUTOFF_C}°C)"
        at = amd()
        if at.get("ok") and at["temp_c"] >= CUTOFF_C:
            reasons["amd"] = f"RX 7600 reached {at['temp_c']}°C (cutoff {CUTOFF_C}°C)"
        avail = host_available_mib()
        if avail and avail < HOST_RESERVE_MIB:
            reasons["host"] = f"host RAM fell to {avail} MiB (< {HOST_RESERVE_MIB} MiB reserve)"
        for job in jobs:
            why = reasons.get("amd" if job.kind == "helper" else "cuda") or reasons.get("host")
            if why and not job.cut_off:
                job.cut(why)
                self._event("cutoff", job=job.label, kind=job.kind, reason=why)
        if "cuda" in reasons:
            self._hold_reason = reasons["cuda"]
        return True

    # -- residency
    def _unload_aria_residents(self, keep: str = "") -> list[str]:
        ps = _get_json(f"{DEFAULT_OLLAMA}/api/ps", timeout=3) or {}
        dropped = []
        for entry in ps.get("models") or []:
            name = entry.get("name") or entry.get("model")
            if name and name != keep:
                _post_json(f"{DEFAULT_OLLAMA}/api/generate", {"model": name, "keep_alive": 0}, timeout=30)
                dropped.append(name)
        if dropped:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                left = {m.get("name") for m in (_get_json(f"{DEFAULT_OLLAMA}/api/ps", 3) or {}).get("models") or []}
                if not (left & set(dropped)):
                    break
                time.sleep(0.5)
            _cache.pop("cuda", None)
        return dropped

    def _free_idle_comfy(self, reason: str, *, acquiring: Job | None = None) -> int:
        """Release a model ComfyUI kept after its last prompt; returns the MiB it held (0 = nothing done).

        Never while an image job other than ``acquiring`` runs, and never with a prompt
        queued, so neither an ARIA job nor direct use of ComfyUI is disturbed.
        """
        with self._cv:
            running = self._heavy
        if running is not None and running.kind == "image" and running is not acquiring:
            return 0
        held = comfy_resident_mib()
        if held < COMFY_IDLE_FREE_MIB or not comfy_queue_empty():
            return 0
        from jarvis.comfyui import COMFY_URL

        _post_json(f"{COMFY_URL}/free", {"unload_models": True, "free_memory": True}, timeout=15)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and comfy_resident_mib() >= COMFY_IDLE_FREE_MIB:
            time.sleep(0.5)
        _cache.pop("cuda", None)
        logger.warning("gpu_scheduler: freed %s MiB idle ComfyUI residue before %s", held, reason)
        self._event("comfy_freed", mib=held, reason=reason)
        return held

    # -- acquisition
    def _acquire_shared(self, job: Job) -> None:
        info = cuda()
        if info.get("ok") and info["free_mib"] < SHARED_LOW_FREE_MIB:
            # A partial Ollama fit stays partial until keep_alive expires: release ComfyUI first.
            self._free_idle_comfy(f"chat {job.label or job.model}")
        deadline = time.monotonic() + SHARED_WAIT_S
        with self._cv:
            self._reap_stale()
            if self._heavy or self._heavy_waiting:
                self._enter_queue()
                try:
                    while self._heavy or self._heavy_waiting:
                        left = deadline - time.monotonic()
                        if left <= 0:
                            raise GpuUnavailable("RTX 3060 is busy with an exclusive job (image or 27B specialist); "
                                                 "try again when it finishes")
                        self._cv.wait(min(left, 1.0))
                finally:
                    self._waiting -= 1
            self._shared += 1
            self._active.add(job)

    def _acquire_heavy(self, job: Job, profile: dict) -> None:
        deadline = time.monotonic() + HEAVY_WAIT_S
        need_ram = HOST_RESERVE_MIB + int(profile.get("ram_mib") or 0)
        avail = host_available_mib()
        if avail < need_ram:
            raise GpuUnavailable(f"not enough free host RAM for {job.label} ({avail} MiB available, "
                                 f"{need_ram} MiB needed incl. 12 GiB desktop reserve)")
        with self._cv:
            self._reap_stale()
            if self._heavy or self._shared:
                self._enter_queue()
                self._heavy_waiting += 1
                try:
                    while self._heavy or self._shared:
                        self._reap_stale()
                        left = deadline - time.monotonic()
                        if left <= 0:
                            raise GpuUnavailable(f"RTX 3060 stayed busy; {job.label} was not started")
                        self._cv.wait(min(left, 1.0))
                finally:
                    self._heavy_waiting -= 1
                    self._waiting -= 1
            self._heavy = job
            self._active.add(job)
        try:
            while ftr_busy(FTR_CUDA):
                if time.monotonic() > deadline:
                    raise GpuUnavailable("FTR is using the RTX 3060; ARIA yields and did not start the job")
                time.sleep(2)
                _cache.pop("ftr:" + ",".join(FTR_CUDA), None)
            need = int(profile.get("vram_mib") or 0) + CUDA_RESERVE_MIB
            settle = time.monotonic() + VRAM_SETTLE_S
            while True:
                # Repeat: a warm-up that was mid-load when we were admitted only appears once loaded.
                self._unload_aria_residents(keep=job.model)
                self._free_idle_comfy(job.label, acquiring=job)
                _cache.pop("cuda", None)
                info = cuda()
                if info.get("ok") and info["free_mib"] >= need:
                    break
                if time.monotonic() > settle:
                    raise GpuUnavailable(f"RTX 3060 has {info.get('free_mib', '?')} MiB free; {job.label} needs "
                                         f"{need} MiB incl. 2 GiB reserve")
                time.sleep(2)
        except BaseException:
            self._release(job)
            raise

    def _acquire_helper(self, job: Job, size: int) -> bool:
        if not helper_ready() or ftr_busy(FTR_AMD):
            return False
        info = amd()
        need = int(size * 1.4 / 1048576) + AMD_RESERVE_MIB
        if not info.get("ok") or info["temp_c"] >= CUTOFF_C or info["free_mib"] < need:
            return False
        deadline = time.monotonic() + HELPER_WAIT_S
        with self._cv:
            while self._helper_busy:
                left = deadline - time.monotonic()
                if left <= 0:
                    return False
                self._cv.wait(min(left, 1.0))
            self._helper_busy = True
            self._active.add(job)
        return True

    def _release(self, job: Job) -> None:
        with self._cv:
            if job not in self._active:
                return  # already reclaimed as stale
            self._active.discard(job)
            if job.kind == "shared":
                self._shared = max(0, self._shared - 1)
            elif job.kind == "helper":
                self._helper_busy = False
            elif self._heavy is job:
                self._heavy = None
            self._cv.notify_all()

    # -- public
    @contextmanager
    def admit_ollama(self, model: str, options: dict | None = None, *, label: str = "") -> Iterator[Job]:
        """Admission for one Ollama request on ARIA's default endpoint (or the RX helper)."""
        try:
            with self._admit_ollama(model, options, label=label) as job:
                yield job
        except GpuUnavailable as exc:
            if not isinstance(exc, WorkloadCutoff):
                self._event("refused", job=label or model, reason=exc.reason)
            logger.warning("gpu_scheduler: %s: %s", label or model, exc.reason)
            raise

    @contextmanager
    def _admit_ollama(self, model: str, options: dict | None = None, *, label: str = "") -> Iterator[Job]:
        options = dict(options or {})
        label = label or model
        profile = HEAVY_MODELS.get(model)
        if profile:
            job = Job("heavy", label, model=model, options={**profile["options"]})
            ctx = int(options.get("num_ctx") or 4096)
            job.options["num_ctx"] = min(ctx, int(profile["max_ctx"]))
            self._wait_cool("cuda", strict=True)
            self._acquire_heavy(job, profile)
            self._event("heavy_start", job=label)
        else:
            size = model_size(model)
            small = 0 < size <= HELPER_MAX_BYTES and int(options.get("num_ctx") or 0) <= HELPER_MAX_CTX \
                and int(options.get("num_predict") or HELPER_MAX_PREDICT) <= HELPER_MAX_PREDICT
            job = Job("shared", label, model=model)
            with self._cv:
                busy = bool(self._heavy or self._heavy_waiting)
            if small and busy:
                helper = Job("helper", label, model=model, host=HELPER_URL,
                             options={"num_ctx": min(int(options.get("num_ctx") or HELPER_MAX_CTX), HELPER_MAX_CTX)})
                if self._acquire_helper(helper, size):
                    job = helper
                    self._event("helper_placement", job=label, reason="RTX 3060 exclusive job active")
            if job.kind == "shared":
                self._wait_cool("cuda")
                self._acquire_shared(job)
        self._ensure_monitor()
        try:
            yield job
        finally:
            self._release(job)
            if job.kind == "heavy":
                _post_json(f"{DEFAULT_OLLAMA}/api/generate", {"model": model, "keep_alive": 0}, timeout=30)
                self._event("heavy_end", job=label, cutoff=job.cutoff_reason)
            elif job.kind == "helper":
                self._event("helper_end", job=label)

    @contextmanager
    def admit_image(self, label: str = "image", *, vram_mib: int | None = None) -> Iterator[Job]:
        """Exclusive RTX 3060 slot for a ComfyUI job; ComfyUI memory is freed afterwards."""
        job = Job("image", label)
        profile = {**IMAGE_PROFILE, **({"vram_mib": int(vram_mib)} if vram_mib else {})}
        try:
            self._wait_cool("cuda", strict=True, start_max=IMAGE_START_MAX_C)
            self._acquire_heavy(job, profile)
        except GpuUnavailable as exc:
            self._event("refused", job=label, reason=exc.reason)
            logger.warning("gpu_scheduler: %s: %s", label, exc.reason)
            raise
        self._event("image_start", job=label)
        self._ensure_monitor()
        try:
            yield job
        finally:
            try:
                from jarvis.comfyui import COMFY_URL

                _post_json(f"{COMFY_URL}/free", {"unload_models": True, "free_memory": True}, timeout=15)
            except Exception:  # noqa: BLE001
                pass
            # Keep the slot until the RTX really has its memory back: a queued Ollama load
            # must see the RTX as the emptier GPU (default Ollama can also place on Vulkan).
            deadline = time.monotonic() + RELEASE_SETTLE_S
            while True:
                _cache.pop("cuda", None)
                info = cuda()
                if not info.get("ok") or info["free_mib"] >= info.get("total_mib", 0) - 1536:
                    break
                if time.monotonic() >= deadline:
                    # Settle expired with VRAM still held (2026-10-12: 4.2 GB stayed resident after
                    # a gallery job). Ask once more — a flag consumed before a queued prompt ran is lost.
                    logger.warning("gpu_scheduler: %s: RTX 3060 still %s MiB used after %ss; re-sending /free",
                                   label, info.get("used_mib"), RELEASE_SETTLE_S)
                    try:
                        from jarvis.comfyui import COMFY_URL

                        _post_json(f"{COMFY_URL}/free", {"unload_models": True, "free_memory": True}, timeout=15)
                    except Exception:  # noqa: BLE001
                        pass
                    break
                time.sleep(1)
            self._release(job)
            self._event("image_end", job=label, cutoff=job.cutoff_reason)

    def heavy_feasible(self, model: str) -> tuple[bool, str]:
        """Cheap pre-check used before escalating to a heavy specialist (no waiting)."""
        profile = HEAVY_MODELS.get(model)
        if not profile:
            return False, "not a configured heavy model"
        if model_size(model) <= 0:
            return False, f"{model} is not installed"
        temp = self._thermal("cuda")
        if temp is None:
            return False, "RTX 3060 telemetry unavailable"
        if temp >= CUTOFF_C or self._hold_reason:
            return False, f"RTX 3060 cooling ({temp}°C)"
        if host_available_mib() < HOST_RESERVE_MIB + int(profile["ram_mib"]):
            return False, "not enough free host RAM"
        if ftr_busy(FTR_CUDA):
            return False, "FTR is using the RTX 3060"
        with self._cv:
            if self._heavy or self._waiting >= MAX_WAITING:
                return False, "RTX 3060 exclusive slot busy"
        return True, ""

    def defer_direct_load(self, model: str) -> str:
        """Reason a warm-up/probe must not load ``model`` directly right now ('' = allowed)."""
        if (model or "").strip() in HEAVY_MODELS:
            return "heavy models load only through GPU admission"
        with self._cv:
            if self._heavy or self._heavy_waiting:
                return "RTX 3060 exclusive job active"
        return ""

    def status(self) -> dict:
        with self._cv:
            state = {
                "shared_active": self._shared,
                "heavy_active": self._heavy.label if self._heavy else None,
                "heavy_waiting": self._heavy_waiting,
                "waiting": self._waiting,
                "helper_busy": self._helper_busy,
                "hold": self._hold_reason,
            }
        return {
            **state,
            "limits": {"cutoff_c": CUTOFF_C, "resume_c": RESUME_C, "image_start_max_c": IMAGE_START_MAX_C, "cuda_reserve_mib": CUDA_RESERVE_MIB,
                       "amd_reserve_mib": AMD_RESERVE_MIB, "host_reserve_mib": HOST_RESERVE_MIB,
                       "max_waiting": MAX_WAITING, "helper_max_ctx": HELPER_MAX_CTX},
            "cuda": cuda(), "amd": amd(), "host_available_mib": host_available_mib(),
            "helper_ready": helper_ready(), "ftr_cuda_busy": ftr_busy(FTR_CUDA), "ftr_amd_busy": ftr_busy(FTR_AMD),
            "recent": list(self._events[-15:]),
        }


SCHEDULER = _Scheduler()
admit_ollama = SCHEDULER.admit_ollama
admit_image = SCHEDULER.admit_image
heavy_feasible = SCHEDULER.heavy_feasible
defer_direct_load = SCHEDULER.defer_direct_load
status = SCHEDULER.status


def reset_for_tests() -> None:
    global SCHEDULER, admit_ollama, admit_image, heavy_feasible, defer_direct_load, status
    SCHEDULER = _Scheduler()
    admit_ollama, admit_image = SCHEDULER.admit_ollama, SCHEDULER.admit_image
    heavy_feasible, status = SCHEDULER.heavy_feasible, SCHEDULER.status
    defer_direct_load = SCHEDULER.defer_direct_load
    _cache.clear()
