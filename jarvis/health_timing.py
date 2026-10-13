"""Targeted live-health timing; logs no bodies, headers, secrets or frame locals."""
from __future__ import annotations

import asyncio
import contextvars
import json
import logging
import os
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

_TRACE = contextvars.ContextVar("aria_live_health_trace", default=None)
_LOCK = threading.RLock()
# Uvicorn explicitly configures this INFO sink before ASGI startup. The default
# root logger in headless serve mode may otherwise discard INFO diagnostics.
_LOG = logging.getLogger("uvicorn.error")

def _emit(event, **fields):
    _LOG.info("ARIA_HEALTH_TIMING %s", json.dumps({"event":event,"at":time.time(),"pid":os.getpid(),**fields},sort_keys=True))

def mark_queued():
    row = _TRACE.get()
    if row is not None:
        with _LOCK:row["queued_ns"] = time.monotonic_ns()

def mark_worker():
    row = _TRACE.get()
    if row is not None:
        with _LOCK:
            row["worker_ns"] = time.monotonic_ns()
            row["worker_tid"] = threading.get_ident()
            row["worker_native_tid"] = threading.get_native_id()

@contextmanager
def stage(name):
    row = _TRACE.get()
    start = time.monotonic_ns();cpu = time.thread_time_ns()
    if row is not None:
        with _LOCK:row["active_stage"] = {"name":name,"since_ns":start,"tid":threading.get_ident(),"native_tid":threading.get_native_id()}
    try:yield
    finally:
        if row is not None:
            with _LOCK:
                row["stages"].append({"name":name,"wall_ms":(time.monotonic_ns()-start)/1e6,"thread_cpu_ms":(time.thread_time_ns()-cpu)/1e6})
                row.pop("active_stage",None)

def _thread_evidence(tids):
    # Only code identity and kernel scheduling counters; never source text/locals.
    frames = sys._current_frames();out = {}
    try:
        for tid,native in tids.items():
            frame = frames.get(tid);stack = []
            while frame is not None and len(stack)<16:
                stack.append({"file":Path(frame.f_code.co_filename).name,"function":frame.f_code.co_name,"line":frame.f_lineno});frame=frame.f_back
            entry = {"stack":stack,"native_tid":native}
            try:entry["schedstat"] = (Path('/proc/self/task')/str(native)/'schedstat').read_text().strip()
            except OSError:entry["schedstat"] = None
            out[str(tid)] = entry
    finally:del frames
    return out

class HealthTimingMiddleware:
    """Outer ASGI ingress timing plus independent loop/stalled-request observer."""
    def __init__(self,app):
        self.app=app;self.pending={};self.stop=threading.Event();self.task=None;self.thread=None
        self.heartbeat_ns=time.monotonic_ns();self.loop_tid=None;self.loop_native_tid=None
    async def _heartbeat(self):
        while True:
            self.heartbeat_ns=time.monotonic_ns();await asyncio.sleep(.1)
    def _watch(self):
        reported=set();loop_reported=False
        while not self.stop.wait(.1):
            now=time.monotonic_ns();lag_ms=(now-self.heartbeat_ns)/1e6
            with _LOCK:
                late=[dict(r) for r in self.pending.values() if now-r['ingress_ns']>=1_000_000_000 and r['id'] not in reported]
            lagged=lag_ms>=500 and not loop_reported
            if late or lagged:
                tids={self.loop_tid:self.loop_native_tid}
                for row in late:
                    if row.get('worker_tid'):tids[row['worker_tid']]=row['worker_native_tid']
                _emit('stall',loop_delay_ms=lag_ms,requests=late,threads=_thread_evidence(tids))
                reported.update(r['id'] for r in late)
            with _LOCK:reported.intersection_update(self.pending)
            loop_reported=lag_ms>=500
    def _start(self):
        self.loop_tid=threading.get_ident();self.loop_native_tid=threading.get_native_id()
        self.heartbeat_ns=time.monotonic_ns();self.task=asyncio.create_task(self._heartbeat())
        self.thread=threading.Thread(target=self._watch,name='aria-health-timing',daemon=True);self.thread.start()
    async def __call__(self,scope,receive,send):
        if scope['type']=='lifespan':
            async def lifecycle_send(message):
                if message['type']=='lifespan.startup.complete':self._start()
                await send(message)
            try:await self.app(scope,receive,lifecycle_send)
            finally:
                self.stop.set()
                if self.task:
                    self.task.cancel()
                    try:await self.task
                    except asyncio.CancelledError:pass
            return
        if scope['type']!='http' or scope.get('path')!='/api/live':
            return await self.app(scope,receive,send)
        row={'id':uuid.uuid4().hex,'ingress_ns':time.monotonic_ns(),'stages':[]}
        token=_TRACE.set(row)
        with _LOCK:self.pending[row['id']]=row
        _emit('ingress',id=row['id'],ingress_ns=row['ingress_ns'])
        async def response_send(message):
            if message['type']=='http.response.start':
                row['status']=message['status'];row['response_ns']=time.monotonic_ns()
            await send(message)
        try:await self.app(scope,receive,response_send)
        finally:
            with _LOCK:
                self.pending.pop(row['id'],None);result=dict(row)
            result['total_ms']=(time.monotonic_ns()-row['ingress_ns'])/1e6
            result['loop_delay_ms']=(time.monotonic_ns()-self.heartbeat_ns)/1e6
            if row.get('queued_ns'):
                result['admission_ms']=(row['queued_ns']-row['ingress_ns'])/1e6
                if row.get('worker_ns'):result['executor_queue_ms']=(row['worker_ns']-row['queued_ns'])/1e6
            _emit('complete',**result);_TRACE.reset(token)
