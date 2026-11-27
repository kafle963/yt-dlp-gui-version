"""Main application window for yt-dlp GUI Pro."""
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
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
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.utils import (
    PYTHON_EXE,
    build_ytdlp_command,
    check_component_available,
    format_seconds,
    get_ytdlp_config_path,
    parse_seconds,
    resolve_ytdlp_cmd,
)
from core.workers import CommandWorker, DownloadWorker, MetadataWorker
from ui.dialogs import HealthCheckDialog
from ui.icons import svg_icon, svg_pixmap
from ui.theme import Tokens, apply_palette, build_stylesheet, set_theme_mode
from ui.widgets import HairlineDivider, RangeSlider, SectionHeader, StatusIndicator


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("yt-dlp GUI Pro")
        self.setMinimumSize(940, 600)
        self.resize(1040, 780)
        self.setStyleSheet(build_stylesheet())

        self._worker: DownloadWorker | None = None
        self._cmd_worker: CommandWorker | None = None
        self._meta_worker: MetadataWorker | None = None
        self._settings = QSettings("YtDlpGui", "Settings")

        # In-memory clip queue: list of dicts
        self._clips: list[dict] = []
        self._video_duration_sec: float = 0.0
        self._theme_mode: str = "dark"

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
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── 1. TOP BAR ────────────────────────────────────────────
        top_bar = QFrame(root)
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(44)
        header = QHBoxLayout(top_bar)
        header.setContentsMargins(16, 0, 16, 0)
        header.setSpacing(10)

        self._brand_icon = QLabel(top_bar)
        self._brand_icon.setPixmap(svg_pixmap("play", color=Tokens.ACCENT_TEXT, size=15))
        self._brand_icon.setFixedSize(16, 16)
        header.addWidget(self._brand_icon)

        lbl_brand = QLabel("yt-dlp GUI Pro", top_bar)
        lbl_brand.setObjectName("brandTitle")
        header.addWidget(lbl_brand)
        header.addStretch()

        self.ind_ytdlp = StatusIndicator("yt-dlp", top_bar)
        header.addWidget(self.ind_ytdlp)
        header.addSpacing(8)

        self.ind_deno = StatusIndicator("Deno", top_bar)
        header.addWidget(self.ind_deno)
        header.addSpacing(8)

        self.ind_ffmpeg = StatusIndicator("FFmpeg", top_bar)
        header.addWidget(self.ind_ffmpeg)
        header.addSpacing(12)

        self.btn_theme = QPushButton(top_bar)
        self.btn_theme.setObjectName("ghostBtn")
        self.btn_theme.setFixedSize(28, 26)
        self.btn_theme.setIcon(svg_icon("sun", Tokens.TEXT_SECONDARY, 14))
        self.btn_theme.setToolTip("Switch to Day mode")
        self.btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_theme.clicked.connect(self._toggle_theme)
        header.addWidget(self.btn_theme)

        self.btn_tools = QPushButton("Tools", top_bar)
        self.btn_tools.setObjectName("ghostBtn")
        self.btn_tools.setIcon(svg_icon("sliders", Tokens.TEXT_SECONDARY, 13))
        self.btn_tools.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tools.clicked.connect(self._show_tools_menu)
        header.addWidget(self.btn_tools)

        root_layout.addWidget(top_bar)

        # ── 2. MAIN WORKSPACE SPLITTER ────────────────────────────
        workspace = QWidget(root)
        ws_layout = QVBoxLayout(workspace)
        ws_layout.setContentsMargins(16, 14, 16, 14)
        ws_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal, workspace)
        splitter.setHandleWidth(1)

        # ── LEFT PANE: CONFIGURATION ──────────────────────────────
        left_panel = QFrame()
        left_panel.setObjectName("panel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 12, 16, 12)
        left_layout.setSpacing(10)

        # Section 1: SOURCE
        left_layout.addWidget(SectionHeader("link", "Source", parent=left_panel))

        row_url = QHBoxLayout()
        row_url.setSpacing(8)
        self.txt_url = QLineEdit(left_panel)
        self.txt_url.setPlaceholderText("Paste a YouTube, Twitch, or media URL...")
        self.txt_url.setClearButtonEnabled(True)
        self.txt_url.setFixedHeight(32)
        self.txt_url.textChanged.connect(self._on_url_changed)
        row_url.addWidget(self.txt_url, 1)

        self.btn_paste = QPushButton("Paste", left_panel)
        self.btn_paste.setIcon(svg_icon("clipboard", Tokens.TEXT_SECONDARY, 13))
        self.btn_paste.setFixedHeight(32)
        self.btn_paste.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_paste.clicked.connect(self._paste_url)
        row_url.addWidget(self.btn_paste)
        left_layout.addLayout(row_url)

        # Metadata Preview Strip
        self.frame_meta = QFrame(left_panel)
        self.frame_meta.setObjectName("metaStrip")
        meta_layout = QVBoxLayout(self.frame_meta)
        meta_layout.setContentsMargins(10, 8, 10, 8)
        meta_layout.setSpacing(4)

        row_meta_title = QHBoxLayout()
        row_meta_title.setSpacing(6)
        self._lbl_film_icon = QLabel(self.frame_meta)
        self._lbl_film_icon.setPixmap(svg_pixmap("film", color=Tokens.ACCENT_TEXT, size=13))
        self._lbl_film_icon.setFixedSize(14, 14)
        row_meta_title.addWidget(self._lbl_film_icon)

        self.lbl_video_title = QLabel("", self.frame_meta)
        self.lbl_video_title.setStyleSheet(
            f"color: {Tokens.TEXT_PRIMARY}; font-weight: 600; font-size: 12px; background: transparent;"
        )
        self.lbl_video_title.setWordWrap(True)
        row_meta_title.addWidget(self.lbl_video_title, 1)
        meta_layout.addLayout(row_meta_title)

        row_meta_sub = QHBoxLayout()
        row_meta_sub.setSpacing(12)

        row_dur = QHBoxLayout()
        row_dur.setSpacing(4)
        self.lbl_dur_icon = QLabel(self.frame_meta)
        self.lbl_dur_icon.setPixmap(svg_pixmap("clock", color=Tokens.TEXT_MUTED, size=12))
        self.lbl_dur_icon.setFixedSize(12, 12)
        row_dur.addWidget(self.lbl_dur_icon)
        self.lbl_video_dur = QLabel("", self.frame_meta)
        self.lbl_video_dur.setObjectName("monoText")
        row_dur.addWidget(self.lbl_video_dur)
        row_meta_sub.addLayout(row_dur)

        row_chan = QHBoxLayout()
        row_chan.setSpacing(4)
        self.lbl_chan_icon = QLabel(self.frame_meta)
        self.lbl_chan_icon.setPixmap(svg_pixmap("user", color=Tokens.TEXT_MUTED, size=12))
        self.lbl_chan_icon.setFixedSize(12, 12)
        row_chan.addWidget(self.lbl_chan_icon)
        self.lbl_video_chan = QLabel("", self.frame_meta)
        self.lbl_video_chan.setObjectName("mutedText")
        row_chan.addWidget(self.lbl_video_chan)
        row_meta_sub.addLayout(row_chan)
        row_meta_sub.addStretch()

        meta_layout.addLayout(row_meta_sub)
        self.frame_meta.setVisible(False)
        left_layout.addWidget(self.frame_meta)

        self.lbl_meta = QLabel("Paste a link to resolve metadata · leave clips empty for full video", left_panel)
        self.lbl_meta.setObjectName("mutedText")
        self.lbl_meta.setWordWrap(True)
        left_layout.addWidget(self.lbl_meta)

        left_layout.addWidget(HairlineDivider(left_panel))

        # Section 2: TRIM & CLIPS
        self.lbl_clip_count = QLabel("0 added (full video)", left_panel)
        self.lbl_clip_count.setObjectName("mutedText")
        left_layout.addWidget(
            SectionHeader("scissors", "Trim & Clips", right_widget=self.lbl_clip_count, parent=left_panel)
        )

        row_slider_hdr = QHBoxLayout()
        row_slider_hdr.setContentsMargins(0, 0, 0, 0)
        self.lbl_slider_min = QLabel("0:00", left_panel)
        self.lbl_slider_min.setObjectName("monoText")
        row_slider_hdr.addWidget(self.lbl_slider_min)

        row_slider_hdr.addStretch()
        self.lbl_slider_info = QLabel("0:00 – 1:00 (1:00)", left_panel)
        self.lbl_slider_info.setObjectName("monoBadge")
        row_slider_hdr.addWidget(self.lbl_slider_info)
        row_slider_hdr.addStretch()

        self.lbl_slider_max = QLabel("10:00", left_panel)
        self.lbl_slider_max.setObjectName("monoText")
        row_slider_hdr.addWidget(self.lbl_slider_max)
        left_layout.addLayout(row_slider_hdr)

        self.slider_range = RangeSlider(left_panel)
        self.slider_range.rangeChanged.connect(self._on_slider_range_changed)
        left_layout.addWidget(self.slider_range)

        row_clip_in = QHBoxLayout()
        row_clip_in.setSpacing(8)

        lbl_st = QLabel("Start", left_panel)
        lbl_st.setObjectName("fieldLabel")
        row_clip_in.addWidget(lbl_st)

        self.txt_start = QLineEdit(left_panel)
        self.txt_start.setObjectName("monoInput")
        self.txt_start.setPlaceholderText("0:00")
        self.txt_start.setFixedWidth(74)
        self.txt_start.setFixedHeight(28)
        self.txt_start.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_start.textEdited.connect(self._on_time_text_edited)
        row_clip_in.addWidget(self.txt_start)

        lbl_en = QLabel("End", left_panel)
        lbl_en.setObjectName("fieldLabel")
        row_clip_in.addWidget(lbl_en)

        self.txt_end = QLineEdit(left_panel)
        self.txt_end.setObjectName("monoInput")
        self.txt_end.setPlaceholderText("1:00")
        self.txt_end.setFixedWidth(74)
        self.txt_end.setFixedHeight(28)
        self.txt_end.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_end.textEdited.connect(self._on_time_text_edited)
        row_clip_in.addWidget(self.txt_end)

        row_clip_in.addStretch()

        self.btn_add_clip = QPushButton("Add", left_panel)
        self.btn_add_clip.setIcon(svg_icon("plus", Tokens.TEXT_PRIMARY, 13))
        self.btn_add_clip.setFixedHeight(28)
        self.btn_add_clip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_clip.clicked.connect(self._add_clip_to_queue)
        row_clip_in.addWidget(self.btn_add_clip)

        self.btn_reset_clip = QPushButton("Reset", left_panel)
        self.btn_reset_clip.setObjectName("ghostBtn")
        self.btn_reset_clip.setIcon(svg_icon("rotate-ccw", Tokens.TEXT_SECONDARY, 12))
        self.btn_reset_clip.setFixedHeight(28)
        self.btn_reset_clip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reset_clip.setToolTip("Clear clip selection to download full video")
        self.btn_reset_clip.clicked.connect(self._reset_clip_inputs)
        row_clip_in.addWidget(self.btn_reset_clip)
        left_layout.addLayout(row_clip_in)

        row_pills = QHBoxLayout()
        row_pills.setSpacing(6)
        lbl_quick = QLabel("Quick end", left_panel)
        lbl_quick.setObjectName("mutedText")
        row_pills.addWidget(lbl_quick)

        for text, sec in [("+30s", 30), ("+1m", 60), ("+2m", 120), ("+5m", 300)]:
            btn = QPushButton(text, left_panel)
            btn.setObjectName("pillBtn")
            btn.setFixedHeight(22)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, s=sec: self._apply_quick_duration(s))
            row_pills.addWidget(btn)
        row_pills.addStretch()
        left_layout.addLayout(row_pills)

        lbl_hint = QLabel("Drag handles for start/end, or drag the bar between to shift the window", left_panel)
        lbl_hint.setObjectName("mutedText")
        lbl_hint.setWordWrap(True)
        left_layout.addWidget(lbl_hint)

        left_layout.addWidget(HairlineDivider(left_panel))

        # Section 3: OUTPUT FORMAT
        left_layout.addWidget(SectionHeader("sliders", "Output Format", parent=left_panel))

        row_qual1 = QHBoxLayout()
        row_qual1.setSpacing(8)
        self.combo_res = QComboBox(left_panel)
        self.combo_res.addItems(["1080p (FHD)", "720p (HD)", "480p (SD)", "Max (4K+)"])
        self.combo_res.setFixedWidth(112)
        self.combo_res.setFixedHeight(30)
        row_qual1.addWidget(self.combo_res)

        self.combo_preset = QComboBox(left_panel)
        self.combo_preset.addItems(
            [
                "Smart Compact (Fastest ~8MB/m)",
                "Direct H.264 (avc1 ~35MB/m)",
                "Fast (Stream copy)",
                "Audio only (MP3)",
            ]
        )
        self.combo_preset.setFixedHeight(30)
        self.combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        row_qual1.addWidget(self.combo_preset, 1)
        left_layout.addLayout(row_qual1)

        row_qual2 = QHBoxLayout()
        row_qual2.setSpacing(8)
        self.combo_crf = QComboBox(left_panel)
        self.combo_crf.addItems(
            [
                "Fast Cut (CRF 22)",
                "High Quality (CRF 18)",
                "Small File (CRF 26)",
            ]
        )
        self.combo_crf.setFixedWidth(156)
        self.combo_crf.setFixedHeight(30)
        row_qual2.addWidget(self.combo_crf)

        self.lbl_preset_desc = QLabel("~8 MB/min · AV1/VP9 + fast cut to H.264 MP4", left_panel)
        self.lbl_preset_desc.setObjectName("mutedText")
        self.lbl_preset_desc.setWordWrap(True)
        row_qual2.addWidget(self.lbl_preset_desc, 1)
        left_layout.addLayout(row_qual2)

        left_layout.addWidget(HairlineDivider(left_panel))

        # Section 4: DESTINATION
        left_layout.addWidget(SectionHeader("folder", "Save To", parent=left_panel))

        row_save = QHBoxLayout()
        row_save.setSpacing(8)
        self.txt_output = QLineEdit(left_panel)
        self.txt_output.setObjectName("monoInput")
        default_dir = (
            str(Path.home() / "Downloads")
            if (Path.home() / "Downloads").exists()
            else str(Path.cwd())
        )
        self.txt_output.setText(default_dir)
        self.txt_output.setFixedHeight(30)
        row_save.addWidget(self.txt_output, 1)

        self.btn_browse = QPushButton(left_panel)
        self.btn_browse.setIcon(svg_icon("folder", Tokens.TEXT_SECONDARY, 14))
        self.btn_browse.setFixedSize(34, 30)
        self.btn_browse.setToolTip("Choose output folder")
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.clicked.connect(self._browse_output)
        row_save.addWidget(self.btn_browse)
        left_layout.addLayout(row_save)

        left_layout.addStretch()

        scroll_left = QScrollArea(splitter)
        scroll_left.setWidgetResizable(True)
        scroll_left.setFrameShape(QFrame.Shape.NoFrame)
        scroll_left.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_left.setWidget(left_panel)
        splitter.addWidget(scroll_left)

        # ── RIGHT PANE: QUEUE & CONSOLE ───────────────────────────
        right_col = QWidget(splitter)
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(12, 0, 0, 0)
        right_layout.setSpacing(12)

        # Queue Panel
        card_q = QFrame(right_col)
        card_q.setObjectName("panel")
        q_layout = QVBoxLayout(card_q)
        q_layout.setContentsMargins(14, 12, 14, 12)
        q_layout.setSpacing(8)

        btn_clear_q = QPushButton("Clear", card_q)
        btn_clear_q.setObjectName("ghostBtn")
        btn_clear_q.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear_q.clicked.connect(self._clear_queue)
        q_layout.addWidget(SectionHeader("download", "Queue", right_widget=btn_clear_q, parent=card_q))

        self.tbl_queue = QTableWidget(0, 4, card_q)
        self.tbl_queue.setHorizontalHeaderLabels(["#", "Range", "Status", ""])
        self.tbl_queue.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_queue.verticalHeader().setVisible(False)
        self.tbl_queue.verticalHeader().setDefaultSectionSize(32)
        self.tbl_queue.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl_queue.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_queue.setShowGrid(False)
        q_layout.addWidget(self.tbl_queue)
        right_layout.addWidget(card_q, 1)

        # Console Panel
        card_log = QFrame(right_col)
        card_log.setObjectName("panel")
        log_layout = QVBoxLayout(card_log)
        log_layout.setContentsMargins(14, 12, 14, 12)
        log_layout.setSpacing(8)

        log_actions = QWidget(card_log)
        log_act_layout = QHBoxLayout(log_actions)
        log_act_layout.setContentsMargins(0, 0, 0, 0)
        log_act_layout.setSpacing(4)

        self._btn_copy = QPushButton("Copy", log_actions)
        self._btn_copy.setObjectName("ghostBtn")
        self._btn_copy.setIcon(svg_icon("copy", Tokens.TEXT_SECONDARY, 12))
        self._btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_copy.clicked.connect(self._copy_log)
        log_act_layout.addWidget(self._btn_copy)

        self._btn_clr_log = QPushButton("Clear", log_actions)
        self._btn_clr_log.setObjectName("ghostBtn")
        self._btn_clr_log.setIcon(svg_icon("trash", Tokens.TEXT_SECONDARY, 12))
        self._btn_clr_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_clr_log.clicked.connect(self._clear_log)
        log_act_layout.addWidget(self._btn_clr_log)

        log_layout.addWidget(SectionHeader("terminal", "Console", right_widget=log_actions, parent=card_log))

        self.log_view = QPlainTextEdit(card_log)
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(800)
        self.log_view.setPlaceholderText("Download logs and format inspection output will appear here...")
        log_layout.addWidget(self.log_view)
        right_layout.addWidget(card_log, 1)

        splitter.addWidget(right_col)
        splitter.setSizes([470, 520])
        ws_layout.addWidget(splitter)
        root_layout.addWidget(workspace, 1)

        # ── 3. BOTTOM ACTION BAR ──────────────────────────────────
        bottom_bar = QFrame(root)
        bottom_bar.setObjectName("bottomBar")
        bottom_bar.setFixedHeight(52)
        bot_layout = QHBoxLayout(bottom_bar)
        bot_layout.setContentsMargins(16, 0, 16, 0)
        bot_layout.setSpacing(12)

        self.progress_bar = QProgressBar(bottom_bar)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(180)
        self.progress_bar.setVisible(False)
        bot_layout.addWidget(self.progress_bar)

        self.lbl_progress = QLabel("", bottom_bar)
        self.lbl_progress.setStyleSheet(
            f"color: {Tokens.TEXT_SECONDARY}; font-size: 12px; font-weight: 500; background: transparent;"
        )
        bot_layout.addWidget(self.lbl_progress)

        bot_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel", bottom_bar)
        self.btn_cancel.setObjectName("dangerBtn")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self._cancel_download)
        bot_layout.addWidget(self.btn_cancel)

        self.btn_download = QPushButton("Download", bottom_bar)
        self.btn_download.setObjectName("primaryBtn")
        self.btn_download.setIcon(svg_icon("download", "#FFFFFF", 14))
        self.btn_download.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_download.clicked.connect(self._start_download)
        bot_layout.addWidget(self.btn_download)

        root_layout.addWidget(bottom_bar)

        # ── 4. STATUS BAR ─────────────────────────────────────────
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"Ready · config: {get_ytdlp_config_path()}")

    # ─────────────────────────────────────────────────────────────
    # Status & Tools Menu
    # ─────────────────────────────────────────────────────────────

    def _check_components_status(self):
        self.ind_ytdlp.set_active(check_component_available(resolve_ytdlp_cmd() + ["--version"]))
        self.ind_deno.set_active(check_component_available(["deno", "--version"]))
        self.ind_ffmpeg.set_active(check_component_available(["ffmpeg", "-version"]))

    def _show_tools_menu(self):
        menu = QMenu(self)
        a_diag = menu.addAction(svg_icon("activity", Tokens.TEXT_SECONDARY, 13), "Diagnostics & Health Check")
        a_diag.triggered.connect(lambda: HealthCheckDialog(self).exec())

        a_fmt = menu.addAction(svg_icon("search", Tokens.TEXT_SECONDARY, 13), "Inspect Video Formats (yt-dlp -F)")
        a_fmt.triggered.connect(self._inspect_formats)

        a_upd = menu.addAction(svg_icon("refresh", Tokens.TEXT_SECONDARY, 13), "Update Tools (yt-dlp & Deno)")
        a_upd.triggered.connect(self._run_tool_update)

        menu.addSeparator()
        a_cmd = menu.addAction(svg_icon("terminal", Tokens.TEXT_SECONDARY, 13), "Preview Command")
        a_cmd.triggered.connect(self._preview_command)

        a_fld = menu.addAction(svg_icon("folder", Tokens.TEXT_SECONDARY, 13), "Open Save Folder")
        a_fld.triggered.connect(self._open_output_folder)

        menu.exec(self.btn_tools.mapToGlobal(self.btn_tools.rect().bottomLeft()))

    def _inspect_formats(self):
        url = self.txt_url.text().strip()
        if not url:
            self._log("Paste a YouTube link first to inspect formats.")
            return
        self._log(f"\nInspecting formats for: {url}...")
        cmd = resolve_ytdlp_cmd() + ["-F", url]
        self._cmd_worker = CommandWorker(cmd)
        self._cmd_worker.output_line.connect(self._log)
        self._cmd_worker.start()

    def _run_tool_update(self):
        self._log("\nUpdating yt-dlp[default] and Deno...")
        cmd = [PYTHON_EXE, "-m", "pip", "install", "-U", "yt-dlp[default]"]
        self._cmd_worker = CommandWorker(cmd)
        self._cmd_worker.output_line.connect(self._log)
        self._cmd_worker.finished.connect(
            lambda ok, msg: self._log("\nTool update complete." if ok else f"\nUpdate failed: {msg}")
        )
        self._cmd_worker.start()

    # ─────────────────────────────────────────────────────────────
    # Form Logic & Time Sync
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_seconds(val: str) -> float | None:
        return parse_seconds(val)

    @staticmethod
    def _format_seconds(total_seconds: float) -> str:
        return format_seconds(total_seconds)

    def _paste_url(self):
        clip = QApplication.clipboard().text().strip()
        if clip:
            self.txt_url.setText(clip)

    def _on_url_changed(self, text: str):
        cleaned = text.strip()
        if any(host in cleaned for host in ("youtube.com", "youtu.be", "twitch.tv", "tiktok.com")):
            self.lbl_meta.setText("Link detected · resolving metadata...")
            self._url_timer.start(750)
        elif not cleaned:
            self.frame_meta.setVisible(False)
            self._video_duration_sec = 0.0
            self.lbl_meta.setText("Paste a link to resolve metadata · leave clips empty for full video")

    def _fetch_metadata(self):
        url = self.txt_url.text().strip()
        if not url:
            return
        if self._meta_worker and self._meta_worker.isRunning():
            self._meta_worker.terminate()
        self._meta_worker = MetadataWorker(url)
        self._meta_worker.metadata_ready.connect(self._on_metadata_loaded)
        self._meta_worker.metadata_error.connect(lambda _err: self.lbl_meta.setText("Link detected · ready"))
        self._meta_worker.start()

    def _on_slider_range_changed(self, low: float, high: float):
        self.txt_start.setText(format_seconds(low))
        self.txt_end.setText(format_seconds(high))
        dur_sec = max(0.0, high - low)
        self.lbl_slider_info.setText(f"{format_seconds(low)} – {format_seconds(high)} ({format_seconds(dur_sec)})")
        if not self._clips:
            self.lbl_clip_count.setText("Clip selected (click Add)")

    def _on_time_text_edited(self):
        st_text = self.txt_start.text().strip()
        en_text = self.txt_end.text().strip()
        st_sec = parse_seconds(st_text)
        en_sec = parse_seconds(en_text)

        if st_sec is not None and en_sec is not None:
            if en_sec > st_sec:
                if en_sec > self.slider_range._max_val:
                    new_max = en_sec * 1.2
                    self.slider_range.setRange(0.0, new_max)
                    self.lbl_slider_max.setText(format_seconds(new_max))
                self.slider_range.setValues(st_sec, en_sec)
                dur = en_sec - st_sec
                self.lbl_slider_info.setText(f"{format_seconds(st_sec)} – {format_seconds(en_sec)} ({format_seconds(dur)})")
                if not self._clips:
                    self.lbl_clip_count.setText("Clip selected (click Add)")
        elif st_sec is not None and not en_text:
            self.slider_range.setLow(st_sec)
        elif en_sec is not None and not st_text:
            self.slider_range.setHigh(en_sec)

    def _reset_clip_inputs(self):
        self.txt_start.clear()
        self.txt_end.clear()
        self.slider_range.setValues(0.0, min(60.0, self.slider_range._max_val))
        self.lbl_slider_info.setText("0:00 – 1:00 (1:00)")
        if not self._clips:
            self.lbl_clip_count.setText("0 added (full video)")

    def _on_metadata_loaded(self, data: dict):
        title = data.get("title", "")
        dur_str = data.get("duration_str", "")
        channel = data.get("channel", "")
        self._video_duration_sec = data.get("duration_sec", 0.0)

        self.lbl_video_title.setText(title)
        self.lbl_video_dur.setText(dur_str or "—")
        self.lbl_video_chan.setText(channel or "Unknown")
        self.frame_meta.setVisible(True)
        self.lbl_meta.setText("Metadata resolved · ready to trim or download")

        if self._video_duration_sec > 0:
            self.slider_range.setRange(0.0, self._video_duration_sec)
            self.lbl_slider_max.setText(format_seconds(self._video_duration_sec))
            st_sec = parse_seconds(self.txt_start.text())
            en_sec = parse_seconds(self.txt_end.text())
            if st_sec is not None and en_sec is not None:
                self.slider_range.setValues(st_sec, min(en_sec, self._video_duration_sec))
            elif not self.txt_start.text() and not self.txt_end.text():
                self.lbl_slider_info.setText(f"0:00 – {format_seconds(min(60.0, self._video_duration_sec))}")

    def _apply_quick_duration(self, added_sec: int):
        start_txt = self.txt_start.text().strip()
        st_sec = parse_seconds(start_txt) if start_txt else 0.0
        if st_sec is None:
            st_sec = 0.0
            self.txt_start.setText("0:00")
        end_sec = st_sec + added_sec
        if self._video_duration_sec > 0 and end_sec > self._video_duration_sec:
            end_sec = self._video_duration_sec

        if end_sec > self.slider_range._max_val:
            self.slider_range.setRange(0.0, max(end_sec * 1.15, self._video_duration_sec))
            self.lbl_slider_max.setText(format_seconds(self.slider_range._max_val))

        self.txt_end.setText(format_seconds(end_sec))
        self.slider_range.setValues(st_sec, end_sec)
        dur = max(0.0, end_sec - st_sec)
        self.lbl_slider_info.setText(f"{format_seconds(st_sec)} – {format_seconds(end_sec)} ({format_seconds(dur)})")
        if not self._clips:
            self.lbl_clip_count.setText("Clip selected (click Add)")

    def _on_preset_changed(self, idx: int):
        if idx == 0:
            self.combo_res.setEnabled(True)
            self.combo_crf.setEnabled(True)
            self.lbl_preset_desc.setText("~8 MB/min · AV1/VP9 + fast cut to H.264 MP4")
        elif idx == 1:
            self.combo_res.setEnabled(True)
            self.combo_crf.setEnabled(False)
            self.lbl_preset_desc.setText("~35 MB/min · native H.264 stream (larger file)")
        elif idx == 2:
            self.combo_res.setEnabled(True)
            self.combo_crf.setEnabled(False)
            self.lbl_preset_desc.setText("Instant · keyframe stream copy without re-encoding")
        elif idx == 3:
            self.combo_res.setEnabled(False)
            self.combo_crf.setEnabled(False)
            self.lbl_preset_desc.setText("Audio only · high-bitrate MP3 extraction")

    def _add_clip_to_queue(self):
        start = self.txt_start.text().strip()
        end = self.txt_end.text().strip()
        if not start and not end:
            return

        st_sec = parse_seconds(start)
        en_sec = parse_seconds(end)
        if st_sec is not None and en_sec is not None and en_sec <= st_sec:
            QMessageBox.warning(
                self,
                "Invalid Time Range",
                "End time must be greater than start time.\n(Example: Start 10:00, End 11:00)",
            )
            return

        if self._video_duration_sec > 0 and st_sec is not None and st_sec > self._video_duration_sec:
            QMessageBox.warning(
                self,
                "Start Time Beyond Video End",
                f"The start time ({start}) is after the video ends ({format_seconds(self._video_duration_sec)}).\n"
                "Remember: 10:00 is 10 minutes; 10:00:00 is 10 hours.",
            )
            return

        range_str = f"{start or '0:00'} – {end or 'end'}"
        clip_num = len(self._clips) + 1
        self._clips.append(
            {
                "clip_num": clip_num,
                "start": start or "0:00",
                "end": end or "inf",
                "range_str": range_str,
                "status": "Waiting",
            }
        )
        self._refresh_queue_table()

        next_start = en_sec if en_sec is not None else 0.0
        step = 60.0
        next_end = min(self.slider_range._max_val, next_start + step)
        if next_start >= self.slider_range._max_val:
            next_start = 0.0
            next_end = min(self.slider_range._max_val, step)
        self.slider_range.setValues(next_start, next_end)
        self.txt_start.setText(format_seconds(next_start))
        self.txt_end.setText(format_seconds(next_end))
        dur = max(0.0, next_end - next_start)
        self.lbl_slider_info.setText(
            f"{format_seconds(next_start)} – {format_seconds(next_end)} ({format_seconds(dur)})"
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
            num_item = QTableWidgetItem(f"{item['clip_num']:02d}")
            num_item.setForeground(QColor(Tokens.TEXT_MUTED))
            self.tbl_queue.setItem(row, 0, num_item)

            range_item = QTableWidgetItem(item["range_str"])
            range_item.setForeground(QColor(Tokens.TEXT_PRIMARY))
            self.tbl_queue.setItem(row, 1, range_item)

            st = item.get("status", "Waiting")
            if st == "Done":
                item_st = QTableWidgetItem("Done")
                item_st.setForeground(QColor(Tokens.SUCCESS))
            elif st == "Downloading":
                item_st = QTableWidgetItem("Downloading")
                item_st.setForeground(QColor(Tokens.ACCENT_TEXT))
            else:
                item_st = QTableWidgetItem("Waiting")
                item_st.setForeground(QColor(Tokens.TEXT_MUTED))
            self.tbl_queue.setItem(row, 2, item_st)

            btn_del = QPushButton(self.tbl_queue)
            btn_del.setObjectName("iconBtn")
            btn_del.setIcon(svg_icon("x", Tokens.TEXT_MUTED, 13))
            btn_del.setFixedSize(24, 24)
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
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
        return build_ytdlp_command(
            url=self.txt_url.text().strip(),
            res_idx=self.combo_res.currentIndex(),
            preset_idx=self.combo_preset.currentIndex(),
            crf_idx=self.combo_crf.currentIndex(),
            output_dir=self.txt_output.text().strip(),
            clips=self._clips,
        )

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
            subprocess.run(
                ["taskkill", "/F", "/IM", "ffmpeg.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
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
            self.lbl_progress.setText("Complete")
            self.status_bar.showMessage("Download complete!")
            for c in self._clips:
                c["status"] = "Done"
            self._refresh_queue_table()
        else:
            self.lbl_progress.setText(msg)
            self.status_bar.showMessage(f"Download ended: {msg}")

        self._worker = None

    def _log(self, text: str):
        color = Tokens.TEXT_SECONDARY
        if "[download]" in text:
            color = Tokens.INFO
        elif "ERROR" in text or "error" in text.lower() or "403" in text or "Update failed" in text:
            color = Tokens.ERROR
        elif "Complete" in text or "Ready" in text or "100%" in text or "complete." in text:
            color = Tokens.SUCCESS
        elif "WARNING" in text or "NOTICE" in text or "Sleeping" in text:
            color = Tokens.WARNING
        elif text.startswith("──") or text.startswith("=="):
            color = Tokens.ACCENT_TEXT

        escaped = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        html = (
            f'<div style="color:{color}; font-family:\'JetBrains Mono\', \'Cascadia Mono\', Consolas, monospace; '
            f'font-size:11px; margin:1px 0; line-height:1.4;">{escaped}</div>'
        )
        self.log_view.appendHtml(html)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    # ─────────────────────────────────────────────────────────────
    # Theme Switching (Night / Day)
    # ─────────────────────────────────────────────────────────────

    def _toggle_theme(self):
        next_mode = "light" if self._theme_mode == "dark" else "dark"
        self.apply_theme(next_mode)

    def apply_theme(self, mode: str):
        self._theme_mode = set_theme_mode(mode)
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_palette(app, self._theme_mode)
        self.setStyleSheet(build_stylesheet(self._theme_mode))

        is_dark = self._theme_mode == "dark"
        self.btn_theme.setIcon(svg_icon("sun" if is_dark else "moon", Tokens.TEXT_SECONDARY, 14))
        self.btn_theme.setToolTip("Switch to Day mode" if is_dark else "Switch to Night mode")

        # Refresh custom components & icons
        for widget in self.findChildren(SectionHeader):
            widget.refresh_theme()
        for widget in self.findChildren(StatusIndicator):
            widget.refresh_theme()

        self._brand_icon.setPixmap(svg_pixmap("play", color=Tokens.ACCENT_TEXT, size=15))
        self.btn_tools.setIcon(svg_icon("sliders", Tokens.TEXT_SECONDARY, 13))
        self.btn_paste.setIcon(svg_icon("clipboard", Tokens.TEXT_SECONDARY, 13))
        self._lbl_film_icon.setPixmap(svg_pixmap("film", color=Tokens.ACCENT_TEXT, size=13))
        self.lbl_dur_icon.setPixmap(svg_pixmap("clock", color=Tokens.TEXT_MUTED, size=12))
        self.lbl_chan_icon.setPixmap(svg_pixmap("user", color=Tokens.TEXT_MUTED, size=12))
        self.btn_add_clip.setIcon(svg_icon("plus", Tokens.TEXT_PRIMARY, 13))
        self.btn_reset_clip.setIcon(svg_icon("rotate-ccw", Tokens.TEXT_SECONDARY, 12))
        self.btn_browse.setIcon(svg_icon("folder", Tokens.TEXT_SECONDARY, 14))
        self._btn_copy.setIcon(svg_icon("copy", Tokens.TEXT_SECONDARY, 12))
        self._btn_clr_log.setIcon(svg_icon("trash", Tokens.TEXT_SECONDARY, 12))

        self.lbl_video_title.setStyleSheet(
            f"color: {Tokens.TEXT_PRIMARY}; font-weight: 600; font-size: 12px; background: transparent;"
        )
        self.lbl_progress.setStyleSheet(
            f"color: {Tokens.TEXT_SECONDARY}; font-size: 12px; font-weight: 500; background: transparent;"
        )

        self._refresh_queue_table()
        self.slider_range.update()

    # ─────────────────────────────────────────────────────────────
    # Persistence & Lifecycle
    # ─────────────────────────────────────────────────────────────

    def _restore_settings(self):
        saved_theme = self._settings.value("theme_mode", "dark")
        if saved_theme in ("dark", "light"):
            self.apply_theme(saved_theme)
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
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(1500)
        if self._meta_worker and self._meta_worker.isRunning():
            self._meta_worker.terminate()
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/IM", "ffmpeg.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

    def closeEvent(self, event):
        self._settings.setValue("theme_mode", self._theme_mode)
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("output_dir", self.txt_output.text())
        self._settings.setValue("preset_index", self.combo_preset.currentIndex())
        self._settings.setValue("res_index", self.combo_res.currentIndex())
        self._settings.setValue("crf_index", self.combo_crf.currentIndex())
        self.cleanup_on_quit()
        event.accept()
