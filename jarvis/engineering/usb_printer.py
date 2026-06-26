# Source Generated with Decompyle++
# File: usb_printer.cpython-312.pyc (Python 3.12)

'''USB/serial printer fallback for simple G-code upload.'''
from __future__ import annotations
import glob
import logging
import time
from pathlib import Path
from typing import Any
from jarvis.p5_flags import usb_printer_enabled
log = logging.getLogger('jarvis.usb_printer')

def serial_available():
    
    try:
        import serial
        return True
    except ImportError:
        return False



def list_serial_ports():
    ports = []
    if not usb_printer_enabled():
        return ports
    
    try:
        import serial.tools.list_ports as serial
        for p in serial.tools.list_ports.comports():
            if not p.description:
                p.description
            if not p.hwid:
                p.hwid
            ports.append({
                'device': p.device,
                'description': '',
                'hwid': '' })
        return ports
    except Exception:
        for path in sorted(glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')):
            ports.append({
                'device': path,
                'description': 'serial',
                'hwid': '' })
        return ports



def send_gcode(device = None, gcode_path = None, *, baud, line_delay):
    if not usb_printer_enabled():
        return {
            'ok': False,
            'error': 'USB printer disabled (JARVIS_USB_PRINTER=0)' }
    if not None():
        return {
            'ok': False,
            'error': 'pyserial not installed (pip install pyserial)' }
    import serial
    path = Path(gcode_path)
    if not path.is_file():
        return {
            'ok': False,
            'error': f'''G-code missing: {path}''' }
    if not None:
        pass
    dev = ''.strip()
    if not dev:
        ports = list_serial_ports()
        if not ports:
            return {
                'ok': False,
                'error': 'No serial ports found' }
        dev = None[0]['device']
# WARNING: Decompyle incomplete

