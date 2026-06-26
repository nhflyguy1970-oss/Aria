# Source Generated with Decompyle++
# File: debug_bundle.cpython-312.pyc (Python 3.12)

'''Collect diagnostics for support and the debug-bundle UI.'''
from __future__ import annotations
import os
import platform
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / 'data' / 'logs'

def _tail(path = None, max_bytes = None):
    if not path.is_file():
        return ''
    
    try:
        data = path.read_text(encoding = 'utf-8', errors = 'replace')
        return data[-max_bytes:]
    except OSError:
        return ''



def collect(*, log_bytes):
    bundle = {
        'ok': True,
        'generated_at': datetime.now(timezone.utc).isoformat(timespec = 'seconds'),
        'python': sys.version.split()[0],
        'platform': platform.platform() }
    bundle['server_version'] = os.getenv('JARVIS_APP_VERSION', '3.1.0')
    bundle['ui_version'] = os.getenv('JARVIS_UI_VERSION', '5.15.0')
    
    try:
        snapshot = snapshot
        import jarvis.metrics
        bundle['metrics'] = snapshot()
        
        try:
            env_snapshot = snapshot
            import jarvis.environment
            bundle['environment'] = env_snapshot(include_resources = True)
            
            try:
                jobs_snapshot = snapshot
                import jarvis.jobs_center
                bundle['jobs'] = jobs_snapshot(recent_limit = 8)
                
                try:
                    has_active_work_persisted = has_active_work_persisted
                    import jarvis.media_jobs
                    bundle['media_work_persisted'] = has_active_work_persisted()
                    bundle['logs'] = {
                        'jarvis': _tail(LOG_DIR / 'jarvis.log', log_bytes),
                        'serve': _tail(LOG_DIR / 'serve.log', log_bytes) }
                    
                    try:
                        cad_status = cad_status
                        import jarvis.engineering.cad_deps
                        list_models = list_models
                        import jarvis.engineering.cad_store
                        list_printers = list_printers
                        import jarvis.engineering.printer_store
                        SETTINGS_FILE = SETTINGS_FILE
                        slicer_status = slicer_status
                        import jarvis.engineering.slicer
                        models = list_models()
                        last = models[0] if models else { }
                        bundle['cad_print'] = {
                            'cad': cad_status(),
                            'slicer': slicer_status(),
                            'printer_settings': SETTINGS_FILE.read_text(encoding = 'utf-8')[:4000] if SETTINGS_FILE.is_file() else '',
                            'printers': list_printers(),
                            'last_model': {
                                'id': last.get('id'),
                                'name': last.get('name'),
                                'stl_path': last.get('stl_path'),
                                'backend': last.get('backend') },
                            'slicer_log': _tail(PROJECT_ROOT / 'data' / 'engineering' / 'slicer.log', log_bytes) }
                        bundle['text'] = format_text(bundle)
                        return bundle
                        except Exception:
                            exc = None
                            bundle['metrics'] = {
                                'error': str(exc) }
                            exc = None
                            del exc
                            continue
                            exc = None
                            del exc
                        except Exception:
                            exc = None
                            bundle['environment'] = {
                                'error': str(exc) }
                            exc = None
                            del exc
                            continue
                            exc = None
                            del exc
                        except Exception:
                            exc = None
                            bundle['jobs'] = {
                                'error': str(exc) }
                            exc = None
                            del exc
                            continue
                            exc = None
                            del exc
                        except Exception:
                            bundle['media_work_persisted'] = None
                            continue
                    except Exception:
                        exc = None
                        bundle['cad_print'] = {
                            'error': str(exc) }
                        exc = None
                        del exc
                        continue
                        exc = None
                        del exc







def format_text(bundle = None):
    lines = [
        'ARIA debug bundle',
        f'''Generated: {bundle.get('generated_at')}''',
        f'''Server: v{bundle.get('server_version')} · Python {bundle.get('python')}''',
        f'''Platform: {bundle.get('platform')}''',
        '']
    if not bundle.get('environment'):
        bundle.get('environment')
    env = { }
    if not isinstance(env, dict) and env.get('error'):
        if not env.get('gpu'):
            env.get('gpu')
        gpu = { }
        lines.append(f'''Profile: {env.get('profile')} · Disk free: {env.get('disk_free_gb')}GB · VRAM free: {gpu.get('free_vram_mb', '?')}MB''')
    if not bundle.get('metrics'):
        bundle.get('metrics')
    metrics = { }
    if isinstance(metrics, dict):
        lines.append(f'''Uptime: {metrics.get('uptime_sec', '?')}s · Watchdog restarts: {metrics.get('watchdog_restarts', 0)}''')
    if not bundle.get('jobs'):
        bundle.get('jobs')
    jobs = { }
    if isinstance(jobs, dict) and jobs.get('any_busy'):
        lines.append('Background jobs: BUSY')
        if not jobs.get('recent'):
            jobs.get('recent')
        for job in [][:5]:
            if job.get('done'):
                continue
            lines.append(f'''  · [{job.get('queue')}] {job.get('label')}: {job.get('message')}''')
    if not bundle.get('cad_print'):
        bundle.get('cad_print')
    cad = { }
    if not isinstance(cad, dict) and cad.get('error'):
        if not cad.get('last_model'):
            cad.get('last_model')
        last = { }
        if last.get('id'):
            if not last.get('name'):
                last.get('name')
            lines.append(f'''Last STL: {last.get('id')} ({last.get('backend', '?')})''')
        if not cad.get('printers'):
            cad.get('printers')
        printers = []
        if printers:
            lines.append(f'''Printers: {len(printers)} configured''')
    lines.append('')
    if not bundle.get('logs'):
        bundle.get('logs')
    for name, content in { }.items():
        if not content:
            continue
        lines.append(f'''--- {name}.log (tail) ---''')
        lines.append(content.rstrip())
        lines.append('')
    return '\n'.join(lines).strip()

