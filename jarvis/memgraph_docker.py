# Source Generated with Decompyle++
# File: memgraph_docker.cpython-312.pyc (Python 3.12)

'''Start Memgraph Docker container when Jarvis boots (optional).'''
from __future__ import annotations
import logging
import os
import socket
import subprocess
import threading
import time
from jarvis.env_loader import load_jarvis_env
from jarvis.ha_docker import container_exists, container_running, docker_available
logger = logging.getLogger('jarvis.memgraph_docker')

def memgraph_container_name():
    if not os.getenv('JARVIS_MEMGRAPH_CONTAINER'):
        os.getenv('JARVIS_MEMGRAPH_CONTAINER')
    return 'jarvis-memgraph'.strip()


def memgraph_bolt_port():
    raw = os.getenv('JARVIS_GRAPH_BOLT_PORT', '7687').strip()
    
    try:
        return int(raw)
    except ValueError:
        return 7687



def memgraph_http_port():
    raw = os.getenv('JARVIS_GRAPH_HTTP_PORT', '7444').strip()
    
    try:
        return int(raw)
    except ValueError:
        return 7444



def should_autostart_memgraph():
    load_jarvis_env()
    autostart_memgraph = autostart_memgraph
    import jarvis.service_policy
    if not autostart_memgraph():
        return False
    return docker_available()


def memgraph_bolt_healthy(timeout = None):
    port = memgraph_bolt_port()
    
    try:
        socket.create_connection(('127.0.0.1', port), timeout = timeout)
        
        try:
            None(None, None)
            return True
            with None:
                if not None:
                    pass
            
            try:
                return None
                
                try:
                    pass
                except OSError:
                    return False






def _wait_for_bolt(timeout = None, interval = None):
    deadline = time.time() + timeout
    if time.time() < deadline:
        if memgraph_bolt_healthy(timeout = min(1.5, interval)):
            return True
        if not container_running(memgraph_container_name()) and container_exists(memgraph_container_name()):
            return False
        time.sleep(interval)
        if time.time() < deadline:
            continue
    return memgraph_bolt_healthy()


def ensure_memgraph(*, block, timeout):
    '''Start the Memgraph Docker container when autostart is enabled.'''
    if not should_autostart_memgraph():
        if not memgraph_bolt_healthy():
            memgraph_bolt_healthy()
        return container_running(memgraph_container_name())
    name = None()
    if memgraph_bolt_healthy():
        logger.info('Memgraph: bolt already up on port %s', memgraph_bolt_port())
        return True
    if container_running(name):
        if block:
            ok = _wait_for_bolt(timeout = timeout)
            if ok:
                logger.info('Memgraph: %s', 'ready')
                return ok
            None(logger.info, 'Memgraph: %s')
            return ok
        None.info('Memgraph: container running, bolt still starting')
        return True
    if not docker_available():
        logger.warning('Memgraph autostart skipped — docker not found')
        return False
    port = memgraph_bolt_port()
    http_port = memgraph_http_port()
    
    try:
        if container_exists(name):
            logger.info('Memgraph: starting container %s', name)
            subprocess.run([
                'docker',
                'start',
                name], check = True, timeout = 60)
        else:
            logger.info('Memgraph: creating container %s', name)
            subprocess.run([
                'docker',
                'run',
                '-d',
                '--name',
                name,
                '--restart=unless-stopped',
                '-p',
                f'''{port}:7687''',
                '-p',
                f'''{http_port}:7444''',
                '-v',
                'jarvis-memgraph-data:/var/lib/memgraph',
                'memgraph/memgraph-platform'], check = True, timeout = 120)
        if block:
            ok = _wait_for_bolt(timeout = timeout)
            if ok:
                logger.info('Memgraph: %s', 'ready')
                return ok
            None(logger.info, 'Memgraph: %s')
            return ok
    except subprocess.CalledProcessError:
        exc = None
        logger.warning('Memgraph docker start failed: %s', exc)
        exc = None
        del exc
        return False
        exc = None
        del exc



def ensure_memgraph_background():
    if not should_autostart_memgraph():
        return None
    threading.Thread(target = (lambda : ensure_memgraph(block = True, timeout = 60)), daemon = True, name = 'jarvis-memgraph-docker').start()

