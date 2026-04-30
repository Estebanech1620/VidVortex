#!/usr/bin/env bash
set -euo pipefail

echo "[VidVortex] Linux dependency setup starting..."

need_cmd() {
  if command -v "$1" >/dev/null 2>&1; then
    echo "[VidVortex] $1 already exists on PATH."
    return 1
  fi
  return 0
}

install_with_apt() {
  sudo apt-get update
  sudo apt-get install -y python3 python3-pip yt-dlp ffmpeg
}

install_with_dnf() {
  sudo dnf install -y python3 python3-pip yt-dlp ffmpeg
}

install_with_pacman() {
  sudo pacman -Sy --noconfirm python python-pip yt-dlp ffmpeg
}

install_with_zypper() {
  sudo zypper --non-interactive install python3 python3-pip yt-dlp ffmpeg
}

update_yt_dlp_only() {
  echo "[VidVortex] Updating yt-dlp to latest package-manager version (recommended for YouTube)..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y yt-dlp
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf upgrade -y yt-dlp || sudo dnf install -y yt-dlp
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm yt-dlp
  elif command -v zypper >/dev/null 2>&1; then
    sudo zypper --non-interactive refresh
    sudo zypper --non-interactive install -y yt-dlp
  else
    echo "[VidVortex] No supported package manager to refresh yt-dlp; upgrade yt-dlp manually if needed." >&2
  fi
}

if need_cmd python3 || need_cmd yt-dlp || need_cmd ffmpeg; then
  if command -v apt-get >/dev/null 2>&1; then
    install_with_apt
  elif command -v dnf >/dev/null 2>&1; then
    install_with_dnf
  elif command -v pacman >/dev/null 2>&1; then
    install_with_pacman
  elif command -v zypper >/dev/null 2>&1; then
    install_with_zypper
  else
    echo "[Error] Supported package manager not found (apt, dnf, pacman, zypper)." >&2
    exit 1
  fi
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "[Error] Python 3 was not installed correctly." >&2
  exit 1
fi

if ! command -v yt-dlp >/dev/null 2>&1 || ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[Error] Dependencies were not installed correctly." >&2
  exit 1
fi

update_yt_dlp_only

echo "[VidVortex] Dependency setup complete."
echo "[VidVortex] Installed in standard Linux package-manager locations (PATH)."
