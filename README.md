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

## Open The App (Windows)

1. Double-click `build_app.bat`
2. Wait until it finishes
3. Open the `app` folder
4. Double-click `VidVortex.exe`

---

## Open The App (macOS)

1. Open your VidVortex project folder
2. Build/package the macOS app version
3. Open the output app folder
4. Double-click the VidVortex app
5. If macOS blocks first launch, allow it in Security & Privacy and open again

---

## Open The App (Linux)

1. Open your VidVortex project folder
2. Build/package the Linux app version
3. Open the output app folder
4. Launch the VidVortex app file
5. If needed, allow execution permissions in your file manager

---

## App File Location

After building on Windows, your app is here:

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

- `yt-dlp`
- `ffmpeg`

If missing, install them on your computer before using the app.

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

- `build_app.bat` - builds the app
- `app\VidVortex.exe` - app you open
- `vidvortex_app.py` - app code
- `vidvortex.py` - download engine

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

## License

MIT
