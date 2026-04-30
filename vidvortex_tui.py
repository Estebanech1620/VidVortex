#!/usr/bin/env python3
"""Textual terminal UI for VidVortex."""

from __future__ import annotations

import json
import platform
import queue
import re
import shutil
import subprocess
import sys
import threading
import ctypes
from pathlib import Path
from urllib.parse import urlparse


def ensure_textual_installed() -> None:
    try:
        import textual  # noqa: F401
        return
    except ModuleNotFoundError:
        print("The 'textual' package is missing. Installing automatically...")

    install = subprocess.run(
        [sys.executable, "-m", "pip", "install", "textual"],
        text=True,
        capture_output=True,
        check=False,
    )
    if install.returncode == 0:
        return

    subprocess.run(
        [sys.executable, "-m", "ensurepip", "--upgrade"],
        text=True,
        capture_output=True,
        check=False,
    )
    retry = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
        text=True,
        capture_output=True,
        check=False,
    )
    if retry.returncode == 0:
        final = subprocess.run(
            [sys.executable, "-m", "pip", "install", "textual"],
            text=True,
            capture_output=True,
            check=False,
        )
        if final.returncode == 0:
            return

    print("Failed to auto-install 'textual'. Please run:")
    print(f"  {sys.executable} -m pip install textual")
    sys.exit(1)


ensure_textual_installed()

from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Input, Label, Log, ProgressBar, Select, Static


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


def build_os_compatible_video_prefs(selected_quality: int | None = None) -> tuple[str, str]:
    system_name = platform.system().lower()
    if system_name in ("windows", "darwin"):
        if selected_quality is not None:
            selector = (
                f"bestvideo[height={selected_quality}][ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={selected_quality}][ext=mp4]+bestaudio[ext=m4a]/"
                f"best[height<={selected_quality}][ext=mp4]/"
                "best[ext=mp4]"
            )
        else:
            selector = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]"
        sort = "res,ext:mp4:m4a,vcodec:h264,acodec:aac,br"
        return selector, sort

    if selected_quality is not None:
        selector = f"bestvideo[height<={selected_quality}]+bestaudio/best[height<={selected_quality}]/best"
    else:
        selector = "bestvideo+bestaudio/best"
    sort = "res,br"
    return selector, sort


class MetadataLoaded(Message):
    def __init__(self, url: str, video_qualities: list[int], audio_qualities: list[int], error: str = "") -> None:
        super().__init__()
        self.url = url
        self.video_qualities = video_qualities
        self.audio_qualities = audio_qualities
        self.error = error


class DownloadFinished(Message):
    def __init__(self, returncode: int) -> None:
        super().__init__()
        self.returncode = returncode


class DependenciesInstalled(Message):
    def __init__(self, success: bool, details: str) -> None:
        super().__init__()
        self.success = success
        self.details = details


class WorkerError(Message):
    def __init__(self, context: str, details: str) -> None:
        super().__init__()
        self.context = context
        self.details = details


class DependenciesProgress(Message):
    def __init__(self, current: int, total: int, label: str) -> None:
        super().__init__()
        self.current = current
        self.total = total
        self.label = label


class ElevationChoice(Message):
    def __init__(self, allowed: bool) -> None:
        super().__init__()
        self.allowed = allowed


class ElevationPrompt(ModalScreen[bool]):
    CSS = """
    #elevation_dialog {
        width: 70;
        height: 12;
        padding: 1 2;
        border: round $accent;
        background: $panel;
    }
    #elevation_actions {
        margin-top: 1;
        align-horizontal: center;
    }
    #elevation_actions Button {
        width: 18;
        margin-right: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="elevation_dialog"):
            yield Label("Dependencies are missing.", classes="field")
            yield Label("Allow elevated install now?")
            yield Label("Linux/macOS: uses sudo. Windows: uses Admin install attempt.")
            with Horizontal(id="elevation_actions"):
                yield Button("Allow", id="allow", variant="success")
                yield Button("Cancel", id="cancel", variant="error")

    @on(Button.Pressed, "#allow")
    def allow(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(False)


class VidVortexTUI(App):
    TITLE = "VidVortex by Estebanech"
    CSS = """
    Screen {
        layout: vertical;
    }
    #pages {
        height: 1fr;
    }
    #navtabs {
        height: 3;
        align-horizontal: center;
        border-bottom: solid $panel;
    }
    #navtabs Button {
        width: auto;
        min-width: 14;
        height: 3;
        margin: 0 1;
        padding: 0 2;
        background: transparent;
        color: $text-muted;
        border: none;
    }
    #navtabs Button:hover {
        color: $text;
        background: $panel;
    }
    .tab_on {
        background: $panel;
        color: $primary;
        border-bottom: solid $primary;
        text-style: bold;
    }
    #main {
        height: 1fr;
    }
    #topbar {
        height: 1;
        align-horizontal: right;
        padding-right: 1;
    }
    #exit_top {
        width: 3;
        min-width: 3;
        max-width: 3;
        height: 1;
        min-height: 1;
        max-height: 1;
        content-align: center middle;
        background: $error;
        color: $text;
        border: none;
    }
    Button {
        border: none;
        content-align: center middle;
    }
    #left {
        width: 1fr;
        min-width: 38;
        padding: 1 2;
        border: none;
    }
    #right {
        width: 2fr;
        min-width: 48;
        padding: 1;
        border: round $accent;
    }
    #status {
        height: 3;
        border: round $warning;
        padding: 0 1;
        margin-bottom: 1;
    }
    #download_stage {
        height: 2;
        border: round $panel-lighten-1;
        padding: 0 1;
        margin-bottom: 1;
    }
    #actions {
        height: auto;
        margin-top: 1;
        align-horizontal: center;
    }
    #actions Button {
        width: 1fr;
        min-width: 22;
        max-width: 34;
        height: 3;
        margin-bottom: 1;
    }
    #load { background: $primary; color: $text; }
    #start { background: $success; color: $text; }
    #open_downloads { background: $warning; color: $text; }
    #stop { background: $error; color: $text; }
    .form_group {
        width: 1fr;
        margin-bottom: 1;
        padding: 0;
        border: none;
        background: transparent;
    }
    .field {
        width: 1fr;
        height: 1;
        margin-top: 0;
        margin-bottom: 0;
        padding: 0;
        color: $text-muted;
        text-style: none;
    }
    Input {
        width: 1fr;
        margin-top: 0;
        margin-bottom: 0;
        border: none;
    }
    Input:focus {
        border: none;
    }
    Select {
        width: 1fr;
        margin-top: 0;
        margin-bottom: 0;
        border: none;
    }
    Select:focus {
        border: none;
    }
    #quality_hint {
        height: 1;
        margin-top: 0;
        margin-bottom: 0;
        padding: 0;
        color: $text-muted;
    }
    #right Log {
        height: 1fr;
        border: round $accent;
    }
    #howto_tab {
        padding: 2 4;
    }
    #about_tab {
        padding: 2 4;
    }
    #howto_text {
        border: none;
        padding: 0;
    }
    #about_text {
        border: none;
        padding: 0;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
        ("l", "load_qualities", "Load Qualities"),
        ("d", "start_download", "Start Download"),
        ("c", "clear_log", "Clear Log"),
    ]

    downloading = reactive(False)
    video_qualities: list[int] = []
    audio_qualities: list[int] = []
    deps_installing = reactive(False)
    pending_quality_url: str | None = None
    pending_download_command: list[str] | None = None
    pending_install_reason: str | None = None
    loaded_quality_url: str | None = None
    task_total_steps = 4
    _last_download_bucket = -1
    compact_breakpoint = 120

    @staticmethod
    def format_video_quality_label(height: int) -> str:
        names = {
            144: "144p (Very Low)",
            240: "240p (Low)",
            360: "360p (SD)",
            480: "480p (SD+)",
            720: "720p (HD)",
            1080: "1080p (Full HD)",
            1440: "1440p (QHD)",
            2160: "2160p (4K)",
            4320: "4320p (8K)",
        }
        return names.get(height, f"{height}p")

    @staticmethod
    def format_audio_quality_label(abr: int) -> str:
        if abr >= 320:
            tier = "Very High"
        elif abr >= 256:
            tier = "High+"
        elif abr >= 192:
            tier = "High"
        elif abr >= 160:
            tier = "Medium+"
        elif abr >= 128:
            tier = "Medium"
        elif abr >= 96:
            tier = "Speech+"
        else:
            tier = "Low"
        return f"{abr} kbps ({tier})"

    def compose(self) -> ComposeResult:
        with Horizontal(id="topbar"):
            yield Button("X", id="exit_top")
        with Horizontal(id="navtabs"):
            yield Button("Download", id="tab_download", classes="tab_on")
            yield Button("How to use", id="tab_howto")
            yield Button("About", id="tab_about")
        with Vertical(id="pages"):
            with Vertical(id="download_tab"):
                with Horizontal(id="main"):
                    with VerticalScroll(id="left"):
                        with Vertical(classes="form_group"):
                            yield Static("URL", classes="field")
                            yield Input(placeholder="Paste URL", id="url")
                        with Vertical(classes="form_group"):
                            yield Static("Mode", classes="field")
                            yield Select([("Audio", "audio"), ("Video", "video")], id="mode", value="video")
                        with Vertical(classes="form_group"):
                            yield Static("Quality", classes="field")
                            yield Select([("Best Available", "best")], id="quality", value="best")
                            yield Static("Load qualities to choose your download quality.", id="quality_hint")
                        with Vertical(classes="form_group"):
                            yield Static("Profile", classes="field")
                            yield Select(
                                [("Fast", "fast"), ("Safe", "safe"), ("Stealth", "stealth")],
                                id="profile",
                                value="safe",
                            )
                        with Vertical(classes="form_group"):
                            yield Static("Extra options", classes="field")
                            yield Select(
                                [
                                    ("Best available defaults", "best"),
                                    ("Use saved defaults from settings", "saved"),
                                ],
                                id="preset_mode",
                                value="best",
                            )
                        with Vertical(id="actions"):
                            yield Button("Load Qualities", id="load", variant="primary")
                            yield Button("Download Now", id="start", variant="success")
                            yield Button("Open Downloads Folder", id="open_downloads")
                            yield Button("Stop", id="stop", variant="error")
                    with Vertical(id="right"):
                        yield Static("Status: Idle", id="status")
                        yield Static("Download stage: waiting", id="download_stage")
                        yield ProgressBar(total=100, id="download_progress")
                        yield ProgressBar(total=4, id="task_progress")
                        yield ProgressBar(total=2, id="dep_progress")
                        yield Log(id="log", auto_scroll=True, highlight=True)
            with VerticalScroll(id="howto_tab"):
                yield Static(
                    "How to use VidVortex:\n\n"
                    "1) Paste link\n"
                    "2) Select mode\n"
                    "3) Load qualities\n"
                    "4) Select quality\n"
                    "5) Download",
                    id="howto_text",
                )
            with VerticalScroll(id="about_tab"):
                yield Static(
                    "About VidVortex\n\n"
                    "Developed by Estebanech\n"
                    "Portfolio: estebanech.com\n\n"
                    "Powered by yt-dlp and ffmpeg.\n\n"
                    "I built this with the intention of always saving the best quality\n"
                    "audio or video of things I loved, without using sketchy websites\n"
                    "full of ads.",
                    id="about_text",
                )

    def on_mount(self) -> None:
        self.log_info("VidVortex is ready.")
        self.log_info("Tip: press 'l' to load video qualities.")
        self.log_info("Press Ctrl+Q to exit.")
        self.query_one("#start", Button).display = False
        self.query_one("#download_progress", ProgressBar).display = False
        self.query_one("#task_progress", ProgressBar).display = False
        self.query_one("#dep_progress", ProgressBar).display = False
        self._set_active_page("download")
        self._apply_responsive_layout(self.size.width)
        self.set_timer(0.08, lambda: self._apply_responsive_layout(self.size.width))

    def _set_active_page(self, page: str) -> None:
        download = self.query_one("#download_tab", Vertical)
        howto = self.query_one("#howto_tab", VerticalScroll)
        about = self.query_one("#about_tab", VerticalScroll)
        btn_download = self.query_one("#tab_download", Button)
        btn_howto = self.query_one("#tab_howto", Button)
        btn_about = self.query_one("#tab_about", Button)

        download.display = page == "download"
        howto.display = page == "howto"
        about.display = page == "about"

        btn_download.set_class(page == "download", "tab_on")
        btn_howto.set_class(page == "howto", "tab_on")
        btn_about.set_class(page == "about", "tab_on")

    def on_resize(self) -> None:
        self._apply_responsive_layout(self.size.width)

    def _apply_responsive_layout(self, width: int) -> None:
        main = self.query_one("#main", Horizontal)
        left = self.query_one("#left", VerticalScroll)
        right = self.query_one("#right", Vertical)

        if width < self.compact_breakpoint:
            main.styles.layout = "vertical"
            left.styles.width = "1fr"
            right.styles.width = "1fr"
            left.styles.min_width = 0
            right.styles.min_width = 0
            left.styles.height = "auto"
            right.styles.height = "1fr"
            self.query_one("#status", Static).update("Status: Compact layout enabled.")
            return

        main.styles.layout = "horizontal"
        left.styles.width = "1fr"
        right.styles.width = "2fr"
        left.styles.min_width = 42
        right.styles.min_width = 52
        left.styles.height = "1fr"
        right.styles.height = "1fr"

    def action_clear_log(self) -> None:
        self.query_one("#log", Log).clear()

    def log_info(self, message: str) -> None:
        self.query_one("#log", Log).write_line(f"[info] {message}")

    def log_success(self, message: str) -> None:
        self.query_one("#log", Log).write_line(f"[ok] {message}")

    def log_warn(self, message: str) -> None:
        self.query_one("#log", Log).write_line(f"[warn] {message}")

    def log_error(self, message: str) -> None:
        self.query_one("#log", Log).write_line(f"[error] {message}")

    def start_task_progress(self, status: str, total: int | None = None) -> None:
        bar = self.query_one("#task_progress", ProgressBar)
        bar.display = True
        bar.update(total=total or self.task_total_steps, progress=0)
        self.query_one("#status", Static).update(status)

    def set_task_progress(self, step: int, status: str) -> None:
        bar = self.query_one("#task_progress", ProgressBar)
        bar.update(progress=step)
        self.query_one("#status", Static).update(status)

    def end_task_progress(self) -> None:
        self.query_one("#task_progress", ProgressBar).display = False

    def start_download_progress(self) -> None:
        self._last_download_bucket = -1
        self.query_one("#download_stage", Static).update("Download stage: starting")
        bar = self.query_one("#download_progress", ProgressBar)
        bar.display = True
        bar.update(total=100, progress=0)

    def set_download_progress(self, percent: float, speed: str = "", eta: str = "") -> None:
        pct = max(0.0, min(100.0, percent))
        self.query_one("#download_progress", ProgressBar).update(progress=pct)
        label = f"Download stage: transferring ({pct:.1f}%)"
        if speed:
            label += f" at {speed}"
        if eta:
            label += f" | ETA {eta}"
        self.query_one("#download_stage", Static).update(label)

        bucket = int(pct // 10)
        if bucket > self._last_download_bucket:
            self._last_download_bucket = bucket
            self.log_info(f"Download progress: {int(pct)}%")

    def set_download_stage(self, text: str) -> None:
        self.query_one("#download_stage", Static).update(f"Download stage: {text}")

    def end_download_progress(self) -> None:
        self.query_one("#download_progress", ProgressBar).display = False

    def action_load_qualities(self) -> None:
        self.start_quality_fetch()

    def action_start_download(self) -> None:
        self.start_download()

    @on(Button.Pressed, "#load")
    def click_load(self) -> None:
        self.start_quality_fetch()

    @on(Button.Pressed, "#start")
    def click_start(self) -> None:
        self.start_download()

    @on(Button.Pressed, "#stop")
    def click_stop(self) -> None:
        if hasattr(self, "_proc") and self._proc and self._proc.poll() is None:
            self._proc.terminate()
            self.query_one("#status", Static).update("Status: Stopping...")
            self.query_one("#log", Log).write_line("Termination requested.")

    @on(Button.Pressed, "#open_downloads")
    def click_open_downloads(self) -> None:
        folder = resolve_desktop_dir() / "VidVortex"
        folder.mkdir(parents=True, exist_ok=True)
        try:
            system_name = platform.system().lower()
            if system_name == "windows":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif system_name == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
            self.log_info(f"Opened downloads folder: {folder}")
            self.notify("Opened downloads folder.", severity="information")
        except Exception as exc:
            self.log_error(f"Failed to open downloads folder: {exc}")
            self.notify("Could not open downloads folder.", severity="error")

    @on(Button.Pressed, "#exit_top")
    def click_exit(self) -> None:
        self.exit()

    @on(Button.Pressed, "#tab_download")
    def click_tab_download(self) -> None:
        self._set_active_page("download")

    @on(Button.Pressed, "#tab_howto")
    def click_tab_howto(self) -> None:
        self._set_active_page("howto")

    @on(Button.Pressed, "#tab_about")
    def click_tab_about(self) -> None:
        self._set_active_page("about")

    @on(Select.Changed, "#mode")
    def mode_changed(self, event: Select.Changed) -> None:
        mode = str(event.value)
        if mode == "audio":
            self.query_one("#status", Static).update("Status: Audio mode (best audio).")
        else:
            self.query_one("#status", Static).update("Status: Video mode. Load qualities first.")
        self.update_quality_options(mode)

    @on(Input.Changed, "#url")
    def url_changed(self, _: Input.Changed) -> None:
        self.loaded_quality_url = None
        self.query_one("#start", Button).display = False
        self.query_one("#quality_hint", Static).update("Load qualities to choose your download quality.")

    def _current_url(self) -> str:
        return self.query_one("#url", Input).value.strip()

    def _validate_url(self, url: str) -> tuple[bool, str]:
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
        if (parsed.hostname or "").lower() == "localhost":
            return False, "Localhost URLs are not allowed."
        return True, ""

    def start_quality_fetch(self) -> None:
        url = self._current_url()
        if not url:
            self.notify("Paste a URL first.", severity="warning")
            return
        ok, reason = self._validate_url(url)
        if not ok:
            self.log_error(f"Invalid URL: {reason}")
            self.notify(reason, severity="error")
            return
        self.loaded_quality_url = None
        self.query_one("#start", Button).display = False
        self.query_one("#quality_hint", Static).update("Scanning available qualities for this video...")
        self.start_task_progress("Status: Preparing quality scan...", total=3)
        self.set_task_progress(1, "Status: Checking dependencies...")
        missing = self._missing_dependencies()
        if missing:
            self.pending_quality_url = url
            self.pending_install_reason = "quality"
            self.log_warn("Missing dependencies detected: " + ", ".join(missing) + ". Auto-installing...")
            self.push_screen(ElevationPrompt(), self._on_elevation_choice)
            return
        self.set_task_progress(2, "Status: Fetching video metadata...")
        self.fetch_qualities_worker(url)

    @work(thread=True)
    def fetch_qualities_worker(self, url: str) -> None:
        try:
            cmd = ["yt-dlp", "-J", "--no-playlist", url]
            try:
                result = subprocess.run(cmd, text=True, capture_output=True, check=False)
            except FileNotFoundError:
                self.post_message(
                    MetadataLoaded(url, [], [], "yt-dlp is missing. Dependencies will be auto-installed.")
                )
                return
            if result.returncode != 0:
                self.post_message(MetadataLoaded(url, [], [], result.stderr.strip() or "Failed to load metadata"))
                return

            payload = json.loads(result.stdout)
            formats = payload.get("formats") or []
            heights = sorted(
                {
                    int(f.get("height"))
                    for f in formats
                    if isinstance(f.get("height"), int) and f.get("vcodec") not in (None, "none")
                },
                reverse=True,
            )
            audio_abrs = sorted(
                {
                    int(f.get("abr"))
                    for f in formats
                    if isinstance(f.get("abr"), (int, float))
                    and f.get("acodec") not in (None, "none")
                    and f.get("vcodec") in (None, "none")
                    and int(f.get("abr")) > 0
                },
                reverse=True,
            )
            self.post_message(MetadataLoaded(url, heights, audio_abrs))
        except Exception as exc:
            self.post_message(WorkerError("load qualities", str(exc)))

    @on(MetadataLoaded)
    def on_metadata_loaded(self, event: MetadataLoaded) -> None:
        log = self.query_one("#log", Log)
        if event.error:
            self.query_one("#status", Static).update("Status: Failed to load qualities.")
            log.write_line(f"[error] {event.error}")
            self.notify(event.error, severity="error")
            self.query_one("#quality_hint", Static).update("Could not load qualities. Fix issue and try again.")
            self.end_task_progress()
            return
        self.loaded_quality_url = event.url
        self.video_qualities = event.video_qualities
        self.audio_qualities = event.audio_qualities
        mode = str(self.query_one("#mode", Select).value)
        default_label = self.update_quality_options(mode)
        self.query_one("#start", Button).display = True
        self.query_one("#quality_hint", Static).update(
            f"Choose your desired quality, then press Download Now. Default: {default_label}."
        )
        self.set_task_progress(3, "Status: Qualities loaded.")
        if self.video_qualities:
            self.log_success("Video qualities: " + ", ".join(f"{q}p" for q in self.video_qualities))
        else:
            self.log_warn("No video qualities detected for this URL.")
        if self.audio_qualities:
            self.log_success("Audio qualities: " + ", ".join(f"{q} kbps" for q in self.audio_qualities))
        else:
            self.log_warn("No audio bitrate list detected; best available will still be used.")
        self.end_task_progress()

    def update_quality_options(self, mode: str) -> str:
        quality_select = self.query_one("#quality", Select)
        if mode == "audio":
            best_audio = self.format_audio_quality_label(self.audio_qualities[0]) if self.audio_qualities else "best audio"
            options: list[tuple[str, str]] = [(f"Best Available (auto: {best_audio})", "best")]
            options += [(self.format_audio_quality_label(abr), f"a{abr}") for abr in self.audio_qualities]
            quality_select.set_options(options)
            quality_select.value = "best"
            return best_audio
        else:
            best_video = self.format_video_quality_label(self.video_qualities[0]) if self.video_qualities else "best video"
            options = [(f"Best Available (auto: {best_video})", "best")]
            options += [(self.format_video_quality_label(q), f"v{q}") for q in self.video_qualities]
            quality_select.set_options(options)
            quality_select.value = "best"
            return best_video

    def _install_with_cmd(self, cmd: list[str], timeout: int = 1800) -> bool:
        try:
            result = subprocess.run(cmd, text=True, capture_output=True, check=False, timeout=timeout)
            if result.returncode != 0:
                stderr = (result.stderr or "").strip()
                stdout = (result.stdout or "").strip()
                details = stderr or stdout or "unknown error"
                self.call_from_thread(
                    self.query_one("#log", Log).write_line,
                    f"[install][failed] {' '.join(cmd)} -> {details}",
                )
                return False
            self.call_from_thread(
                self.query_one("#log", Log).write_line,
                f"[install][ok] {' '.join(cmd)}",
            )
            return True
        except Exception as exc:
            self.call_from_thread(
                self.query_one("#log", Log).write_line,
                f"[install][exception] {' '.join(cmd)} -> {exc}",
            )
            return False

    def _missing_dependencies(self) -> list[str]:
        return [name for name in ("yt-dlp", "ffmpeg") if shutil.which(name) is None]

    def _run_windows_elevated(self, command: list[str]) -> bool:
        quoted = subprocess.list2cmdline(command)
        ps_cmd = (
            "Start-Process -FilePath cmd.exe "
            f"-ArgumentList '/c {quoted}' -Verb RunAs -Wait"
        )
        return self._install_with_cmd(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=3600)

    def _auto_install_dependency(self, dependency: str, elevated: bool = False) -> bool:
        system_name = platform.system().lower()
        if system_name == "windows":
            commands = {
                "yt-dlp": [
                    [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
                    ["winget", "install", "--id", "yt-dlp.yt-dlp", "--scope", "user", "--silent", "--accept-source-agreements", "--accept-package-agreements"],
                    ["winget", "install", "--id", "yt-dlp.yt-dlp", "--silent", "--accept-source-agreements", "--accept-package-agreements"],
                    ["choco", "install", "yt-dlp", "-y"],
                    ["scoop", "install", "yt-dlp"],
                ],
                "ffmpeg": [
                    ["winget", "install", "--id", "Gyan.FFmpeg", "--scope", "user", "--silent", "--accept-source-agreements", "--accept-package-agreements"],
                    ["winget", "install", "--id", "Gyan.FFmpeg", "--silent", "--accept-source-agreements", "--accept-package-agreements"],
                    ["choco", "install", "ffmpeg", "-y"],
                    ["scoop", "install", "ffmpeg"],
                ],
            }
            for cmd in commands.get(dependency, []):
                if shutil.which(cmd[0]) and self._install_with_cmd(cmd):
                    return True
                if elevated and shutil.which(cmd[0]) and self._run_windows_elevated(cmd):
                    return True
            return False

        if system_name == "darwin":
            if not shutil.which("brew"):
                if dependency == "yt-dlp":
                    return self._install_with_cmd([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])
                return False
            pkg = "yt-dlp" if dependency == "yt-dlp" else "ffmpeg"
            cmd = ["brew", "install", pkg]
            if elevated and shutil.which("sudo"):
                cmd = ["sudo"] + cmd
            return self._install_with_cmd(cmd)

        if system_name == "linux":
            if shutil.which("apt-get"):
                pkg = "yt-dlp" if dependency == "yt-dlp" else "ffmpeg"
                prefix = ["sudo"] if elevated and shutil.which("sudo") else []
                return self._install_with_cmd(prefix + ["apt-get", "update"]) and self._install_with_cmd(
                    prefix + ["apt-get", "install", "-y", pkg]
                )
            if shutil.which("dnf"):
                pkg = "yt-dlp" if dependency == "yt-dlp" else "ffmpeg"
                prefix = ["sudo"] if elevated and shutil.which("sudo") else []
                return self._install_with_cmd(prefix + ["dnf", "install", "-y", pkg])
            if shutil.which("pacman"):
                pkg = "yt-dlp" if dependency == "yt-dlp" else "ffmpeg"
                prefix = ["sudo"] if elevated and shutil.which("sudo") else []
                return self._install_with_cmd(prefix + ["pacman", "-Sy", "--noconfirm", pkg])
            if shutil.which("zypper"):
                pkg = "yt-dlp" if dependency == "yt-dlp" else "ffmpeg"
                prefix = ["sudo"] if elevated and shutil.which("sudo") else []
                return self._install_with_cmd(prefix + ["zypper", "--non-interactive", "install", pkg])
            if dependency == "yt-dlp":
                return self._install_with_cmd([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])
            return False

        return False

    def _on_elevation_choice(self, allowed: bool) -> None:
        if not allowed:
            self.query_one("#status", Static).update("Status: Dependency install cancelled.")
            self.log_warn("Dependency install cancelled by user.")
            self.pending_quality_url = None
            self.pending_download_command = None
            self.end_task_progress()
            return
        self.log_info("Elevation approved. Starting dependency install...")
        self.start_dependency_install(use_elevation=True)

    def start_dependency_install(self, use_elevation: bool = False) -> None:
        if self.downloading:
            self.notify("Stop active download before installing dependencies.", severity="warning")
            return
        if self.deps_installing:
            return
        self._use_elevation = use_elevation
        self.deps_installing = True
        self.query_one("#status", Static).update("Status: Installing dependencies...")
        bar = self.query_one("#dep_progress", ProgressBar)
        bar.display = True
        bar.update(total=2, progress=0)
        self.install_dependencies_worker()

    @work(thread=True)
    def install_dependencies_worker(self) -> None:
        missing = self._missing_dependencies()
        if not missing:
            self.post_message(DependenciesInstalled(True, "All dependencies are already installed."))
            return

        details: list[str] = []
        success = True
        total = len(missing)
        current = 0
        for dep in missing:
            current += 1
            self.post_message(DependenciesProgress(current, total, f"Installing {dep}..."))
            ok = self._auto_install_dependency(dep, elevated=getattr(self, "_use_elevation", False))
            success = success and ok and shutil.which(dep) is not None
            details.append(f"{dep}: {'installed' if ok else 'failed'}")

        self.post_message(DependenciesInstalled(success, " | ".join(details)))

    @on(DependenciesProgress)
    def on_dependencies_progress(self, event: DependenciesProgress) -> None:
        bar = self.query_one("#dep_progress", ProgressBar)
        bar.update(total=max(event.total, 1), progress=event.current)
        self.query_one("#status", Static).update(f"Status: {event.label}")

    @on(DependenciesInstalled)
    def on_dependencies_installed(self, event: DependenciesInstalled) -> None:
        self.deps_installing = False
        bar = self.query_one("#dep_progress", ProgressBar)
        bar.display = False
        self.log_info("Dependency install result: " + event.details)
        if event.success:
            self.query_one("#status", Static).update("Status: Dependencies ready.")
            self.notify("Dependencies are ready.", severity="information")
            if self.pending_quality_url:
                url = self.pending_quality_url
                self.pending_quality_url = None
                self.start_quality_fetch_for_url(url)
            if self.pending_download_command:
                command = self.pending_download_command
                self.pending_download_command = None
                self.query_one("#status", Static).update("Status: Download running...")
                self.downloading = True
                self.download_worker(command)
        else:
            self.query_one("#status", Static).update("Status: Dependency install failed.")
            self.notify("Some dependencies failed to install. Check logs.", severity="error")
            self.pending_quality_url = None
            self.pending_download_command = None
            self.end_task_progress()

    def start_quality_fetch_for_url(self, url: str) -> None:
        self.query_one("#status", Static).update("Status: Loading qualities...")
        self.fetch_qualities_worker(url)

    def start_download(self) -> None:
        if self.downloading:
            self.notify("A download is already running.", severity="warning")
            return
        url = self._current_url()
        if not url:
            self.notify("Paste a URL first.", severity="warning")
            return
        ok, reason = self._validate_url(url)
        if not ok:
            self.log_error(f"Invalid URL: {reason}")
            self.notify(reason, severity="error")
            return
        if self.loaded_quality_url != url:
            self.notify("Load qualities first for this URL.", severity="warning")
            self.query_one("#status", Static).update("Status: Load qualities before downloading.")
            return
        self.start_task_progress("Status: Preparing download...", total=4)
        self.set_task_progress(1, "Status: Validating input...")

        mode = str(self.query_one("#mode", Select).value)
        profile = str(self.query_one("#profile", Select).value)
        preset_mode = str(self.query_one("#preset_mode", Select).value)
        quality = str(self.query_one("#quality", Select).value)

        command = self._build_download_command(
            url=url,
            mode=mode,
            profile=profile,
            quality=quality,
            preset_mode=preset_mode,
        )

        self.set_task_progress(2, "Status: Checking dependencies...")
        missing = self._missing_dependencies()
        if missing:
            self.pending_download_command = command
            self.pending_install_reason = "download"
            self.log_warn("Missing dependencies detected: " + ", ".join(missing) + ". Auto-installing...")
            self.push_screen(ElevationPrompt(), self._on_elevation_choice)
            return

        self.set_task_progress(3, "Status: Download running...")
        self.start_download_progress()
        self.log_info("Running: " + " ".join(command))
        self.downloading = True
        self.download_worker(command)

    def _handle_download_line(self, line: str) -> None:
        text = line.strip()
        if not text:
            return

        if "[download]" in text:
            pct_match = re.search(r"(\d+(?:\.\d+)?)%", text)
            speed_match = re.search(r" at ([^ ]+)", text)
            eta_match = re.search(r"ETA ([^ ]+)", text)
            if pct_match:
                pct = float(pct_match.group(1))
                speed = speed_match.group(1) if speed_match else ""
                eta = eta_match.group(1) if eta_match else ""
                self.set_download_progress(pct, speed=speed, eta=eta)
                return
            if "Destination:" in text:
                self.set_download_stage("writing destination file")
                self.log_info("Preparing destination file.")
                return
            if "100%" in text and " in " in text:
                self.set_download_stage("download completed, finalizing")
                return
            return

        if text.startswith("[Merger]"):
            self.set_download_stage("merging video and audio")
            self.log_info("Merging streams.")
            return
        if text.startswith("Deleting original file"):
            self.set_download_stage("cleaning temporary files")
            return

        self.query_one("#log", Log).write_line(text)

    def _build_download_command(
        self,
        *,
        url: str,
        mode: str,
        profile: str,
        quality: str,
        preset_mode: str,
    ) -> list[str]:
        script_path = Path(__file__).resolve().parent / "vidvortex.py"
        is_frozen = bool(getattr(sys, "frozen", False))
        if script_path.exists() and not is_frozen:
            command = [sys.executable, str(script_path), url, "--mode", mode, "--profile", profile]
            if mode == "video" and quality.startswith("v") and quality[1:].isdigit():
                command += ["--quality", quality[1:]]
            if mode == "audio" and quality.startswith("a") and quality[1:].isdigit():
                command += ["--audio-abr", quality[1:]]
            if preset_mode == "saved":
                command += ["--config-location", "yt-dlp.conf.example"]
            return command

        # Fallback for packaged EXE: run yt-dlp directly to avoid EXE self-recursion.
        self.log_warn("Running packaged fallback mode for download engine.")
        download_root = resolve_desktop_dir() / "VidVortex"
        target_dir = download_root / ("audio" if mode == "audio" else "video")
        target_dir.mkdir(parents=True, exist_ok=True)
        out_template = str(target_dir / "%(title)s.%(ext)s")

        common = ["yt-dlp", "--no-playlist", "--newline", "--retries", "10", "--fragment-retries", "10"]
        if mode == "audio":
            fmt = "bestaudio/best"
            if quality.startswith("a") and quality[1:].isdigit():
                fmt = f"bestaudio[abr<={quality[1:]}]/bestaudio/best"
            return common + ["-f", fmt, "--extract-audio", "--audio-format", "best", "-o", out_template, url]

        if quality.startswith("v") and quality[1:].isdigit():
            q = quality[1:]
            fmt, sort_selector = build_os_compatible_video_prefs(int(q))
        else:
            fmt, sort_selector = build_os_compatible_video_prefs(None)
        return common + [
            "-f",
            fmt,
            "-S",
            sort_selector,
            "--merge-output-format",
            "mp4",
            "-o",
            out_template,
            url,
        ]

    @work(thread=True)
    def download_worker(self, command: list[str]) -> None:
        try:
            log_queue: queue.Queue[str] = queue.Queue()

            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(Path(__file__).resolve().parent),
            )
            self._proc = proc

            def reader() -> None:
                if proc.stdout is None:
                    return
                for line in proc.stdout:
                    log_queue.put(line.rstrip())

            read_thread = threading.Thread(target=reader, daemon=True)
            read_thread.start()

            while proc.poll() is None or not log_queue.empty():
                try:
                    line = log_queue.get(timeout=0.2)
                    self.call_from_thread(self._handle_download_line, line)
                except queue.Empty:
                    continue

            code = proc.returncode or 0
            self.post_message(DownloadFinished(code))
        except Exception as exc:
            self.post_message(WorkerError("download", str(exc)))

    @on(DownloadFinished)
    def on_download_finished(self, event: DownloadFinished) -> None:
        self.downloading = False
        if event.returncode == 0:
            self.set_task_progress(4, "Status: Download completed.")
            self.set_download_progress(100.0)
            self.set_download_stage("completed")
            self.log_success("Download finished successfully.")
            self.notify("Download completed.", severity="information")
        else:
            self.query_one("#status", Static).update("Status: Download failed.")
            self.set_download_stage("failed")
            self.log_error(f"Download failed (exit {event.returncode}).")
            self.notify("Download failed. Check logs panel.", severity="error")
        self.end_task_progress()
        self.end_download_progress()

    @on(WorkerError)
    def on_worker_error(self, event: WorkerError) -> None:
        self.downloading = False
        self.query_one("#status", Static).update(f"Status: {event.context} failed.")
        self.set_download_stage("failed")
        self.log_error(f"{event.context}: {event.details}")
        self.notify(f"{event.context} failed. Check logs panel.", severity="error")
        self.end_task_progress()
        self.end_download_progress()
        if "yt-dlp is missing" in event.details.lower() or "ffmpeg is missing" in event.details.lower():
            self.start_dependency_install()


if __name__ == "__main__":
    VidVortexTUI().run()
