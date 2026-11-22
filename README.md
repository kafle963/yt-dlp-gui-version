# yt-dlp GUI Pro

A clean, modern desktop frontend for `yt-dlp` designed for clipping and downloading online media with frame-accurate video/audio synchronization.

---

## What You Need to Download (Prerequisites)

Before running the app, ensure the following three core tools are installed on your computer:

### 1. Python (Version 3.10 or newer)
- **Windows:** Download from [python.org](https://www.python.org/downloads/). During installation, be sure to check **"Add Python to PATH"**.
- **macOS:** Install via Homebrew: `brew install python`
- **Linux (Ubuntu/Debian):** `sudo apt update && sudo apt install -y python3 python3-pip`

### 2. FFmpeg (Required for audio/video merging & clip cutting)
- **Windows:** Open PowerShell or Command Prompt and run:
  ```powershell
  winget install Gyan.FFmpeg
  ```
- **macOS:**
  ```bash
  brew install ffmpeg
  ```
- **Linux:**
  ```bash
  sudo apt install -y ffmpeg
  ```

### 3. Deno or Node.js (Required for YouTube JavaScript signature solver)
YouTube requires JavaScript challenge execution to prevent bandwidth throttling. Having Deno or Node.js installed allows `yt-dlp-ejs` to resolve these challenges automatically.
- **Windows:**
  ```powershell
  winget install DenoLand.Deno
  ```
- **macOS:**
  ```bash
  brew install deno
  ```
- **Linux:**
  ```bash
  curl -fsSL https://deno.land/install.sh | sh
  ```

---

## Quick Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
- **Windows:** Double-click `run.bat` or run:
  ```powershell
  python ytdlp_gui.py
  ```
- **macOS / Linux:**
  ```bash
  python3 ytdlp_gui.py
  ```

---

## Understanding Timestamp Formats

When clipping streams or videos, format your timestamps carefully:

| Desired Time | Correct Input | Common Mistake (Avoid) |
|---|---|---|
| **1 minute 15 seconds** | `1:15` or `01:15` | `1:15:00` *(This means 1 hour 15 minutes!)* |
| **10 minutes** | `10:00` or `0:10:00` | `10:00:00` *(This means 10 hours!)* |
| **1 hour 10 minutes** | `1:10:00` | `70:00` |

> **Why did FFmpeg fail with `-t value must be non-negative`?**
> If you enter `10:00:00` on a 20-minute video, yt-dlp interprets `10:00:00` as **10 hours (36,000 seconds)**. Because 10 hours is past the end of the video, FFmpeg calculates a negative duration and aborts. For 10 minutes, always use `10:00`.

---

## Quality Presets & Download Speed

The app provides granular control over download size, quality, and processing speed:

| Preset | Download Size | How It Works | Best For |
|---|---|---|---|
| **Smart Compact (Fastest)** | ~8 MB / min | Downloads lightweight AV1/VP9 streams (~2 Mbps) and uses FFmpeg (`-preset ultrafast`) to cut directly into editor-ready H.264 + AAC MP4. | 90% faster downloads; zero video editor desync. |
| **Direct H.264 (avc1)** | ~35 MB / min | Downloads YouTube's native H.264 stream directly. | Systems with very slow CPUs. |
| **Fast (Stream Copy)** | Variable | Copies video frames directly without re-encoding. Snaps cuts to nearest keyframe. | Instant cutting when frame-accuracy is not critical. |
| **Audio Only (MP3)** | ~1.5 MB / min | Extracts high-bitrate 320 kbps audio. | Podcasts, music, and voiceover clips. |

### Encoding Quality (CRF)
When re-encoding clips with **Smart Compact**, you can select your desired visual quality:
- **Fast Cut (CRF 22):** Balanced file size and encoding speed.
- **High Quality (CRF 18):** Visually lossless output for high-end video editing.
- **Small File (CRF 26):** Maximum disk space savings.

---

## Key Features

- **Multi-Clip Single Pass:** Download several clips from a single stream in one run without re-fetching page data or re-solving challenges.
- **Multi-Threaded Fragment Downloading (`-N 4`):** Uses 4 concurrent connections per download to saturate your bandwidth.
- **Editing-Safe Codec:** Exact synchronization in DaVinci Resolve, Adobe Premiere, and CapCut with `--force-keyframes-at-cuts`.
- **1,800+ Supported Sites:** Works with YouTube, Twitch, TikTok, Instagram, Twitter/X, and more.
- **Built-in Diagnostics:** Click `⚙ Tools -> 🩺 Diagnostics & Health Check` anytime to verify all components.

---

## License
MIT License.
