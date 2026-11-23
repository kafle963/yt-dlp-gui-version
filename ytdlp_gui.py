"""
yt-dlp GUI Pro — Modern desktop interface for clipping and downloading online media.
Designed for high performance, frame-accurate cuts, and clean visual ergonomics:
- Left Column: Step 1 (Link + live metadata card), Step 2 (Clips + quick duration pills), Step 3 (Quality & Size presets), Step 4 (Save To)
- Right Column: Interactive Queue (with per-row deletion) + Rich HTML Log Viewer (color-coded by severity)
- Header: Minimal brand + live status indicators (yt-dlp, Deno, FFmpeg) + Tools menu
- Bottom Bar: Dynamic progress bar + Cancel / Download controls + Status bar
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRectF, QSettings, QSize, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QMouseEvent,
    QPaintEvent,
    QPainter,
    QPalette,
    QPen,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

PYTHON_EXE = sys.executable


def resolve_ytdlp_cmd() -> list[str]:
    """Finds a verified, working yt-dlp command. Prefers Python's yt_dlp module, then PATH."""
    candidates = [
        [PYTHON_EXE, "-m", "yt_dlp"],
    ]
    which_path = shutil.which("yt-dlp")
    if which_path:
        candidates.append([which_path])

    for cmd in candidates:
        try:
            res = subprocess.run(
                cmd + ["--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            if res.returncode == 0:
                return cmd
        except Exception:
            continue

    return [PYTHON_EXE, "-m", "yt_dlp"]


STYLESHEET = """
QMainWindow, QDialog, QWidget {
    background-color: #0f111a;
    color: #e2e8f0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

/* Card Containers */
QFrame#card {
    background-color: #161926;
    border: 1px solid #23283a;
    border-radius: 8px;
}

QFrame#metaCard {
    background-color: #1a2035;
    border: 1px solid #2d3b5e;
    border-radius: 6px;
    padding: 6px 10px;
}

/* Typography */
QLabel#cardTitle {
    color: #94a3b8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
}

QLabel#stepNumber {
    color: #3b82f6;
    font-size: 13px;
    font-weight: 800;
}

QLabel#subText {
    color: #64748b;
    font-size: 11px;
}

QLabel#brandTitle {
    color: #ffffff;
    font-size: 16px;
    font-weight: 700;
    letter-spacing: -0.3px;
}

/* Status dots */
QLabel#statusDotActive {
    color: #22c55e;
    font-size: 11px;
    font-weight: 600;
}
QLabel#statusDotInactive {
    color: #ef4444;
    font-size: 11px;
    font-weight: 600;
}

/* Form Inputs */
QLineEdit {
    background-color: #1e2336;
    color: #f8fafc;
    border: 1px solid #2d354f;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 13px;
    min-height: 32px;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}
QLineEdit:focus {
    border: 1px solid #3b82f6;
    background-color: #242a42;
}
QLineEdit:disabled {
    background-color: #141724;
    color: #475569;
    border-color: #1e2233;
}

QComboBox {
    background-color: #1e2336;
    color: #f8fafc;
    border: 1px solid #2d354f;
    border-radius: 6px;
    padding: 4px 10px;
    min-height: 32px;
    font-size: 13px;
}
QComboBox:hover { border-color: #3e4a6d; }
QComboBox:focus { border-color: #3b82f6; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: #1a1e30;
    border: 1px solid #3b82f6;
    selection-background-color: #3b82f6;
    color: #f8fafc;
    padding: 4px;
    outline: none;
}

/* Buttons */
QPushButton {
    background-color: #1e2336;
    color: #cbd5e1;
    border: 1px solid #2d354f;
    border-radius: 6px;
    padding: 5px 14px;
    font-weight: 500;
    font-size: 12px;
    min-height: 32px;
}
QPushButton:hover {
    background-color: #283049;
    color: #ffffff;
    border-color: #43527a;
}
QPushButton:pressed {
    background-color: #181d2e;
    border-color: #3b82f6;
}
QPushButton:disabled {
    background-color: #141724;
    color: #475569;
    border-color: #1e2233;
}

/* Ghost / Header Text Buttons */
QPushButton#ghostBtn {
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    min-height: 22px;
}
QPushButton#ghostBtn:hover {
    background-color: #1e2336;
    color: #f1f5f9;
    border-color: #2d354f;
}

/* Quick Duration Pills */
QPushButton#pillBtn {
    background-color: #182033;
    color: #93c5fd;
    border: 1px solid #2d3d63;
    border-radius: 11px;
    padding: 2px 7px;
    font-size: 11px;
    font-weight: 600;
    min-height: 22px;
}
QPushButton#pillBtn:hover {
    background-color: #233152;
    border-color: #3b82f6;
    color: #ffffff;
}

/* Row Delete Button */
QPushButton#delBtn {
    background-color: transparent;
    color: #ef4444;
    border: none;
    font-size: 13px;
    font-weight: 700;
    border-radius: 4px;
    padding: 0;
    min-height: 20px;
}
QPushButton#delBtn:hover {
    background-color: #3b1818;
    color: #fca5a5;
}

/* Secondary Button */
QPushButton#secondaryBtn {
    background-color: #1a1e2e;
    color: #94a3b8;
    border: 1px solid #283049;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 11px;
    font-weight: 500;
    min-height: 28px;
}
QPushButton#secondaryBtn:hover {
    background-color: #232a3f;
    color: #e2e8f0;
    border-color: #3e4d73;
}

/* Action Primary Download Button */
QPushButton#downloadBtn {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 24px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.3px;
    min-height: 36px;
}
QPushButton#downloadBtn:hover { background-color: #1d4ed8; }
QPushButton#downloadBtn:pressed { background-color: #1e40af; }
QPushButton#downloadBtn:disabled {
    background-color: #1e293b;
    color: #475569;
}

/* Cancel / Stop Button */
QPushButton#cancelBtn {
    background-color: #1e2336;
    color: #f87171;
    border: 1px solid #4a1f1f;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 12px;
    font-weight: 600;
    min-height: 36px;
}
QPushButton#cancelBtn:hover {
    background-color: #7f1d1d;
    color: #ffffff;
    border-color: #991b1b;
}
QPushButton#cancelBtn:disabled {
    background-color: #141724;
    color: #452b2b;
    border-color: #1f1b1b;
}

/* Table */
QTableWidget {
    background-color: #131622;
    border: 1px solid #23283a;
    border-radius: 6px;
    gridline-color: transparent;
    outline: none;
}
QTableWidget::item {
    padding: 4px 6px;
    border-bottom: 1px solid #1c2030;
}
QTableWidget::item:selected {
    background-color: #1e2842;
    color: #ffffff;
}

/* Log Text */
QPlainTextEdit {
    background-color: #0c0e17;
    color: #94a3b8;
    border: 1px solid #1e2336;
    border-radius: 6px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 11px;
    padding: 8px;
}

/* Progress Bar */
QProgressBar {
    background-color: #181d2c;
    border: 1px solid #23293d;
    border-radius: 4px;
    height: 10px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #38bdf8);
    border-radius: 3px;
}

/* Status Bar */
QStatusBar {
    background-color: #0c0e17;
    color: #64748b;
    border-top: 1px solid #1a1e2d;
    font-size: 11px;
    padding: 4px 10px;
}
"""


class RangeSlider(QWidget):
    """
    Sleek dual-handle range slider for video clipping.
    - Left handle adjusts Start time.
    - Right handle adjusts End time.
    - Middle active bar can be dragged to slide the selected window.
    - Clicking the track jumps the nearest handle.
    - Emits rangeChanged(float, float) in seconds.
    """

    rangeChanged = Signal(float, float)
    lowChanged = Signal(float)
    highChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._min_val = 0.0
        self._max_val = 600.0  # 10 min default until video duration loads
        self._low_val = 0.0
        self._high_val = 60.0  # default 1 min selection
        self._min_gap = 1.0    # 1 second minimum clip length

        self._handle_r = 8.5
        self._hover_target = None   # 'low', 'high', 'bar', None
        self._active_target = None  # 'low', 'high', 'bar', None
        self._drag_start_x = 0.0
        self._drag_start_low = 0.0
        self._drag_start_high = 0.0

    def setRange(self, min_val: float, max_val: float):
        self._min_val = max(0.0, float(min_val))
        self._max_val = max(self._min_val + self._min_gap, float(max_val))
        self._low_val = max(self._min_val, min(self._low_val, self._max_val - self._min_gap))
        self._high_val = max(self._low_val + self._min_gap, min(self._high_val, self._max_val))
        self.update()

    def setValues(self, low: float, high: float):
        low = max(self._min_val, min(float(low), self._max_val - self._min_gap))
        high = max(low + self._min_gap, min(float(high), self._max_val))
        if abs(low - self._low_val) > 0.01 or abs(high - self._high_val) > 0.01:
            self._low_val = low
            self._high_val = high
            self.update()

    def setLow(self, low: float):
        self.setValues(low, self._high_val)

    def setHigh(self, high: float):
        self.setValues(self._low_val, high)

    def low(self) -> float:
        return self._low_val

    def high(self) -> float:
        return self._high_val

    def _val_to_x(self, val: float) -> float:
        pad = self._handle_r + 6.0
        track_w = max(1.0, float(self.width()) - 2.0 * pad)
        span = max(0.001, self._max_val - self._min_val)
        ratio = max(0.0, min(1.0, (val - self._min_val) / span))
        return pad + ratio * track_w

    def _x_to_val(self, x: float) -> float:
        pad = self._handle_r + 6.0
        track_w = max(1.0, float(self.width()) - 2.0 * pad)
        ratio = max(0.0, min(1.0, (x - pad) / track_w))
        return self._min_val + ratio * (self._max_val - self._min_val)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        pos = event.position()
        x = pos.x()
        y = pos.y()
        cy = self.height() / 2.0

        x_low = self._val_to_x(self._low_val)
        x_high = self._val_to_x(self._high_val)

        dist_low = abs(x - x_low)
        dist_high = abs(x - x_high)
        hit_tol = self._handle_r + 6.0

        if dist_low <= hit_tol and dist_low <= dist_high:
            self._active_target = "low"
        elif dist_high <= hit_tol:
            self._active_target = "high"
        elif x_low < x < x_high and abs(y - cy) <= 12.0:
            self._active_target = "bar"
            self._drag_start_x = x
            self._drag_start_low = self._low_val
            self._drag_start_high = self._high_val
        else:
            # Clicked outside handles: jump the closer handle
            if x < x_low:
                self._active_target = "low"
                new_low = max(self._min_val, min(self._x_to_val(x), self._high_val - self._min_gap))
                self._low_val = new_low
                self.rangeChanged.emit(self._low_val, self._high_val)
                self.lowChanged.emit(self._low_val)
            elif x > x_high:
                self._active_target = "high"
                new_high = min(self._max_val, max(self._x_to_val(x), self._low_val + self._min_gap))
                self._high_val = new_high
                self.rangeChanged.emit(self._low_val, self._high_val)
                self.highChanged.emit(self._high_val)
            else:
                if dist_low <= dist_high:
                    self._active_target = "low"
                else:
                    self._active_target = "high"

        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()
        x = pos.x()
        y = pos.y()
        cy = self.height() / 2.0

        if self._active_target is None:
            # Update hover state
            x_low = self._val_to_x(self._low_val)
            x_high = self._val_to_x(self._high_val)
            dist_low = abs(x - x_low)
            dist_high = abs(x - x_high)
            hit_tol = self._handle_r + 6.0

            old_hover = self._hover_target
            if dist_low <= hit_tol and dist_low <= dist_high:
                self._hover_target = "low"
            elif dist_high <= hit_tol:
                self._hover_target = "high"
            elif x_low < x < x_high and abs(y - cy) <= 12.0:
                self._hover_target = "bar"
            else:
                self._hover_target = None

            if self._hover_target != old_hover:
                self.update()
            return

        # Dragging active handle or bar
        if self._active_target == "low":
            new_val = self._x_to_val(x)
            new_low = max(self._min_val, min(new_val, self._high_val - self._min_gap))
            if abs(new_low - self._low_val) > 0.01:
                self._low_val = new_low
                self.rangeChanged.emit(self._low_val, self._high_val)
                self.lowChanged.emit(self._low_val)
                self.update()

        elif self._active_target == "high":
            new_val = self._x_to_val(x)
            new_high = min(self._max_val, max(new_val, self._low_val + self._min_gap))
            if abs(new_high - self._high_val) > 0.01:
                self._high_val = new_high
                self.rangeChanged.emit(self._low_val, self._high_val)
                self.highChanged.emit(self._high_val)
                self.update()

        elif self._active_target == "bar":
            delta_val = self._x_to_val(x) - self._x_to_val(self._drag_start_x)
            dur = self._drag_start_high - self._drag_start_low
            new_low = self._drag_start_low + delta_val
            new_high = self._drag_start_high + delta_val

            if new_low < self._min_val:
                new_low = self._min_val
                new_high = new_low + dur
            elif new_high > self._max_val:
                new_high = self._max_val
                new_low = new_high - dur

            if abs(new_low - self._low_val) > 0.01 or abs(new_high - self._high_val) > 0.01:
                self._low_val = new_low
                self._high_val = new_high
                self.rangeChanged.emit(self._low_val, self._high_val)
                self.lowChanged.emit(self._low_val)
                self.highChanged.emit(self._high_val)
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._active_target = None
        self.update()

    def leaveEvent(self, event):
        self._hover_target = None
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pad = self._handle_r + 6.0
        w = float(self.width())
        h = float(self.height())
        cy = h / 2.0
        track_h = 6.0
        track_y = cy - track_h / 2.0
        track_w = max(1.0, w - 2.0 * pad)

        # 1. Groove track
        painter.setPen(QPen(QColor("#283049"), 1.0))
        painter.setBrush(QBrush(QColor("#161a29")))
        painter.drawRoundedRect(QRectF(pad, track_y, track_w, track_h), 3.0, 3.0)

        # 2. Selected Active Range Span
        x_low = self._val_to_x(self._low_val)
        x_high = self._val_to_x(self._high_val)
        span_w = max(0.0, x_high - x_low)

        grad = QLinearGradient(x_low, 0, x_high, 0)
        grad.setColorAt(0.0, QColor("#38bdf8"))  # Sky blue
        grad.setColorAt(1.0, QColor("#818cf8"))  # Indigo

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(QRectF(x_low, track_y, span_w, track_h), 3.0, 3.0)

        # 3. Handles (Left: Start, Right: End)
        for target, x_pos, fill_color in [
            ("low", x_low, QColor("#38bdf8")),
            ("high", x_high, QColor("#818cf8")),
        ]:
            is_hover = (self._hover_target == target)
            is_active = (self._active_target == target)
            r = self._handle_r

            # Outer glow halo when hover or active
            if is_active or is_hover:
                halo_color = QColor(fill_color)
                halo_color.setAlpha(65 if is_active else 35)
                painter.setBrush(QBrush(halo_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(x_pos, cy), r + 4.5, r + 4.5)

            # Handle knob body
            painter.setBrush(QBrush(fill_color))
            border_pen = QPen(QColor("#ffffff" if (is_hover or is_active) else "#cbd5e1"), 2.0)
            painter.setPen(border_pen)
            painter.drawEllipse(QPointF(x_pos, cy), r, r)

            # Center white dot
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(QPointF(x_pos, cy), 2.2, 2.2)

        painter.end()


class HealthCheckDialog(QDialog):
    """System health check for yt-dlp, FFmpeg, Deno, and EJS."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Diagnostics & Dependencies")
        self.resize(520, 320)
        self.setStyleSheet(STYLESHEET)
        self._init_ui()
        self._run_checks()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        lbl = QLabel("System Component Status", self)
        lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        layout.addWidget(lbl)

        self.table = QTableWidget(5, 3, self)
        self.table.setHorizontalHeaderLabels(["Component", "Status", "Version / Path"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        btn_box = QHBoxLayout()
        btn_refresh = QPushButton("Re-check", self)
        btn_refresh.clicked.connect(self._run_checks)
        btn_box.addWidget(btn_refresh)
        btn_box.addStretch()

        btn_close = QPushButton("Close", self)
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    def _run_checks(self):
        tools = [
            ("yt-dlp", resolve_ytdlp_cmd() + ["--version"]),
            ("FFmpeg", ["ffmpeg", "-version"]),
            ("Deno", ["deno", "--version"]),
            ("yt-dlp-ejs", [PYTHON_EXE, "-c", "import importlib.metadata; print(importlib.metadata.version('yt-dlp-ejs'))"]),
        ]
        self.table.setRowCount(len(tools) + 1)
        for row, (name, cmd) in enumerate(tools):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            try:
                out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True,
                                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                first_line = out.strip().split("\n")[0]
                self.table.setItem(row, 1, QTableWidgetItem("● Ready"))
                self.table.item(row, 1).setForeground(QColor("#22c55e"))
                self.table.setItem(row, 2, QTableWidgetItem(first_line[:65]))
            except Exception as e:
                self.table.setItem(row, 1, QTableWidgetItem("● Missing"))
                self.table.item(row, 1).setForeground(QColor("#ef4444"))
                self.table.setItem(row, 2, QTableWidgetItem(str(e)[:65]))

        # Config check
        cfg_row = len(tools)
        cfg_path = Path(os.path.expandvars(r"%APPDATA%\yt-dlp\config.txt")) if sys.platform == "win32" else (Path.home() / ".config" / "yt-dlp" / "config")
        self.table.setItem(cfg_row, 0, QTableWidgetItem("Config"))
        if cfg_path.exists():
            self.table.setItem(cfg_row, 1, QTableWidgetItem("● Active"))
            self.table.item(cfg_row, 1).setForeground(QColor("#22c55e"))
            self.table.setItem(cfg_row, 2, QTableWidgetItem(str(cfg_path)))
        else:
            self.table.setItem(cfg_row, 1, QTableWidgetItem("● None"))
            self.table.item(cfg_row, 1).setForeground(QColor("#eab308"))
            self.table.setItem(cfg_row, 2, QTableWidgetItem("No config found"))


class MetadataWorker(QThread):
    """Fetches video title, duration, and channel metadata asynchronously without UI freeze."""
    metadata_ready = Signal(dict)
    metadata_error = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self._url = url

    def run(self):
        try:
            cmd = resolve_ytdlp_cmd() + [
                "--print", "%(title)s\t%(duration)s\t%(duration_string)s\t%(uploader,channel)s",
                "--no-playlist", "--no-warnings",
                self._url,
            ]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            out = proc.stdout.strip()
            if out:
                parts = out.split("\t")
                title = parts[0]
                dur_raw = parts[1] if len(parts) > 1 else "0"
                dur_str = parts[2] if len(parts) > 2 else ""
                channel = parts[3] if len(parts) > 3 else ""

                try:
                    dur_sec = float(dur_raw)
                except ValueError:
                    dur_sec = 0.0

                data = {
                    "title": title,
                    "duration_sec": dur_sec,
                    "duration_str": dur_str,
                    "channel": channel,
                }
                self.metadata_ready.emit(data)
            else:
                self.metadata_error.emit(proc.stderr[:120])
        except Exception as e:
            self.metadata_error.emit(str(e))


class CommandWorker(QThread):
    """Runs a background task (e.g. yt-dlp -F or pip install) and streams output."""
    output_line = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, cmd: list[str]):
        super().__init__()
        self._cmd = cmd
        self._proc = None

    def run(self):
        try:
            self._proc = subprocess.Popen(
                self._cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            for line in self._proc.stdout:
                line = line.rstrip()
                if line:
                    self.output_line.emit(line)
            self._proc.wait()
            self.finished.emit(self._proc.returncode == 0, "")
        except Exception as e:
            self.finished.emit(False, str(e))


class DownloadWorker(QThread):
    """Executes yt-dlp and parses download progress."""
    output_line = Signal(str)
    progress_update = Signal(int, str)  # percent, rate/status string
    finished = Signal(bool, str)

    def __init__(self, cmd: list[str]):
        super().__init__()
        self._cmd = cmd
        self._proc = None
        self._cancelled = False

    def run(self):
        try:
            self._proc = subprocess.Popen(
                self._cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            for line in self._proc.stdout:
                line = line.rstrip()
                if line:
                    if "-t value must be non-negative" in line:
                        self.output_line.emit("⚠️ ERROR: Start time is beyond the end of the video! (Note: 10:00 = 10 minutes; 10:00:00 = 10 hours).")
                    elif "Output file is empty, nothing was encoded" in line or "moov atom not found" in line:
                        self.output_line.emit("⚠️ LIVESTREAM NOTICE: This livestream has not been fully processed into a standard VOD by YouTube yet. Its live stream timestamps do not start at 0:00:00. Time-range clipping will work normally once YouTube completes backend processing of the archive.")
                    # Filter benign developer notice
                    if "Late SEI is not implemented" in line or "upload a sample of this file" in line:
                        continue
                    self.output_line.emit(line)

                    # Parse progress & speed
                    m = re.search(r"\[download\]\s+([\d.]+)%\s+of\s+~?[\d.]+\w+\s+at\s+([\d.]+\w+/s)", line)
                    if m:
                        try:
                            pct = min(100, int(float(m.group(1))))
                            speed = m.group(2)
                            self.progress_update.emit(pct, speed)
                        except ValueError:
                            pass
                    else:
                        m2 = re.search(r"\[download\]\s+([\d.]+)%", line)
                        if m2:
                            try:
                                pct = min(100, int(float(m2.group(1))))
                                self.progress_update.emit(pct, "")
                            except ValueError:
                                pass

            self._proc.wait()
            if self._cancelled:
                self.finished.emit(False, "Cancelled")
            elif self._proc.returncode == 0:
                self.finished.emit(True, "Complete")
            else:
                self.finished.emit(False, f"Error (code {self._proc.returncode})")
        except Exception as e:
            self.finished.emit(False, str(e))

    def cancel(self):
        self._cancelled = True
        if self._proc and self._proc.poll() is None:
            pid = self._proc.pid
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                self._proc.terminate()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("yt-dlp GUI Pro")
        self.setMinimumSize(940, 580)
        self.resize(1020, 740)
        self.setStyleSheet(STYLESHEET)

        self._worker: DownloadWorker | None = None
        self._cmd_worker: CommandWorker | None = None
        self._meta_worker: MetadataWorker | None = None
        self._settings = QSettings("YtDlpGui", "Settings")

        # In-memory clip queue: list of dicts: {"clip_num": 1, "start": "10:00", "end": "11:00", "range_str": "...", "status": "Waiting"}
        self._clips: list[dict] = []
        self._video_duration_sec: float = 0.0

        # Debounced URL timer to fetch metadata smoothly
        self._url_timer = QTimer(self)
        self._url_timer.setSingleShot(True)
        self._url_timer.timeout.connect(self._fetch_metadata)

        self._init_ui()
        self._restore_settings()
        self._check_components_status()

    def _init_ui(self):
        root = QWidget(self)
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(14, 10, 14, 6)
        layout.setSpacing(10)

        # ── 1. COMPACT HEADER BAR ─────────────────────────────────
        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 2, 0)

        lbl_brand = QLabel("▶ yt-dlp GUI Pro", root)
        lbl_brand.setObjectName("brandTitle")
        header.addWidget(lbl_brand)
        header.addStretch()

        # Status dots
        self.lbl_dot_ytdlp = QLabel("● yt-dlp", root)
        self.lbl_dot_ytdlp.setObjectName("statusDotActive")
        header.addWidget(self.lbl_dot_ytdlp)
        header.addSpacing(10)

        self.lbl_dot_deno = QLabel("● Deno", root)
        self.lbl_dot_deno.setObjectName("statusDotActive")
        header.addWidget(self.lbl_dot_deno)
        header.addSpacing(10)

        self.lbl_dot_ffmpeg = QLabel("● FFmpeg", root)
        self.lbl_dot_ffmpeg.setObjectName("statusDotActive")
        header.addWidget(self.lbl_dot_ffmpeg)
        header.addSpacing(14)

        # Tools Menu Button
        self.btn_tools = QPushButton("⚙ Tools ▾", root)
        self.btn_tools.setObjectName("ghostBtn")
        self.btn_tools.clicked.connect(self._show_tools_menu)
        header.addWidget(self.btn_tools)

        layout.addLayout(header)

        # ── 2. TWO-COLUMN SPLITTER ────────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal, root)
        splitter.setHandleWidth(8)

        # ── LEFT COLUMN: FORM CONTROLS ────────────────────────────
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 4, 0)
        left_layout.setSpacing(10)

        # CARD 1: LINK
        card_link = QFrame(left_col)
        card_link.setObjectName("card")
        c1_layout = QVBoxLayout(card_link)
        c1_layout.setContentsMargins(12, 10, 12, 12)
        c1_layout.setSpacing(8)

        c1_hdr = QHBoxLayout()
        lbl_s1 = QLabel("1", card_link)
        lbl_s1.setObjectName("stepNumber")
        c1_hdr.addWidget(lbl_s1)
        lbl_t1 = QLabel("Link", card_link)
        lbl_t1.setObjectName("cardTitle")
        c1_hdr.addWidget(lbl_t1)
        c1_hdr.addStretch()
        c1_layout.addLayout(c1_hdr)

        row_url = QHBoxLayout()
        row_url.setSpacing(6)
        self.txt_url = QLineEdit(card_link)
        self.txt_url.setPlaceholderText("Paste a YouTube link")
        self.txt_url.setClearButtonEnabled(True)
        self.txt_url.setMinimumHeight(34)
        self.txt_url.textChanged.connect(self._on_url_changed)
        row_url.addWidget(self.txt_url, 1)

        self.btn_paste = QPushButton("Paste", card_link)
        self.btn_paste.setFixedWidth(65)
        self.btn_paste.setMinimumHeight(34)
        self.btn_paste.clicked.connect(self._paste_url)
        row_url.addWidget(self.btn_paste)
        c1_layout.addLayout(row_url)

        # Live Metadata Preview Box (appears automatically once link is resolved)
        self.frame_meta = QFrame(card_link)
        self.frame_meta.setObjectName("metaCard")
        meta_layout = QVBoxLayout(self.frame_meta)
        meta_layout.setContentsMargins(6, 6, 6, 6)
        meta_layout.setSpacing(3)

        self.lbl_video_title = QLabel("", self.frame_meta)
        self.lbl_video_title.setStyleSheet("color: #f1f5f9; font-weight: 600; font-size: 12px;")
        self.lbl_video_title.setWordWrap(True)
        meta_layout.addWidget(self.lbl_video_title)

        self.lbl_video_sub = QLabel("", self.frame_meta)
        self.lbl_video_sub.setStyleSheet("color: #38bdf8; font-size: 11px;")
        meta_layout.addWidget(self.lbl_video_sub)
        self.frame_meta.setVisible(False)
        c1_layout.addWidget(self.frame_meta)

        self.lbl_meta = QLabel("Paste link to automatically resolve info · leave blank for full video", card_link)
        self.lbl_meta.setObjectName("subText")
        self.lbl_meta.setWordWrap(True)
        c1_layout.addWidget(self.lbl_meta)

        left_layout.addWidget(card_link)

        # CARD 2: CLIPS & TRIMMING
        card_clips = QFrame(left_col)
        card_clips.setObjectName("card")
        card_clips.setMinimumHeight(215)
        c2_layout = QVBoxLayout(card_clips)
        c2_layout.setContentsMargins(12, 10, 12, 12)
        c2_layout.setSpacing(8)

        c2_hdr = QHBoxLayout()
        lbl_s2 = QLabel("2", card_clips)
        lbl_s2.setObjectName("stepNumber")
        c2_hdr.addWidget(lbl_s2)
        lbl_t2 = QLabel("Clips & Trimming", card_clips)
        lbl_t2.setObjectName("cardTitle")
        c2_hdr.addWidget(lbl_t2)
        c2_hdr.addStretch()

        self.lbl_clip_count = QLabel("0 added (full video)", card_clips)
        self.lbl_clip_count.setObjectName("subText")
        c2_hdr.addWidget(self.lbl_clip_count)
        c2_layout.addLayout(c2_hdr)

        # Timeline duration header row above slider
        row_slider_hdr = QHBoxLayout()
        self.lbl_slider_min = QLabel("0:00", card_clips)
        self.lbl_slider_min.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600;")
        row_slider_hdr.addWidget(self.lbl_slider_min)

        row_slider_hdr.addStretch()

        self.lbl_slider_info = QLabel("▶ 0:00 – 1:00 (1m 00s)", card_clips)
        self.lbl_slider_info.setStyleSheet("color: #38bdf8; font-size: 11px; font-weight: 700; background-color: #1a2234; padding: 2px 8px; border-radius: 4px; border: 1px solid #233152;")
        row_slider_hdr.addWidget(self.lbl_slider_info)

        row_slider_hdr.addStretch()

        self.lbl_slider_max = QLabel("10:00", card_clips)
        self.lbl_slider_max.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600;")
        row_slider_hdr.addWidget(self.lbl_slider_max)
        c2_layout.addLayout(row_slider_hdr)

        # Dual Handle Range Slider (left handle = Start, right handle = End)
        self.slider_range = RangeSlider(card_clips)
        self.slider_range.rangeChanged.connect(self._on_slider_range_changed)
        c2_layout.addWidget(self.slider_range)

        # Inputs row with Start, End, Add, and Reset
        row_clip_in = QHBoxLayout()
        row_clip_in.setSpacing(6)
        lbl_st = QLabel("Start", card_clips)
        lbl_st.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
        row_clip_in.addWidget(lbl_st)

        self.txt_start = QLineEdit(card_clips)
        self.txt_start.setPlaceholderText("0:00")
        self.txt_start.setFixedWidth(70)
        self.txt_start.setFixedHeight(28)
        self.txt_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_start.textEdited.connect(self._on_time_text_edited)
        row_clip_in.addWidget(self.txt_start)

        lbl_en = QLabel("End", card_clips)
        lbl_en.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 600;")
        row_clip_in.addWidget(lbl_en)

        self.txt_end = QLineEdit(card_clips)
        self.txt_end.setPlaceholderText("1:00")
        self.txt_end.setFixedWidth(70)
        self.txt_end.setFixedHeight(28)
        self.txt_end.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_end.textEdited.connect(self._on_time_text_edited)
        row_clip_in.addWidget(self.txt_end)

        self.btn_add_clip = QPushButton("+ Add", card_clips)
        self.btn_add_clip.setFixedWidth(58)
        self.btn_add_clip.setFixedHeight(28)
        self.btn_add_clip.clicked.connect(self._add_clip_to_queue)
        row_clip_in.addWidget(self.btn_add_clip)

        self.btn_reset_clip = QPushButton("Reset", card_clips)
        self.btn_reset_clip.setObjectName("secondaryBtn")
        self.btn_reset_clip.setFixedWidth(52)
        self.btn_reset_clip.setFixedHeight(28)
        self.btn_reset_clip.setToolTip("Clear clip selection to download full video")
        self.btn_reset_clip.clicked.connect(self._reset_clip_inputs)
        row_clip_in.addWidget(self.btn_reset_clip)

        row_clip_in.addStretch()
        c2_layout.addLayout(row_clip_in)

        # Quick Duration Pills (+30s, +1m, +2m, +5m)
        row_pills = QHBoxLayout()
        row_pills.setSpacing(6)
        lbl_quick = QLabel("Quick end:", card_clips)
        lbl_quick.setStyleSheet("color: #64748b; font-size: 11px;")
        row_pills.addWidget(lbl_quick)

        for text, sec in [("+30s", 30), ("+1m", 60), ("+2m", 120), ("+5m", 300)]:
            btn = QPushButton(text, card_clips)
            btn.setObjectName("pillBtn")
            btn.setFixedWidth(48)
            btn.setFixedHeight(22)
            btn.clicked.connect(lambda _, s=sec: self._apply_quick_duration(s))
            row_pills.addWidget(btn)
        row_pills.addStretch()
        c2_layout.addLayout(row_pills)

        lbl_hint = QLabel("💡 Slide left knob for Start, right knob for End, or drag bar between", card_clips)
        lbl_hint.setObjectName("subText")
        c2_layout.addWidget(lbl_hint)

        left_layout.addWidget(card_clips)

        # CARD 3: QUALITY & SIZE
        card_qual = QFrame(left_col)
        card_qual.setObjectName("card")
        c3_layout = QVBoxLayout(card_qual)
        c3_layout.setContentsMargins(12, 10, 12, 12)
        c3_layout.setSpacing(8)

        c3_hdr = QHBoxLayout()
        lbl_s3 = QLabel("3", card_qual)
        lbl_s3.setObjectName("stepNumber")
        c3_hdr.addWidget(lbl_s3)
        lbl_t3 = QLabel("Quality & Size", card_qual)
        lbl_t3.setObjectName("cardTitle")
        c3_hdr.addWidget(lbl_t3)
        c3_hdr.addStretch()
        c3_layout.addLayout(c3_hdr)

        # Row 1: Resolution & Strategy
        row_qual1 = QHBoxLayout()
        row_qual1.setSpacing(6)

        self.combo_res = QComboBox(card_qual)
        self.combo_res.addItems(["1080p (FHD)", "720p (HD)", "480p (SD)", "Max (4K+)"])
        self.combo_res.setFixedWidth(105)
        self.combo_res.setMinimumHeight(32)
        row_qual1.addWidget(self.combo_res)

        self.combo_preset = QComboBox(card_qual)
        self.combo_preset.addItems([
            "Smart Compact (Fastest ~8MB/m)",
            "Direct H.264 (avc1 ~35MB/m)",
            "Fast (Stream copy)",
            "Audio only (MP3)",
        ])
        self.combo_preset.setMinimumHeight(32)
        self.combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        row_qual1.addWidget(self.combo_preset, 1)
        c3_layout.addLayout(row_qual1)

        # Row 2: Re-encode Quality (CRF) & dynamic hint
        row_qual2 = QHBoxLayout()
        row_qual2.setSpacing(6)

        self.combo_crf = QComboBox(card_qual)
        self.combo_crf.addItems([
            "Fast Cut (CRF 22)",
            "High Quality (CRF 18)",
            "Small File (CRF 26)",
        ])
        self.combo_crf.setFixedWidth(150)
        self.combo_crf.setMinimumHeight(30)
        row_qual2.addWidget(self.combo_crf)

        self.lbl_preset_desc = QLabel("~8 MB/min · tiny AV1/VP9 download + fast cut to H.264 MP4", card_qual)
        self.lbl_preset_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        row_qual2.addWidget(self.lbl_preset_desc, 1)
        c3_layout.addLayout(row_qual2)

        left_layout.addWidget(card_qual)

        # CARD 4: SAVE TO
        card_save = QFrame(left_col)
        card_save.setObjectName("card")
        c4_layout = QVBoxLayout(card_save)
        c4_layout.setContentsMargins(12, 10, 12, 12)
        c4_layout.setSpacing(8)

        c4_hdr = QHBoxLayout()
        lbl_s4 = QLabel("4", card_save)
        lbl_s4.setObjectName("stepNumber")
        c4_hdr.addWidget(lbl_s4)
        lbl_t4 = QLabel("Save to", card_save)
        lbl_t4.setObjectName("cardTitle")
        c4_hdr.addWidget(lbl_t4)
        c4_hdr.addStretch()
        c4_layout.addLayout(c4_hdr)

        row_save = QHBoxLayout()
        row_save.setSpacing(6)
        self.txt_output = QLineEdit(card_save)
        default_dir = str(Path.home() / "Downloads") if (Path.home() / "Downloads").exists() else str(Path.cwd())
        self.txt_output.setText(default_dir)
        row_save.addWidget(self.txt_output, 1)

        self.btn_browse = QPushButton("...", card_save)
        self.btn_browse.setFixedWidth(36)
        self.btn_browse.clicked.connect(self._browse_output)
        row_save.addWidget(self.btn_browse)
        c4_layout.addLayout(row_save)

        left_layout.addWidget(card_save)
        left_layout.addStretch()

        scroll_left = QScrollArea(splitter)
        scroll_left.setWidgetResizable(True)
        scroll_left.setFrameShape(QFrame.Shape.NoFrame)
        scroll_left.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_left.setStyleSheet("""
            QScrollArea { background-color: transparent; border: none; }
            QScrollBar:vertical {
                border: none;
                background: #0f111a;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #23283a;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #3b82f6;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
                border: none;
                background: none;
            }
        """)
        scroll_left.setWidget(left_col)
        splitter.addWidget(scroll_left)

        # ── RIGHT COLUMN: QUEUE & DETAILS LOG ─────────────────────
        right_col = QWidget(splitter)
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(4, 0, 0, 0)
        right_layout.setSpacing(10)

        # QUEUE CARD
        card_q = QFrame(right_col)
        card_q.setObjectName("card")
        q_layout = QVBoxLayout(card_q)
        q_layout.setContentsMargins(10, 8, 10, 8)
        q_layout.setSpacing(6)

        q_hdr = QHBoxLayout()
        lbl_qt = QLabel("Queue", card_q)
        lbl_qt.setObjectName("cardTitle")
        q_hdr.addWidget(lbl_qt)
        q_hdr.addStretch()

        btn_clear_q = QPushButton("Clear", card_q)
        btn_clear_q.setObjectName("ghostBtn")
        btn_clear_q.clicked.connect(self._clear_queue)
        q_hdr.addWidget(btn_clear_q)
        q_layout.addLayout(q_hdr)

        self.tbl_queue = QTableWidget(0, 4, card_q)
        self.tbl_queue.setHorizontalHeaderLabels(["#", "Range", "Status", ""])
        self.tbl_queue.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.verticalHeader().setVisible(False)
        self.tbl_queue.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        q_layout.addWidget(self.tbl_queue)

        right_layout.addWidget(card_q, 1)

        # DETAILS (LOG) CARD
        card_log = QFrame(right_col)
        card_log.setObjectName("card")
        log_layout = QVBoxLayout(card_log)
        log_layout.setContentsMargins(10, 8, 10, 8)
        log_layout.setSpacing(6)

        log_hdr = QHBoxLayout()
        lbl_lt = QLabel("▸ Details (log)", card_log)
        lbl_lt.setObjectName("cardTitle")
        log_hdr.addWidget(lbl_lt)
        log_hdr.addStretch()

        btn_copy = QPushButton("Copy", card_log)
        btn_copy.setObjectName("ghostBtn")
        btn_copy.clicked.connect(self._copy_log)
        log_hdr.addWidget(btn_copy)

        btn_clr_log = QPushButton("Clear", card_log)
        btn_clr_log.setObjectName("ghostBtn")
        btn_clr_log.clicked.connect(self._clear_log)
        log_hdr.addWidget(btn_clr_log)
        log_layout.addLayout(log_hdr)

        self.log_view = QPlainTextEdit(card_log)
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(800)
        self.log_view.setPlaceholderText("Download logs and format inspection details will appear here...")
        log_layout.addWidget(self.log_view)

        right_layout.addWidget(card_log, 1)

        splitter.addWidget(right_col)
        splitter.setSizes([470, 490])
        layout.addWidget(splitter, 1)

        # ── 3. BOTTOM CONTROL BAR ─────────────────────────────────
        bottom_bar = QFrame(root)
        bottom_bar.setObjectName("card")
        bot_layout = QHBoxLayout(bottom_bar)
        bot_layout.setContentsMargins(10, 6, 10, 6)
        bot_layout.setSpacing(12)

        # Progress display (hidden / inactive when idle)
        self.progress_bar = QProgressBar(bottom_bar)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(160)
        self.progress_bar.setVisible(False)
        bot_layout.addWidget(self.progress_bar)

        self.lbl_progress = QLabel("", bottom_bar)
        self.lbl_progress.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        bot_layout.addWidget(self.lbl_progress)

        bot_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel", bottom_bar)
        self.btn_cancel.setObjectName("cancelBtn")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._cancel_download)
        bot_layout.addWidget(self.btn_cancel)

        self.btn_download = QPushButton("Download", bottom_bar)
        self.btn_download.setObjectName("downloadBtn")
        self.btn_download.clicked.connect(self._start_download)
        bot_layout.addWidget(self.btn_download)

        layout.addWidget(bottom_bar)

        # ── 4. STATUS BAR ─────────────────────────────────────────
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        cfg_str = os.path.expandvars(r"%APPDATA%\yt-dlp\config.txt")
        self.status_bar.showMessage(f"Ready · config: {cfg_str}")

    # ─────────────────────────────────────────────────────────────
    # Status & Tools Menu
    # ─────────────────────────────────────────────────────────────

    def _check_components_status(self):
        """Quick check to set green or red status dots in the header."""
        cmd = resolve_ytdlp_cmd() + ["--version"]
        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            self.lbl_dot_ytdlp.setObjectName("statusDotActive")
        except Exception:
            self.lbl_dot_ytdlp.setObjectName("statusDotInactive")
        self.lbl_dot_ytdlp.setText("● yt-dlp")

        # Deno
        try:
            subprocess.run(["deno", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            self.lbl_dot_deno.setObjectName("statusDotActive")
        except Exception:
            self.lbl_dot_deno.setObjectName("statusDotInactive")
        self.lbl_dot_deno.setText("● Deno")

        # FFmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            self.lbl_dot_ffmpeg.setObjectName("statusDotActive")
        except Exception:
            self.lbl_dot_ffmpeg.setObjectName("statusDotInactive")
        self.lbl_dot_ffmpeg.setText("● FFmpeg")

    def _show_tools_menu(self):
        menu = QMenu(self)
        a_diag = menu.addAction("🩺 Diagnostics & Health Check")
        a_diag.triggered.connect(lambda: HealthCheckDialog(self).exec())

        a_fmt = menu.addAction("🔍 Inspect Video Formats (yt-dlp -F)")
        a_fmt.triggered.connect(self._inspect_formats)

        a_upd = menu.addAction("🔄 Update Tools (yt-dlp & Deno)")
        a_upd.triggered.connect(self._run_tool_update)

        menu.addSeparator()
        a_cmd = menu.addAction("👁 Preview Command")
        a_cmd.triggered.connect(self._preview_command)

        a_fld = menu.addAction("📂 Open Save Folder")
        a_fld.triggered.connect(self._open_output_folder)

        pos = self.btn_tools.mapToGlobal(QPoint(0, self.btn_tools.height() + 2))
        menu.exec(pos)

    def _inspect_formats(self):
        url = self.txt_url.text().strip()
        if not url:
            self.status_bar.showMessage("Paste a YouTube link first to check formats.")
            return
        self._log(f"\n🔍 Inspecting formats for: {url}...")
        cmd = resolve_ytdlp_cmd() + ["-F", url]
        self._cmd_worker = CommandWorker(cmd)
        self._cmd_worker.output_line.connect(self._log)
        self._cmd_worker.start()

    def _run_tool_update(self):
        self._log("\n🔄 Updating yt-dlp[default] and Deno...")
        if sys.platform == "win32":
            cmd = ["powershell", "-Command", f"& '{PYTHON_EXE}' -m pip install -U 'yt-dlp[default]'; deno upgrade"]
        else:
            cmd = [PYTHON_EXE, "-m", "pip", "install", "-U", "yt-dlp[default]"]
        self._cmd_worker = CommandWorker(cmd)
        self._cmd_worker.output_line.connect(self._log)
        def _done(ok, msg):
            self._log("\n✅ Tool update complete." if ok else f"\n❌ Update failed: {msg}")
            self._check_components_status()
        self._cmd_worker.finished.connect(_done)
        self._cmd_worker.start()

    # ─────────────────────────────────────────────────────────────
    # Form Logic & Metadata
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_seconds(val: str) -> float | None:
        """Parses timestamps like '10:00', '1:10:00', '75' into total seconds."""
        s = val.strip()
        if not s or s.lower() in ("inf", "end"):
            return None
        parts = s.split(":")
        try:
            if len(parts) == 1:
                return float(parts[0])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except ValueError:
            return None
        return None

    @staticmethod
    def _format_seconds(total_seconds: float) -> str:
        s = max(0, int(total_seconds))
        h = s // 3600
        m = (s % 3600) // 60
        sec = s % 60
        if h > 0:
            return f"{h}:{m:02d}:{sec:02d}"
        return f"{m}:{sec:02d}"

    def _paste_url(self):
        clip = QApplication.clipboard().text().strip()
        if clip:
            self.txt_url.setText(clip)

    def _on_url_changed(self, text: str):
        cleaned = text.strip()
        if "youtube.com" in cleaned or "youtu.be" in cleaned or "twitch.tv" in cleaned or "tiktok.com" in cleaned:
            self.lbl_meta.setText("Link detected · resolving info...")
            self._url_timer.start(750)
        elif not cleaned:
            self.frame_meta.setVisible(False)
            self._video_duration_sec = 0.0
            self.lbl_meta.setText("Paste link to automatically resolve info · leave blank for full video")

    def _fetch_metadata(self):
        url = self.txt_url.text().strip()
        if not url:
            return
        if self._meta_worker and self._meta_worker.isRunning():
            self._meta_worker.terminate()
        self._meta_worker = MetadataWorker(url)
        self._meta_worker.metadata_ready.connect(self._on_metadata_loaded)
        self._meta_worker.metadata_error.connect(lambda err: self.lbl_meta.setText("Link detected · ready"))
        self._meta_worker.start()

    def _on_slider_range_changed(self, low: float, high: float):
        """Called when user drags or clicks the range slider handles."""
        self.txt_start.setText(self._format_seconds(low))
        self.txt_end.setText(self._format_seconds(high))
        dur_sec = max(0.0, high - low)
        self.lbl_slider_info.setText(
            f"▶ {self._format_seconds(low)} – {self._format_seconds(high)} ({self._format_seconds(dur_sec)})"
        )
        if not self._clips:
            self.lbl_clip_count.setText("Clip selected (press + Add)")

    def _on_time_text_edited(self):
        """Called when user manually types into Start or End text boxes."""
        st_text = self.txt_start.text().strip()
        en_text = self.txt_end.text().strip()
        st_sec = self._parse_seconds(st_text)
        en_sec = self._parse_seconds(en_text)

        if st_sec is not None and en_sec is not None:
            if en_sec > st_sec:
                if en_sec > self.slider_range._max_val:
                    new_max = en_sec * 1.2
                    self.slider_range.setRange(0.0, new_max)
                    self.lbl_slider_max.setText(self._format_seconds(new_max))
                self.slider_range.setValues(st_sec, en_sec)
                dur = en_sec - st_sec
                self.lbl_slider_info.setText(
                    f"▶ {self._format_seconds(st_sec)} – {self._format_seconds(en_sec)} ({self._format_seconds(dur)})"
                )
                if not self._clips:
                    self.lbl_clip_count.setText("Clip selected (press + Add)")
        elif st_sec is not None and not en_text:
            self.slider_range.setLow(st_sec)
        elif en_sec is not None and not st_text:
            self.slider_range.setHigh(en_sec)

    def _reset_clip_inputs(self):
        """Clears clip inputs to allow full video download."""
        self.txt_start.clear()
        self.txt_end.clear()
        self.slider_range.setValues(0.0, min(60.0, self.slider_range._max_val))
        self.lbl_slider_info.setText("Drag handles to set clip range")
        if not self._clips:
            self.lbl_clip_count.setText("0 added (full video)")

    def _on_metadata_loaded(self, data: dict):
        title = data.get("title", "")
        dur_str = data.get("duration_str", "")
        channel = data.get("channel", "")
        self._video_duration_sec = data.get("duration_sec", 0.0)

        self.lbl_video_title.setText(f"🎬 {title}")
        sub = []
        if dur_str:
            sub.append(f"⏱ {dur_str}")
        if channel:
            sub.append(f"👤 {channel}")
        self.lbl_video_sub.setText(" · ".join(sub))
        self.frame_meta.setVisible(True)
        self.lbl_meta.setText("Metadata resolved · ready to add clips or download")

        # Dynamically scale slider to full video duration
        if self._video_duration_sec > 0:
            self.slider_range.setRange(0.0, self._video_duration_sec)
            self.lbl_slider_max.setText(self._format_seconds(self._video_duration_sec))
            st_sec = self._parse_seconds(self.txt_start.text())
            en_sec = self._parse_seconds(self.txt_end.text())
            if st_sec is not None and en_sec is not None:
                self.slider_range.setValues(st_sec, min(en_sec, self._video_duration_sec))
            elif not self.txt_start.text() and not self.txt_end.text():
                self.lbl_slider_info.setText(
                    f"Drag handles to set clip (0:00 – {self._format_seconds(self._video_duration_sec)})"
                )

    def _apply_quick_duration(self, added_sec: int):
        """Automatically calculates and sets End time based on Start time and syncs slider."""
        start_txt = self.txt_start.text().strip()
        st_sec = self._parse_seconds(start_txt) if start_txt else 0.0
        if st_sec is None:
            st_sec = 0.0
            self.txt_start.setText("0:00")
        end_sec = st_sec + added_sec
        if self._video_duration_sec > 0 and end_sec > self._video_duration_sec:
            end_sec = self._video_duration_sec

        if end_sec > self.slider_range._max_val:
            self.slider_range.setRange(0.0, max(end_sec * 1.15, self._video_duration_sec))
            self.lbl_slider_max.setText(self._format_seconds(self.slider_range._max_val))

        self.txt_end.setText(self._format_seconds(end_sec))
        self.slider_range.setValues(st_sec, end_sec)
        dur = max(0.0, end_sec - st_sec)
        self.lbl_slider_info.setText(
            f"▶ {self._format_seconds(st_sec)} – {self._format_seconds(end_sec)} ({self._format_seconds(dur)})"
        )
        if not self._clips:
            self.lbl_clip_count.setText("Clip selected (press + Add)")

    def _on_preset_changed(self, idx: int):
        if idx == 0:  # Smart Compact
            self.combo_res.setEnabled(True)
            self.combo_crf.setEnabled(True)
            self.lbl_preset_desc.setText("~8 MB/min · tiny AV1/VP9 download + fast cut to H.264 MP4")
        elif idx == 1:  # Direct H.264
            self.combo_res.setEnabled(True)
            self.combo_crf.setEnabled(False)
            self.lbl_preset_desc.setText("~35 MB/min · native YouTube H.264 stream (larger file)")
        elif idx == 2:  # Fast Stream Copy
            self.combo_res.setEnabled(True)
            self.combo_crf.setEnabled(False)
            self.lbl_preset_desc.setText("Instant · keyframe stream copy without re-encoding")
        elif idx == 3:  # Audio only
            self.combo_res.setEnabled(False)
            self.combo_crf.setEnabled(False)
            self.lbl_preset_desc.setText("Audio only · high-bitrate MP3 extraction")

    def _add_clip_to_queue(self):
        start = self.txt_start.text().strip()
        end = self.txt_end.text().strip()
        if not start and not end:
            return

        st_sec = self._parse_seconds(start)
        en_sec = self._parse_seconds(end)
        if st_sec is not None and en_sec is not None and en_sec <= st_sec:
            QMessageBox.warning(self, "Invalid Time Range", "End time must be greater than start time.\n(Example: Start 10:00, End 11:00)")
            return

        # Check against video total duration if known
        if self._video_duration_sec > 0 and st_sec is not None and st_sec > self._video_duration_sec:
            QMessageBox.warning(
                self,
                "Start Time Beyond Video End",
                f"The start time ({start}) is after the video ends ({self._format_seconds(self._video_duration_sec)})!\n"
                "Remember: 10:00 is 10 minutes; 10:00:00 is 10 hours."
            )
            return

        range_str = f"{start or '0:00'}–{end or 'end'}"
        clip_num = len(self._clips) + 1
        item = {"clip_num": clip_num, "start": start or "0:00", "end": end or "inf", "range_str": range_str, "status": "Waiting"}
        self._clips.append(item)
        self._refresh_queue_table()

        self.tbl_queue.setRowCount(len(self._clips))
        for row, item in enumerate(self._clips):
            self.tbl_queue.setItem(row, 0, QTableWidgetItem(f"Clip {item['clip_num']}"))
            self.tbl_queue.setItem(row, 1, QTableWidgetItem(item["range_str"]))

        # Seamlessly advance slider to next segment
        next_start = en_sec if en_sec is not None else 0.0
        step = 60.0
        next_end = min(self.slider_range._max_val, next_start + step)
        if next_start >= self.slider_range._max_val:
            next_start = 0.0
            next_end = min(self.slider_range._max_val, step)
        self.slider_range.setValues(next_start, next_end)
        self.txt_start.setText(self._format_seconds(next_start))
        self.txt_end.setText(self._format_seconds(next_end))
        dur = max(0.0, next_end - next_start)
        self.lbl_slider_info.setText(
            f"▶ {self._format_seconds(next_start)} – {self._format_seconds(next_end)} ({self._format_seconds(dur)})"
        )
        self.txt_start.setFocus()
        self.lbl_clip_count.setText(f"{len(self._clips)} clip{'s' if len(self._clips) > 1 else ''} queued")

    def _delete_clip(self, clip_num: int):
        self._clips = [c for c in self._clips if c["clip_num"] != clip_num]
        for i, c in enumerate(self._clips, 1):
            c["clip_num"] = i
        self._refresh_queue_table()
        cnt = len(self._clips)
        self.lbl_clip_count.setText(f"{cnt} clip{'s' if cnt > 1 else ''} queued" if cnt else "0 added (full video)")

    def _refresh_queue_table(self):
        self.tbl_queue.setRowCount(len(self._clips))
        for row, item in enumerate(self._clips):
            self.tbl_queue.setItem(row, 0, QTableWidgetItem(f"Clip {item['clip_num']}"))
            self.tbl_queue.setItem(row, 1, QTableWidgetItem(item["range_str"]))

            st = item.get("status", "Waiting")
            if st == "Done":
                item_st = QTableWidgetItem("✔ Done")
                item_st.setForeground(QColor("#22c55e"))
            elif st == "Downloading":
                item_st = QTableWidgetItem("⟳ Downloading")
                item_st.setForeground(QColor("#38bdf8"))
            else:
                item_st = QTableWidgetItem("○ Waiting")
                item_st.setForeground(QColor("#94a3b8"))
            self.tbl_queue.setItem(row, 2, item_st)

            # Delete button per row
            btn_del = QPushButton("✕", self.tbl_queue)
            btn_del.setObjectName("delBtn")
            btn_del.setFixedSize(24, 22)
            btn_del.setToolTip("Remove this clip")
            btn_del.clicked.connect(lambda _, n=item["clip_num"]: self._delete_clip(n))
            self.tbl_queue.setCellWidget(row, 3, btn_del)

    def _clear_queue(self):
        self._clips.clear()
        self.tbl_queue.setRowCount(0)
        self.lbl_clip_count.setText("0 added (full video)")

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Save Location", self.txt_output.text())
        if folder:
            self.txt_output.setText(folder)

    def _open_output_folder(self):
        out_dir = Path(self.txt_output.text().strip()).resolve()
        if out_dir.exists():
            if sys.platform == "win32":
                subprocess.Popen(["explorer.exe", str(out_dir)], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(out_dir)])

    def _copy_log(self):
        QApplication.clipboard().setText(self.log_view.toPlainText())
        self.status_bar.showMessage("Log copied to clipboard.", 2000)

    def _clear_log(self):
        self.log_view.clear()

    # ─────────────────────────────────────────────────────────────
    # Command Construction & Execution
    # ─────────────────────────────────────────────────────────────

    def _build_command(self) -> list[str]:
        url = self.txt_url.text().strip()
        res_idx = self.combo_res.currentIndex()
        preset_idx = self.combo_preset.currentIndex()
        crf_idx = self.combo_crf.currentIndex()
        output_dir = self.txt_output.text().strip() or "."

        res_limits = {0: "1080", 1: "720", 2: "480", 3: None}
        max_h = res_limits.get(res_idx, "1080")
        crf_val = {0: "22", 1: "18", 2: "26"}.get(crf_idx, "22")

        if len(self._clips) > 1:
            out_template = str(Path(output_dir) / "%(title)s [%(section_start)s].%(ext)s")
        else:
            out_template = str(Path(output_dir) / "%(title)s.%(ext)s")

        cmd = resolve_ytdlp_cmd().copy()

        # Format & codec configuration
        if preset_idx == 0:  # Smart Compact (AV1/VP9 -> fast H.264 MP4 cut)
            if max_h:
                cmd += ["-f", f"bv*[height<={max_h}]+ba/b"]
            else:
                cmd += ["-f", "bv*+ba/b"]
            cmd += ["--merge-output-format", "mp4"]
            if self._clips:
                cmd += ["--force-keyframes-at-cuts", "--downloader-args", f"ffmpeg:-c:v libx264 -crf {crf_val} -preset ultrafast -c:a aac"]

        elif preset_idx == 1:  # Direct H.264 (avc1)
            if max_h:
                cmd += ["-f", f"bv*[height<={max_h}][vcodec^=avc1]+ba[ext=m4a]/bv*[height<={max_h}]+ba/b"]
            else:
                cmd += ["-f", "bv*[vcodec^=avc1]+ba[ext=m4a]/bv*+ba/b"]
            cmd += ["--merge-output-format", "mp4"]
            if self._clips:
                cmd += ["--force-keyframes-at-cuts"]

        elif preset_idx == 2:  # Fast Stream Copy
            if max_h:
                cmd += ["-f", f"bv*[height<={max_h}]+ba/b"]
            else:
                cmd += ["-f", "bv*+ba/b"]
            cmd += ["--merge-output-format", "mp4"]

        elif preset_idx == 3:  # Audio Only
            cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]

        # Clips
        if self._clips:
            for c in self._clips:
                cmd += ["--download-sections", f"*{c['start']}-{c['end']}"]
            if len(self._clips) >= 10:
                cmd += ["--sleep-interval", "3", "--max-sleep-interval", "8"]

        cmd += ["-N", "4"]
        cmd += ["-o", out_template]
        cmd += ["--file-access-retries", "10", "--fragment-retries", "10"]
        cmd += ["--progress", "--newline"]
        cmd.append(url)
        return cmd

    def _preview_command(self):
        url = self.txt_url.text().strip()
        if not url:
            self._log("Paste a YouTube link first.")
            return
        cmd = self._build_command()
        self._log("\n── Preview Command ──")
        self._log(" ".join(f'"{c}"' if " " in c else c for c in cmd))
        self._log("─────────────────────\n")

    def _start_download(self):
        url = self.txt_url.text().strip()
        if not url:
            self.status_bar.showMessage("Please paste a YouTube link first.")
            return

        st = self.txt_start.text().strip()
        en = self.txt_end.text().strip()
        if (st or en) and not self._clips:
            self._add_clip_to_queue()

        cmd = self._build_command()

        # Update UI state
        self.btn_download.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        clip_str = f"{len(self._clips)} clips" if self._clips else "full video"
        self.lbl_progress.setText(f"Starting {clip_str}...")
        self.status_bar.showMessage("Downloading...")

        if self._clips:
            self._clips[0]["status"] = "Downloading"
            self._refresh_queue_table()

        self._worker = DownloadWorker(cmd)
        self._worker.output_line.connect(self._log)
        self._worker.progress_update.connect(self._on_progress_update)
        self._worker.finished.connect(self._on_download_finished)
        self._worker.start()

    def _cancel_download(self):
        if self._worker:
            self._worker.cancel()
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "ffmpeg.exe"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        self.lbl_progress.setText("Cancelled")
        self.status_bar.showMessage("Download cancelled.")

    def _on_progress_update(self, pct: int, speed: str):
        self.progress_bar.setValue(pct)
        total_clips = len(self._clips)
        speed_txt = f" · {speed}" if speed else ""
        if total_clips > 1:
            self.lbl_progress.setText(f"{pct}% ({total_clips} clips{speed_txt})")
        else:
            self.lbl_progress.setText(f"{pct}%{speed_txt}")

    def _on_download_finished(self, success: bool, msg: str):
        self.btn_download.setEnabled(True)
        self.btn_cancel.setEnabled(False)

        if success:
            self.progress_bar.setValue(100)
            self.lbl_progress.setText("✔ Complete")
            self.status_bar.showMessage("Download complete!")
            for c in self._clips:
                c["status"] = "Done"
            self._refresh_queue_table()
        else:
            self.lbl_progress.setText(f"⏹ {msg}")
            self.status_bar.showMessage(f"Download ended: {msg}")

        self._worker = None

    def _log(self, text: str):
        """Rich HTML colored logging inspired by QtLogging standards."""
        color = "#94a3b8"  # Slate (default)
        if "[download]" in text:
            color = "#38bdf8"  # Cyan/sky blue
        elif "ERROR" in text or "⚠️" in text or "error" in text.lower() or "403" in text:
            color = "#f87171"  # Coral red
        elif "✔" in text or "Complete" in text or "Ready" in text or "100%" in text or "✅" in text:
            color = "#22c55e"  # Emerald green
        elif "WARNING" in text or "NOTICE" in text or "Sleeping" in text:
            color = "#fbbf24"  # Amber
        elif text.startswith("──") or text.startswith("=="):
            color = "#60a5fa"  # Accent blue

        escaped = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        html = f'<div style="color:{color}; font-family:\'Cascadia Code\', Consolas, monospace; font-size:11px; margin:1px 0; line-height:1.35;">{escaped}</div>'
        self.log_view.appendHtml(html)
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )

    # ─────────────────────────────────────────────────────────────
    # Persistence & Lifecycle
    # ─────────────────────────────────────────────────────────────

    def _restore_settings(self):
        geom = self._settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)
        saved_dir = self._settings.value("output_dir")
        if saved_dir:
            self.txt_output.setText(saved_dir)
        saved_preset = self._settings.value("preset_index")
        if saved_preset is not None:
            self.combo_preset.setCurrentIndex(int(saved_preset))
        saved_res = self._settings.value("res_index")
        if saved_res is not None:
            self.combo_res.setCurrentIndex(int(saved_res))
        saved_crf = self._settings.value("crf_index")
        if saved_crf is not None:
            self.combo_crf.setCurrentIndex(int(saved_crf))

    def cleanup_on_quit(self):
        """Ensures worker threads and subprocesses terminate cleanly."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(1500)
        if self._meta_worker and self._meta_worker.isRunning():
            self._meta_worker.terminate()
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "ffmpeg.exe"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW)

    def closeEvent(self, event):
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("output_dir", self.txt_output.text())
        self._settings.setValue("preset_index", self.combo_preset.currentIndex())
        self._settings.setValue("res_index", self.combo_res.currentIndex())
        self._settings.setValue("crf_index", self.combo_crf.currentIndex())
        self.cleanup_on_quit()
        event.accept()


def _apply_dark_palette(app: QApplication):
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,          QColor("#0f111a"))
    p.setColor(QPalette.ColorRole.WindowText,      QColor("#f1f5f9"))
    p.setColor(QPalette.ColorRole.Base,            QColor("#1e2336"))
    p.setColor(QPalette.ColorRole.AlternateBase,   QColor("#161926"))
    p.setColor(QPalette.ColorRole.ToolTipBase,     QColor("#1e2336"))
    p.setColor(QPalette.ColorRole.ToolTipText,     QColor("#f1f5f9"))
    p.setColor(QPalette.ColorRole.Text,            QColor("#f8fafc"))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor("#64748b"))
    p.setColor(QPalette.ColorRole.BrightText,      QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.ButtonText,      QColor("#f1f5f9"))
    p.setColor(QPalette.ColorRole.Button,          QColor("#1e2336"))
    p.setColor(QPalette.ColorRole.Highlight,       QColor("#2563eb"))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,       QColor("#475569"))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor("#475569"))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor("#475569"))
    app.setPalette(p)


def main():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ytdlp.gui.pro.2.5")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("yt-dlp GUI Pro")
    app.setOrganizationName("YtDlpGui")
    _apply_dark_palette(app)

    win = MainWindow()
    app.aboutToQuit.connect(win.cleanup_on_quit)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
