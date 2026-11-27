"""
yt-dlp GUI Pro — Entry point for the desktop media clipping & download interface.
"""
import sys

from PySide6.QtWidgets import QApplication

from core.utils import resolve_ytdlp_cmd
from core.workers import CommandWorker, DownloadWorker, MetadataWorker
from ui.dialogs import HealthCheckDialog
from ui.main_window import MainWindow
from ui.theme import apply_dark_palette
from ui.widgets import RangeSlider

__all__ = [
    "CommandWorker",
    "DownloadWorker",
    "HealthCheckDialog",
    "MainWindow",
    "MetadataWorker",
    "RangeSlider",
    "main",
    "resolve_ytdlp_cmd",
]


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
    apply_dark_palette(app)

    win = MainWindow()
    app.aboutToQuit.connect(win.cleanup_on_quit)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
