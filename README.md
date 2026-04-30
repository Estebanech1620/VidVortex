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

1. Download `VidVortex-macos.zip` from Releases
2. Extract the zip (double-click it in Finder)
3. Open the extracted folder and double-click `RUN_FIRST.command`
4. If macOS blocks first launch, open **System Settings → Privacy & Security**, approve VidVortex, then double-click `RUN_FIRST.command` again
5. On first run, follow any installer prompts (Python, yt-dlp, ffmpeg via Homebrew)

Note: macOS may open a short setup window while installers run. You should not need to type commands yourself.

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
- Launch helper (`RUN_FIRST.command` on macOS; `RUN_FIRST.desktop` on Linux)
- Dependency installer for that OS:
  - `setup_windows.bat`
  - `setup_linux.sh`
  - `setup_macos.sh`

---

## Open The App (build from this repo on Windows)

1. Double-click `build_app.bat`
2. Wait until it finishes
3. Open the `app` folder
4. Double-click `VidVortex.exe`

---

## Open The App (macOS / Linux from source)

1. Open your VidVortex project folder
2. Build/package the app for that OS (see project scripts or PyInstaller specs)
3. Open the output app folder
4. Launch the VidVortex app
5. If needed, allow execution in Security settings or file permissions

---

## App File Location

After building on Windows, the app is here:

- `app\VidVortex.exe`

For macOS/Linux, the output app path depends on your packaging format.

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

## Main Files

- `build_app.bat` — builds the app (Windows)
- `app\VidVortex.exe` — app you open after a Windows build
- `vidvortex_app.py` — app UI code
- `vidvortex.py` — download engine

---

## Git-Friendly Workflow

Use this structure to keep the repo clean and easy to maintain:

- Keep source files in version control (`vidvortex.py`, `vidvortex_app.py`, `build_app.bat`, docs)
- Do not commit local build output folders or temporary artifacts
- Write clear commit messages that explain the user-facing change
- Keep README updates in the same commit as related behavior/UI changes
- Tag stable versions before sharing builds so users can download known-good releases

Suggested branch naming:

- `feature/<short-name>`
- `fix/<short-name>`
- `docs/<short-name>`

---

## On This Repository

Prebuilt downloads are on **GitHub Releases** for the distribution repo. This repo tracks source aligned with [VidVortex_Source](https://github.com/Estebanech1620/VidVortex_Source).

---

## License

MIT
