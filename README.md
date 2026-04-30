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
3. Double-click **`setup_windows.bat`** (installs Python, yt-dlp, and ffmpeg if they are missing, and **updates yt-dlp** when your package manager has a newer build). The window stays open afterward so you can read any messages; for automated runs use **`setup_windows.bat nopause`**.
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
4. If macOS blocks the first launch, follow **[If macOS blocks VidVortex (security popup)](#if-macos-blocks-vidvortex-security-popup)** below, then try **`RUN_FIRST.command`** again
5. On first run, **`RUN_FIRST.command`** installs **Homebrew** if needed, then **Python**, **yt-dlp**, and **ffmpeg**, and refreshes them so builds stay current (needs **internet**; macOS may ask for your **password** / **Command Line Tools**)
6. **After setup**, open the app with **`VidVortex.command`** every time (double-click it in the same folder). It loads Homebrew’s **`PATH`** then starts **`VidVortex.bin`** (the actual program). **Do not** double-click **`VidVortex.bin`** from Finder—macOS gives it almost no **`PATH`**, so downloads often fail even when Homebrew’s **`yt-dlp`** works in Terminal.

#### If macOS blocks VidVortex (security popup)

Downloaded apps that are **not** from the Mac App Store are often blocked the first time. macOS may show an alert (for example that the app **can’t be opened** because it was **not from the App Store**), or a notification that leads you toward **Privacy & Security**.

Do this:

1. Open **System Settings** (**Apple menu** → **System Settings**).
2. In the sidebar, click **Privacy & Security**.
3. Scroll down to the **Security** section.
4. Look for a message about **VidVortex** (or “was blocked”) and click **Open Anyway**. Enter your Mac password if macOS asks.
5. Open **`RUN_FIRST.command`** or **`VidVortex.command`** again.

If there is no **Open Anyway** button yet:

- **Control-click** (right-click) **`VidVortex.command`** or **`RUN_FIRST.command`** in Finder → **Open** → click **Open** in the dialog to confirm, **or**
- Try double-clicking once more after step 4 so macOS registers your choice.

**Notes**

- **Homebrew** is installed automatically on first setup if it isn’t already there (official installer). You still need **internet**; macOS may prompt for **Command Line Tools** or your **password**. If auto-install fails, install manually from [brew.sh](https://brew.sh).
- Use the **Intel** zip only on Intel Macs and the **Apple Silicon** zip only on Apple Silicon Macs.

#### Homebrew not writable (chown fix)

If setup stops with **`/opt/homebrew is not writable`**, **`brew update` Permission denied**, or VidVortex prints the same **`chown`** hint, Homebrew’s folder is owned by the wrong user (often after **`sudo brew`**).

Do this **once** in **Terminal** — **not** in `~/.zprofile` or `~/.zshrc` (never auto-run `sudo` from your shell profile):

1. Prefer this if **`brew`** works:

```bash
sudo chown -R "$(whoami)" "$(brew --prefix)"
```

2. If **`brew`** isn’t on your PATH yet, **Apple Silicon** (M1+):

```bash
sudo chown -R "$(whoami)" /opt/homebrew
```

3. Many **Intel** Macs:

```bash
sudo chown -R "$(whoami)" /usr/local
```

Enter your Mac password when prompted (the cursor won’t move — that’s normal). Then run **`RUN_FIRST.command`** again.

---

## Download And Run (Linux)

1. Download **`VidVortex-linux.zip`** from Releases
2. Extract the zip with your file manager
3. Open the folder and run **`RUN_FIRST.desktop`** (or your desktop’s equivalent)
4. Approve running the script if your environment asks
5. On first run, follow any prompts to install Python, yt-dlp, and ffmpeg

---

## What’s in each zip

- The **VidVortex** app (`.exe` on Windows; on macOS **`VidVortex.bin`** opened via **`VidVortex.command`**; **`VidVortex`** executable on Linux)
- A **setup** script for that system (`setup_windows.bat`, `setup_macos.sh`, or `setup_linux.sh`)
- On **macOS**: **`RUN_FIRST.command`** (first-time setup + launch), **`VidVortex.command`** (daily launcher—the **`.bin`** file is only the built executable), and **`setup_macos.sh`**. On **Linux**, a **first-run launcher** so setup runs before the app. **Windows** has no launcher—run **`setup_windows.bat`**, then **`VidVortex.exe`**.

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

- On the **Download** tab, set **Browser for YouTube** to a browser yt-dlp can read cookies from — **prefer Firefox**. **Chrome / Edge / Chromium browsers often do not work** for automatic cookie import anymore (see below).
- Use the in-app **YouTube cookies** tab for steps to export a cookies file if the app suggests it.
- After you attach a cookies file, the chosen browser may stay **locked** until you clear the file or use **Unlock YouTube browser** in the app.

#### macOS and YouTube cookies (common fixes)

These patterns match what **yt-dlp** users report on Mac when **Browser for YouTube** or cookies keep failing:

1. **Prefer Firefox over Chrome or Edge** — **Google Chrome’s cookies often cannot be read by yt-dlp anymore** (app-bound / encrypted storage), on Mac **and** Windows — so **“Browser for YouTube: Chrome” may simply never work** even when you are signed in. The same limitation applies to **Edge**, **Brave**, **Atlas**, and other Chromium-based browsers. **Firefox** keeps cookies in a plain database yt-dlp can use: sign in to YouTube in **Firefox**, set **Browser for YouTube** to **Firefox**, and try again.

   **ChatGPT Atlas** counts as Chromium-based: **yt-dlp does not treat Atlas as its own browser for cookie import**, and the same cookie-protection limits as Chrome apply—so **Atlas in “Browser for YouTube” often will not work** even though you use it daily. Use **Firefox** for YouTube inside VidVortex, **or** attach a **`cookies.txt`** using the in-app **YouTube cookies** instructions (not Atlas auto-read).

2. **Safari** — macOS may deny access to Safari’s cookie data. Grant **Full Disk Access** to VidVortex (macOS does **not** offer an automatic popup for this; you enable it in Settings):

   1. **Apple menu** → **System Settings**
   2. **Privacy & Security** → **Full Disk Access**
   3. Click the **lock** icon if needed and enter your password so you can change settings
   4. Click **+**, select **`VidVortex.bin`** in the folder where you extracted the zip (that is the running executable), then click **Open**
   5. Turn **on** the switch next to **VidVortex** / **`VidVortex.bin`**
   6. **Quit VidVortex completely** (VidVortex menu → Quit, not only closing the window), then open it again  
   *(If you run yt-dlp from **Terminal** instead of the app, add **Terminal** or **iTerm** here the same way.)*

3. **Update yt-dlp** — YouTube changes often; keep yt-dlp current (e.g. after Homebrew setup: `brew upgrade yt-dlp`).

4. **Exported `cookies.txt`** — The file must be **Netscape** format with **Unix (LF)** line endings. **Windows (CRLF)** endings commonly trigger **HTTP 400 Bad Request** when passed to yt-dlp (see [yt-dlp troubleshooting](https://github.com/yt-dlp/yt-dlp/wiki/FAQ)).

5. **Firefox chosen but cookies still fail** — Try these before assuming YouTube or VidVortex is broken:

   - **Update yt-dlp** (`brew upgrade yt-dlp`) or install the [**latest nightly**](https://github.com/yt-dlp/yt-dlp/wiki/Installation) — YouTube often needs a **very** recent yt-dlp even when Firefox cookies are fine.
   - **Isolate yt-dlp in Terminal** (proves whether the problem is Firefox vs the app vs PATH):  
     `yt-dlp -v --cookies-from-browser firefox -F "https://www.youtube.com/watch?v=jNQXAC9IVRw"`  
     If this errors, copy the **last lines** of output — they name the real cause (profile not found, DB locked, missing cookies table, sign-in required, etc.).
   - **VidVortex-only**: Clear any attached **`cookies.txt`** and use **Unlock YouTube browser** so the app is not mixing “file cookies” with **Browser for YouTube: Firefox**.
   - **Profile mismatch**: If you use multiple Firefox profiles or **Firefox Developer Edition**, yt-dlp may read the wrong one. In Firefox open **`about:profiles`**, note the **default** profile name; yt-dlp accepts **`firefox:ProfileFolderName`** (see [yt-dlp readme](https://github.com/yt-dlp/yt-dlp#usage)).
   - **Fresh session**: Quit Firefox fully, open YouTube in Firefox, confirm you’re logged in, visit the video once, then try VidVortex again (session cookies refresh).

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

The included setup scripts install these when they are missing and **keep them current**: **macOS** installs **Homebrew** automatically if needed, then refreshes **Python**, **yt-dlp**, and **ffmpeg** on each **`RUN_FIRST.command`**; **Linux** uses your distro packages; **Windows** uses winget/choco/scoop when available.

---

## Troubleshooting

1. Read messages in the **Activity** panel
2. Check that the link starts with **`http://`** or **`https://`**
3. Try **Load Qualities** again
4. Make sure **yt-dlp** and **ffmpeg** are installed and up to date
5. On **YouTube**, use **Browser for YouTube** or the **YouTube cookies** tab if you see sign-in or bot errors (on **macOS**, try **Firefox** first and see **macOS and YouTube cookies** above)
6. On **macOS**, if the app or **`RUN_FIRST.command`** won’t run and you see a security warning, follow **[If macOS blocks VidVortex (security popup)](#if-macos-blocks-vidvortex-security-popup)** above
7. On **macOS**, if qualities fail or downloads never start but **`yt-dlp -F`** works in Terminal, always open **`VidVortex.command`** (not **`VidVortex.bin`**), or run **`VidVortex.bin`** only from Terminal after **`eval "$(brew shellenv)"`**
8. On **macOS**, if setup says **`/opt/homebrew is not writable`** or **`brew`** cannot update, see **[Homebrew not writable (chown fix)](#homebrew-not-writable-chown-fix)** above

---

## Packaging (maintainers)

CI builds **`VidVortex-windows.zip`** with **`app/scripts/build_windows.ps1`** after overlaying this repo’s **`scripts/`** into the application checkout (**`app/`**).

**Updating the zip on GitHub Releases:** Pushing commits alone does not change release downloads. Assets upload when you **push a `v*` tag**, or when you run **Actions → Build Cross-Platform Packages → Run workflow** and set **release_tag** to an **existing** tag (for example `v1.2.0`). Leave **release_tag** empty if you only want workflow artifacts (the Releases page stays unchanged).

To rebuild the Windows zip **without** running PyInstaller again (for example after changing **`setup_windows.bat`**), use **`dist/windows/VidVortex.exe`** from a previous build—or pass any **`VidVortex.exe`** path:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/repack_windows_zip.ps1
powershell -ExecutionPolicy Bypass -File scripts/repack_windows_zip.ps1 path\to\VidVortex.exe
```

Output is **`dist/VidVortex-windows.zip`** (same layout as CI: **`VidVortex.exe`** + **`setup_windows.bat`**).

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
