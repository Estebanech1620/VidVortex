#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Terminal / double-click launches often have a minimal PATH; yt-dlp must resolve to Homebrew’s copy.
if [[ -x /opt/homebrew/bin/brew ]]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
elif [[ -x /usr/local/bin/brew ]]; then
  eval "$(/usr/local/bin/brew shellenv)"
fi

echo "[VidVortex] Running first-time setup for macOS..."
chmod +x ./setup_macos.sh ./VidVortex
./setup_macos.sh

echo "[VidVortex] Setup complete. Launching VidVortex..."
exec ./VidVortex
