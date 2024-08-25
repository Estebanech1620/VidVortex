# VidVortex

**VidVortex** is a powerful, cross-platform Bash script that makes it easy to download and merge YouTube videos and audio in the highest quality. It works seamlessly on Windows, Linux, and macOS.

## Features

- **Cross-Platform**: Runs on Windows, Linux, and macOS.
- **High-Quality Downloads**: Prioritizes 4K resolution or higher. If the best available resolution is less than 1080p, it prompts you before proceeding.
- **Automatic Merging**: Merges downloaded video and audio into a single file using `ffmpeg`.
- **Simple Setup**: Automatically creates a "Video Downloads" folder on your desktop, where all files are processed.

## Requirements

Before using VidVortex, ensure that the following tools are installed:

- **yt-dlp**: A YouTube downloader that supports a wide variety of sites. [Install instructions](https://github.com/yt-dlp/yt-dlp#installation)
- **ffmpeg**: A tool to process and merge video/audio files. [Install instructions](https://ffmpeg.org/download.html)

### Installation of Dependencies

#### Windows

1. **yt-dlp**: 
   - Download the `yt-dlp.exe` from the [official releases page](https://github.com/yt-dlp/yt-dlp/releases/latest).
   - Add the directory containing `yt-dlp.exe` to your system's PATH.

2. **ffmpeg**:
   - Download `ffmpeg` from [ffmpeg.org](https://ffmpeg.org/download.html).
   - Extract the files and add the `bin` directory containing `ffmpeg.exe` to your system's PATH.

#### macOS

1. **yt-dlp**:
   - Install via Homebrew: `brew install yt-dlp`

2. **ffmpeg**:
   - Install via Homebrew: `brew install ffmpeg`

#### Linux

1. **yt-dlp**:
   - Install via your package manager or download directly from the [official releases page](https://github.com/yt-dlp/yt-dlp/releases/latest).

2. **ffmpeg**:
   - Install via your package manager, e.g., `sudo apt install ffmpeg`.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/VidVortex.git
   cd VidVortex
   ```

2. **Make the Script Executable**:
   ```bash
   chmod +x VidVortex.sh
   ```

   ### Installing `yt-dlp` and `ffmpeg`

#### **For Windows**

1. **Install `yt-dlp`**:
   - **Download**: Go to the [yt-dlp releases page](https://github.com/yt-dlp/yt-dlp/releases/latest) and download the `yt-dlp.exe` file.
   - **Move to a Folder**: Place the downloaded `yt-dlp.exe` file in a folder (e.g., `C:\yt-dlp\`).
   - **Add to PATH**:
     - Right-click on `This PC` or `Computer` and select `Properties`.
     - Click on `Advanced system settings` on the left.
     - Click `Environment Variables`.
     - Under `System variables`, find the `Path` variable, select it, and click `Edit`.
     - Click `New` and add the path where you placed `yt-dlp.exe` (e.g., `C:\yt-dlp\`).
     - Click `OK` to close all windows.

2. **Install `ffmpeg`**:
   - **Download**: Go to the [ffmpeg.org download page](https://ffmpeg.org/download.html) and download the Windows build.
   - **Extract**: Unzip the downloaded file to a folder (e.g., `C:\ffmpeg\`).
   - **Add to PATH**:
     - Follow the same steps as above to open `Environment Variables`.
     - Add the `bin` directory inside the `ffmpeg` folder to the `Path` variable (e.g., `C:\ffmpeg\bin\`).
     - Click `OK` to close all windows.

#### **For macOS**

1. **Install `Homebrew`** (if you don’t have it):
   - Open Terminal and run:
     ```bash
     /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
     ```

2. **Install `yt-dlp`**:
   - In Terminal, run:
     ```bash
     brew install yt-dlp
     ```

3. **Install `ffmpeg`**:
   - In Terminal, run:
     ```bash
     brew install ffmpeg
     ```

#### **For Linux**

1. **Install `yt-dlp`**:
   - **Using pip**:
     - Open Terminal and run:
       ```bash
       python3 -m pip install -U yt-dlp
       ```
   - **Using your package manager**:
     - On Ubuntu/Debian:
       ```bash
       sudo apt update
       sudo apt install yt-dlp
       ```
     - On Fedora:
       ```bash
       sudo dnf install yt-dlp
       ```

2. **Install `ffmpeg`**:
   - On Ubuntu/Debian:
     ```bash
     sudo apt update
     sudo apt install ffmpeg
     ```
   - On Fedora:
     ```bash
     sudo dnf install ffmpeg
     ```

### Verify Installation

After installing, you can verify that both `yt-dlp` and `ffmpeg` are correctly installed by opening your terminal or command prompt and running:

```bash
yt-dlp --version
ffmpeg -version
```

If both commands return version information, the installations were successful.

## Usage

1. **Run the Script**:
   ```bash
   ./VidVortex.sh
   ```

2. **Enter the YouTube Video URL**: When prompted, paste the URL of the YouTube video you wish to download.

3. **Follow the Prompts**:
   - The script will automatically select the best video and audio formats available.
   - If the best available resolution is below 1080p, it will ask if you wish to proceed.

4. **Check Your Downloads**:
   - All downloads are saved to the "Video Downloads" folder on your desktop.
   - Logs are also saved in the same folder and will open automatically after the process completes.

## Troubleshooting

- **Permissions Denied**: If you encounter a "Permissions Denied" error, ensure you have made the script executable using the `chmod +x VidVortex.sh` command.
- **Missing Dependencies**: Ensure `yt-dlp` and `ffmpeg` are installed and accessible from your system's PATH.

## Contributing

Feel free to fork this repository, make changes, and submit a pull request. Contributions are welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
