#!/usr/bin/env python3
"""VidVortex Beast Pack downloader."""

from __future__ import annotations

import argparse
import ctypes
import ipaddress
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

DEFAULT_TIMEOUT = 900
MIN_FILE_SIZE_BYTES = 1024


class ProfileResolutionError(ValueError):
    """Profile JSON missing, invalid, or requested profile name is unknown."""


USER_MESSAGE_YOUTUBE_METADATA_FAILED = (
    "YouTube lookup failed. On Download, under Are cookies uploaded?, pick your browser, "
    "then tap Load Qualities again. If it still fails, open the YouTube cookies tab and upload your cookies."
)


class MetadataFetchError(RuntimeError):
    """Metadata fetch failed (non-zero exit or invalid JSON payload).

    ``technical`` is logged on the CLI (full yt-dlp detail). The desktop GUI uses ``user_summary``
    and can omit dumping ``technical`` into the Activity log when ``silent_gui_log`` is True.
    """

    def __init__(
        self,
        technical: str,
        *,
        user_summary: str | None = None,
        silent_gui_log: bool = False,
    ) -> None:
        super().__init__(technical)
        self.technical = technical
        self.user_summary = user_summary if user_summary is not None else technical
        self.silent_gui_log = silent_gui_log

    def __str__(self) -> str:
        return self.technical


def _yt_dlp_error_hint(details: str) -> str:
    text = (details or "").lower()
    if "failed to decrypt with dpapi" in text:
        return (
            "\n\nWindows could not decrypt Chrome/Chromium/Edge cookies (DPAPI). This is common; "
            "Firefox often still works with cookies-from-browser because it does not use the same storage.\n"
            "- Try selecting Firefox in the app (log into YouTube in Firefox first).\n"
            "- Or use a cookies.txt file from your browser (see yt-dlp wiki for exporting).\n"
            "- Run as a normal user (not Administrator), and fully quit Chrome/Edge/Brave, then retry if you must use them."
        )
    if "sign in to confirm you" in text or "cookies-from-browser or --cookies" in text:
        return (
            "\n\nYouTube is asking for a logged-in session (bot check). This can start happening even "
            "when it used to work — YouTube and yt-dlp change over time; VidVortex did not cause this.\n"
            "- In the app: Browser & cookies → select the browser where you are logged into YouTube, "
            "or set a cookies.txt path.\n"
            "- Update yt-dlp often: run `yt-dlp -U` (or reinstall via winget/pip).\n"
            "- Try another network if you use VPN/datacenter IP; residential IPs hit this less often."
        )
    return ""


RATE_LIMIT_PATTERNS = (
    "429",
    "too many requests",
    "rate limit",
    "http error 403",
    "temporarily unavailable",
)

DEFAULT_PROFILES: dict[str, dict[str, Any]] = {
    "fast": {
        "retries": 5,
        "fragment_retries": 5,
        "retry_sleep": "exp=1:8",
        "fragment_retry_sleep": "fragment:exp=1:8",
        "sleep_requests": 0.0,
        "min_sleep_interval": 0.0,
        "max_sleep_interval": 0.0,
        "use_aria2c": True,
    },
    "safe": {
        "retries": 10,
        "fragment_retries": 10,
        "retry_sleep": "exp=1:20",
        "fragment_retry_sleep": "fragment:exp=1:20",
        "sleep_requests": 1.0,
        "min_sleep_interval": 1.0,
        "max_sleep_interval": 3.0,
        "use_aria2c": False,
    },
    "stealth": {
        "retries": 15,
        "fragment_retries": 15,
        "retry_sleep": "exp=1:30",
        "fragment_retry_sleep": "fragment:exp=1:30",
        "sleep_requests": 2.0,
        "min_sleep_interval": 2.0,
        "max_sleep_interval": 6.0,
        "use_aria2c": False,
    },
}

DEFAULT_SETTINGS: dict[str, Any] = {
    "default_mode": "ask",
    "audio_default": "best_available",
    "video_default": "best_available",
    "video_fixed_quality": 1080,
    "profile": "safe",
    "use_aria2c": None,
    "subtitles": "none",
    "subtitle_langs": "en.*,es.*,.*",
    "sponsorblock_remove": "",
    "add_metadata": False,
    "embed_thumbnail": False,
    "check_updates": False,
    "cookies_file": "",
    "cookies_from_browser": "",
    "cookies_locked_browser": "",
}


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool


@dataclass
class RuntimeProfile:
    retries: int
    fragment_retries: int
    retry_sleep: str
    fragment_retry_sleep: str
    sleep_requests: float
    min_sleep_interval: float
    max_sleep_interval: float
    use_aria2c: bool


@dataclass
class RuntimeState:
    throttle_level: int = 0


ProgressLineCallback = Callable[[str], None]


@dataclass
class DownloadController:
    cancel_requested: bool = False
    active_process: subprocess.Popen[str] | None = None

    def request_cancel(self) -> None:
        self.cancel_requested = True
        proc = self.active_process
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass


def _subprocess_run_kwargs() -> dict[str, Any]:
    """On Windows, avoid flashing a new console for each CLI child (GUI apps)."""
    if sys.platform != "win32":
        return {}
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if not flags:
        return {}
    return {"creationflags": flags}


def setup_logging(logfile: Path | None) -> None:
    """Configure root logger. If logfile is None, only console (or no handlers if no stdout)."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    if sys.stdout is not None and getattr(sys.stdout, "write", None) is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if logfile is not None:
        logfile.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(logfile, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def execute_command(
    command: list[str],
    timeout_seconds: int,
    *,
    on_output_line: ProgressLineCallback | None = None,
    cancel_controller: DownloadController | None = None,
) -> CommandResult:
    if on_output_line is not None:
        output_lines: list[str] = []
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            **_subprocess_run_kwargs(),
        )
        if cancel_controller is not None:
            cancel_controller.active_process = process
        try:
            assert process.stdout is not None
            for line in iter(process.stdout.readline, ""):
                if cancel_controller is not None and cancel_controller.cancel_requested:
                    process.kill()
                    return CommandResult(
                        returncode=130,
                        stdout="\n".join(output_lines).strip(),
                        stderr="Download cancelled by user.",
                        timed_out=False,
                    )
                clean = (line or "").rstrip("\r\n")
                if not clean:
                    continue
                output_lines.append(clean)
                on_output_line(clean)
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            return CommandResult(
                returncode=124,
                stdout="\n".join(output_lines).strip(),
                stderr=f"Command timed out after {timeout_seconds} seconds",
                timed_out=True,
            )
        except Exception as err:
            process.kill()
            return CommandResult(
                returncode=1,
                stdout="\n".join(output_lines).strip(),
                stderr=str(err),
                timed_out=False,
            )
        finally:
            if cancel_controller is not None:
                cancel_controller.active_process = None
        return CommandResult(
            returncode=int(process.returncode or 0),
            stdout="\n".join(output_lines).strip(),
            stderr="",
            timed_out=False,
        )

    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
            **_subprocess_run_kwargs(),
        )
        return CommandResult(
            returncode=completed.returncode,
            stdout=(completed.stdout or "").strip(),
            stderr=(completed.stderr or "").strip(),
            timed_out=False,
        )
    except subprocess.TimeoutExpired as err:
        return CommandResult(
            returncode=124,
            stdout=((err.stdout or "") if err.stdout else "").strip(),
            stderr=((err.stderr or "") if err.stderr else "").strip(),
            timed_out=True,
        )


def run_command_with_retry(
    command: list[str],
    *,
    timeout_seconds: int,
    max_attempts: int = 2,
    adjust_callback: Any | None = None,
    on_output_line: ProgressLineCallback | None = None,
    cancel_controller: DownloadController | None = None,
) -> CommandResult:
    last: CommandResult | None = None
    for attempt in range(1, max_attempts + 1):
        result = execute_command(
            command,
            timeout_seconds,
            on_output_line=on_output_line,
            cancel_controller=cancel_controller,
        )
        if result.returncode == 0 and not result.timed_out:
            return result
        last = result
        if cancel_controller is not None and cancel_controller.cancel_requested:
            return result
        if adjust_callback is not None:
            adjust_callback(result)
        logging.warning(
            "Command failed (attempt %s/%s)%s: %s",
            attempt,
            max_attempts,
            " [timeout]" if result.timed_out else "",
            " ".join(command),
        )
        if result.stderr:
            logging.warning(result.stderr)
    if last is None:
        raise RuntimeError("Internal error: missing command result")
    return last


def ensure_required_dependency(command_name: str) -> None:
    if shutil.which(command_name) is None:
        logging.warning("Missing dependency: %s", command_name)
        should_install = True
        if sys.stdin is not None and sys.stdin.isatty():
            while True:
                choice = input(
                    f"'{command_name}' is required but missing. Install it now so VidVortex can continue? (y/n): "
                ).strip().lower()
                if choice in ("y", "yes"):
                    should_install = True
                    break
                if choice in ("n", "no"):
                    should_install = False
                    break
                print("Please enter y or n.")
        if not should_install:
            logging.error("%s is required. Exiting because installation was declined.", command_name)
            sys.exit(1)

        logging.info("Attempting automatic install for %s...", command_name)
        if auto_install_dependency(command_name) and shutil.which(command_name) is not None:
            logging.info("%s installed successfully.", command_name)
            return
        logging.error("%s is not installed or not in PATH.", command_name)
        sys.exit(1)


def check_dependency(command_name: str) -> bool:
    return shutil.which(command_name) is not None


def auto_install_dependency(command_name: str) -> bool:
    system_name = platform.system().lower()

    if system_name == "darwin":
        if not check_dependency("brew"):
            logging.error("Homebrew is required for auto-install on macOS.")
            return False
        package_map = {"yt-dlp": "yt-dlp", "ffmpeg": "ffmpeg"}
        package = package_map.get(command_name)
        if not package:
            return False
        result = execute_command(["brew", "install", package], timeout_seconds=1800)
        if result.returncode != 0:
            if result.stderr:
                logging.error(result.stderr)
            return False
        return True

    if system_name == "windows":
        install_commands: dict[str, list[list[str]]] = {
            "yt-dlp": [
                ["winget", "install", "--id", "yt-dlp.yt-dlp", "--silent", "--accept-source-agreements", "--accept-package-agreements"],
                ["choco", "install", "yt-dlp", "-y"],
                ["scoop", "install", "yt-dlp"],
            ],
            "ffmpeg": [
                ["winget", "install", "--id", "Gyan.FFmpeg", "--silent", "--accept-source-agreements", "--accept-package-agreements"],
                ["choco", "install", "ffmpeg", "-y"],
                ["scoop", "install", "ffmpeg"],
            ],
        }
        candidates = install_commands.get(command_name, [])
        for cmd in candidates:
            if not check_dependency(cmd[0]):
                continue
            result = execute_command(cmd, timeout_seconds=1800)
            if result.returncode == 0:
                return True
        return False

    if system_name == "linux":
        install_commands: dict[str, list[list[str]]] = {
            "yt-dlp": [
                ["apt-get", "update"],
                ["apt-get", "install", "-y", "yt-dlp"],
            ],
            "ffmpeg": [
                ["apt-get", "update"],
                ["apt-get", "install", "-y", "ffmpeg"],
            ],
        }

        if check_dependency("apt-get"):
            for cmd in install_commands.get(command_name, []):
                result = execute_command(["sudo"] + cmd, timeout_seconds=1800)
                if result.returncode != 0:
                    return False
            return True

        if check_dependency("dnf"):
            pkg = "yt-dlp" if command_name == "yt-dlp" else "ffmpeg"
            result = execute_command(["sudo", "dnf", "install", "-y", pkg], timeout_seconds=1800)
            return result.returncode == 0

        if check_dependency("pacman"):
            pkg = "yt-dlp" if command_name == "yt-dlp" else "ffmpeg"
            result = execute_command(["sudo", "pacman", "-Sy", "--noconfirm", pkg], timeout_seconds=1800)
            return result.returncode == 0

        if check_dependency("zypper"):
            pkg = "yt-dlp" if command_name == "yt-dlp" else "ffmpeg"
            result = execute_command(["sudo", "zypper", "--non-interactive", "install", pkg], timeout_seconds=1800)
            return result.returncode == 0

        logging.error("No supported Linux package manager found for auto-install.")
        return False

    logging.error("Auto-install is currently supported on macOS, Windows, and Linux.")
    return False


def sanitize_title(value: str) -> str:
    clean = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in value).strip("_")
    return clean or "video"


def resolve_desktop_dir() -> Path:
    if platform.system().lower() == "windows":
        try:
            CSIDL_DESKTOPDIRECTORY = 0x0010
            buffer = ctypes.create_unicode_buffer(260)
            result = ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOPDIRECTORY, None, 0, buffer)
            if result == 0 and buffer.value:
                candidate = Path(buffer.value)
                if candidate.exists():
                    return candidate
        except Exception:
            pass

    return Path.home() / "Desktop"


def resolve_app_config_dir() -> Path:
    """User home app data (e.g. settings). Media downloads use Desktop/VidVortex only."""
    return Path.home() / ".vidvortex"


def resolve_settings_path() -> Path:
    return resolve_app_config_dir() / "settings.json"


def migrate_legacy_settings_if_needed() -> None:
    """If settings.json still lives under Desktop/VidVortex, move it to ~/.vidvortex once."""
    new_path = resolve_settings_path()
    legacy_path = resolve_desktop_dir() / "VidVortex" / "settings.json"
    if new_path.exists() or not legacy_path.is_file():
        return
    try:
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(legacy_path), str(new_path))
    except OSError as exc:
        logging.warning("Could not migrate settings from %s to %s: %s", legacy_path, new_path, exc)


def validate_url(url: str) -> tuple[bool, str]:
    candidate = (url or "").strip()
    if not candidate:
        return False, "URL is empty."
    if len(candidate) > 2048:
        return False, "URL is too long."

    parsed = urlparse(candidate)
    if parsed.scheme not in ("http", "https"):
        return False, "Only http/https URLs are allowed."
    if not parsed.netloc:
        return False, "URL host is missing."

    hostname = parsed.hostname or ""
    lowered = hostname.lower()
    if lowered in ("localhost",):
        return False, "Localhost URLs are not allowed."

    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            return False, "Private or local network IP URLs are not allowed."
    except ValueError:
        # Non-IP hostnames are fine.
        pass

    return True, ""


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.with_name(f"{path.stem}_{stamp}{path.suffix}")


def format_size(num_bytes: int) -> str:
    size = float(max(0, num_bytes))
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{num_bytes} B"


def get_available_heights(formats: list[dict[str, Any]]) -> list[int]:
    """Unique video heights, highest first (for UI + prompts)."""
    heights: set[int] = set()
    for fmt in formats:
        raw_h = fmt.get("height")
        if raw_h is None:
            continue
        try:
            h = int(float(raw_h))
        except (TypeError, ValueError):
            continue
        if h <= 0:
            continue
        if fmt.get("vcodec") in (None, "none"):
            continue
        # Some extractors omit format_id on merged or legacy entries; height + vcodec is enough.
        heights.add(h)
    return sorted(heights, reverse=True)


def build_os_compatible_video_prefs(selected_quality: int) -> tuple[str, str]:
    system_name = platform.system().lower()
    if system_name in ("windows", "darwin"):
        selector = (
            f"bestvideo[height={selected_quality}][ext=mp4]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={selected_quality}][ext=mp4]+bestaudio[ext=m4a]/"
            f"best[height<={selected_quality}][ext=mp4]/"
            "best[ext=mp4]"
        )
        sort = "res,ext:mp4:m4a,vcodec:h264,acodec:aac,br"
        return selector, sort

    # Linux players are generally broader with codec/container support.
    selector = (
        f"bestvideo[height={selected_quality}]+bestaudio/"
        f"best[height<={selected_quality}]/"
        "best"
    )
    sort = "res,br"
    return selector, sort


def prompt_mode() -> str:
    while True:
        print("\nWhat do you want to download?")
        print("1) Audio")
        print("2) Video (you will choose available quality)")
        value = input("Enter 1 or 2: ").strip().lower()
        if value in ("1", "a", "audio"):
            return "audio"
        if value in ("2", "v", "video"):
            return "video"
        print("Invalid selection.")


def prompt_url() -> str:
    while True:
        value = input("Paste video URL: ").strip()
        if value:
            return value
        print("URL cannot be empty.")


def prompt_quality(heights: list[int]) -> int:
    print("\nAvailable qualities:")
    for idx, h in enumerate(heights, start=1):
        print(f"{idx}) {h}p")
    while True:
        value = input("Choose quality by number: ").strip()
        if value.isdigit():
            num = int(value)
            if 1 <= num <= len(heights):
                return heights[num - 1]
        print("Invalid selection.")


def prompt_yes_no(message: str, default: bool = False) -> bool:
    suffix = "Y/n" if default else "y/N"
    while True:
        value = input(f"{message} ({suffix}): ").strip().lower()
        if not value:
            return default
        if value in ("y", "yes"):
            return True
        if value in ("n", "no"):
            return False
        print("Please enter y or n.")


def load_settings(settings_path: Path) -> dict[str, Any]:
    settings = dict(DEFAULT_SETTINGS)
    if not settings_path.exists():
        return settings
    try:
        loaded = json.loads(settings_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            settings.update(loaded)
    except Exception:
        logging.warning("Settings file is invalid, using defaults: %s", settings_path)
    return settings


def save_settings(settings_path: Path, settings: dict[str, Any]) -> None:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def open_options_menu(settings: dict[str, Any], settings_path: Path) -> None:
    while True:
        print("\n=== VidVortex Options ===")
        print(f"1) Default mode: {settings['default_mode']}")
        print(f"2) Audio default: {settings['audio_default']}")
        print(f"3) Video default: {settings['video_default']}")
        print(f"4) Video fixed quality: {settings['video_fixed_quality']}p")
        print(f"5) Profile: {settings['profile']}")
        print(f"6) Use aria2c: {settings['use_aria2c']}")
        print(f"7) Subtitles: {settings['subtitles']}")
        print(f"8) Subtitle languages: {settings['subtitle_langs']}")
        print(f"9) SponsorBlock remove: {settings['sponsorblock_remove'] or '(off)'}")
        print(f"10) Add metadata: {settings['add_metadata']}")
        print(f"11) Embed thumbnail: {settings['embed_thumbnail']}")
        print(f"12) Check updates on run: {settings['check_updates']}")
        print("13) Save and return")
        choice = input("Select option to edit (1-13): ").strip()

        if choice == "1":
            raw = input("Default mode [ask/audio/video]: ").strip().lower()
            if raw in ("ask", "audio", "video"):
                settings["default_mode"] = raw
        elif choice == "2":
            raw = input("Audio default [best_available/general_options]: ").strip().lower()
            if raw in ("best_available", "general_options"):
                settings["audio_default"] = raw
        elif choice == "3":
            raw = input("Video default [ask_quality/best_available/fixed_quality]: ").strip().lower()
            if raw in ("ask_quality", "best_available", "fixed_quality"):
                settings["video_default"] = raw
        elif choice == "4":
            raw = input("Video fixed quality (e.g. 1080): ").strip()
            if raw.isdigit() and int(raw) > 0:
                settings["video_fixed_quality"] = int(raw)
        elif choice == "5":
            raw = input("Profile [fast/safe/stealth]: ").strip().lower()
            if raw in ("fast", "safe", "stealth"):
                settings["profile"] = raw
        elif choice == "6":
            raw = input("Use aria2c [auto/on/off]: ").strip().lower()
            if raw == "auto":
                settings["use_aria2c"] = None
            elif raw == "on":
                settings["use_aria2c"] = True
            elif raw == "off":
                settings["use_aria2c"] = False
        elif choice == "7":
            raw = input("Subtitles [none/download/embed]: ").strip().lower()
            if raw in ("none", "download", "embed"):
                settings["subtitles"] = raw
        elif choice == "8":
            raw = input("Subtitle languages (yt-dlp format): ").strip()
            if raw:
                settings["subtitle_langs"] = raw
        elif choice == "9":
            settings["sponsorblock_remove"] = input(
                "SponsorBlock categories (blank to disable): "
            ).strip()
        elif choice == "10":
            settings["add_metadata"] = prompt_yes_no("Enable metadata embedding?", settings["add_metadata"])
        elif choice == "11":
            settings["embed_thumbnail"] = prompt_yes_no("Enable thumbnail embedding?", settings["embed_thumbnail"])
        elif choice == "12":
            settings["check_updates"] = prompt_yes_no("Enable update check by default?", settings["check_updates"])
        elif choice == "13":
            save_settings(settings_path, settings)
            print("Options saved.")
            return
        else:
            print("Invalid selection.")


def load_profiles(profile_file: str | None) -> dict[str, dict[str, Any]]:
    profiles = json.loads(json.dumps(DEFAULT_PROFILES))
    if not profile_file:
        return profiles
    path = Path(profile_file).expanduser()
    if not path.exists():
        raise ProfileResolutionError(f"Profile file not found: {path}")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("Profile file must contain a JSON object.")
    except ProfileResolutionError:
        raise
    except Exception as exc:
        raise ProfileResolutionError(f"Invalid profile file: {exc}") from exc
    for key, value in loaded.items():
        if isinstance(value, dict):
            current = profiles.get(key, {})
            current.update(value)
            profiles[key] = current
    return profiles


def resolve_runtime_profile(args: argparse.Namespace) -> RuntimeProfile:
    profiles = load_profiles(args.profile_file)
    name = str(args.profile)
    selected = profiles.get(name)
    if selected is None:
        valid = ", ".join(sorted(profiles.keys()))
        raise ProfileResolutionError(f"Unknown profile {name!r}. Valid profiles: {valid}")

    retries = int(args.retries if args.retries is not None else selected["retries"])
    fragment_retries = int(
        args.fragment_retries if args.fragment_retries is not None else selected["fragment_retries"]
    )
    retry_sleep = str(args.retry_sleep if args.retry_sleep is not None else selected["retry_sleep"])
    fragment_retry_sleep = str(
        args.fragment_retry_sleep if args.fragment_retry_sleep is not None else selected["fragment_retry_sleep"]
    )
    sleep_requests = float(
        args.sleep_requests if args.sleep_requests is not None else selected["sleep_requests"]
    )
    min_sleep_interval = float(
        args.min_sleep_interval if args.min_sleep_interval is not None else selected["min_sleep_interval"]
    )
    max_sleep_interval = float(
        args.max_sleep_interval if args.max_sleep_interval is not None else selected["max_sleep_interval"]
    )
    use_aria2c = bool(args.use_aria2c if args.use_aria2c is not None else selected["use_aria2c"])

    return RuntimeProfile(
        retries=retries,
        fragment_retries=fragment_retries,
        retry_sleep=retry_sleep,
        fragment_retry_sleep=fragment_retry_sleep,
        sleep_requests=sleep_requests,
        min_sleep_interval=min_sleep_interval,
        max_sleep_interval=max_sleep_interval,
        use_aria2c=use_aria2c,
    )


def resolve_config_path(config_location: str) -> Path:
    """Resolve yt-dlp config path for script, frozen EXE (PyInstaller), or absolute paths."""
    path = Path(config_location).expanduser()
    if path.is_file():
        return path
    beside = Path(__file__).resolve().parent / path.name
    if beside.is_file():
        return beside
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled = Path(sys._MEIPASS) / path.name
        if bundled.is_file():
            return bundled
    return path


def build_yt_dlp_base(
    config_location: str | None,
    *,
    omit_missing_config: bool = False,
) -> list[str]:
    base = ["yt-dlp"]
    if not config_location:
        return base
    config_path = resolve_config_path(config_location)
    if not config_path.is_file():
        msg = f"Config file does not exist: {config_path}"
        if omit_missing_config:
            logging.warning("%s — continuing without --config-location", msg)
            return base
        logging.error(msg)
        sys.exit(1)
    base += ["--config-location", str(config_path.resolve())]
    return base


def append_yt_dlp_cookie_flags(cmd: list[str], args: Any) -> list[str]:
    """Append yt-dlp cookie options when set on args (cookies file wins over browser)."""
    raw_file = getattr(args, "cookies_file", None)
    if raw_file:
        path = Path(str(raw_file).strip()).expanduser()
        if path.is_file():
            return cmd + ["--cookies", str(path.resolve())]
        logging.warning("Cookies file not found, skipping --cookies: %s", path)

    browser = getattr(args, "cookies_from_browser", None)
    if browser:
        b = str(browser).strip()
        if b and b.lower() not in ("none", "off"):
            return cmd + ["--cookies-from-browser", b]
    return cmd


def build_common_flags(
    profile: RuntimeProfile,
    *,
    state: RuntimeState,
    use_aria2c_effective: bool,
) -> list[str]:
    flags = [
        "--no-playlist",
        "--newline",
        "--retries",
        str(profile.retries + state.throttle_level),
        "--fragment-retries",
        str(profile.fragment_retries + state.throttle_level),
        "--retry-sleep",
        profile.retry_sleep,
        "--retry-sleep",
        profile.fragment_retry_sleep,
    ]

    sleep_requests = profile.sleep_requests + state.throttle_level
    min_sleep = profile.min_sleep_interval + state.throttle_level
    max_sleep = profile.max_sleep_interval + state.throttle_level
    if sleep_requests > 0:
        flags += ["--sleep-requests", str(sleep_requests)]
    if min_sleep > 0:
        flags += ["--min-sleep-interval", str(min_sleep)]
    if max_sleep > 0:
        flags += ["--max-sleep-interval", str(max_sleep)]

    if use_aria2c_effective:
        flags += ["--downloader", "aria2c", "--downloader-args", "aria2c:-x 16 -s 16 -k 1M"]
    return flags


def maybe_adjust_throttle(state: RuntimeState, result: CommandResult) -> None:
    text = f"{result.stderr}\n{result.stdout}".lower()
    if any(token in text for token in RATE_LIMIT_PATTERNS):
        state.throttle_level = min(state.throttle_level + 1, 5)
        logging.warning("Adaptive throttling escalated to level %s.", state.throttle_level)
    elif state.throttle_level > 0:
        state.throttle_level -= 1


def build_media_flags(args: argparse.Namespace) -> list[str]:
    flags: list[str] = []
    if args.add_metadata:
        flags.append("--add-metadata")
    if args.embed_thumbnail:
        flags += ["--embed-thumbnail", "--convert-thumbnails", "jpg"]

    if args.sponsorblock_remove:
        flags += ["--sponsorblock-remove", args.sponsorblock_remove]

    if args.subtitles in ("download", "embed"):
        flags += ["--write-subs", "--write-auto-subs", "--sub-langs", args.subtitle_langs]
        if args.subtitles == "embed":
            flags.append("--embed-subs")
    return flags


def get_metadata(
    url: str,
    *,
    yt_dlp_base: list[str],
    timeout_seconds: int,
) -> dict[str, Any]:
    result = run_command_with_retry(
        yt_dlp_base + ["-J", "--no-playlist", url],
        timeout_seconds=timeout_seconds,
        max_attempts=2,
    )
    if result.returncode != 0:
        details = result.stderr or result.stdout or "Unknown yt-dlp error."
        technical = (
            f"Failed to fetch metadata for URL: {url}\n"
            f"yt-dlp exited with code {result.returncode}: {details}"
            f"{_yt_dlp_error_hint(details)}"
        )
        raise MetadataFetchError(
            technical,
            user_summary=USER_MESSAGE_YOUTUBE_METADATA_FAILED,
            silent_gui_log=True,
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        snippet = (result.stdout or "").strip()
        snippet = snippet[:300] + ("..." if len(snippet) > 300 else "")
        technical = f"Could not parse metadata JSON. Raw output: {snippet or '<empty>'}"
        raise MetadataFetchError(
            technical,
            user_summary=USER_MESSAGE_YOUTUBE_METADATA_FAILED,
            silent_gui_log=True,
        )


def find_output_file(download_dir: Path, before: set[Path]) -> Path:
    after = set(download_dir.glob("*"))
    created = [p for p in (after - before) if p.is_file()]
    if not created:
        logging.error("No output file was created.")
        sys.exit(1)
    created.sort(key=lambda p: p.stat().st_mtime)
    return created[-1]


def validate_with_ffprobe(path: Path, expected_mode: str, timeout_seconds: int) -> None:
    if not path.exists() or path.stat().st_size < MIN_FILE_SIZE_BYTES:
        logging.error("Output file missing or too small: %s", path)
        sys.exit(1)

    if not check_dependency("ffprobe"):
        logging.warning("ffprobe not found; skipping deep validation.")
        return

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type",
        "-of",
        "json",
        str(path),
    ]
    result = execute_command(cmd, timeout_seconds)
    if result.returncode != 0 or result.timed_out:
        logging.error("ffprobe validation failed for %s", path)
        sys.exit(1)

    try:
        payload = json.loads(result.stdout)
        duration = float(payload.get("format", {}).get("duration") or 0.0)
        streams = payload.get("streams") or []
    except Exception:
        logging.error("Invalid ffprobe output for %s", path)
        sys.exit(1)

    if duration <= 0:
        logging.error("Invalid output duration for %s", path)
        sys.exit(1)

    stream_types = {str(s.get("codec_type")) for s in streams}
    if expected_mode == "audio" and "audio" not in stream_types:
        logging.error("Audio stream missing in output: %s", path)
        sys.exit(1)
    if expected_mode == "video" and "video" not in stream_types:
        logging.error("Video stream missing in output: %s", path)
        sys.exit(1)


def remux_faststart(source_file: Path, target_file: Path, timeout_seconds: int) -> Path:
    target_file = unique_path(target_file)
    fast_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_file),
        "-map",
        "0",
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        str(target_file),
    ]
    fast_result = execute_command(fast_cmd, timeout_seconds)
    if fast_result.returncode == 0 and not fast_result.timed_out:
        return target_file

    fallback_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_file),
        "-map",
        "0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(target_file),
    ]
    fallback = execute_command(fallback_cmd, timeout_seconds)
    if fallback.returncode != 0 or fallback.timed_out:
        logging.error("ffmpeg remux failed for %s", source_file)
        if fallback.stderr:
            logging.error(fallback.stderr)
        sys.exit(1)
    return target_file


def check_for_update_hint(timeout_seconds: int) -> None:
    result = execute_command(["yt-dlp", "--version"], timeout_seconds)
    if result.returncode != 0 or not result.stdout:
        return
    version = result.stdout.splitlines()[0].strip()
    try:
        release_date = datetime.strptime(version, "%Y.%m.%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return
    days_old = (datetime.now(timezone.utc) - release_date).days
    if days_old > 90:
        logging.info("yt-dlp version is %s days old (%s). Consider updating.", days_old, version)


def diagnose(args: argparse.Namespace) -> int:
    checks = {
        "python": bool(sys.version_info >= (3, 9)),
        "yt-dlp": check_dependency("yt-dlp"),
        "ffmpeg": check_dependency("ffmpeg"),
        "ffprobe": check_dependency("ffprobe"),
        "aria2c": check_dependency("aria2c"),
    }
    print("VidVortex Diagnose")
    for name, ok in checks.items():
        print(f"- {name}: {'OK' if ok else 'MISSING'}")

    if args.config_location:
        config_path = Path(args.config_location).expanduser()
        print(f"- config-location: {'OK' if config_path.exists() else 'MISSING'} ({config_path})")

    if not checks["yt-dlp"]:
        print("Action: Install yt-dlp and add it to PATH.")
    if not checks["ffmpeg"]:
        print("Action: Install ffmpeg and add it to PATH.")
    if not checks["python"]:
        print("Action: Use Python 3.9+.")
    if not checks["aria2c"]:
        print("Note: aria2c acceleration is optional.")
    return 0 if checks["python"] and checks["yt-dlp"] and checks["ffmpeg"] else 1


def open_log_file(path: Path) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        logging.info("Log file saved at: %s", path)


def load_queue(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logging.error("Failed to read queue file: %s", exc)
        sys.exit(1)
    if not isinstance(data, list):
        logging.error("Queue file must contain a JSON array.")
        sys.exit(1)
    return [item for item in data if isinstance(item, dict) and item.get("url")]


def save_queue(path: Path, queue: list[dict[str, Any]]) -> None:
    path.write_text(json.dumps(queue, indent=2), encoding="utf-8")


def process_one(
    *,
    url: str,
    forced_mode: str | None,
    forced_quality: int | None,
    args: argparse.Namespace,
    profile: RuntimeProfile,
    state: RuntimeState,
    audio_dir: Path,
    video_dir: Path,
    yt_dlp_base: list[str],
    allow_video_override_prompt: bool = False,
    progress_callback: ProgressLineCallback | None = None,
    cancel_controller: DownloadController | None = None,
) -> Path:
    ok, reason = validate_url(url)
    if not ok:
        logging.error("Invalid URL: %s", reason)
        sys.exit(1)

    try:
        metadata = get_metadata(url, yt_dlp_base=yt_dlp_base, timeout_seconds=args.timeout)
    except MetadataFetchError as exc:
        logging.error("%s", exc)
        sys.exit(1)
    title = sanitize_title(str(metadata.get("title") or "video"))
    heights = get_available_heights(metadata.get("formats") or [])

    mode = forced_mode or args.mode or prompt_mode()
    if mode == "audio" and args.audio_default == "best_available":
        media_flags = []
    else:
        media_flags = build_media_flags(args)
    aria2c_ok = profile.use_aria2c and check_dependency("aria2c")
    if profile.use_aria2c and not aria2c_ok:
        logging.warning("aria2c requested but not installed; falling back to yt-dlp internal downloader.")

    common_flags = build_common_flags(profile, state=state, use_aria2c_effective=aria2c_ok)
    target_dir = audio_dir if mode == "audio" else video_dir
    before = set(target_dir.glob("*"))
    out_template = str(target_dir / "%(title)s.%(ext)s")

    if mode == "audio":
        audio_selector = "bestaudio/best"
        if isinstance(args.audio_abr, int) and args.audio_abr > 0:
            audio_selector = f"bestaudio[abr<={args.audio_abr}]/bestaudio/best"
        command = (
            yt_dlp_base
            + common_flags
            + media_flags
            + [
                "-f",
                audio_selector,
                "-S",
                "acodec:aac,abr",
                "--extract-audio",
                "--audio-format",
                "best",
                "-o",
                out_template,
                url,
            ]
        )
        result = run_command_with_retry(
            command,
            timeout_seconds=args.timeout,
            max_attempts=2,
            adjust_callback=lambda r: maybe_adjust_throttle(state, r),
            on_output_line=progress_callback,
            cancel_controller=cancel_controller,
        )
        if result.returncode != 0:
            if cancel_controller is not None and cancel_controller.cancel_requested:
                logging.error("Download cancelled by user.")
                sys.exit(130)
            logging.error("Audio download failed for: %s", url)
            sys.exit(1)
        output = find_output_file(target_dir, before)
        validate_with_ffprobe(output, "audio", args.timeout)
        return output

    if not heights:
        logging.error("No video formats available for URL: %s", url)
        sys.exit(1)

    selected_quality = forced_quality if forced_quality in heights else None
    if forced_quality is not None and selected_quality is None:
        logging.warning("Requested quality %sp unavailable; prompting selection.", forced_quality)

    if selected_quality is None and args.quality in heights:
        selected_quality = args.quality

    if selected_quality is None and args.video_default == "best_available":
        selected_quality = max(heights)
        if allow_video_override_prompt and sys.stdin is not None and sys.stdin.isatty():
            use_best = prompt_yes_no(
                f"Use best available quality ({selected_quality}p)?",
                default=True,
            )
            if not use_best:
                selected_quality = prompt_quality(heights)
    elif selected_quality is None and args.video_default == "fixed_quality":
        fixed = args.video_fixed_quality
        if fixed in heights:
            selected_quality = fixed
        else:
            lower = [h for h in heights if h <= fixed]
            selected_quality = max(lower) if lower else max(heights)
            logging.warning(
                "Fixed quality %sp unavailable; using closest available %sp.",
                fixed,
                selected_quality,
            )

    if selected_quality not in heights:
        if sys.stdin is not None and sys.stdin.isatty():
            selected_quality = prompt_quality(heights)
        else:
            selected_quality = max(heights)
            logging.warning(
                "Requested quality unavailable in non-interactive mode; using best available %sp.",
                selected_quality,
            )

    format_selector, sort_selector = build_os_compatible_video_prefs(selected_quality)
    command = (
        yt_dlp_base
        + common_flags
        + media_flags
        + [
            "-f",
            format_selector,
            "-S",
            sort_selector,
            "--merge-output-format",
            "mp4",
            "-o",
            out_template,
            url,
        ]
    )
    result = run_command_with_retry(
        command,
        timeout_seconds=args.timeout,
        max_attempts=2,
        adjust_callback=lambda r: maybe_adjust_throttle(state, r),
        on_output_line=progress_callback,
        cancel_controller=cancel_controller,
    )
    if result.returncode != 0:
        if cancel_controller is not None and cancel_controller.cancel_requested:
            logging.error("Download cancelled by user.")
            sys.exit(130)
        logging.error("Video download failed for: %s", url)
        sys.exit(1)

    source = find_output_file(target_dir, before)
    if source.suffix.lower() == ".mp4":
        final = source
    else:
        target = target_dir / f"{source.stem}.mp4"
        final = remux_faststart(source, target, args.timeout)
        if final != source:
            source.unlink(missing_ok=True)
    validate_with_ffprobe(final, "video", args.timeout)
    return final


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VidVortex Beast Pack")
    parser.add_argument("url", nargs="?", help="Video URL")
    parser.add_argument("--mode", choices=["audio", "video"], help="Force mode")
    parser.add_argument("--quality", type=int, help="Video quality height for video mode")
    parser.add_argument("--audio-abr", type=int, help="Audio bitrate target in kbps (e.g. 192)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Per-command timeout in seconds")
    parser.add_argument("--config-location", help="Optional yt-dlp config path")
    parser.add_argument("--profile", choices=["fast", "safe", "stealth"], default="safe", help="Runtime profile")
    parser.add_argument("--profile-file", help="Optional JSON profile override file")
    parser.add_argument("--use-aria2c", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--retries", type=int, help="Override profile retries")
    parser.add_argument("--fragment-retries", type=int, help="Override profile fragment retries")
    parser.add_argument("--retry-sleep", help="Override profile retry sleep strategy")
    parser.add_argument("--fragment-retry-sleep", help="Override profile fragment retry sleep strategy")
    parser.add_argument("--sleep-requests", type=float, help="Override profile sleep-requests value")
    parser.add_argument("--min-sleep-interval", type=float, help="Override profile min sleep interval")
    parser.add_argument("--max-sleep-interval", type=float, help="Override profile max sleep interval")
    parser.add_argument("--subtitles", choices=["none", "download", "embed"], default="none")
    parser.add_argument("--subtitle-langs", default="en.*,es.*,.*")
    parser.add_argument("--sponsorblock-remove", help="SponsorBlock categories, e.g. sponsor,intro,outro,selfpromo")
    parser.add_argument("--add-metadata", action="store_true")
    parser.add_argument("--embed-thumbnail", action="store_true")
    parser.add_argument("--queue-file", help="Path to JSON queue file (array of items)")
    parser.add_argument("--resume-queue", action="store_true", help="Skip queue items already marked done")
    parser.add_argument("--diagnose", action="store_true", help="Run environment diagnostics and exit")
    parser.add_argument("--check-updates", action="store_true", help="Show yt-dlp staleness hint")
    parser.add_argument("--no-open-log", action="store_true")
    parser.add_argument(
        "--cookies-from-browser",
        default=None,
        metavar="BROWSER",
        help="yt-dlp: load cookies from browser profile (e.g. chrome, firefox, edge)",
    )
    parser.add_argument(
        "--cookies-file",
        dest="cookies_file",
        default=None,
        metavar="PATH",
        help="yt-dlp: Netscape-format cookies file (--cookies)",
    )
    return parser.parse_args()


def cli_has_flag(*flags: str) -> bool:
    return any(flag in sys.argv for flag in flags)


def apply_settings_defaults(args: argparse.Namespace, settings: dict[str, Any]) -> None:
    if not cli_has_flag("--mode"):
        default_mode = settings.get("default_mode")
        args.mode = default_mode if default_mode in ("audio", "video") else None
    if not cli_has_flag("--profile"):
        args.profile = str(settings.get("profile", args.profile))
    if args.use_aria2c is None and settings.get("use_aria2c") in (True, False):
        args.use_aria2c = bool(settings["use_aria2c"])
    if not cli_has_flag("--subtitles"):
        args.subtitles = str(settings.get("subtitles", args.subtitles))
    if not cli_has_flag("--subtitle-langs"):
        args.subtitle_langs = str(settings.get("subtitle_langs", args.subtitle_langs))
    if args.sponsorblock_remove is None and settings.get("sponsorblock_remove"):
        args.sponsorblock_remove = str(settings["sponsorblock_remove"])
    if not cli_has_flag("--add-metadata") and bool(settings.get("add_metadata")):
        args.add_metadata = True
    if not cli_has_flag("--embed-thumbnail") and bool(settings.get("embed_thumbnail")):
        args.embed_thumbnail = True
    if not cli_has_flag("--check-updates") and bool(settings.get("check_updates")):
        args.check_updates = True

    if args.cookies_from_browser is None and not cli_has_flag("--cookies-from-browser"):
        cb = str(settings.get("cookies_from_browser") or "").strip()
        args.cookies_from_browser = cb or None
    if args.cookies_file is None and not cli_has_flag("--cookies-file"):
        cf = str(settings.get("cookies_file") or "").strip()
        args.cookies_file = cf or None

    args.audio_default = str(settings.get("audio_default", "best_available"))
    args.video_default = str(settings.get("video_default", "best_available"))
    args.video_fixed_quality = int(settings.get("video_fixed_quality", 1080))


def main() -> None:
    args = parse_args()
    if args.diagnose:
        sys.exit(diagnose(args))

    settings_path = resolve_settings_path()
    setup_logging(None)
    migrate_legacy_settings_if_needed()
    base_dir = resolve_desktop_dir() / "VidVortex"
    audio_dir = base_dir / "audio"
    video_dir = base_dir / "video"
    base_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    settings = load_settings(settings_path)
    apply_settings_defaults(args, settings)

    ensure_required_dependency("yt-dlp")
    ensure_required_dependency("ffmpeg")

    if args.check_updates:
        check_for_update_hint(args.timeout)

    try:
        profile = resolve_runtime_profile(args)
    except ProfileResolutionError as exc:
        logging.error("%s", exc)
        sys.exit(1)
    state = RuntimeState()
    yt_dlp_base = append_yt_dlp_cookie_flags(build_yt_dlp_base(args.config_location), args)
    start = time.time()

    results: list[tuple[str, str, str]] = []
    if args.queue_file:
        queue_path = Path(args.queue_file).expanduser()
        if not queue_path.exists():
            logging.error("Queue file not found: %s", queue_path)
            sys.exit(1)
        queue = load_queue(queue_path)
        for item in queue:
            status = str(item.get("status") or "pending")
            if args.resume_queue and status == "done":
                continue
            url = str(item.get("url") or "").strip()
            mode = str(item.get("mode") or "") or None
            quality = item.get("quality")
            quality_num = int(quality) if isinstance(quality, int) else None
            try:
                output = process_one(
                    url=url,
                    forced_mode=mode,
                    forced_quality=quality_num,
                    args=args,
                    profile=profile,
                    state=state,
                    audio_dir=audio_dir,
                    video_dir=video_dir,
                    yt_dlp_base=yt_dlp_base,
                    allow_video_override_prompt=False,
                )
                item["status"] = "done"
                item["output"] = str(output)
                item["error"] = ""
                saved_size = format_size(output.stat().st_size) if output.exists() else "unknown size"
                results.append((url, "done", f"{output} ({saved_size})"))
            except SystemExit as exc:
                item["status"] = "failed"
                item["error"] = f"exit {exc.code}"
                results.append((url, "failed", item["error"]))
            finally:
                save_queue(queue_path, queue)
    else:
        if not args.url:
            while True:
                print("\n=== VidVortex ===")
                print("1) Download")
                print("2) Options")
                print("3) Exit")
                home_choice = input("Select 1-3: ").strip()
                if home_choice == "1":
                    break
                if home_choice == "2":
                    open_options_menu(settings, settings_path)
                    settings = load_settings(settings_path)
                    apply_settings_defaults(args, settings)
                    continue
                if home_choice == "3":
                    return
                print("Invalid selection.")

        url = (args.url or prompt_url()).strip()
        if not url:
            logging.error("No URL provided.")
            sys.exit(1)
        mode = args.mode or prompt_mode()
        output = process_one(
            url=url,
            forced_mode=mode,
            forced_quality=None,
            args=args,
            profile=profile,
            state=state,
            audio_dir=audio_dir,
            video_dir=video_dir,
            yt_dlp_base=yt_dlp_base,
            allow_video_override_prompt=True,
        )
        saved_size = format_size(output.stat().st_size) if output.exists() else "unknown size"
        results.append((url, "done", f"{output} ({saved_size})"))

    elapsed = round(time.time() - start, 2)
    done_count = sum(1 for _, status, _ in results if status == "done")
    failed_count = sum(1 for _, status, _ in results if status == "failed")
    logging.info("Run completed in %ss | done=%s failed=%s", elapsed, done_count, failed_count)
    for url, status, detail in results:
        logging.info("[%s] %s -> %s", status, url, detail)


if __name__ == "__main__":
    main()
