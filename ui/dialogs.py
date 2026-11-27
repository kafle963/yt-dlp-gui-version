"""Dialogs for yt-dlp GUI Pro."""
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.utils import run_diagnostics
from ui.icons import svg_icon
from ui.theme import Tokens, build_stylesheet


class HealthCheckDialog(QDialog):
    """System health check for yt-dlp, FFmpeg, Deno, and yt-dlp-ejs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Diagnostics & Dependencies")
        self.resize(540, 320)
        self.setStyleSheet(build_stylesheet())
        self._init_ui()
        self._run_checks()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        lbl = QLabel("System Component Status", self)
        lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {Tokens.TEXT_PRIMARY}; background: transparent;"
        )
        layout.addWidget(lbl)

        self.table = QTableWidget(5, 3, self)
        self.table.setHorizontalHeaderLabels(["Component", "Status", "Version / Path"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        btn_box = QHBoxLayout()
        btn_refresh = QPushButton("Re-check", self)
        btn_refresh.setIcon(svg_icon("refresh", Tokens.TEXT_SECONDARY, 13))
        btn_refresh.clicked.connect(self._run_checks)
        btn_box.addWidget(btn_refresh)
        btn_box.addStretch()

        btn_close = QPushButton("Close", self)
        btn_close.setObjectName("primaryBtn")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    def _run_checks(self):
        rows = run_diagnostics()
        self.table.setRowCount(len(rows))
        color_map = {
            "Ready": Tokens.SUCCESS,
            "Active": Tokens.SUCCESS,
            "Missing": Tokens.ERROR,
            "None": Tokens.WARNING,
        }
        for row, (name, status, detail) in enumerate(rows):
            self.table.setItem(row, 0, QTableWidgetItem(name))
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor(color_map.get(status, Tokens.TEXT_SECONDARY)))
            self.table.setItem(row, 1, status_item)
            self.table.setItem(row, 2, QTableWidgetItem(detail))
