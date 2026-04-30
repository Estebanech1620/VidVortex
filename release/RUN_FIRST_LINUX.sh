#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[VidVortex] Running first-time setup for Linux..."
chmod +x ./setup_linux.sh ./VidVortex
./setup_linux.sh

echo "[VidVortex] Setup complete. Launching VidVortex..."
./VidVortex
