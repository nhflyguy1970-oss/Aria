"""FluentWindow shell: native dashboard + WebEngine for other views."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("jarvis.pyside.fluent_shell")


def fluent_shell_available() -> bool:
    try:
        from qfluentwidgets import FluentWindow  # noqa: F401

        return True
    except ImportError:
        return False


def build_aria_fluent_window(base_url: str, *, icon_path: str = "") -> Any:
    """Build FluentWindow with native dashboard tab + shared web panel."""
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QIcon
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QVBoxLayout, QWidget
    from qfluentwidgets import FluentIcon as FIF, FluentWindow, NavigationItemPosition

    from jarvis.desktop_shell import app_url, window_title
    from jarvis.gui.pyside.dashboard import DashboardView
    from jarvis.gui.pyside.styles import AURA_STYLESHEET
    from jarvis.pyside_shell import _configure_web_view

    home = app_url(base_url, shell="pyside")

    class WebPanel(QWidget):
        def __init__(self, parent=None) -> None:
            super().__init__(parent)
            self.setObjectName("ariaWebPanel")
            lay = QVBoxLayout(self)
            lay.setContentsMargins(0, 0, 0, 0)
            self.view = QWebEngineView(self)
            lay.addWidget(self.view)
            _configure_web_view(self.view)
            self._ready = False
            self._pending_view: str | None = None
            self.view.loadFinished.connect(self._on_load)
            self.view.load(QUrl(home))

        def _on_load(self, ok: bool) -> None:
            if not ok:
                return
            self._ready = True
            if self._pending_view:
                self.open_view(self._pending_view)
                self._pending_view = None

        def open_view(self, view: str) -> None:
            if not self._ready:
                self._pending_view = view
                return
            script = f"if (window.switchToView) window.switchToView({json.dumps(view)});"
            self.view.page().runJavaScript(script)

    class AriaFluentShell(FluentWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle(window_title())
            self.resize(1240, 860)
            self.setMinimumSize(1000, 680)
            if icon_path:
                self.setWindowIcon(QIcon(icon_path))
            self.setStyleSheet(AURA_STYLESHEET)

            self.dashboard = DashboardView(base_url, self)
            self.dashboard.setObjectName("dashboardInterface")
            self.web = WebPanel(self)
            self.web.setObjectName("webInterface")

            self.addSubInterface(self.dashboard, FIF.HOME, "Dashboard", NavigationItemPosition.TOP)
            self.addSubInterface(self.web, FIF.CHAT, "Chat", NavigationItemPosition.TOP)
            self.addSubInterface(self.web, FIF.CALENDAR, "Planner", NavigationItemPosition.TOP)
            self.addSubInterface(self.web, FIF.IOT, "Maker", NavigationItemPosition.TOP)
            self.addSubInterface(self.web, FIF.GLOBE, "Browser", NavigationItemPosition.TOP)

            self.dashboard.navigate_to.connect(self._navigate)
            self.stackedWidget.currentChanged.connect(self._on_page_changed)

        def _navigate(self, view: str) -> None:
            self.web.open_view(view)
            # Switch stacked widget to web interface (index 1 — first web tab after dashboard)
            self.stackedWidget.setCurrentWidget(self.web)
            for item in self.navigationInterface.items.values():
                route = getattr(item, "routeKey", None)
                if route == "webInterface":
                    self.navigationInterface.setCurrentItem(route)
                    break

        def _on_page_changed(self, index: int) -> None:
            widget = self.stackedWidget.widget(index)
            if widget is self.web:
                return
            if widget is self.dashboard:
                self.dashboard.reload()

    # Wire nav clicks to web views — FluentWindow duplicates web subinterface; hook navigation
    window = AriaFluentShell()

    _VIEW_BY_ROUTE = {
        "webInterface": "chat",
        "plannerInterface": "planner",
        "makerInterface": "maker",
        "browserInterface": "browser",
    }

    def _patch_navigation(win: AriaFluentShell) -> None:
        nav = win.navigationInterface
        original = nav.setCurrentItem

        def set_current(route_key: str) -> None:
            original(route_key)
            view = _VIEW_BY_ROUTE.get(route_key)
            if view:
                win.web.open_view(view)

        nav.setCurrentItem = set_current  # type: ignore[method-assign]

    _patch_navigation(window)
    return window
