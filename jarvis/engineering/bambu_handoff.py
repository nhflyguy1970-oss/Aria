# Source Generated with Decompyle++
# File: bambu_handoff.cpython-312.pyc (Python 3.12)

'''Bambu Lab print handoff — slice locally, send via Bambu Studio / SD (no LAN mode).'''
from __future__ import annotations
import shutil
import time
from pathlib import Path
from typing import Any
from jarvis.config import DATA_DIR
from jarvis.engineering.printer_profiles import get_model
HANDOFF_ROOT = DATA_DIR / 'engineering' / 'handoff'

def handoff_dir(printer = None):
    if not printer.get('id'):
        printer.get('id')
        if not printer.get('model'):
            printer.get('model')
    pid = 'bambu'
    return HANDOFF_ROOT / pid


def printer_status(printer = None):
    '''Status without LAN — last handoff file + Studio instructions.'''
    if not printer.get('model'):
        printer.get('model')
    if not get_model(''):
        get_model('')
    model = { }
    out_dir = handoff_dir(printer)
    latest = out_dir / 'latest.gcode'
    meta_path = out_dir / 'handoff.json'
    last_at = ''
# WARNING: Decompyle incomplete


def handoff_gcode(printer = None, gcode_path = None):
    '''Copy G-code to handoff folder for Bambu Studio / SD transfer.'''
    src = Path(gcode_path)
    if not src.is_file():
        return {
            'ok': False,
            'error': f'''G-code missing: {src}''' }
    out_dir = None(printer)
    out_dir.mkdir(parents = True, exist_ok = True)
    dest = out_dir / 'latest.gcode'
    shutil.copy2(src, dest)
    named = out_dir / src.name
    if named != dest:
        shutil.copy2(src, named)
    readme = out_dir / 'SEND.txt'
    if not printer.get('model'):
        printer.get('model')
    if not get_model(''):
        get_model('')
    model = { }
    readme.write_text(f'''ARIA handoff — {model.get('label', 'Bambu printer')}\n\nG-code: {dest.name}\n\n{model.get('handoff_hint', '')}\n\n1. Open Bambu Studio\n2. File → Import → select latest.gcode (or drag onto plate)\n3. Send to printer (cloud bind) or export to SD card\n''', encoding = 'utf-8')
    import json
    meta = {
        'at': time.time(),
        'source': str(src),
        'gcode': str(dest) }
    (out_dir / 'handoff.json').write_text(json.dumps(meta, indent = 2), encoding = 'utf-8')
    return {
        'ok': True,
        'handoff_dir': str(out_dir),
        'gcode_path': str(dest),
        'readme': str(readme),
        'message': f'''G-code ready for **{printer.get('name', 'Bambu')}** — open `{dest}` in Bambu Studio or copy to SD card.''' }

