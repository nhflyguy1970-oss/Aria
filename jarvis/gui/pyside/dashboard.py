"""Ada-style native dashboard for ARIA PySide / Fluent shell."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger("jarvis.pyside.dashboard")

try:
    from qfluentwidgets import (
        BodyLabel,
        CardWidget,
        FluentIcon as FIF,
        IconWidget,
        StrongBodyLabel,
        TitleLabel,
    )

    _FLUENT = True
except ImportError:
    _FLUENT = False

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from jarvis.gui.pyside.api_client import activate_scene, fetch_dashboard


def _card(parent: QWidget | None = None) -> QWidget:
    if _FLUENT:
        w = CardWidget(parent)
        w.setBorderRadius(14)
        return w
    f = QFrame(parent)
    f.setObjectName("ariaCard")
    return f


class DashboardLoader(QThread):
    finished = Signal(dict)

    def __init__(self, base_url: str, parent=None) -> None:
        super().__init__(parent)
        self.base_url = base_url

    def run(self) -> None:
        try:
            self.finished.emit(fetch_dashboard(self.base_url))
        except Exception as exc:
            logger.warning("dashboard load failed: %s", exc)
            self.finished.emit({})


class GreetingsHeader(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 12)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        self.sub_label = BodyLabel("Welcome back") if _FLUENT else QLabel("Welcome back")
        self.title_label = TitleLabel("ARIA") if _FLUENT else QLabel("ARIA")
        if not _FLUENT:
            self.title_label.setObjectName("ariaTitle")
            f = QFont()
            f.setPointSize(22)
            f.setBold(True)
            self.title_label.setFont(f)
        self.date_label = BodyLabel("") if _FLUENT else QLabel("")
        text_col.addWidget(self.sub_label)
        text_col.addWidget(self.title_label)
        text_col.addWidget(self.date_label)
        root.addLayout(text_col)
        root.addStretch()

        bubbles = QHBoxLayout()
        bubbles.setSpacing(12)
        self.time_bubble = self._bubble()
        self.time_label = QLabel("--:--")
        self.time_label.setAlignment(Qt.AlignCenter)
        tl = QVBoxLayout(self.time_bubble)
        tl.setAlignment(Qt.AlignCenter)
        tl.addWidget(self.time_label)
        bubbles.addWidget(self.time_bubble)

        self.weather_bubble = self._bubble()
        self.w_icon = QLabel("🌡️")
        self.w_icon.setAlignment(Qt.AlignCenter)
        self.temp_label = QLabel("--")
        self.temp_label.setAlignment(Qt.AlignCenter)
        self.cond_label = QLabel("Loading…")
        self.cond_label.setObjectName("ariaMuted")
        self.cond_label.setAlignment(Qt.AlignCenter)
        wl = QVBoxLayout(self.weather_bubble)
        wl.setAlignment(Qt.AlignCenter)
        wl.addWidget(self.w_icon)
        wl.addWidget(self.temp_label)
        wl.addWidget(self.cond_label)
        bubbles.addWidget(self.weather_bubble)
        root.addLayout(bubbles)

        self._tick()
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)

    def _bubble(self) -> QFrame:
        b = QFrame()
        b.setObjectName("ariaBubble")
        b.setFixedSize(150, 92)
        return b

    def _tick(self) -> None:
        now = datetime.now()
        hour = now.hour
        if hour < 12:
            greet = "Good morning"
        elif hour < 18:
            greet = "Good afternoon"
        else:
            greet = "Good evening"
        self.title_label.setText(greet)
        self.date_label.setText(now.strftime("%A, %B %d"))
        self.time_label.setText(now.strftime("%I:%M %p").lstrip("0"))

    def apply_weather(self, weather: dict[str, Any] | None) -> None:
        if not weather or weather.get("error"):
            self.cond_label.setText("Weather unavailable")
            return
        self.w_icon.setText(str(weather.get("icon") or "🌡️"))
        hi = weather.get("high")
        lo = weather.get("low")
        sym = weather.get("unit") or "°"
        if hi is not None:
            self.temp_label.setText(f"{round(float(hi))}{sym}")
        self.cond_label.setText(str(weather.get("condition") or weather.get("summary") or ""))


class StatCard(QFrame):
    navigate_requested = Signal(str)

    def __init__(
        self,
        title: str,
        route: str = "",
        icon=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.route = route
        self.setObjectName("ariaCard")
        self.setFixedHeight(100)
        self.setCursor(Qt.PointingHandCursor if route else Qt.ArrowCursor)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        left = QVBoxLayout()
        if _FLUENT and icon is not None:
            ib = QFrame()
            ib.setFixedSize(36, 36)
            ib_l = QVBoxLayout(ib)
            ib_l.setContentsMargins(0, 0, 0, 0)
            ib_l.setAlignment(Qt.AlignCenter)
            ib_l.addWidget(IconWidget(icon, ib))
            left.addWidget(ib)
        cap = BodyLabel(title) if _FLUENT else QLabel(title)
        if not _FLUENT:
            cap.setObjectName("ariaMuted")
        left.addWidget(cap)
        lay.addLayout(left)
        lay.addStretch()
        self.num_label = QLabel("0")
        nf = QFont()
        nf.setPointSize(20)
        nf.setBold(True)
        self.num_label.setFont(nf)
        self.num_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lay.addWidget(self.num_label)

    def set_count(self, n: int | str) -> None:
        self.num_label.setText(str(n))

    def mousePressEvent(self, event) -> None:  # noqa: N802
        super().mousePressEvent(event)
        if self.route:
            self.navigate_requested.emit(self.route)


class HomeScenesCard(QWidget):
    def __init__(self, base_url: str, parent=None) -> None:
        super().__init__(parent)
        self.base_url = base_url
        card = _card(self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.addWidget(StrongBodyLabel("Home scenes") if _FLUENT else QLabel("Home scenes"))
        lay.addWidget(BodyLabel("Instant environmental adjustments.") if _FLUENT else QLabel("Instant environmental adjustments."))
        row = QHBoxLayout()
        self.focus_btn = QPushButton("Focus mode")
        self.focus_btn.setObjectName("ariaScenePrimary")
        self.relax_btn = QPushButton("Relax")
        self.relax_btn.setObjectName("ariaSceneGhost")
        self.focus_btn.clicked.connect(lambda: self._scene("focus mode"))
        self.relax_btn.clicked.connect(lambda: self._scene("relax"))
        row.addWidget(self.focus_btn)
        row.addWidget(self.relax_btn)
        lay.addLayout(row)
        self.status = BodyLabel("") if _FLUENT else QLabel("")
        lay.addWidget(self.status)

    def _scene(self, preset_id: str) -> None:
        ok, msg = activate_scene(self.base_url, preset_id)
        self.status.setText(msg.replace("**", ""))
        self.focus_btn.setEnabled(True)
        self.relax_btn.setEnabled(True)
        if not ok:
            logger.info("scene %s: %s", preset_id, msg)


class IntelligenceFeed(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        card = _card(self)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(22, 18, 22, 18)
        head = QHBoxLayout()
        head.addWidget(TitleLabel("System intelligence") if _FLUENT else QLabel("System intelligence"))
        head.addStretch()
        live = QLabel("Live")
        live.setStyleSheet("color:#8b9bb4;font-size:10px;padding:4px 8px;background:#1a2236;border-radius:6px;")
        head.addWidget(live)
        lay.addLayout(head)
        self.focus_lbl = BodyLabel("") if _FLUENT else QLabel("")
        self.news_lbl = BodyLabel("") if _FLUENT else QLabel("")
        self.home_lbl = BodyLabel("") if _FLUENT else QLabel("")
        for title, widget in (
            ("Daily focus", self.focus_lbl),
            ("Intel alert", self.news_lbl),
            ("Smart home", self.home_lbl),
        ):
            lay.addWidget(StrongBodyLabel(title) if _FLUENT else QLabel(title))
            lay.addWidget(widget)
        self.priority = QFrame()
        self.priority.setObjectName("ariaPriority")
        self.priority.setFixedHeight(88)
        pl = QVBoxLayout(self.priority)
        pl.setContentsMargins(20, 12, 20, 12)
        self.priority_title = QLabel("Upcoming priority")
        self.priority_title.setStyleSheet("color:white;font-weight:bold;")
        self.priority_body = QLabel("—")
        self.priority_body.setStyleSheet("color:rgba(255,255,255,0.9);")
        pl.addWidget(self.priority_title)
        pl.addWidget(self.priority_body)
        lay.addWidget(self.priority)

    def update_intel(self, intel: dict[str, Any]) -> None:
        self.focus_lbl.setText(str(intel.get("daily_focus") or ""))
        self.news_lbl.setText(str(intel.get("intel_alert") or ""))
        self.home_lbl.setText(str(intel.get("smart_home") or ""))
        self.priority_body.setText(str(intel.get("priority") or "Nothing urgent"))


class BriefingStrip(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 8, 0, 0)
        self.breaking = QLabel("BREAKING — loading headlines…")
        self.breaking.setWordWrap(True)
        bl = QLabel("BREAKING")
        bl.setObjectName("ariaBreaking")
        row = QHBoxLayout()
        row.addWidget(bl)
        self.headline = QLabel("…")
        self.headline.setWordWrap(True)
        row.addWidget(self.headline, 1)
        lay.addLayout(row)

    def set_headline(self, title: str) -> None:
        self.headline.setText(title or "No headlines")


class DashboardView(QWidget):
    """Native Fluent dashboard — Ada local parity."""

    navigate_to = Signal(str)

    def __init__(self, base_url: str, parent=None) -> None:
        super().__init__(parent)
        self.base_url = base_url
        self.setObjectName("ariaDashboardView")
        self._loader: DashboardLoader | None = None

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        body = QWidget()
        scroll.setWidget(body)
        main = QVBoxLayout(body)
        main.setContentsMargins(32, 28, 32, 28)
        main.setSpacing(20)

        self.header = GreetingsHeader()
        main.addWidget(self.header)

        content = QHBoxLayout()
        content.setSpacing(18)
        left = QVBoxLayout()
        left.setSpacing(14)
        icon_cal = FIF.CALENDAR if _FLUENT else None
        icon_iot = FIF.IOT if _FLUENT else None
        icon_news = FIF.TILES if _FLUENT else None
        self.planner_stat = StatCard("Planner tasks", "planner", icon_cal)
        self.devices_stat = StatCard("Kasa devices", "chat", icon_iot)
        self.news_stat = StatCard("Headlines", "chat", icon_news)
        for card in (self.planner_stat, self.devices_stat, self.news_stat):
            card.navigate_requested.connect(self.navigate_to.emit)
            left.addWidget(card)
        self.scenes = HomeScenesCard(base_url)
        left.addWidget(self.scenes)
        left.addStretch()
        content.addLayout(left, 0)
        self.feed = IntelligenceFeed()
        content.addWidget(self.feed, 1)
        main.addLayout(content)

        self.briefing = BriefingStrip()
        main.addWidget(self.briefing)

        refresh = QPushButton("Refresh dashboard")
        refresh.clicked.connect(self.reload)
        main.addWidget(refresh, alignment=Qt.AlignLeft)

        QTimer.singleShot(200, self.reload)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self.reload)
        self._refresh_timer.start(120_000)

    def reload(self) -> None:
        if self._loader and self._loader.isRunning():
            return
        self._loader = DashboardLoader(self.base_url, self)
        self._loader.finished.connect(self._on_data)
        self._loader.finished.connect(self._loader.deleteLater)
        self._loader.start()

    def _on_data(self, data: dict[str, Any]) -> None:
        info = data.get("info") or {}
        news = data.get("news") or {}
        planner = info.get("planner") or {}
        tasks = planner.get("tasks") or []
        active = [t for t in tasks if not t.get("completed")]
        kasa = info.get("kasa") or {}
        headlines = news.get("headlines") or []
        intel = info.get("intelligence") or {}

        self.planner_stat.set_count(len(active))
        self.devices_stat.set_count(kasa.get("count", 0))
        self.news_stat.set_count(len(headlines))
        self.header.apply_weather(info.get("weather"))
        self.feed.update_intel(intel)
        top = news.get("breaking") or (headlines[0] if headlines else {})
        title = top.get("title") if isinstance(top, dict) else str(top or "")
        self.briefing.set_headline(title)
