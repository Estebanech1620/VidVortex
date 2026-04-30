#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "[VidVortex] Installing build dependencies..."
"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r requirements-desktop.txt

DIST_DIR="$REPO_ROOT/dist/macos"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

ICON_FILE=""
if [[ -f app_logo.icns ]]; then
  ICON_FILE="app_logo.icns"
elif [[ -f app_logo.png ]]; then
  ICON_FILE="app_logo.png"
else
  echo "[VidVortex] ERROR: Missing app_logo.icns or app_logo.png in application repo root — macOS builds need one for an embedded icon." >&2
  exit 1
fi

EXTRA_DATA=()
if [[ -f app_logo.png ]]; then
  EXTRA_DATA+=(--add-data "app_logo.png:.")
fi

echo "[VidVortex] Building macOS executable..."
"$PYTHON_BIN" -m PyInstaller \
  --noconfirm \
  --clean \
  --name VidVortex \
  --onefile \
  --windowed \
  --distpath "$DIST_DIR" \
  --icon "$ICON_FILE" \
  --add-data "yt-dlp.conf.example:." \
  --add-data "profiles.json.example:." \
  --add-data "queue.json.example:." \
  ${EXTRA_DATA[@]+"${EXTRA_DATA[@]}"} \
  --collect-all ttkbootstrap \
  vidvortex_app.py

if [[ ! -f "$DIST_DIR/VidVortex" ]]; then
  echo "[VidVortex] Build finished but output file is missing." >&2
  exit 1
fi

chmod +x "$DIST_DIR/VidVortex"
echo "[VidVortex] macOS package ready: $DIST_DIR/VidVortex"
