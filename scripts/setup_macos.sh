#!/usr/bin/env bash
set -euo pipefail

echo "[VidVortex] macOS dependency setup starting..."

if ! command -v brew >/dev/null 2>&1; then
  echo "[Error] Homebrew is required. Install it first: https://brew.sh" >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  echo "[VidVortex] Python already exists on PATH."
else
  echo "[VidVortex] Installing Python with Homebrew..."
  brew install python
fi

echo "[VidVortex] Ensuring yt-dlp is installed and up to date..."
brew update
if brew list yt-dlp >/dev/null 2>&1; then
  brew upgrade yt-dlp || echo "[VidVortex] yt-dlp already current or upgrade skipped."
else
  brew install yt-dlp
fi

if command -v ffmpeg >/dev/null 2>&1; then
  echo "[VidVortex] ffmpeg already exists on PATH."
else
  echo "[VidVortex] Installing ffmpeg with Homebrew..."
  brew install ffmpeg
fi

if ! command -v yt-dlp >/dev/null 2>&1 || ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[Error] Dependencies were not installed correctly." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[Error] Python 3 was not installed correctly." >&2
  exit 1
fi

echo "[VidVortex] Dependency setup complete."
echo "[VidVortex] Installed in standard Homebrew locations (PATH)."
