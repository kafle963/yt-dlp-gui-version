"""
yt-dlp GUI Pro — Streamlined two-column desktop interface for downloading YouTube clips.
Designed strictly around user specification:
- Left Column: Step 1 (Link), Step 2 (Clips), Step 3 (Quality Preset), Step 4 (Save To)
- Right Column: Queue (visual clip status) + Collapsible Log (with header Copy / Clear)
- Header: Minimal brand + live status dots (yt-dlp, Deno, FFmpeg) + Gear menu
- Bottom Bar: Unified progress label + Cancel / Download buttons + Padded status bar
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, QSettings, QSize, Qt, QThread, Signal
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPalette
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
    background-color: #12141c;
    color: #e2e8f0;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

/* Card Containers */
QFrame#card {
    background-color: #1a1d29;
    border: 1px solid #272c3d;
    border-radius: 8px;
}

QFrame#cardHeader {
    background-color: transparent;
    border-bottom: 1px solid #272c3d;
    padding-bottom: 6px;
    margin-bottom: 8px;
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
    background-color: #222636;
    color: #f8fafc;
    border: 1px solid #333a4f;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 13px;
    min-height: 32px;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
}
QLineEdit:focus {
    border: 1px solid #3b82f6;
    background-color: #262c3e;
}
QLineEdit:disabled {
    background-color: #161822;
    color: #475569;
    border-color: #222634;
}

QComboBox {
    background-color: #222636;
    color: #f8fafc;
    border: 1px solid #333a4f;
    border-radius: 6px;
    padding: 4px 10px;
    min-height: 32px;
    font-size: 13px;
}
QComboBox:hover { border-color: #434c67; }
QComboBox:focus { border-color: #3b82f6; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: #222636;
    border: 1px solid #3b82f6;
    selection-background-color: #3b82f6;
    color: #f8fafc;
    padding: 4px;
    outline: none;
}

/* Buttons */
QPushButton {
    background-color: #222636;
    color: #cbd5e1;
    border: 1px solid #333a4f;
    border-radius: 6px;
    padding: 5px 14px;
    font-weight: 500;
    font-size: 12px;
    min-height: 32px;
}
QPushButton:hover {
    background-color: #2b3145;
    color: #ffffff;
    border-color: #4f5d83;
}
QPushButton:pressed {
    background-color: #1e2230;
    border-color: #3b82f6;
}
QPushButton:disabled {
    background-color: #171924;
    color: #475569;
    border-color: #222634;
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
    background-color: #222636;
    color: #f1f5f9;
    border-color: #333a4f;
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
    background-color: #222636;
    color: #f87171;
    border: 1px solid #451a1a;
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
    background-color: #181922;
    color: #452b2b;
    border-color: #231c1c;
}

/* Table */
QTableWidget {
    background-color: #161822;
    border: 1px solid #272c3d;
    border-radius: 6px;
    gridline-color: transparent;
    outline: none;
}
QTableWidget::item {
    padding: 4px 6px;
    border-bottom: 1px solid #1f2331;
}
QTableWidget::item:selected {
    background-color: #222a3d;
    color: #ffffff;
}

/* Log Text */
QPlainTextEdit {
    background-color: #13141d;
    color: #94a3b8;
    border: 1px solid #242938;
    border-radius: 6px;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 11px;
    padding: 6px;
}

/* Progress */
QProgressBar {
    background-color: #1e2230;
    border: 1px solid #272c3d;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: #3b82f6;
    border-radius: 3px;
}

/* Status Bar */
QStatusBar {
    background-color: #101118;
    color: #64748b;
    border-top: 1px solid #1e2230;
    font-size: 11px;
    padding: 4px 10px;
}
"""


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
                        self.output_line.emit("⚠️ ERROR: Start time is beyond the end of the video! Remember: 10:00 is 10 minutes; 10:00:00 is 10 hours.")
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
        self.setMinimumSize(880, 580)
        self.resize(920, 640)
        self.setStyleSheet(STYLESHEET)

        self._worker: DownloadWorker | None = None
        self._cmd_worker: CommandWorker | None = None
        self._settings = QSettings("YtDlpGui", "Settings")

        # In-memory clip queue: list of dicts: {"start": "1:10:00", "end": "1:11:00", "status": "Waiting"}
        self._clips: list[dict] = []

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
        left_col = QWidget(splitter)
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

        self.lbl_meta = QLabel("Paste link to automatically resolve info · leave blank for full video", card_link)
        self.lbl_meta.setObjectName("subText")
        self.lbl_meta.setWordWrap(True)
        c1_layout.addWidget(self.lbl_meta)

        left_layout.addWidget(card_link)

        # CARD 2: CLIPS
        card_clips = QFrame(left_col)
        card_clips.setObjectName("card")
        c2_layout = QVBoxLayout(card_clips)
        c2_layout.setContentsMargins(12, 10, 12, 12)
        c2_layout.setSpacing(8)

        c2_hdr = QHBoxLayout()
        lbl_s2 = QLabel("2", card_clips)
        lbl_s2.setObjectName("stepNumber")
        c2_hdr.addWidget(lbl_s2)
        lbl_t2 = QLabel("Clips", card_clips)
        lbl_t2.setObjectName("cardTitle")
        c2_hdr.addWidget(lbl_t2)
        c2_hdr.addStretch()

        self.lbl_clip_count = QLabel("0 added (full video)", card_clips)
        self.lbl_clip_count.setObjectName("subText")
        c2_hdr.addWidget(self.lbl_clip_count)
        c2_layout.addLayout(c2_hdr)

        row_clip_in = QHBoxLayout()
        row_clip_in.setSpacing(6)
        row_clip_in.addWidget(QLabel("Start", card_clips))
        self.txt_start = QLineEdit(card_clips)
        self.txt_start.setPlaceholderText("10:00")
        self.txt_start.setFixedWidth(80)
        self.txt_start.setMinimumHeight(32)
        self.txt_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_clip_in.addWidget(self.txt_start)

        row_clip_in.addWidget(QLabel("End", card_clips))
        self.txt_end = QLineEdit(card_clips)
        self.txt_end.setPlaceholderText("11:00")
        self.txt_end.setFixedWidth(80)
        self.txt_end.setMinimumHeight(32)
        self.txt_end.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row_clip_in.addWidget(self.txt_end)

        self.btn_add_clip = QPushButton("+ Add", card_clips)
        self.btn_add_clip.setFixedWidth(65)
        self.btn_add_clip.setMinimumHeight(32)
        self.btn_add_clip.clicked.connect(self._add_clip_to_queue)
        row_clip_in.addWidget(self.btn_add_clip)
        row_clip_in.addStretch()
        c2_layout.addLayout(row_clip_in)

        lbl_hint = QLabel("Hint: 10:00 is 10 min · 1:10:00 is 1 hr 10 min", card_clips)
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

        splitter.addWidget(left_col)

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

        self.tbl_queue = QTableWidget(0, 3, card_q)
        self.tbl_queue.setHorizontalHeaderLabels(["Clip", "Range", "Status"])
        self.tbl_queue.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
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
        self.log_view.setMaximumBlockCount(600)
        self.log_view.setPlaceholderText("Download logs and format inspection details will appear here...")
        log_layout.addWidget(self.log_view)

        right_layout.addWidget(card_log, 1)

        splitter.addWidget(right_col)
        splitter.setSizes([430, 450])
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
        # yt-dlp
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
    # Form Logic
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

    def _paste_url(self):
        clip = QApplication.clipboard().text().strip()
        if clip:
            self.txt_url.setText(clip)

    def _on_url_changed(self, text: str):
        if "youtube.com" in text or "youtu.be" in text:
            self.lbl_meta.setText("Link detected · ready to add clips or download")
        elif not text:
            self.lbl_meta.setText("Paste link to automatically resolve info · leave blank for full video")

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

        range_str = f"{start or '0:00'}–{end or 'end'}"
        clip_num = len(self._clips) + 1
        item = {"clip_num": clip_num, "start": start or "0:00", "end": end or "inf", "range_str": range_str, "status": "Waiting"}
        self._clips.append(item)

        row = self.tbl_queue.rowCount()
        self.tbl_queue.insertRow(row)
        self.tbl_queue.setItem(row, 0, QTableWidgetItem(f"Clip {clip_num}"))
        self.tbl_queue.setItem(row, 1, QTableWidgetItem(range_str))
        self.tbl_queue.setItem(row, 2, QTableWidgetItem("○ Waiting"))
        self.tbl_queue.item(row, 2).setForeground(QColor("#94a3b8"))

        self.txt_start.clear()
        self.txt_end.clear()
        self.txt_start.setFocus()
        self.lbl_clip_count.setText(f"{len(self._clips)} clip{'s' if len(self._clips) > 1 else ''} queued")

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

        # Template handling: if multiple clips, add section start to prevent overwrites
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
            # Pure stream copy (no re-encode)

        elif preset_idx == 3:  # Audio Only
            cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]

        # Clips
        if self._clips:
            for c in self._clips:
                cmd += ["--download-sections", f"*{c['start']}-{c['end']}"]
            if len(self._clips) >= 10:
                cmd += ["--sleep-interval", "3", "--max-sleep-interval", "8"]

        # High speed concurrent fragment downloading
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

        # If user typed times into start/end boxes without clicking "+ Add", add it automatically
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

        # Mark first queue item running if any
        if self._clips:
            self.tbl_queue.setItem(0, 2, QTableWidgetItem("⟳ Downloading"))
            self.tbl_queue.item(0, 2).setForeground(QColor("#3b82f6"))

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
        if total_clips > 1:
            speed_txt = f" · {speed}" if speed else ""
            self.lbl_progress.setText(f"{pct}% ({total_clips} clips{speed_txt})")
        else:
            speed_txt = f" · {speed}" if speed else ""
            self.lbl_progress.setText(f"{pct}%{speed_txt}")

    def _on_download_finished(self, success: bool, msg: str):
        self.btn_download.setEnabled(True)
        self.btn_cancel.setEnabled(False)

        if success:
            self.progress_bar.setValue(100)
            self.lbl_progress.setText("✔ Complete")
            self.status_bar.showMessage("Download complete!")
            # Mark all queue items done
            for row in range(self.tbl_queue.rowCount()):
                self.tbl_queue.setItem(row, 2, QTableWidgetItem("✔ Done"))
                self.tbl_queue.item(row, 2).setForeground(QColor("#22c55e"))
        else:
            self.lbl_progress.setText(f"⏹ {msg}")
            self.status_bar.showMessage(f"Download ended: {msg}")

        self._worker = None

    def _log(self, text: str):
        self.log_view.appendPlainText(text)
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )

    # ─────────────────────────────────────────────────────────────
    # Persistence
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

    def closeEvent(self, event):
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("output_dir", self.txt_output.text())
        self._settings.setValue("preset_index", self.combo_preset.currentIndex())
        self._settings.setValue("res_index", self.combo_res.currentIndex())
        self._settings.setValue("crf_index", self.combo_crf.currentIndex())
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(1500)
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "ffmpeg.exe"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW)
        event.accept()


def _apply_dark_palette(app: QApplication):
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,          QColor("#12141c"))
    p.setColor(QPalette.ColorRole.WindowText,      QColor("#f1f5f9"))
    p.setColor(QPalette.ColorRole.Base,            QColor("#222636"))
    p.setColor(QPalette.ColorRole.AlternateBase,   QColor("#1a1d29"))
    p.setColor(QPalette.ColorRole.ToolTipBase,     QColor("#222636"))
    p.setColor(QPalette.ColorRole.ToolTipText,     QColor("#f1f5f9"))
    p.setColor(QPalette.ColorRole.Text,            QColor("#f8fafc"))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor("#64748b"))
    p.setColor(QPalette.ColorRole.BrightText,      QColor("#ffffff"))
    p.setColor(QPalette.ColorRole.ButtonText,      QColor("#f1f5f9"))
    p.setColor(QPalette.ColorRole.Button,          QColor("#222636"))
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
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ytdlp.gui.pro.2.0")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("yt-dlp GUI Pro")
    app.setOrganizationName("YtDlpGui")
    _apply_dark_palette(app)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
