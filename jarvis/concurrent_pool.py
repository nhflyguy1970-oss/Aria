# Source Generated with Decompyle++
# File: concurrent_pool.cpython-312.pyc (Python 3.12)

'''Background thread pool for parallel long-running jobs.'''
from __future__ import annotations
import os
from concurrent.futures import ThreadPoolExecutor
_executor: 'ThreadPoolExecutor | None' = None

def max_workers():
    raw = os.getenv('JARVIS_PARALLEL_WORKERS', '2').strip()
    
    try:
        return max(1, min(4, int(raw)))
    except ValueError:
        return 2



def background_executor():
    pass
# WARNING: Decompyle incomplete

