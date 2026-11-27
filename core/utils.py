"""Backend utilities: executable resolution, timestamp parsing, diagnostics, and yt-dlp command building."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

PYTHON_EXE = sys.executable
_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def resolve_ytdlp_cmd() -> list[str]:
    """Finds a verified, working yt-dlp command. Prefers Python's yt_dlp module, then PATH."""
    candidates: list[list[str]] = [[PYTHON_EXE, "-m", "yt_dlp"]]
    which_path = shutil.which("yt-dlp")
    if which_path:
        candidates.append([which_path])

    for cmd in candidates:
        try:
            res = subprocess.run(
                cmd + ["--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=_NO_WINDOW,
            )
            if res.returncode == 0:
                return cmd
        except Exception:
            continue

    return [PYTHON_EXE, "-m", "yt_dlp"]


def parse_seconds(val: str) -> float | None:
    """Parses timestamps like '10:00', '1:10:00', '75' into total seconds."""
    s = val.strip()
    if not s or s.lower() in ("inf", "end"):
        return None
    parts = s.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        if len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    except ValueError:
        return None
    return None


def format_seconds(total_seconds: float) -> str:
    """Formats seconds into M:SS or H:MM:SS."""
    s = max(0, int(total_seconds))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    if h > 0:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def get_ytdlp_config_path() -> Path:
    """Returns the expected yt-dlp user config path for the current OS."""
    if sys.platform == "win32":
        return Path(os.path.expandvars(r"%APPDATA%\yt-dlp\config.txt"))
    return Path.home() / ".config" / "yt-dlp" / "config"


def check_component_available(cmd: list[str]) -> bool:
    """Returns True if the given command exits with 0."""
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=_NO_WINDOW,
        )
        return res.returncode == 0
    except Exception:
        return False


def run_diagnostics() -> list[tuple[str, str, str]]:
    """Checks core tools and yt-dlp config, returning (name, status, detail) rows."""
    tools = [
        ("yt-dlp", resolve_ytdlp_cmd() + ["--version"]),
        ("FFmpeg", ["ffmpeg", "-version"]),
        ("Deno", ["deno", "--version"]),
        (
            "yt-dlp-ejs",
            [
                PYTHON_EXE,
                "-c",
                "import importlib.metadata; print(importlib.metadata.version('yt-dlp-ejs'))",
            ],
        ),
    ]
    rows: list[tuple[str, str, str]] = []
    for name, cmd in tools:
        try:
            out = subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, text=True, creationflags=_NO_WINDOW
            )
            first_line = out.strip().split("\n")[0]
            rows.append((name, "Ready", first_line[:65]))
        except Exception as exc:
            rows.append((name, "Missing", str(exc)[:65]))

    cfg_path = get_ytdlp_config_path()
    if cfg_path.exists():
        rows.append(("Config", "Active", str(cfg_path)))
    else:
        rows.append(("Config", "None", "No config found"))
    return rows


def build_ytdlp_command(
    url: str,
    res_idx: int,
    preset_idx: int,
    crf_idx: int,
    output_dir: str,
    clips: list[dict],
) -> list[str]:
    """Builds the yt-dlp CLI argument list from UI selections."""
    res_limits = {0: "1080", 1: "720", 2: "480", 3: None}
    max_h = res_limits.get(res_idx, "1080")
    crf_val = {0: "22", 1: "18", 2: "26"}.get(crf_idx, "22")
    out_dir = output_dir.strip() or "."

    if len(clips) > 1:
        out_template = str(Path(out_dir) / "%(title)s [%(section_start)s].%(ext)s")
    else:
        out_template = str(Path(out_dir) / "%(title)s.%(ext)s")

    cmd = resolve_ytdlp_cmd().copy()

    if preset_idx == 0:  # Smart Compact (AV1/VP9 -> fast H.264 MP4 cut)
        if max_h:
            cmd += ["-f", f"bv*[height<={max_h}]+ba/b"]
        else:
            cmd += ["-f", "bv*+ba/b"]
        cmd += ["--merge-output-format", "mp4"]
        if clips:
            cmd += [
                "--force-keyframes-at-cuts",
                "--downloader-args",
                f"ffmpeg:-c:v libx264 -crf {crf_val} -preset ultrafast -c:a aac",
            ]

    elif preset_idx == 1:  # Direct H.264 (avc1)
        if max_h:
            cmd += [
                "-f",
                f"bv*[height<={max_h}][vcodec^=avc1]+ba[ext=m4a]/bv*[height<={max_h}]+ba/b",
            ]
        else:
            cmd += ["-f", "bv*[vcodec^=avc1]+ba[ext=m4a]/bv*+ba/b"]
        cmd += ["--merge-output-format", "mp4"]
        if clips:
            cmd += ["--force-keyframes-at-cuts"]

    elif preset_idx == 2:  # Fast Stream Copy
        if max_h:
            cmd += ["-f", f"bv*[height<={max_h}]+ba/b"]
        else:
            cmd += ["-f", "bv*+ba/b"]
        cmd += ["--merge-output-format", "mp4"]

    elif preset_idx == 3:  # Audio Only
        cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]

    if clips:
        for clip in clips:
            cmd += ["--download-sections", f"*{clip['start']}-{clip['end']}"]
        if len(clips) >= 10:
            cmd += ["--sleep-interval", "3", "--max-sleep-interval", "8"]

    cmd += ["-N", "4"]
    cmd += ["-o", out_template]
    cmd += ["--file-access-retries", "10", "--fragment-retries", "10"]
    cmd += ["--progress", "--newline"]
    cmd.append(url)
    return cmd
