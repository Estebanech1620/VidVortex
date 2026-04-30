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

## Get the app

Download the zip for your system from **[GitHub Releases](https://github.com/Estebanech1620/VidVortex/releases)**.

---

## Download And Run (Windows)

1. Download **`VidVortex-windows.zip`** from Releases
2. Extract the zip to any folder
3. Double-click **`setup_windows.bat`** (installs Python, yt-dlp, and ffmpeg if they are missing)
4. After setup finishes, double-click **`VidVortex.exe`**

---

## Download And Run (macOS)

Pick the zip that matches your Mac (**About This Mac** → Chip or Processor):

| Your Mac | Zip file |
|----------|-----------|
| **Apple Silicon** (M1 / M2 / M3 / M4 or later) | **`VidVortex-macos-arm64.zip`** |
| **Intel** | **`VidVortex-macos-intel.zip`** |

Steps:

1. Download the matching zip from Releases
2. Extract it (double-click the zip in Finder)
3. Open the folder and double-click **`RUN_FIRST.command`**
4. If macOS blocks the first launch, open **System Settings → Privacy & Security**, approve VidVortex, then try **`RUN_FIRST.command`** again
5. On first run, follow any prompts to install dependencies (Python, yt-dlp, ffmpeg via Homebrew)

**Notes**

- **Homebrew** is required for the macOS setup step. If you do not have it, install it from [brew.sh](https://brew.sh) first.
- The app is **not** from the Mac App Store, so macOS may show a security warning. Use **Control-click → Open** on the app or launcher the first time if needed.
- Use the **Intel** zip only on Intel Macs and the **Apple Silicon** zip only on Apple Silicon Macs.

---

## Download And Run (Linux)

1. Download **`VidVortex-linux.zip`** from Releases
2. Extract the zip with your file manager
3. Open the folder and run **`RUN_FIRST.desktop`** (or your desktop’s equivalent)
4. Approve running the script if your environment asks
5. On first run, follow any prompts to install Python, yt-dlp, and ffmpeg

---

## What’s in each zip

- The **VidVortex** app (`.exe` on Windows, named **`VidVortex`** on macOS and Linux)
- A **setup** script for that system (`setup_windows.bat`, `setup_macos.sh`, or `setup_linux.sh`)
- On **macOS** and **Linux**, a **first-run launcher** so setup can run before opening the app. **Windows** has no launcher file—run **`setup_windows.bat`**, then **`VidVortex.exe`**.

---

## How to use the app

1. Paste a link
2. Choose **Audio** or **Video**
3. For **YouTube**, if sign-in or “bot” messages appear when loading qualities or downloading, use **Browser for YouTube** on the **Download** tab, or follow the **YouTube cookies** tab in the app for help
4. Click **Load Qualities**
5. Keep **Best Available** or pick a format
6. Click **Download Now**
7. Watch status and progress on the right

### YouTube sign-in issues

If **YouTube** asks you to sign in or blocks quality listing:

- On the **Download** tab, set **Browser for YouTube** to the browser where you are already signed in to YouTube. **Firefox** often works best on Windows for this.
- Use the in-app **YouTube cookies** tab for steps to export a cookies file if the app suggests it.
- After you attach a cookies file, the chosen browser may stay **locked** until you clear the file or use **Unlock YouTube browser** in the app.

App preferences are saved under your normal **user profile** (not inside the `VidVortex` download folders on the desktop).

---

## Where files are saved

On your **Desktop**, the app uses:

- `VidVortex/audio`
- `VidVortex/video`

Logs are shown in the app’s **Activity** area; the app does not write separate log files into those folders.

---

## What needs to be installed

The app relies on:

- **Python 3**
- **yt-dlp**
- **ffmpeg**

The included setup scripts try to install these when they are missing.

---

## Troubleshooting

1. Read messages in the **Activity** panel
2. Check that the link starts with **`http://`** or **`https://`**
3. Try **Load Qualities** again
4. Make sure **yt-dlp** and **ffmpeg** are installed and up to date
5. On **YouTube**, use **Browser for YouTube** or the **YouTube cookies** tab if you see sign-in or bot errors

---

## About

- Made by **Estebanech**
- Site: [estebanech.com](https://estebanech.com)
- Powered by [**yt-dlp**](https://github.com/yt-dlp/yt-dlp) and [**FFmpeg**](https://github.com/FFmpeg/FFmpeg)

---

## License

**Proprietary — all rights reserved.** See [`LICENSE`](LICENSE). You may not use, copy, modify, or distribute the materials in this project without written permission from the copyright holder.

# VidVortex_Public_Source

# VidVortex
