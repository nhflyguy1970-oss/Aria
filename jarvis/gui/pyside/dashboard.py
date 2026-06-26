# Source Generated with Decompyle++
# File: dashboard.cpython-312.pyc (Python 3.12)

'''Ada-style native dashboard for ARIA PySide / Fluent shell.'''
from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Callable
logger = logging.getLogger('jarvis.pyside.dashboard')

try:
    from qfluentwidgets import BodyLabel, CardWidget, FluentIcon as FIF, IconWidget, StrongBodyLabel, TitleLabel
    _FLUENT = True
    from PySide6.QtCore import Qt, QThread, QTimer, Signal
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
    from jarvis.gui.pyside.api_client import activate_scene, fetch_dashboard
    
    def _time_greeting(hour = None):
        if  <= 5, hour or 5, hour < 12:
            return 'Good morning'
        if  <= 12, hour or 12, hour < 17:
            return 'Good afternoon'
        if  <= 17, hour or 17, hour < 22:
            return 'Good evening'
            return 'Hello'
        return 'Hello'

    
    def _card(parent = None):
        if _FLUENT:
            w = CardWidget(parent)
            w.setBorderRadius(14)
            return w
        f = None(parent)
        f.setObjectName('ariaCard')
        return f

    
    class DashboardLoader(QThread):
        pass
    # WARNING: Decompyle incomplete

    
    class GreetingsHeader(QWidget):
        pass
    # WARNING: Decompyle incomplete

    
    class StatCard(QFrame):
        pass
    # WARNING: Decompyle incomplete

    
    class HomeScenesCard(QWidget):
        pass
    # WARNING: Decompyle incomplete

    
    class IntelligenceFeed(QWidget):
        pass
    # WARNING: Decompyle incomplete

    
    class BriefingStrip(QWidget):
        pass
    # WARNING: Decompyle incomplete

    
    class DashboardView(QWidget):
        pass
    # WARNING: Decompyle incomplete

    return None
except ImportError:
    _FLUENT = False
    continue

