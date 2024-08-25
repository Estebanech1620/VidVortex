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

3. **Set Up Dependencies**:
   - Install `yt-dlp` and `ffmpeg` if you haven't already.

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

---

### Key Points in the README:
- **Introduction**: Briefly introduces what VidVortex does.
- **Features**: Highlights key features.
- **Requirements**: Lists dependencies and how to install them.
- **Installation**: Step-by-step guide to getting started.
- **Usage**: Instructions on how to use the script.
- **Troubleshooting**: Common issues and solutions.
- **Contributing**: Encourages contributions and provides a license.

This README should help users understand what VidVortex is, how to set it up, and how to use it effectively. Feel free to customize it further based on your preferences!
