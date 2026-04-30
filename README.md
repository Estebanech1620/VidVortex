# VidVortex

Download audio or video from a URL with a simple desktop app.

## What This App Does

- Paste a URL
- Choose **Video** or **Audio** (Video is the default mode)
- Click **Load Qualities**
- Keep **Best Available** or choose a specific quality
- Save output to:
  - `VidVortex/audio`
  - `VidVortex/video`

---

## Download And Run (Windows)

1. Download `VidVortex-windows.zip` from Releases
2. Extract the zip to any folder
3. Double-click `setup_windows.bat` (installs Python, yt-dlp, ffmpeg if missing)
4. After setup finishes, double-click `VidVortex.exe`

---

## Download And Run (macOS)

There are **two** release zips—pick the one that matches your Mac:

| Your Mac | Download from Releases |
|----------|-------------------------|
| **Apple Silicon** (M1 / M2 / M3 / M4 or later) | `VidVortex-macos-arm64.zip` |
| **Intel** (older Macs) | `VidVortex-macos-intel.zip` |

Steps:

1. Download the correct zip for your CPU (see **About This Mac** → Chip / Processor).
2. Extract the zip (double-click it in Finder).
3. Open the extracted folder and double-click `RUN_FIRST.command`.
4. If macOS blocks first launch, open **System Settings → Privacy & Security**, approve VidVortex, then double-click `RUN_FIRST.command` again.
5. On first run, follow any installer prompts (Python, yt-dlp, ffmpeg via Homebrew).

Note: macOS may open a short setup window while installers run. You should not need to type commands yourself.

**Release zip notes (macOS):**

- **Architecture:** CI builds **arm64** on [`macos-15`](https://github.com/actions/runner-images/blob/main/README.md) and **x86_64** on `macos-15-intel`, so each zip matches one CPU family. Rosetta does **not** run an arm64 app on Intel (and you normally use the Intel zip on Intel Macs).
- **Gatekeeper:** Downloads are usually **not notarized**. If macOS blocks the app, use **System Settings → Privacy & Security** as above, or **Control-click → Open** on `VidVortex` or `RUN_FIRST.command` the first time. Safari/Chrome may mark the folder with quarantine; that is normal for unsigned zips.
- **Setup script:** `setup_macos.sh` requires **[Homebrew](https://brew.sh)**. Users without Homebrew must install it before first run (the script exits with a clear error otherwise).

---

## Download And Run (Linux)

1. Download `VidVortex-linux.zip` from Releases
2. Extract the zip using your file manager
3. Open the extracted folder and double-click `RUN_FIRST.desktop`
4. If your desktop asks for permission to run the script, choose **Run** or **Execute**
5. On first run, follow any installer prompts (Python, yt-dlp, ffmpeg)

Note: Some distributions hide `.desktop` launches behind one approval click the first time.

---

## Zip Contents

Each OS zip includes:

- Main app executable (`VidVortex.exe` or `VidVortex`)
- Dependency installer for that OS:
  - `setup_windows.bat`
  - `setup_linux.sh`
  - `setup_macos.sh`
- **macOS / Linux only:** a launch helper (`RUN_FIRST.command`, `RUN_FIRST.desktop`, or `RUN_FIRST.sh`) that runs setup and starts the app. **Windows** does not ship a launcher in the zip—run `setup_windows.bat`, then `VidVortex.exe`.

---

## Build release zips locally (maintainers)

CI clones **[VidVortex_Source](https://github.com/Estebanech1620/VidVortex_Source)**, copies this repo’s **`scripts/`** and **`release/`** into that tree, then builds (same as overlay in Actions).

**On your machine:** clone **VidVortex_Source**, copy **`scripts`** and **`release`** from this (**VidVortex**) repo into that clone so paths match CI, `cd` into the Source clone, then:

```bat
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

That writes **`dist\VidVortex-windows.zip`** (and `dist\windows\VidVortex.exe`). Linux/macOS: `bash scripts/build_linux.sh` or `bash scripts/build_macos.sh`.

---

## Open The App (build from source)

Development and local builds use **[VidVortex_Source](https://github.com/Estebanech1620/VidVortex_Source)** — for example **`build_app.bat`** on Windows (outputs under `app\`), or **`scripts/build_macos.sh`** / **`scripts/build_linux.sh`** after copying packaging scripts from this repo if needed.

---

## App File Location

After building from **VidVortex_Source** with **`build_app.bat`** on Windows, the exe is typically **`app\VidVortex.exe`** inside that repo. PyInstaller output paths are described in **`scripts/build_*.sh`** and **`build_windows.ps1`**.

---

## How To Use Inside The App

1. Paste URL
2. Choose **Mode**:
   - Audio
   - Video
3. For **YouTube** links, set **Browser for YouTube** on the **Download** tab if the site asks you to sign in or blocks metadata (see [YouTube cookies](#youtube-cookies-youtube-downloads) below)
4. Click **Load Qualities**
5. Keep **Best Available** or choose specific quality
6. Click **Download Now**
7. Watch status and progress bars on the right

---

## YouTube cookies (YouTube downloads)

These options exist so **YouTube** downloads and metadata (`Load Qualities`) work when Google treats traffic like a bot or asks you to sign in. They apply to **YouTube** in the app’s UI; `yt-dlp` may still send cookies to other sites if you paste other URLs.

### Download tab

- **Browser for YouTube** — Choose the browser where you are already logged into [youtube.com](https://www.youtube.com). VidVortex passes that to `yt-dlp` (`--cookies-from-browser`). On Windows, **Firefox** often works more reliably than Chrome/Edge for this shortcut.
- Link: **YouTube cookie help** — Opens the **YouTube cookies** tab with per-browser steps.

### YouTube cookies tab

- Short explanation of why cookies help **YouTube** downloads.
- **YouTube export steps for:** — Dropdown (Google Chrome, Microsoft Edge, Firefox, etc.) with instructions for each.
- **YouTube cookies.txt (upload)** — Choose a Netscape-format `cookies.txt` exported while signed into YouTube (after picking **Browser for YouTube** on Download). **Clear YouTube cookies file** removes the path and unlocks the browser.
- Official **yt-dlp** links for exporting YouTube cookies and the cookies FAQ.

### Locking the browser after upload

After you save a **YouTube cookies.txt** file, **Browser for YouTube** **locks** to the browser you had selected at upload time. That keeps the session aligned with the file. To change it:

- Upload a new `cookies.txt` (re-locks to the current browser choice), or  
- **Clear YouTube cookies file**, or  
- **Unlock YouTube browser** on the Download tab.

Settings (including path, browser, and lock) are stored in your user folder as **`~/.vidvortex/settings.json`** (on Windows: **`%USERPROFILE%\.vidvortex\settings.json`**). The desktop **`VidVortex`** folder is only for downloads.

### Command line (advanced)

The engine also supports `--cookies-from-browser` and `--cookies-file`; see `vidvortex.py --help`. Settings keys `cookies_file`, `cookies_from_browser`, and `cookies_locked_browser` match the desktop app.

---

## Output Location

The app creates this folder on the current user's desktop:

- `VidVortex/audio`
- `VidVortex/video`

VidVortex does **not** write log files under `VidVortex/`. The desktop app shows messages in the **Activity** panel only.

---

## Dependencies

Required runtime dependencies:

- `python3`
- `yt-dlp`
- `ffmpeg`

If missing, install them on your computer before using the app.

Release zips include setup scripts so dependencies can be installed when missing.

---

## About

- Developed by Estebanech
- Portfolio: [estebanech.com](https://estebanech.com)
- Powered by `yt-dlp` and `ffmpeg`
- I built this with the intention of always saving the best quality audio or video of things that I loved, without using sketchy websites full of ads.

---

## Troubleshooting

1. Check right-side logs in the app
2. Confirm URL is valid (`http` / `https`)
3. Click **Load Qualities** again for the current link
4. Ensure `yt-dlp` and `ffmpeg` are installed
5. **YouTube:** If you see sign-in / bot messages, use **Browser for YouTube** or upload **YouTube cookies.txt** on the **YouTube cookies** tab, update `yt-dlp` (`yt-dlp -U`), and try again

---

## Repositories

| Repo | Purpose |
|------|---------|
| **[VidVortex](https://github.com/Estebanech1620/VidVortex)** (this page) | End-user README, release packaging scripts, CI that builds **zips from source pulled at build time**. No application source code in git. |
| **[VidVortex_Source](https://github.com/Estebanech1620/VidVortex_Source)** | Full **Python source**, specs, icons, examples — clone here to develop or build locally. |

---

## Maintainer / Git workflow

- Application code changes belong in **VidVortex_Source**.
- This repo keeps **`.github/workflows`**, **`scripts/`** (PyInstaller + OS setup helpers), and **`release/`** (RUN_FIRST helpers). CI checks out Source into `app/` and overlays those dirs before building.
- Tag **`v*`** here to run Actions and publish release assets.
- Do not commit `vidvortex*.py`, `requirements-desktop.txt`, or build outputs into this repo (see `.gitignore`).

---

## On This Repository

Downloads are on **[GitHub Releases](https://github.com/Estebanech1620/VidVortex/releases)**. **Source code is not stored in this git repository** — only [VidVortex_Source](https://github.com/Estebanech1620/VidVortex_Source).

---

## License

MIT
