#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[VidVortex] Running first-time setup for macOS..."
chmod +x ./setup_macos.sh ./VidVortex
./setup_macos.sh

echo "[VidVortex] Setup complete. Launching VidVortex..."
exec ./VidVortex
