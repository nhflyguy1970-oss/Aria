"""PySide6 / Fluent desktop shell for ARIA."""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
from typing import Any

from jarvis.desktop_shell import (
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    ICON_PATH,
    InstanceLock,
    acquire_gui_shell_lock,
    app_url,
    default_url,
    focus_existing_window,
    gui_shell_running,
    pid_alive,
    python_exe,
    release_gui_shell_lock,
    spawn_detached,
    wait_for_server,
    window_title,
)

logger = logging.getLogger("jarvis.pyside_shell")

LOCK = InstanceLock("pyside_shell")
_main_window: Any = None


def _import_pyside():
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QAction, QColor, QIcon, QPalette
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QMainWindow,
        QStatusBar,
        QToolBar,
        QVBoxLayout,
        QWidget,
    )

    return (
        QApplication,
        QMainWindow,
        QToolBar,
        QStatusBar,
        QWebEngineView,
        QUrl,
        QAction,
        QIcon,
        QPalette,
        QColor,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
    )


def is_available() -> bool:
    try:
        _import_pyside()
        return True
    except ImportError:
        return False


def can_run_window() -> bool:
    from jarvis.desktop_runtime import pyside_window_ready

    return pyside_window_ready()


def fluent_available() -> bool:
    try:
        from qfluentwidgets import Theme, setTheme  # noqa: F401

        return True
    except ImportError:
        return False


def _use_fluent_chrome() -> bool:
    mode = (os.getenv("JARVIS_GUI_MODE") or "fluent").strip().lower()
    if mode == "fluent":
        return True
    if mode == "pyside":
        return os.getenv("JARVIS_FLUENT_WIDGETS", "1").strip().lower() not in ("0", "false", "no", "off")
    return False


def missing_dependency_hint() -> str:
    from jarvis.desktop_runtime import desktop_deps_hint

    extra = desktop_deps_hint()
    lines = [
        "PySide6 desktop shell cannot start on this system.",
        "Run: pip install PySide6 PySide6-Addons",
        "(optional: PySide6-Fluent-Widgets)",
    ]
    if extra:
        lines.append(f"System packages: {extra}")
    return "\n".join(lines)


def focus_window() -> bool:
    """Raise the in-process PySide main window."""
    win = _main_window
    if win is None:
        return False
    try:
        if win.isMinimized():
            win.showNormal()
        win.show()
        win.raise_()
        win.activateWindow()
        return True
    except Exception as exc:
        logger.debug("focus_window: %s", exc)
        return False


def _register_main_window(window: Any) -> None:
    global _main_window
    _main_window = window
    LOCK.pid_file.parent.mkdir(parents=True, exist_ok=True)
    LOCK.pid_file.write_text(str(os.getpid()), encoding="utf-8")


def _clear_main_window() -> None:
    global _main_window
    _main_window = None
    try:
        LOCK.pid_file.unlink(missing_ok=True)
    except OSError:
        pass


def terminate_running_shell(*, timeout_sec: float = 4.0) -> bool:
    """Stop a running PySide shell so a fresh window can open."""
    pids: set[int] = set()
    for path in (LOCK.pid_file,):
        if not path.is_file():
            continue
        try:
            pid = int(path.read_text(encoding="utf-8").strip() or "0")
            if pid and pid != os.getpid():
                pids.add(pid)
        except (OSError, ValueError):
            pass
    if not pids:
        return False
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if not any(pid_alive(pid) for pid in pids):
            break
        time.sleep(0.15)
    for pid in pids:
        if pid_alive(pid):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass
    for path in (LOCK.pid_file, LOCK.lock_file):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    return True


def _prepare_shell_launch(*, force_new: bool) -> bool:
    """Return True when a new shell should be created."""
    if LOCK.another_running() or gui_shell_running():
        if force_new:
            terminate_running_shell()
            return True
        if focus_window() or focus_existing_window():
            return False
        logger.warning("PySide shell running but could not be focused — restarting window")
        terminate_running_shell()
    return True


def _apply_dark_palette(app: Any) -> None:
    parts = _import_pyside()
    QPalette = parts[8]
    QColor = parts[9]
    palette = QPalette()
    bg = QColor("#0a0c10")
    fg = QColor("#e8eaed")
    palette.setColor(QPalette.ColorRole.Window, bg)
    palette.setColor(QPalette.ColorRole.WindowText, fg)
    palette.setColor(QPalette.ColorRole.Base, QColor("#11141a"))
    palette.setColor(QPalette.ColorRole.Text, fg)
    palette.setColor(QPalette.ColorRole.Button, QColor("#181c24"))
    palette.setColor(QPalette.ColorRole.ButtonText, fg)
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#4da3ff"))
    palette.setColor(QPalette.ColorRole.HighlightedText, fg)
    app.setPalette(palette)


def _apply_fluent_theme(app: Any) -> bool:
    if not fluent_available():
        app.setStyle("Fusion")
        _apply_dark_palette(app)
        return False
    try:
        from qfluentwidgets import Theme, setTheme

        setTheme(Theme.DARK)
        return True
    except ImportError:
        app.setStyle("Fusion")
        _apply_dark_palette(app)
        return False


def _grant_web_media_permissions(page) -> None:
    try:
        from PySide6.QtWebEngineCore import QWebEnginePage

        def _on_feature(url, feature):
            if feature in (
                QWebEnginePage.Feature.MediaAudioCapture,
                QWebEnginePage.Feature.MediaVideoCapture,
                QWebEnginePage.Feature.MediaAudioVideoCapture,
            ):
                page.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)

        page.featurePermissionRequested.connect(_on_feature)
    except Exception as exc:
        logger.debug("web media permissions: %s", exc)


def _configure_web_view(view) -> None:
    from PySide6.QtWebEngineCore import QWebEngineSettings

    settings = view.settings()
    settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
    settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
    _grant_web_media_permissions(view.page())


def _build_fluent_window(url: str) -> Any:
    from qfluentwidgets import CaptionLabel, FluentIcon, FluentWindow, Theme, setTheme, TransparentToolButton

    QApplication, *_p, QWebEngineView, QUrl, QIcon, _pal, _col, QWidget, QVBoxLayout, QHBoxLayout = _import_pyside()

    setTheme(Theme.DARK)
    shell = "fluent" if _use_fluent_chrome() else "pyside"
    home = app_url(url, shell=shell)

    class AriaFluentWindow(FluentWindow):
        def __init__(self) -> None:
            super().__init__()
            self._home = home
            self.setWindowTitle(window_title())
            self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
            self.setMinimumSize(720, 480)
            if ICON_PATH.is_file():
                self.setWindowIcon(QIcon(str(ICON_PATH)))

            page = QWidget(self)
            page.setObjectName("ariaMain")
            root = QVBoxLayout(page)
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(0)

            nav = QHBoxLayout()
            nav.setContentsMargins(12, 8, 12, 4)

            self.view = QWebEngineView(page)
            _configure_web_view(self.view)
            self.view.load(QUrl(self._home))

            btn_back = TransparentToolButton(FluentIcon.RETURN, page)
            btn_back.clicked.connect(self.view.back)
            btn_fwd = TransparentToolButton(FluentIcon.CHEVRON_RIGHT, page)
            btn_fwd.clicked.connect(self.view.forward)
            btn_reload = TransparentToolButton(FluentIcon.SYNC, page)
            btn_reload.clicked.connect(self.view.reload)
            btn_home = TransparentToolButton(FluentIcon.HOME, page)
            btn_home.clicked.connect(lambda: self.view.load(QUrl(self._home)))

            nav.addWidget(btn_back)
            nav.addWidget(btn_fwd)
            nav.addWidget(btn_reload)
            nav.addWidget(btn_home)
            nav.addStretch(1)
            self._status = CaptionLabel("", page)
            nav.addWidget(self._status)
            root.addLayout(nav)
            root.addWidget(self.view, 1)
            self.view.loadFinished.connect(lambda ok: self._status.setText("Ready" if ok else "Load failed"))
            self.addSubInterface(page, FluentIcon.HOME, "ARIA", isTransparent=True)

    win = AriaFluentWindow()
    _register_main_window(win)
    return win


def _build_window(url: str) -> Any:
    (
        QApplication,
        QMainWindow,
        QToolBar,
        QStatusBar,
        QWebEngineView,
        QUrl,
        QAction,
        QIcon,
        *_,
    ) = _import_pyside()

    home = app_url(url, shell="pyside")

    class JarvisMainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self._home = home
            self.setWindowTitle(window_title())
            self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)
            self.setMinimumSize(720, 480)
            if ICON_PATH.is_file():
                self.setWindowIcon(QIcon(str(ICON_PATH)))
            self.view = QWebEngineView(self)
            _configure_web_view(self.view)
            self.setCentralWidget(self.view)
            self.view.load(QUrl(self._home))
            toolbar = QToolBar("Navigation", self)
            toolbar.setMovable(False)
            self.addToolBar(toolbar)
            for label, slot in (
                ("Back", self.view.back),
                ("Forward", self.view.forward),
                ("Reload", self.view.reload),
                ("Home", lambda: self.view.load(QUrl(self._home))),
            ):
                act = QAction(label, self)
                act.triggered.connect(slot)
                toolbar.addAction(act)
            status = QStatusBar(self)
            self.setStatusBar(status)
            self.view.loadFinished.connect(lambda ok: status.showMessage("Ready" if ok else "Load failed", 3000))

    win = JarvisMainWindow()
    _register_main_window(win)
    return win


def run_window_blocking(url: str, *, wait_for_ready: bool = True) -> int:
    if not is_available() or not can_run_window():
        sys.stderr.write(missing_dependency_hint() + "\n")
        return 1

    force_new = os.getenv("JARVIS_SHELL_FORCE_NEW", "").strip().lower() in ("1", "true", "yes", "on")
    if not _prepare_shell_launch(force_new=force_new):
        return 0

    shell_name = "fluent" if _use_fluent_chrome() else "pyside"
    if not acquire_gui_shell_lock(shell_name):
        if focus_window() or focus_existing_window():
            return 0
        terminate_running_shell()
        if not acquire_gui_shell_lock(shell_name):
            sys.stderr.write("Another GUI shell is still starting\n")
            return 1

    try:
        if wait_for_ready and not wait_for_server(url):
            sys.stderr.write(f"Server not ready at {url}\n")
            return 1

        QApplication, *_ = _import_pyside()
        app = QApplication.instance() or QApplication(sys.argv)
        use_fluent = _use_fluent_chrome() and fluent_available()
        if use_fluent:
            _apply_fluent_theme(app)
            os.environ["JARVIS_SHELL"] = "pyside-fluent"
            window = _build_fluent_window(url)
        else:
            if _use_fluent_chrome() and not fluent_available():
                logger.warning("Fluent widgets requested but not installed — using Fusion theme")
            _apply_fluent_theme(app) if fluent_available() else _apply_dark_palette(app)
            os.environ["JARVIS_SHELL"] = "pyside"
            window = _build_window(url)
        window.show()
        code = app.exec()
        _clear_main_window()
        return int(code)
    finally:
        release_gui_shell_lock()
        LOCK.release()


def launch_pyside_shell(url: str) -> bool:
    if not is_available() or not can_run_window():
        return False
    if not _prepare_shell_launch(force_new=False):
        return True
    return spawn_detached(
        [python_exe(), "-m", "jarvis.pyside_shell", url, "--no-wait"],
    )


def status() -> dict:
    return {
        "available": is_available(),
        "fluent": fluent_available(),
        "fluent_active": fluent_available() and _use_fluent_chrome(),
        "running": LOCK.another_running() or gui_shell_running(),
        "mode": os.getenv("JARVIS_GUI_MODE", ""),
    }


def main(argv: list[str] | None = None) -> int:
    from jarvis.env_loader import load_jarvis_env

    load_jarvis_env()
    args = list(argv if argv is not None else sys.argv[1:])
    wait_for_ready = True
    if args and args[-1] == "--no-wait":
        wait_for_ready = False
        args.pop()
    url = args[0] if args else default_url()
    # Desktop shortcut and `python -m jarvis.pyside_shell` run the window in this process.
    return run_window_blocking(url, wait_for_ready=wait_for_ready)


if __name__ == "__main__":
    raise SystemExit(main())
