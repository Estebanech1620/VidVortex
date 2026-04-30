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
3. Double-click `RUN_FIRST.bat` (installs Python, yt-dlp, ffmpeg if missing)
4. The script launches `VidVortex.exe`

---

## Download And Run (macOS)

1. Download `VidVortex-macos.zip` from Releases
2. Extract the zip
3. Run `chmod +x RUN_FIRST.sh` once if needed
4. Run `./RUN_FIRST.sh` in Terminal (installs Python, yt-dlp, ffmpeg if missing)
5. If macOS blocks launch, allow it in Security settings and run again

---

## Download And Run (Linux)

1. Download `VidVortex-linux.zip` from Releases
2. Extract the zip
3. Run `chmod +x RUN_FIRST.sh` once if needed
4. Run `./RUN_FIRST.sh` in Terminal (installs Python, yt-dlp, ffmpeg if missing)
5. The script launches `VidVortex`

---

## Zip Contents

Each OS zip includes:

- Main app executable (`VidVortex.exe` or `VidVortex`)
- First-run launcher (`RUN_FIRST.bat` on Windows, `RUN_FIRST.sh` on Linux/macOS)
- Dependency installer for that OS:
  - `setup_windows.bat`
  - `setup_linux.sh`
  - `setup_macos.sh`

---

## How To Use Inside The App

1. Paste URL
2. Choose **Mode**:
   - Audio
   - Video
3. Click **Load Qualities**
4. Keep **Best Available** or choose specific quality
5. Click **Download Now**
6. Watch status and progress bars on the right

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

The release zips already include first-run setup scripts. If you run from source, use:

- Windows: `scripts\setup_windows.bat`
- Linux: `scripts/setup_linux.sh`
- macOS: `scripts/setup_macos.sh`

---

## About

- Developed by Estebanech
- Portfolio: [estebanech.com](https://estebanech.com)
- Powered by `yt-dlp` and `ffmpeg`
- I bulit this with the intention of always saving the best quality audio or video of things that i loved, without using skertchy websited full of ads.

---

## Troubleshooting

1. Check right-side logs in the app
2. Confirm URL is valid (`http` / `https`)
3. Click **Load Qualities** again for the current link
4. Ensure `yt-dlp` and `ffmpeg` are installed

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
# VidVortex