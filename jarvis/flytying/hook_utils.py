# Source Generated with Decompyle++
# File: hook_utils.cpython-312.pyc (Python 3.12)

'''Hook size parsing and normalization.'''
from __future__ import annotations
import re
from typing import Any
_HOOK_SIZE_RE = re.compile('(?:#|size\\s*|sz\\.?\\s*)?(\\d{1,2})\\s*(?:-\\s*(\\d{1,2}))?\\s*(?:hook|dry|nymph|streamer|emerg|scud|curved|jig|barbless)?', re.I)

def parse_hook(hook = None):
    if not hook:
        hook
    text = str('').strip()
    if not text:
        return {
            'raw': '',
            'size_min': None,
            'size_max': None,
            'size_label': '' }
    m = None.search(text)
    if not m:
        nums = re.findall('\\d{1,2}', text)
        if nums:
            n = int(nums[0])
            return {
                'raw': text,
                'size_min': n,
                'size_max': n,
                'size_label': f'''#{n}''' }
        return {
            'raw': None,
            'size_min': None,
            'size_max': None,
            'size_label': text }
    lo = None(m.group(1))
    hi = int(m.group(2)) if m.group(2) else lo
    hi = max(lo, hi)
    lo = min(lo, hi)
    label = f'''#{lo}''' if lo == hi else f'''#{lo}-{hi}'''
    return {
        'raw': text,
        'size_min': lo,
        'size_max': hi,
        'size_label': label }


def hook_matches_filter(hook = None, *, size):
    pass
# WARNING: Decompyle incomplete

