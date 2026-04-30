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

The release zips include setup scripts so dependencies can be installed when missing.

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

## On This Repository

This public repository keeps downloads on **GitHub Releases**. Grab the zip for your OS there.

---

## License

MIT