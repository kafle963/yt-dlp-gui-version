"""Asynchronous QThread workers for metadata resolution, utility commands, and downloads."""
import os
import re
import subprocess

from PySide6.QtCore import QThread, Signal

from core.utils import resolve_ytdlp_cmd

_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


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
                "--print",
                "%(title)s\t%(duration)s\t%(duration_string)s\t%(uploader,channel)s",
                "--no-playlist",
                "--no-warnings",
                self._url,
            ]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=_NO_WINDOW,
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

                self.metadata_ready.emit(
                    {
                        "title": title,
                        "duration_sec": dur_sec,
                        "duration_str": dur_str,
                        "channel": channel,
                    }
                )
            else:
                self.metadata_error.emit(proc.stderr[:120])
        except Exception as exc:
            self.metadata_error.emit(str(exc))


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
                creationflags=_NO_WINDOW,
            )
            if self._proc.stdout:
                for line in self._proc.stdout:
                    line = line.rstrip()
                    if line:
                        self.output_line.emit(line)
            self._proc.wait()
            self.finished.emit(self._proc.returncode == 0, "")
        except Exception as exc:
            self.finished.emit(False, str(exc))


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
                creationflags=_NO_WINDOW,
            )
            if self._proc.stdout:
                for line in self._proc.stdout:
                    line = line.rstrip()
                    if not line:
                        continue
                    if "-t value must be non-negative" in line:
                        self.output_line.emit(
                            "ERROR: Start time is beyond the end of the video! (Note: 10:00 = 10 minutes; 10:00:00 = 10 hours)."
                        )
                    elif (
                        "Output file is empty, nothing was encoded" in line
                        or "moov atom not found" in line
                    ):
                        self.output_line.emit(
                            "LIVESTREAM NOTICE: This livestream has not been fully processed into a standard VOD by YouTube yet. "
                            "Its live stream timestamps do not start at 0:00:00. Time-range clipping will work normally once YouTube completes backend processing of the archive."
                        )
                    if "Late SEI is not implemented" in line or "upload a sample of this file" in line:
                        continue
                    self.output_line.emit(line)

                    m = re.search(
                        r"\[download\]\s+([\d.]+)%\s+of\s+~?[\d.]+\w+\s+at\s+([\d.]+\w+/s)",
                        line,
                    )
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
        except Exception as exc:
            self.finished.emit(False, str(exc))

    def cancel(self):
        self._cancelled = True
        if self._proc and self._proc.poll() is None:
            pid = self._proc.pid
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=_NO_WINDOW,
                )
            else:
                self._proc.terminate()
