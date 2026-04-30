#!/usr/bin/env python3
"""VidVortex desktop GUI (no terminal UI)."""

from __future__ import annotations

import os
import platform
import re
import subprocess
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from tkinter import font as tkfont
from types import SimpleNamespace

import ttkbootstrap as tb
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.widgets.scrolled import ScrolledText

import vidvortex as engine

# Dark modern themes: "darkly", "superhero", "cyborg", "vapor" (see ttkbootstrap docs).
APP_THEME = "darkly"


TEXT_PRIMARY = "#ffffff"
TEXT_SOFT = "#f0f4f8"
COOKIE_UPLOAD_BADGE_GREEN = "#3ecf8e"

_BROWSER_SIGNIN_TITLE = "Are cookies uploaded?"
_BROWSER_COOKIES_UPLOADED_BADGE = "YouTube Cookies Uploaded"
_BROWSER_COOKIES_SUCCESS_MSG = (
    "Nice! Your cookies are set — you should be able to download from YouTube now. "
    "If you need to change or remove your cookies, go to the YouTube cookies tab."
)
_BROWSER_COOKIES_HINT_NO_UPLOAD = (
    "If YouTube downloads fail, use the YouTube cookies tab to export and upload cookies."
)

# YouTube cookies tab: instruction dropdown (slug, display name). Order is menu order.
COOKIE_GUIDE_PAIRS: list[tuple[str, str]] = [
    ("chrome", "Google Chrome"),
    ("edge", "Microsoft Edge"),
    ("firefox", "Mozilla Firefox"),
    ("brave", "Brave"),
    ("opera", "Opera"),
    ("chromium", "Chromium"),
    ("vivaldi", "Vivaldi"),
    ("safari", "Safari"),
]

# Display labels for yt-dlp --cookies-from-browser (YouTube downloads on Download tab + docs).
YT_SIGNIN_BROWSER_LABELS: dict[str, str] = {
    "": "Choose browser (YouTube)…",
    "chrome": "Google Chrome",
    "edge": "Microsoft Edge",
    "firefox": "Mozilla Firefox",
    "brave": "Brave",
    "opera": "Opera",
    "chromium": "Chromium",
    "vivaldi": "Vivaldi",
    "safari": "Safari",
}


def _guide_export_chromium_family(browser_title: str, step1_where: str) -> str:
    """Minimal step-by-step cookies.txt export for Chromium-based browsers."""
    return (
        f"{browser_title}\n\n"
        "Step 1 — Add extension\n"
        f'Search for: Get cookies.txt LOCALLY\n{step1_where}\n'
        '(Use the one with "LOCALLY" in the name.)\n\n'
        "Step 2 — YouTube\n"
        "Open youtube.com and sign in.\n\n"
        "Step 3 — Export\n"
        "Click the extension icon. Export cookies for this site. Save the file.\n\n"
        "Step 4 — VidVortex\n"
        "YouTube cookies tab → choose this browser in the menu above → Choose YouTube cookies.txt → select your file."
    )


COOKIE_GUIDE_BODIES: dict[str, str] = {
    "chrome": _guide_export_chromium_family(
        "Google Chrome",
        "Install from: Chrome Web Store.",
    ),
    "edge": _guide_export_chromium_family(
        "Microsoft Edge",
        "Install from: Edge Add-ons, or Chrome Web Store (turn on other stores in Extensions if needed).",
    ),
    "brave": _guide_export_chromium_family(
        "Brave",
        "Install from: Chrome Web Store (enable Chrome extensions in Brave settings).",
    ),
    "opera": _guide_export_chromium_family(
        "Opera",
        "Install from: Chrome Web Store (Opera can use Chrome extensions).",
    ),
    "chromium": _guide_export_chromium_family(
        "Chromium",
        "Install from: your distro's instructions for Chromium extensions, or Chrome Web Store if enabled.",
    ),
    "vivaldi": _guide_export_chromium_family(
        "Vivaldi",
        "Install from: Chrome Web Store (allowed in Vivaldi extension settings).",
    ),
    "firefox": (
        "Mozilla Firefox\n\n"
        "Step 1 — Add add-on\n"
        "Go to addons.mozilla.org.\n"
        'Install one: "cookies.txt" OR "Get cookies.txt LOCALLY".\n\n'
        "Step 2 — YouTube\n"
        "Open youtube.com and sign in.\n\n"
        "Step 3 — Export\n"
        "Use the add-on to export cookies. Save the file.\n\n"
        "Step 4 — VidVortex\n"
        "YouTube cookies tab → Firefox in the menu above → Choose YouTube cookies.txt → select your file."
    ),
    "safari": (
        "Safari (Mac)\n\n"
        "Safari cannot export cookies.txt in a simple way.\n\n"
        "Step 1\n"
        "Install Chrome or Firefox on this Mac.\n\n"
        "Step 2\n"
        "Sign into youtube.com in that browser.\n\n"
        "Step 3\n"
        "Pick Chrome or Firefox in this dropdown. Follow its Step 1–4.\n\n"
        "Step 4\n"
        "Upload the cookies.txt file here."
    ),
}


class VidVortexApp:
    def __init__(self) -> None:
        self.root = tb.Window(themename=APP_THEME)
        self.root.title("VidVortex")
        self.root.geometry("1000x720")
        self.root.minsize(640, 520)

        self.base_dir = engine.resolve_desktop_dir() / "VidVortex"
        self.audio_dir = self.base_dir / "audio"
        self.video_dir = self.base_dir / "video"
        self.settings_path = engine.resolve_settings_path()
        engine.setup_logging(None)
        engine.migrate_legacy_settings_if_needed()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.video_dir.mkdir(parents=True, exist_ok=True)

        self.settings = engine.load_settings(self.settings_path)

        self.cookies_file_var = tk.StringVar(value=str(self.settings.get("cookies_file") or ""))
        # Chromium cookie decrypt often fails on Windows (DPAPI); Firefox-first nudges a working shortcut.
        _chromium_family = ["chrome", "edge", "brave", "opera", "chromium", "vivaldi"]
        _rest = ["firefox"] + _chromium_family
        if platform.system().lower() == "windows":
            _browser_raw = [""] + _rest
        else:
            _browser_raw = [""] + ["chrome", "edge", "firefox", "brave", "opera", "chromium", "vivaldi"]
        if platform.system().lower() == "darwin":
            _browser_raw.append("safari")
        _cb_initial = str(self.settings.get("cookies_from_browser") or "").strip().lower()
        if _cb_initial not in _browser_raw:
            _cb_initial = ""
        if str(self.settings.get("cookies_locked_browser") or "").strip() and not str(
            self.settings.get("cookies_file") or ""
        ).strip():
            self.settings["cookies_locked_browser"] = ""
        _locked = str(self.settings.get("cookies_locked_browser") or "").strip().lower()
        if _locked in _browser_raw:
            _cb_initial = _locked
        self.cookies_browser_var = tk.StringVar(value=_cb_initial)
        self._cookies_browser_values = _browser_raw

        self.video_qualities: list[int] = []
        self.audio_qualities: list[int] = []
        self.loaded_quality_url: str | None = None
        self.is_busy = False
        self._progress_tick = 0
        self._wrap_resize_after_id: str | None = None
        self._animate_after_id: str | None = None

        self.mode_var = tk.StringVar(value="video")
        self.url_var = tk.StringVar()
        self.profile_var = tk.StringVar(value="safe")
        self.quality_var = tk.StringVar(value="best")
        self.status_var = tk.StringVar(value="Status: Idle")
        self.stage_var = tk.StringVar(value="Download stage: waiting")
        self.quality_hint_var = tk.StringVar()
        self.quality_combo: tb.Combobox | None = None
        self.download_cancel_controller: engine.DownloadController | None = None
        self.cancel_btn: tb.Button | None = None

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self.url_var.trace_add("write", self._on_url_changed)
        self._refresh_quality_pending_ui()
        self._set_download_visible(False)
        self.log_info("VidVortex desktop app ready.")

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

    @staticmethod
    def _parse_download_progress(line: str) -> tuple[float | None, str | None]:
        if "[download]" not in line:
            return None, None
        pct_match = re.search(r"(\d{1,3}(?:\.\d+)?)%", line)
        eta_match = re.search(r"ETA\s+([0-9:]+)", line)
        pct = float(pct_match.group(1)) if pct_match else None
        eta = eta_match.group(1) if eta_match else None
        if pct is not None:
            pct = max(0.0, min(100.0, pct))
        return pct, eta

    def _build_ui(self) -> None:
        self._ui_ready = False
        self._left_wrap_labels: list[tb.Label] = []

        outer = tb.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)

        self._notebook = tb.Notebook(outer)
        self._notebook.pack(fill="both", expand=True)

        download_tab = tb.Frame(self._notebook, padding=(0, 12, 0, 0))
        howto_tab = tb.Frame(self._notebook, padding=20)
        cookies_tab = tb.Frame(self._notebook, padding=20)
        about_tab = tb.Frame(self._notebook, padding=20)
        self._notebook.add(download_tab, text="  Download  ")
        self._notebook.add(howto_tab, text="  How to use  ")
        self._notebook.add(cookies_tab, text="  YouTube cookies  ")
        self._notebook.add(about_tab, text="  About  ")
        self._cookies_tab = cookies_tab
        self._howto_tab = howto_tab
        self._about_tab = about_tab

        layout = tb.Frame(download_tab)
        layout.pack(fill="both", expand=True)
        layout.columnconfigure(0, weight=1, minsize=200)
        layout.columnconfigure(1, weight=2, minsize=240)
        layout.rowconfigure(0, weight=1)

        left = tb.Labelframe(layout, text=" Source & options ", padding=16)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)
        left.columnconfigure(0, weight=1)
        self.left_panel = left

        right = tb.Labelframe(layout, text=" Activity ", padding=16)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=4)
        right.columnconfigure(0, weight=1)
        right.columnconfigure(1, weight=1)
        right.rowconfigure(4, weight=1)

        row = 0
        self._labeled_entry(left, "URL — paste a video or audio link", self.url_var, row)
        row += 1
        self._labeled_combo(left, "Mode", self.mode_var, ["audio", "video"], row, self._on_mode_change)
        row += 1
        self._labeled_combo(left, "Quality", self.quality_var, ["best"], row)
        row += 1
        self.quality_hint_label = tb.Label(left, textvariable=self.quality_hint_var, justify="left", wraplength=360)
        self.quality_hint_label.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        row += 1
        self._labeled_combo(left, "Profile", self.profile_var, ["fast", "safe", "stealth"], row)
        row += 1

        row = self._build_browser_signin_row(left, row)
        yt_help = tb.Label(
            left,
            text="YouTube cookie help — opens the YouTube cookies tab",
            bootstyle="info",
            justify="left",
            wraplength=280,
            cursor="hand2",
        )
        yt_help.bind("<Button-1>", lambda _e: self._notebook.select(self._cookies_tab))
        yt_help.grid(row=row, column=0, sticky="ew", pady=(0, 8))
        self._left_wrap_labels.append(yt_help)
        row += 1

        buttons = tb.Frame(left)
        buttons.grid(row=row, column=0, sticky="ew", pady=(18, 0))
        buttons.columnconfigure(0, weight=1)

        _btn_outline = "info-outline"

        self.load_btn = tb.Button(
            buttons,
            text="Load Qualities",
            command=self.on_load_qualities,
            bootstyle=_btn_outline,
        )
        self.load_btn.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.start_btn = tb.Button(
            buttons,
            text="Download Now",
            command=self.on_start_download,
            bootstyle=_btn_outline,
        )
        self.start_btn.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.cancel_btn = tb.Button(
            buttons,
            text="Cancel Download",
            command=self.on_cancel_download,
            bootstyle="danger-outline",
        )
        self.cancel_btn.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.cancel_btn.grid_remove()

        self.open_btn = tb.Button(
            buttons,
            text="Open Downloads Folder",
            command=self.on_open_downloads,
            bootstyle=_btn_outline,
        )
        self.open_btn.grid(row=3, column=0, sticky="ew", pady=(0, 0))

        tb.Label(right, textvariable=self.status_var, font=("", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6)
        )
        tb.Label(right, textvariable=self.stage_var).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.task_progress = tb.Progressbar(right, mode="determinate", maximum=100, value=0, bootstyle="success-striped")
        self.task_progress.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self.download_progress = tb.Progressbar(
            right, mode="determinate", maximum=100, value=0, bootstyle="info-striped"
        )
        self.download_progress.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        self.log_text = ScrolledText(
            right,
            height=18,
            wrap="word",
            padding=2,
            autohide=False,
            bootstyle="round",
        )
        self.log_text.grid(row=4, column=0, columnspan=2, sticky="nsew")
        self.log_text.text.configure(font=tkfont.nametofont("TkFixedFont"))

        self._build_cookies_tab(cookies_tab)

        howto_text = (
            "How to use VidVortex\n\n"
            "1) Paste a URL\n"
            "2) Choose Audio or Video\n"
            "3) Click Load Qualities (wait until the list updates)\n"
            "4) Read the hint under Quality — it shows the best default for this link\n"
            "5) Change quality if you want, then click Download Now (button appears after step 3)\n"
            "6) Open Downloads Folder when done\n\n"
            "For YouTube: under Are cookies uploaded?, pick the browser where you use YouTube. "
            "Use the YouTube cookies tab if downloads fail or you need export steps."
        )
        tb.Label(howto_tab, text=howto_text, justify="left", font=("", 11)).pack(anchor="nw")

        about_text = (
            "About VidVortex\n\n"
            "Developed by Estebanech\n"
            "Portfolio: estebanech.com\n\n"
            "Powered by yt-dlp and ffmpeg.\n\n"
            "I bulit this with the intention of always saving the best quality\n"
            "audio or video of things that i loved, without using skertchy\n"
            "websited full of ads."
        )
        tb.Label(about_tab, text=about_text, justify="left", font=("", 11)).pack(anchor="nw")

        self._apply_contrast_styles()
        self._bind_left_wrap_resize()
        self._bind_cookies_wrap_resize()
        self._apply_browser_lock_ui()

        self._ui_ready = True

    def _build_cookies_tab(self, cookies_tab: tb.Frame) -> None:
        cookies_tab.columnconfigure(0, weight=1)
        self._cookies_wrap_labels = []
        intro = (
            "You probably already picked your browser on Download and YouTube still complained — that's why this tab "
            "exists. Export cookies from the browser where you're signed into YouTube, then upload the file here.\n\n"
            "Pick your browser in the menu below for export steps.\n\n"
            "After you upload, we'll use that file so lookups and downloads line up with your logged-in session."
        )
        intro_lbl = tb.Label(cookies_tab, text=intro, justify="left", wraplength=360, font=("", 11))
        intro_lbl.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        self._cookies_wrap_labels.append(intro_lbl)

        guide_header = tb.Frame(cookies_tab)
        guide_header.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        tb.Label(guide_header, text="YouTube export steps for:", font=("", 10, "bold")).pack(side="left")
        self._cookie_guide_combo = tb.Combobox(
            guide_header,
            state="readonly",
            width=32,
            values=[p[1] for p in COOKIE_GUIDE_PAIRS],
        )
        self._cookie_guide_combo.pack(side="left", padx=(10, 0))
        self._cookie_guide_combo.current(0)
        self._cookie_guide_combo.bind("<<ComboboxSelected>>", self._on_cookie_guide_changed)

        self._cookie_guide_scroll = ScrolledText(
            cookies_tab,
            height=14,
            wrap="word",
            padding=2,
            autohide=True,
            bootstyle="round",
        )
        self._cookie_guide_scroll.grid(row=2, column=0, sticky="nsew", pady=(0, 12))
        cookies_tab.rowconfigure(2, weight=1)
        self._cookie_guide_scroll.text.configure(font=tkfont.nametofont("TkFixedFont"))

        upload_lf = tb.Labelframe(cookies_tab, text=" YouTube cookies.txt (upload) ", padding=(12, 10))
        upload_lf.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        upload_lf.columnconfigure(0, weight=1)
        upload_hint_lbl = tb.Label(
            upload_lf,
            text=(
                "Export while signed into youtube.com in that browser. Choose your cookies.txt below. "
                "The browser menu above should match where you exported from (and locks Download unless one was already set there)."
            ),
            wraplength=360,
            justify="left",
        )
        upload_hint_lbl.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self._cookies_wrap_labels.append(upload_hint_lbl)
        up_btns = tb.Frame(upload_lf)
        up_btns.grid(row=1, column=0, sticky="w", pady=(0, 8))
        tb.Button(
            up_btns,
            text="Choose YouTube cookies.txt…",
            command=self._on_select_cookies_file,
            bootstyle="info-outline",
        ).pack(side="left", padx=(0, 8))
        tb.Button(
            up_btns,
            text="Clear YouTube cookies file",
            command=self._on_clear_cookies_file,
            bootstyle="danger-outline",
        ).pack(side="left")
        tb.Label(upload_lf, text="Current YouTube cookies file:", font=("", 9)).grid(row=2, column=0, sticky="w", pady=(4, 0))
        cookies_path_lbl = tb.Label(
            upload_lf,
            textvariable=self.cookies_file_var,
            font=("TkFixedFont", 9),
            wraplength=360,
            justify="left",
        )
        cookies_path_lbl.grid(row=3, column=0, sticky="ew")
        self._cookies_wrap_labels.append(cookies_path_lbl)

        link_row = tb.Frame(cookies_tab)
        link_row.grid(row=4, column=0, sticky="w", pady=(8, 0))
        tb.Button(
            link_row,
            text="Official guide: exporting YouTube cookies",
            command=self._open_youtube_cookie_export_help,
            bootstyle="link",
        ).pack(side="left")
        tb.Button(
            link_row,
            text="FAQ: passing cookies to yt-dlp",
            command=self._open_youtube_cookie_faq,
            bootstyle="link",
        ).pack(side="left", padx=(16, 0))

        self._on_cookie_guide_changed()

    def _on_cookie_guide_changed(self, _event: object = None) -> None:
        idx = self._cookie_guide_combo.current()
        if idx < 0 or idx >= len(COOKIE_GUIDE_PAIRS):
            return
        slug = COOKIE_GUIDE_PAIRS[idx][0]
        body = COOKIE_GUIDE_BODIES.get(slug, "")
        tw = self._cookie_guide_scroll.text
        tw.configure(state="normal")
        tw.delete("1.0", "end")
        tw.insert("1.0", body)
        tw.configure(state="disabled")

    @staticmethod
    def _open_youtube_cookie_faq() -> None:
        webbrowser.open("https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp")

    def _apply_contrast_styles(self) -> None:
        """Force readable light text on dark background (theme defaults are often too dim)."""
        st = self.root.style
        inp = getattr(st.colors, "inputbg", "#2f2f2f")

        def safe_configure(style_name: str, **kwargs: object) -> None:
            try:
                st.configure(style_name, **kwargs)
            except tk.TclError:
                pass

        safe_configure("TLabel", foreground=TEXT_PRIMARY)
        safe_configure("TLabelframe.Label", foreground=TEXT_PRIMARY)
        safe_configure("TNotebook.Tab", foreground=TEXT_PRIMARY)
        for variant in (
            "secondary.TLabel",
            "info.TLabel",
            "success.TLabel",
            "warning.TLabel",
            "danger.TLabel",
        ):
            safe_configure(variant, foreground=TEXT_SOFT)
        safe_configure("TEntry", foreground=TEXT_PRIMARY, insertcolor=TEXT_PRIMARY)
        safe_configure("TCombobox", foreground=TEXT_PRIMARY, fieldforeground=TEXT_PRIMARY)

        try:
            self.log_text.text.configure(
                foreground=TEXT_PRIMARY,
                background=inp,
                insertbackground=TEXT_PRIMARY,
                selectbackground="#3d5a80",
                selectforeground=TEXT_PRIMARY,
            )
        except (tk.TclError, AttributeError):
            pass

        try:
            self._cookie_guide_scroll.text.configure(
                foreground=TEXT_PRIMARY,
                background=inp,
                insertbackground=TEXT_PRIMARY,
                selectbackground="#3d5a80",
                selectforeground=TEXT_PRIMARY,
            )
        except (tk.TclError, AttributeError):
            pass

        try:
            badge = getattr(self, "_browser_cookies_uploaded_lbl", None)
            if badge is not None:
                badge.configure(foreground=COOKIE_UPLOAD_BADGE_GREEN)
        except (tk.TclError, AttributeError):
            pass

    def _apply_left_wraplength_for_panel_width(self, width: int) -> None:
        """Match label wraplength to the Source & options column so text does not clip."""
        if width <= 60:
            return
        wl = max(120, width - 56)
        try:
            self.quality_hint_label.configure(wraplength=wl)
            for lbl in self._left_wrap_labels:
                lbl.configure(wraplength=wl)
        except tk.TclError:
            pass

    def _sync_left_wraplength_idle(self) -> None:
        try:
            self.root.update_idletasks()
            w = int(self.left_panel.winfo_width() or 0)
            self._apply_left_wraplength_for_panel_width(w)
        except (tk.TclError, AttributeError):
            pass

    def _bind_left_wrap_resize(self) -> None:
        """Avoid huge fixed wraplength issues when the window is maximized / resized."""

        def on_configure(event: tk.Event) -> None:
            if event.widget is not self.left_panel:
                return
            w = int(getattr(event, "width", 0) or 0)
            if w <= 60:
                return
            if self._wrap_resize_after_id is not None:
                try:
                    self.root.after_cancel(self._wrap_resize_after_id)
                except (tk.TclError, ValueError):
                    pass
                self._wrap_resize_after_id = None

            captured = w

            def apply_wrap() -> None:
                self._wrap_resize_after_id = None
                self._apply_left_wraplength_for_panel_width(captured)

            self._wrap_resize_after_id = self.root.after(48, apply_wrap)

        self.left_panel.bind("<Configure>", on_configure, add=True)
        self.root.after_idle(self._sync_left_wraplength_idle)

    def _bind_wrap_resize_for_tab(self, frame: tk.Misc, labels_attr: str) -> None:
        """Update wraplength for all labels in labels_attr when frame width changes."""
        pending_after: list[str | None] = [None]

        def on_configure(event: tk.Event) -> None:
            if event.widget is not frame:
                return
            w = int(getattr(event, "width", 0) or 0)
            if w <= 60:
                return
            if pending_after[0] is not None:
                try:
                    self.root.after_cancel(pending_after[0])
                except (tk.TclError, ValueError):
                    pass
                pending_after[0] = None

            captured = w

            def apply_wrap() -> None:
                pending_after[0] = None
                try:
                    wl = max(120, captured - 56)
                    for lbl in getattr(self, labels_attr, []):
                        lbl.configure(wraplength=wl)
                except tk.TclError:
                    pass

            pending_after[0] = self.root.after(48, apply_wrap)

        frame.bind("<Configure>", on_configure, add=True)

    def _sync_tab_wraplength_idle(self, frame: tk.Misc, labels_attr: str) -> None:
        try:
            self.root.update_idletasks()
            w = int(frame.winfo_width() or 0)
            if w <= 60:
                return
            wl = max(120, w - 56)
            for lbl in getattr(self, labels_attr, []):
                lbl.configure(wraplength=wl)
        except (tk.TclError, AttributeError):
            pass

    def _bind_cookies_wrap_resize(self) -> None:
        """Keep YouTube cookies tab labels wrapping when the window width changes."""
        self._bind_wrap_resize_for_tab(self._cookies_tab, "_cookies_wrap_labels")
        self.root.after_idle(lambda: self._sync_tab_wraplength_idle(self._cookies_tab, "_cookies_wrap_labels"))

    def _labeled_entry(
        self,
        parent: tb.Frame,
        title: str,
        variable: tk.StringVar,
        row: int,
        *,
        title_wraplength: int | None = None,
        register_left_wrap: bool = True,
    ) -> None:
        frame = tb.Frame(parent)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        frame.columnconfigure(0, weight=1)
        lbl = tb.Label(frame, text=title)
        if title_wraplength is not None:
            lbl.configure(wraplength=title_wraplength)
            if register_left_wrap:
                self._left_wrap_labels.append(lbl)
        lbl.grid(row=0, column=0, sticky="w", pady=(0, 6))
        entry = tb.Entry(frame, textvariable=variable)
        entry.grid(row=1, column=0, sticky="ew", ipady=6)

    def _labeled_combo(
        self,
        parent: tb.Frame,
        title: str,
        variable: tk.StringVar,
        values: list[str],
        row: int,
        on_change: callable | None = None,
        values_labels: dict[str, str] | None = None,
        *,
        title_wraplength: int | None = None,
        register_left_wrap: bool = True,
    ) -> None:
        frame = tb.Frame(parent)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        frame.columnconfigure(0, weight=1)
        lbl = tb.Label(frame, text=title)
        if title_wraplength is not None:
            lbl.configure(wraplength=title_wraplength)
            if register_left_wrap:
                self._left_wrap_labels.append(lbl)
        lbl.grid(row=0, column=0, sticky="w", pady=(0, 6))

        display_values = (
            [values_labels.get(v, v.title()) for v in values] if values_labels else [v.title() for v in values]
        )
        combo = tb.Combobox(frame, state="readonly", values=display_values)
        combo.grid(row=1, column=0, sticky="ew", ipady=4)
        initial = variable.get()
        combo.current(values.index(initial) if initial in values else 0)
        combo._raw_values = values  # type: ignore[attr-defined]
        combo._display_values = display_values  # type: ignore[attr-defined]

        def sync_var(_: object = None) -> None:
            idx = combo.current()
            raw = getattr(combo, "_raw_values", values)
            if 0 <= idx < len(raw):
                variable.set(raw[idx])
            if on_change and self._ui_ready:
                on_change()

        combo.bind("<<ComboboxSelected>>", sync_var)
        sync_var()

        if title == "Quality":
            self.quality_combo = combo

    def _build_browser_signin_row(self, parent: tb.Frame, row: int) -> int:
        """Download tab: browser for YouTube cookies; locked after YouTube cookies.txt upload."""
        frame = tb.Frame(parent)
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(0, weight=1)
        lbl = tb.Label(frame, text=_BROWSER_SIGNIN_TITLE)
        lbl.configure(wraplength=320)
        self._left_wrap_labels.append(lbl)
        lbl.grid(row=0, column=0, sticky="w", pady=(0, 6))
        self._browser_signin_title_lbl = lbl

        values = self._cookies_browser_values
        display_values = [YT_SIGNIN_BROWSER_LABELS.get(v, v.title()) for v in values]
        combo = tb.Combobox(frame, state="readonly", values=display_values)
        combo.grid(row=1, column=0, sticky="ew", ipady=4)

        self._browser_cookies_uploaded_lbl = tb.Label(
            frame,
            text=_BROWSER_COOKIES_UPLOADED_BADGE,
            font=("", 11, "bold"),
            foreground=COOKIE_UPLOAD_BADGE_GREEN,
        )
        self._browser_cookies_uploaded_lbl.grid(row=1, column=0, sticky="w", ipady=6)
        self._browser_cookies_uploaded_lbl.grid_remove()
        initial = self.cookies_browser_var.get()
        combo.current(values.index(initial) if initial in values else 0)
        combo._raw_values = values  # type: ignore[attr-defined]
        combo._display_values = display_values  # type: ignore[attr-defined]

        def sync_var(_: object = None) -> None:
            if getattr(self, "_browser_cookie_lock_active", False):
                return
            idx = combo.current()
            raw = getattr(combo, "_raw_values", values)
            if 0 <= idx < len(raw):
                self.cookies_browser_var.set(raw[idx])

        combo.bind("<<ComboboxSelected>>", sync_var)
        sync_var()

        self.cookies_browser_combo = combo
        self._browser_signin_frame = frame
        self._browser_cookie_lock_active = False

        self._browser_no_cookies_hint_lbl = tb.Label(
            frame,
            text=_BROWSER_COOKIES_HINT_NO_UPLOAD,
            font=("", 9),
            foreground=TEXT_SOFT,
            wraplength=320,
            justify="left",
        )
        self._left_wrap_labels.append(self._browser_no_cookies_hint_lbl)
        self._browser_no_cookies_hint_lbl.grid(row=2, column=0, sticky="ew", pady=(4, 0))

        self._browser_lock_row = tb.Frame(frame)
        self._browser_lock_row.columnconfigure(0, weight=1)
        self._browser_lock_msg = tb.Label(
            self._browser_lock_row,
            text="",
            font=("", 10),
            foreground=TEXT_SOFT,
            wraplength=320,
            justify="left",
        )
        self._left_wrap_labels.append(self._browser_lock_msg)
        self._browser_lock_msg.grid(row=0, column=0, sticky="ew")
        self._browser_unlock_btn = tb.Button(
            self._browser_lock_row,
            text="Remove YouTube Cookies",
            command=self._on_unlock_browser_lock,
            bootstyle="danger-outline",
        )
        self._browser_unlock_btn.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self._browser_lock_row.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        self._browser_lock_row.grid_remove()

        return row + 1

    def _apply_browser_lock_ui(self) -> None:
        combo = getattr(self, "cookies_browser_combo", None)
        lr = getattr(self, "_browser_lock_row", None)
        if combo is None:
            return
        uploaded_lbl = getattr(self, "_browser_cookies_uploaded_lbl", None)
        no_upload_hint = getattr(self, "_browser_no_cookies_hint_lbl", None)
        locked = (self.settings.get("cookies_locked_browser") or "").strip()
        # "" is in _cookies_browser_values (means "no browser"); only treat non-empty slugs as locked.
        if locked and locked in self._cookies_browser_values:
            self._browser_cookie_lock_active = True
            try:
                self.cookies_browser_var.set(locked)
                idx = self._cookies_browser_values.index(locked)
                combo.current(idx)
                combo.configure(state="disabled")
                combo.grid_remove()
                if uploaded_lbl is not None:
                    uploaded_lbl.configure(foreground=COOKIE_UPLOAD_BADGE_GREEN)
                    uploaded_lbl.grid()
                self._browser_lock_msg.configure(text=_BROWSER_COOKIES_SUCCESS_MSG, foreground=TEXT_SOFT)
                if no_upload_hint is not None:
                    no_upload_hint.grid_remove()
                if lr is not None:
                    lr.grid(row=2, column=0, sticky="ew", pady=(4, 0))
            finally:
                self._browser_cookie_lock_active = False
        else:
            combo.configure(state="readonly")
            combo.grid(row=1, column=0, sticky="ew", ipady=4)
            if uploaded_lbl is not None:
                uploaded_lbl.grid_remove()
            if no_upload_hint is not None:
                no_upload_hint.grid(row=2, column=0, sticky="ew", pady=(4, 0))
            if lr is not None:
                lr.grid_remove()

    def _on_unlock_browser_lock(self) -> None:
        self.settings["cookies_locked_browser"] = ""
        try:
            self._persist_settings_from_gui()
        except Exception:
            pass
        self._apply_browser_lock_ui()

    def _cookie_guide_slug(self) -> str | None:
        combo = getattr(self, "_cookie_guide_combo", None)
        if combo is None:
            return None
        try:
            idx = combo.current()
        except tk.TclError:
            return None
        if idx < 0 or idx >= len(COOKIE_GUIDE_PAIRS):
            return None
        return COOKIE_GUIDE_PAIRS[idx][0]

    def _browser_slug_for_cookie_upload(self) -> str | None:
        raw = (self.cookies_browser_var.get() or "").strip().lower()
        if raw and raw in self._cookies_browser_values:
            return raw
        guide = self._cookie_guide_slug()
        if guide and guide in self._cookies_browser_values:
            return guide
        return None

    def _sync_cookies_browser_combo_to_slug(self, slug: str) -> None:
        if slug not in self._cookies_browser_values:
            return
        self.cookies_browser_var.set(slug)
        combo = getattr(self, "cookies_browser_combo", None)
        if combo is None:
            return
        idx = self._cookies_browser_values.index(slug)
        try:
            combo.current(idx)
        except tk.TclError:
            pass

    def _on_select_cookies_file(self) -> None:
        path = filedialog.askopenfilename(
            parent=self.root,
            title="Select Netscape cookies.txt (YouTube)",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        chosen = self._browser_slug_for_cookie_upload()
        if not chosen:
            Messagebox.show_warning(
                "Pick a browser in the export-steps menu above that matches your cookies, "
                "or choose your browser on the Download tab under Are cookies uploaded?, then try again.",
                "VidVortex",
                parent=self.root,
            )
            return
        self._sync_cookies_browser_combo_to_slug(chosen)
        p = Path(path).expanduser()
        if not p.is_file():
            Messagebox.show_error("That path is not a file.", "VidVortex", parent=self.root)
            return
        self.cookies_file_var.set(str(p))
        self.settings["cookies_locked_browser"] = chosen
        try:
            self._persist_settings_from_gui()
        except Exception:
            pass
        self._apply_browser_lock_ui()
        self.log_info(
            "YouTube cookies saved. Download tab shows YouTube Cookies Uploaded — change or remove them from the "
            "YouTube cookies tab, or tap Remove YouTube Cookies on Download."
        )

    def _on_clear_cookies_file(self) -> None:
        self.cookies_file_var.set("")
        self.settings["cookies_locked_browser"] = ""
        try:
            self._persist_settings_from_gui()
        except Exception:
            pass
        self._apply_browser_lock_ui()

    def _current_url(self) -> str:
        return self.url_var.get().strip()

    def _on_url_changed(self, *_args: object) -> None:
        url = self._current_url()
        if self.loaded_quality_url is not None and self.loaded_quality_url != url:
            self.loaded_quality_url = None
            self._set_download_visible(False)
            self._refresh_quality_pending_ui()

    def _download_should_show(self) -> bool:
        u = self._current_url()
        return bool(u and self.loaded_quality_url is not None and self.loaded_quality_url == u)

    def _set_download_visible(self, show: bool) -> None:
        if show:
            self.start_btn.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        else:
            self.start_btn.grid_remove()

    def _set_cancel_visible(self, show: bool) -> None:
        if self.cancel_btn is None:
            return
        if show:
            self.cancel_btn.configure(state="normal")
            self.cancel_btn.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        else:
            self.cancel_btn.grid_remove()

    def _refresh_quality_pending_ui(self) -> None:
        if self.quality_combo is None:
            return
        self.quality_combo.configure(state="readonly")
        self.quality_combo["values"] = ["Click 'Load Qualities' to list options for this link"]
        self.quality_combo._raw_values = ["best"]  # type: ignore[attr-defined]
        self.quality_combo.current(0)
        self.quality_var.set("best")
        self.quality_hint_var.set(
            "Paste a URL, choose Audio or Video, then click Load Qualities. "
            "Download Now appears only after options are loaded for that link."
        )

    def _update_quality_hint_after_load(self, default_fragment: str, mode: str) -> None:
        mode_word = "audio" if mode == "audio" else "video"
        extra = ""
        if mode == "audio" and self.video_qualities:
            top_v = self.format_video_quality_label(self.video_qualities[0])
            extra = f" This URL also offers up to {top_v} — switch Mode to Video to download that resolution."
        elif mode == "video" and self.audio_qualities:
            top_a = self.format_audio_quality_label(self.audio_qualities[0])
            extra = f" Best listed audio streams peak around {top_a}."
        self.quality_hint_var.set(
            f"Best available {mode_word} for this link: {default_fragment}.{extra} "
            "Pick another quality if you want, then use Download Now."
        )

    def _set_quality_values_from_metadata(self, mode: str) -> str:
        """Fill quality combobox like the TUI: human-friendly 'Best Available (auto: …)'. Returns default label text."""
        if self.quality_combo is None:
            return ""
        self.quality_combo.configure(state="readonly")
        if mode == "audio":
            best_audio = (
                self.format_audio_quality_label(self.audio_qualities[0]) if self.audio_qualities else "best audio"
            )
            labels = [f"Best Available — audio: {best_audio}"] + [
                self.format_audio_quality_label(abr) for abr in self.audio_qualities
            ]
            raw: list[str] = ["best"] + [f"a{abr}" for abr in self.audio_qualities]
            default_fragment = best_audio
        else:
            best_video = (
                self.format_video_quality_label(self.video_qualities[0]) if self.video_qualities else "best video"
            )
            labels = [f"Best Available — video: {best_video}"] + [
                self.format_video_quality_label(h) for h in self.video_qualities
            ]
            raw = ["best"] + [f"v{h}" for h in self.video_qualities]
            default_fragment = best_video
        self.quality_combo["values"] = labels
        self.quality_combo._raw_values = raw  # type: ignore[attr-defined]
        self.quality_combo.current(0)
        self.quality_var.set("best")
        return default_fragment

    def _set_busy(self, busy: bool) -> None:
        self.is_busy = busy
        state = "disabled" if busy else "normal"
        self.load_btn.configure(state=state)
        self.start_btn.configure(state=state)
        if not busy:
            if self._animate_after_id is not None:
                try:
                    self.root.after_cancel(self._animate_after_id)
                except (tk.TclError, ValueError):
                    pass
                self._animate_after_id = None
            self._set_cancel_visible(False)
            self.download_cancel_controller = None
            self.task_progress.configure(mode="determinate")
            self.task_progress["value"] = 0
            self.download_progress["value"] = 0
            self._set_download_visible(self._download_should_show())

    def _invoke_on_main(self, callback: callable) -> None:
        def run() -> None:
            try:
                if self.root.winfo_exists():
                    callback()
            except tk.TclError:
                pass

        try:
            self.root.after(0, run)
        except tk.TclError:
            pass

    def _run_bg(self, fn: callable, done: callable | None = None) -> None:
        def runner() -> None:
            result = fn()
            if done:

                def call_done() -> None:
                    done(result)

                self._invoke_on_main(call_done)

        threading.Thread(target=runner, daemon=True).start()

    def _validate_url(self, url: str) -> tuple[bool, str]:
        return engine.validate_url(url)

    def _missing_deps(self) -> list[str]:
        return [dep for dep in ("yt-dlp", "ffmpeg") if not engine.check_dependency(dep)]

    def _yt_dlp_cookie_namespace(self) -> SimpleNamespace:
        return SimpleNamespace(
            cookies_file=self.cookies_file_var.get().strip() or None,
            cookies_from_browser=self.cookies_browser_var.get().strip() or None,
        )

    def _yt_dlp_base_for_gui(self) -> list[str]:
        base = engine.build_yt_dlp_base(None, omit_missing_config=True)
        return engine.append_yt_dlp_cookie_flags(base, self._yt_dlp_cookie_namespace())

    def _persist_settings_from_gui(self) -> None:
        merged = dict(engine.DEFAULT_SETTINGS)
        merged.update(engine.load_settings(self.settings_path))
        merged["cookies_file"] = self.cookies_file_var.get().strip()
        merged["cookies_from_browser"] = self.cookies_browser_var.get().strip()
        merged["cookies_locked_browser"] = str(self.settings.get("cookies_locked_browser") or "")
        engine.save_settings(self.settings_path, merged)
        self.settings = merged

    def _on_close(self) -> None:
        try:
            self._persist_settings_from_gui()
        except Exception:
            pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    @staticmethod
    def _open_youtube_cookie_export_help() -> None:
        webbrowser.open("https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies")

    def _quality_raw_value(self) -> str:
        if self.quality_combo is None:
            return "best"
        idx = self.quality_combo.current()
        raw_values = getattr(self.quality_combo, "_raw_values", ["best"])
        if 0 <= idx < len(raw_values):
            return raw_values[idx]
        return "best"

    def _build_engine_args(self, url: str, mode: str, quality: str) -> SimpleNamespace:
        settings = engine.load_settings(self.settings_path)
        args = SimpleNamespace(
            mode=mode,
            quality=int(quality[1:]) if mode == "video" and quality.startswith("v") and quality[1:].isdigit() else None,
            audio_abr=int(quality[1:]) if mode == "audio" and quality.startswith("a") and quality[1:].isdigit() else None,
            timeout=engine.DEFAULT_TIMEOUT,
            config_location=None,
            profile=self.profile_var.get(),
            profile_file=None,
            use_aria2c=None,
            retries=None,
            fragment_retries=None,
            retry_sleep=None,
            fragment_retry_sleep=None,
            sleep_requests=None,
            min_sleep_interval=None,
            max_sleep_interval=None,
            subtitles="none",
            subtitle_langs="en.*,es.*,.*",
            sponsorblock_remove="",
            add_metadata=False,
            embed_thumbnail=False,
            queue_file=None,
            resume_queue=False,
            diagnose=False,
            check_updates=False,
            no_open_log=True,
            url=url,
            audio_default="best_available",
            video_default="best_available",
            video_fixed_quality=1080,
            cookies_file=None,
            cookies_from_browser=None,
        )
        engine.apply_settings_defaults(args, settings)
        args.profile = self.profile_var.get()
        args.mode = mode
        args.cookies_file = self.cookies_file_var.get().strip() or None
        args.cookies_from_browser = self.cookies_browser_var.get().strip() or None
        if mode == "video" and quality.startswith("v") and quality[1:].isdigit():
            args.quality = int(quality[1:])
        if mode == "audio" and quality.startswith("a") and quality[1:].isdigit():
            args.audio_abr = int(quality[1:])
        return args

    def _on_mode_change(self) -> None:
        url = self._current_url()
        if self.loaded_quality_url and self.loaded_quality_url == url:
            mode = self.mode_var.get()
            default_fragment = self._set_quality_values_from_metadata(mode)
            self._update_quality_hint_after_load(default_fragment, mode)
        else:
            self._refresh_quality_pending_ui()

    def on_load_qualities(self) -> None:
        if self.is_busy:
            return
        url = self._current_url()
        ok, reason = self._validate_url(url)
        if not ok:
            Messagebox.show_error(reason, "Invalid URL", parent=self.root)
            return
        missing = self._missing_deps()
        if missing:
            Messagebox.show_warning(
                "Install dependencies first: " + ", ".join(missing),
                "Missing dependencies",
                parent=self.root,
            )
            return

        self.loaded_quality_url = None
        self._set_download_visible(False)
        self.quality_hint_var.set("Scanning this URL for available formats…")
        self._set_busy(True)
        self.status_var.set("Status: Loading qualities...")
        self.stage_var.set("Download stage: fetching metadata")
        self.task_progress.configure(mode="indeterminate")
        self.task_progress.start(14)

        yt_base_snapshot = self._yt_dlp_base_for_gui()

        def worker() -> tuple[bool, list[int], list[int], str, bool]:
            try:
                metadata = engine.get_metadata(
                    url,
                    yt_dlp_base=yt_base_snapshot,
                    timeout_seconds=engine.DEFAULT_TIMEOUT,
                )
                formats = metadata.get("formats") or []
                heights = engine.get_available_heights(formats)
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
                return True, heights, audio_abrs, "", False
            except SystemExit as exc:
                return False, [], [], f"Failed to load metadata (exit {exc.code})", False
            except engine.MetadataFetchError as exc:
                return False, [], [], exc.user_summary, exc.silent_gui_log
            except Exception as exc:
                return False, [], [], str(exc), False

        def done(result: tuple[bool, list[int], list[int], str, bool]) -> None:
            try:
                if not self.root.winfo_exists():
                    return
                self.task_progress.stop()
                self.task_progress.configure(mode="determinate")
                success, heights, audio_abrs, err, silent_gui_log = result
                if not success:
                    self.status_var.set("Status: Failed to load qualities.")
                    if not silent_gui_log:
                        self.log_error(err)
                    self.loaded_quality_url = None
                    self.quality_hint_var.set(err)
                    Messagebox.show_error(err, "VidVortex", parent=self.root)
                    self._set_busy(False)
                    return

                self.video_qualities = heights
                self.audio_qualities = audio_abrs
                if self._current_url() != url:
                    self.log_warn_gui("URL changed while loading. Click Load Qualities again for the new link.")
                    self.loaded_quality_url = None
                    self._refresh_quality_pending_ui()
                    self._set_busy(False)
                    return
                self.loaded_quality_url = url
                mode = self.mode_var.get()
                default_fragment = self._set_quality_values_from_metadata(mode)
                self._update_quality_hint_after_load(default_fragment, mode)
                self.status_var.set("Status: Qualities loaded.")
                self.stage_var.set("Download stage: ready")
                if self.video_qualities:
                    self.log_info("Video options: " + ", ".join(self.format_video_quality_label(h) for h in heights))
                else:
                    self.log_warn_gui("No video resolutions listed for this URL (audio-only or restricted).")
                if self.audio_qualities:
                    self.log_info("Audio options: " + ", ".join(self.format_audio_quality_label(a) for a in audio_abrs))
                else:
                    self.log_warn_gui("No separate audio bitrates listed; best audio will still be used.")
                self._set_busy(False)
            except tk.TclError:
                pass

        self._run_bg(worker, done)

    def on_start_download(self) -> None:
        if self.is_busy:
            return
        url = self._current_url()
        ok, reason = self._validate_url(url)
        if not ok:
            Messagebox.show_error(reason, "Invalid URL", parent=self.root)
            return
        if self.loaded_quality_url != url:
            Messagebox.show_warning("Load qualities first for this URL.", "VidVortex", parent=self.root)
            return
        missing = self._missing_deps()
        if missing:
            Messagebox.show_warning(
                "Install dependencies first: " + ", ".join(missing),
                "Missing dependencies",
                parent=self.root,
            )
            return

        mode = self.mode_var.get()
        quality = self._quality_raw_value()
        args = self._build_engine_args(url, mode, quality)
        try:
            profile = engine.resolve_runtime_profile(args)
        except engine.ProfileResolutionError as exc:
            Messagebox.show_error(str(exc), "VidVortex", parent=self.root)
            return
        yt_base = engine.append_yt_dlp_cookie_flags(
            engine.build_yt_dlp_base(args.config_location, omit_missing_config=True),
            args,
        )
        state = engine.RuntimeState()
        self.download_cancel_controller = engine.DownloadController()

        self._set_busy(True)
        self._set_cancel_visible(True)
        self.status_var.set("Status: Download running...")
        self.stage_var.set("Download stage: downloading")
        self.download_progress["value"] = 0
        self.task_progress.configure(mode="determinate")
        self.task_progress["value"] = 0

        def worker() -> tuple[bool, str]:
            try:
                def progress_hook(line: str) -> None:
                    pct, eta = self._parse_download_progress(line)

                    def apply_progress() -> None:
                        if not self.root.winfo_exists() or not self.is_busy:
                            return
                        if pct is not None:
                            self.download_progress["value"] = pct
                            self.task_progress["value"] = pct
                            if eta:
                                self.stage_var.set(f"Download stage: downloading ({pct:.1f}% • ETA {eta})")
                            else:
                                self.stage_var.set(f"Download stage: downloading ({pct:.1f}%)")

                    self._invoke_on_main(apply_progress)

                output = engine.process_one(
                    url=url,
                    forced_mode=mode,
                    forced_quality=args.quality if mode == "video" else None,
                    args=args,
                    profile=profile,
                    state=state,
                    audio_dir=self.audio_dir,
                    video_dir=self.video_dir,
                    yt_dlp_base=yt_base,
                    allow_video_override_prompt=False,
                    progress_callback=progress_hook,
                    cancel_controller=self.download_cancel_controller,
                )
                size = engine.format_size(output.stat().st_size) if output.exists() else "unknown size"
                return True, f"{output} ({size})"
            except SystemExit as exc:
                if int(exc.code or 1) == 130:
                    return False, "Download cancelled."
                return False, f"Download failed (exit {exc.code})."
            except Exception as exc:
                return False, f"Download failed: {exc}"

        def done(result: tuple[bool, str]) -> None:
            try:
                if not self.root.winfo_exists():
                    return
                self.task_progress.stop()
                self.task_progress.configure(mode="determinate")
                self.download_progress["value"] = 100 if result[0] else 0
                self._set_busy(False)
                success, details = result
                if success:
                    self.status_var.set("Status: Download completed.")
                    self.stage_var.set("Download stage: done")
                    self.log_info("Saved: " + details)
                    Messagebox.show_info("Download completed.\n\n" + details, "VidVortex", parent=self.root)
                else:
                    if details == "Download cancelled.":
                        self.status_var.set("Status: Download cancelled.")
                        self.stage_var.set("Download stage: cancelled")
                        self.log_warn_gui(details)
                    else:
                        self.status_var.set("Status: Download failed.")
                        self.stage_var.set("Download stage: failed")
                        self.log_error(details)
                        Messagebox.show_error(details, "VidVortex", parent=self.root)
            except tk.TclError:
                pass

        self._run_bg(worker, done)

    def on_cancel_download(self) -> None:
        controller = self.download_cancel_controller
        if controller is None:
            return
        controller.request_cancel()
        self.status_var.set("Status: Cancelling download...")
        self.stage_var.set("Download stage: cancelling")
        if self.cancel_btn is not None:
            self.cancel_btn.configure(state="disabled")

    def on_open_downloads(self) -> None:
        folder = self.base_dir
        try:
            system_name = platform.system().lower()
            if system_name == "windows":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif system_name == "darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except Exception as exc:
            Messagebox.show_error(f"Could not open folder: {exc}", "VidVortex", parent=self.root)

    def log_info(self, message: str) -> None:
        self._append_log(f"[info] {message}")

    def log_warn_gui(self, message: str) -> None:
        self._append_log(f"[warn] {message}")

    def log_error(self, message: str) -> None:
        self._append_log(f"[error] {message}")

    def _append_log(self, line: str) -> None:
        try:
            if not self.root.winfo_exists():
                return
            self.log_text.text.configure(state="normal")
            self.log_text.text.insert("end", line + "\n")
            self.log_text.text.see("end")
            self.log_text.text.configure(state="disabled")
        except tk.TclError:
            pass

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = VidVortexApp()
    app.run()


if __name__ == "__main__":
    main()
