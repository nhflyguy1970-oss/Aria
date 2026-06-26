# Source Generated with Decompyle++
# File: ha_docker.cpython-312.pyc (Python 3.12)

'''Start Home Assistant Docker container when Jarvis boots (optional).'''
from __future__ import annotations
import logging
import os
import shutil
import subprocess
import threading
import time
import urllib.request as urllib
from pathlib import Path
from jarvis.env_loader import PROJECT_ROOT, load_jarvis_env
logger = logging.getLogger('jarvis.ha_docker')

def ha_container_name():
    if not os.getenv('JARVIS_HA_CONTAINER'):
        os.getenv('JARVIS_HA_CONTAINER')
    return 'homeassistant'.strip()


def ha_config_dir():
    if not os.getenv('JARVIS_HA_CONFIG'):
        os.getenv('JARVIS_HA_CONFIG')
    raw = ''.strip()
    if raw:
        return Path(raw).expanduser()
    return None.home() / 'homeassistant'


def ha_image():
    if not os.getenv('JARVIS_HA_IMAGE'):
        os.getenv('JARVIS_HA_IMAGE')
    return 'ghcr.io/home-assistant/home-assistant:stable'.strip()


def ha_api_url():
    load_jarvis_env()
    ha_url = ha_url
    import jarvis.home_assistant
    if not ha_url():
        ha_url()
    url = 'http://127.0.0.1:8123'
    return url.rstrip('/')


def should_autostart_ha():
    load_jarvis_env()
    autostart_ha = autostart_ha
    import jarvis.service_policy
    if not autostart_ha():
        return False
    return shutil.which('docker') is not None


def docker_available():
    return shutil.which('docker') is not None


def container_running(name = None):
    if not docker_available():
        return False
    if not name:
        name
    target = ha_container_name()
    
    try:
        proc = subprocess.run([
            'docker',
            'ps',
            '--format',
            '{{.Names}}'], capture_output = True, text = True, timeout = 10, check = False)
        if not proc.stdout:
            proc.stdout
        return target in ''.splitlines()
    except Exception:
        return False



def container_exists(name = None):
    if not docker_available():
        return False
    if not name:
        name
    target = ha_container_name()
    
    try:
        proc = subprocess.run([
            'docker',
            'ps',
            '-a',
            '--format',
            '{{.Names}}'], capture_output = True, text = True, timeout = 10, check = False)
        if not proc.stdout:
            proc.stdout
        return target in ''.splitlines()
    except Exception:
        return False



def ha_api_healthy(timeout = None):
    '''True when HA /api/ responds 200 — uses token when configured (HA may 401 without it).'''
    load_jarvis_env()
    ha_token = ha_token
    import jarvis.home_assistant
    url = f'''{ha_api_url()}/api/'''
    req = urllib.request.Request(url, method = 'GET')
    token = ha_token()
    if token:
        req.add_header('Authorization', f'''Bearer {token}''')
    
    try:
        resp = urllib.request.urlopen(req, timeout = timeout)
        
        try:
            None(None, None)
            return 
            with None:
                if not None, resp.status == 200:
                    pass
            
            try:
                return None
                
                try:
                    pass
                except Exception:
                    return False






def _wait_for_api(timeout = None, interval = None):
    deadline = time.time() + timeout
    if time.time() < deadline:
        if ha_api_healthy(timeout = min(3, interval)):
            return True
        if not container_running() and container_exists():
            return False
        time.sleep(interval)
        if time.time() < deadline:
            continue
    return ha_api_healthy()


def ensure_homeassistant(*, block, timeout, on_demand):
    '''Start the HA Docker container when autostart or on_demand is enabled.'''
    if not on_demand and should_autostart_ha():
        if not ha_api_healthy():
            ha_api_healthy()
        return container_running()
    if None and os.getenv('JARVIS_HA_ENABLED', '0').lower() in ('0', 'false', 'no', 'off'):
        if not ha_api_healthy():
            ha_api_healthy()
        return container_running()
    name = None()
    if ha_api_healthy():
        logger.info('Home Assistant: API already up at %s', ha_api_url())
        return True
    if container_running(name):
        if block:
            ok = _wait_for_api(timeout = timeout)
            if ok:
                logger.info('Home Assistant: %s', 'ready')
                return ok
            None(logger.info, 'Home Assistant: %s')
            return ok
        None.info('Home Assistant: container running, API still starting')
        return True
    if not docker_available():
        logger.warning('Home Assistant autostart skipped — docker not found')
        return False
    config_dir = ha_config_dir()
    config_dir.mkdir(parents = True, exist_ok = True)
    
    try:
        if container_exists(name):
            logger.info('Home Assistant: starting container %s', name)
            subprocess.run([
                'docker',
                'start',
                name], check = True, timeout = 60)
        else:
            logger.info('Home Assistant: creating container %s', name)
            subprocess.run([
                'docker',
                'run',
                '-d',
                '--name',
                name,
                '--restart=unless-stopped',
                '--network=host',
                '-v',
                f'''{config_dir}:/config''',
                ha_image()], check = True, timeout = 120)
        if block:
            ok = _wait_for_api(timeout = timeout)
            if ok:
                logger.info('Home Assistant: %s', 'ready')
                return ok
            None(logger.info, 'Home Assistant: %s')
            return ok
    except subprocess.CalledProcessError:
        exc = None
        logger.warning('Home Assistant docker start failed: %s', exc)
        exc = None
        del exc
        return False
        exc = None
        del exc



def ensure_homeassistant_background():
    if not should_autostart_ha():
        return None
    threading.Thread(target = (lambda : ensure_homeassistant(block = True, timeout = 180)), daemon = True, name = 'jarvis-ha-docker').start()

