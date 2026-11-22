# Contributing to yt-dlp GUI Pro

Thank you for your interest in contributing! This project is open-source and welcomes contributions from developers of all experience levels.

---

## Getting Started

### 1. Prerequisites
Ensure you have the following installed locally:
- Python 3.10 or higher
- FFmpeg (for video processing)
- Deno or Node.js (for YouTube JavaScript challenge solving)
- Git

### 2. Fork and Clone
```bash
git clone https://github.com/<your-username>/yt-dlp-gui-pro.git
cd yt-dlp-gui-pro
```

### 3. Create a Virtual Environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Application

Launch the desktop interface:
```bash
python ytdlp_gui.py
```

---

## How to Contribute

We welcome improvements in several key areas:

### 1. New Features & Ideas
- Support for URL batch importing (e.g. from `.txt` or CSV files).
- Audio waveform visualizer for easier clip trimming.
- Dark / Light theme selector.
- Hardware acceleration encoder profiles (e.g., NVENC, QSV, VAAPI).

### 2. Bug Fixes
- Check existing issues or submit a detailed bug report.
- Include your operating system, Python version, FFmpeg version, and relevant terminal logs.

### 3. Submitting Pull Requests
1. Create a descriptive feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your edits and verify the app compiles and launches cleanly:
   ```bash
   python -m py_compile ytdlp_gui.py
   ```
3. Commit your changes with a clear commit message.
4. Push to your fork and submit a Pull Request to the `main` branch.

---

## Code Style
- Follow PEP 8 guidelines for Python code.
- Ensure cross-platform compatibility (Windows, macOS, Linux).
- Avoid hardcoded file paths; use `pathlib.Path` and environment variables.
