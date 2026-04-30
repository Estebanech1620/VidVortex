#!/usr/bin/env bash
set -euo pipefail

echo "[VidVortex] macOS dependency setup starting..."

ensure_brew_shellenv() {
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

ensure_brew_shellenv

if ! command -v brew >/dev/null 2>&1; then
  echo "[VidVortex] Homebrew was not found. Installing Homebrew (official installer from brew.sh)..."
  echo "[VidVortex] This needs internet access. macOS may ask for your password (Command Line Tools / installer)."
  export HOMEBREW_NO_ANALYTICS=1
  NONINTERACTIVE=1 CI=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

ensure_brew_shellenv

if ! command -v brew >/dev/null 2>&1; then
  echo "[Error] Homebrew is still not available on PATH after install." >&2
  echo "        Try closing Terminal, opening a new window, and running RUN_FIRST.command again." >&2
  echo "        Or install manually: https://brew.sh" >&2
  exit 1
fi

BREW_PREFIX="$(brew --prefix)"
if [[ ! -w "$BREW_PREFIX" ]]; then
  echo "[Error] Homebrew’s install folder is not writable by your user:" >&2
  echo "        $BREW_PREFIX" >&2
  echo "" >&2
  echo "This usually happens if brew was run with sudo or ownership changed." >&2
  echo "Fix ownership (run once in Terminal, replace user if needed):" >&2
  echo "        sudo chown -R \"$(whoami)\" \"$BREW_PREFIX\"" >&2
  echo "" >&2
  echo "Then run RUN_FIRST.command again." >&2
  exit 1
fi

echo "[VidVortex] Updating Homebrew and formulae index..."
brew update

echo "[VidVortex] Installing / upgrading Python..."
brew install python
brew upgrade python || echo "[VidVortex] Python already current or upgrade skipped."

echo "[VidVortex] Installing / upgrading yt-dlp..."
brew install yt-dlp
brew upgrade yt-dlp || echo "[VidVortex] yt-dlp already current or upgrade skipped."

echo "[VidVortex] Installing / upgrading ffmpeg..."
brew install ffmpeg
brew upgrade ffmpeg || echo "[VidVortex] ffmpeg already current or upgrade skipped."

ensure_brew_shellenv

if ! command -v yt-dlp >/dev/null 2>&1 || ! command -v ffmpeg >/dev/null 2>&1 || ! command -v python3 >/dev/null 2>&1; then
  echo "[Error] Dependencies were not installed correctly." >&2
  echo "[Hint] Open a new Terminal and run: eval \"\$($(brew --prefix)/bin/brew shellenv)\"" >&2
  exit 1
fi

echo "[VidVortex] Versions on PATH: python3=$(python3 --version 2>&1 | tr -d '\n'), yt-dlp=$(yt-dlp --version 2>/dev/null | head -1 | tr -d '\n'), ffmpeg=$(ffmpeg -version 2>/dev/null | head -1 | tr -d '\n')"
echo "[VidVortex] Dependency setup complete."
echo "[VidVortex] Tools are under Homebrew; keep opening VidVortex via VidVortex.command so PATH includes them."
