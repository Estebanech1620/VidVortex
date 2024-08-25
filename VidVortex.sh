#!/bin/bash

######################################################################
# VidVortex.sh - The Ultimate YouTube Video and Audio Snatcher
#
# Description:
# VidVortex automates the process of downloading and merging video
# and audio files from YouTube using yt-dlp and ffmpeg. It prioritizes
# the highest available quality (4K or higher) and prompts the user if
# the best available option is less than 1080p. All files are processed
# and stored in a "Video Downloads" folder on your desktop.
######################################################################

# Check for yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo "Error: yt-dlp is not installed. Please install yt-dlp and make sure it's in your PATH."
    exit 1
fi

# Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install ffmpeg and make sure it's in your PATH."
    exit 1
fi

LOGFILE="$HOME/Desktop/Video Downloads/download_and_merge.log"

# Create "Video Downloads" directory on the user's desktop
DOWNLOAD_DIR="$HOME/Desktop/Video Downloads"
OUTPUT_DIR="$DOWNLOAD_DIR"

mkdir -p "$DOWNLOAD_DIR"

# Redirect output to the log file
exec > >(tee -a "$LOGFILE") 2>&1

echo "Starting the VidVortex process..."

# Prompt for the video URL
read -p "Enter the video URL: " URL

echo "Processing URL: $URL"

echo "Getting available formats..."
FORMATS=$(yt-dlp -F "$URL")
echo "Available formats: $FORMATS"

echo "Selecting the best video format..."
VIDEO_FORMAT=$(echo "$FORMATS" | grep -Eo '^[0-9]+.*4320p' | head -1 | awk '{print $1}')
if [ -z "$VIDEO_FORMAT" ]; then
    VIDEO_FORMAT=$(echo "$FORMATS" | grep -Eo '^[0-9]+.*2160p' | head -1 | awk '{print $1}')
fi
if [ -z "$VIDEO_FORMAT" ]; then
    VIDEO_FORMAT=$(echo "$FORMATS" | grep -Eo '^[0-9]+.*1440p' | head -1 | awk '{print $1}')
fi
if [ -z "$VIDEO_FORMAT" ]; then
    VIDEO_FORMAT=$(echo "$FORMATS" | grep -Eo '^[0-9]+.*1080p' | head -1 | awk '{print $1}')
fi
if [ -z "$VIDEO_FORMAT" ]; then
    VIDEO_FORMAT=$(echo "$FORMATS" | grep -Eo '^[0-9]+.*720p' | head -1 | awk '{print $1}')
    if [ -n "$VIDEO_FORMAT" ]; then
        echo "Warning: The best available resolution is less than 1080p."
        echo "The best available option is 720p. Do you want to proceed? (y/n)"
        read -p "Enter your choice: " PROCEED
        if [ "$PROCEED" != "y" ]; then
            echo "Skipping download for $URL."
            exit 1
        fi
    fi
fi

echo "Selected video format: $VIDEO_FORMAT"

echo "Selecting the best audio format..."
AUDIO_FORMAT=$(echo "$FORMATS" | grep -Eo '^[0-9]+.*m4a' | head -1 | awk '{print $1}')

echo "Selected audio format: $AUDIO_FORMAT"

if [ -z "$VIDEO_FORMAT" ] || [ -z "$AUDIO_FORMAT" ]; then
    echo "Error: Unable to find suitable video or audio format for $URL"
    exit 1
fi

echo "Snatching video..."
yt-dlp --restrict-filenames -f "$VIDEO_FORMAT" "$URL" -o "$DOWNLOAD_DIR/%(title)s.%(ext)s"

echo "Snatching audio..."
yt-dlp --restrict-filenames -f "$AUDIO_FORMAT" "$URL" -o "$DOWNLOAD_DIR/%(title)s.%(ext)s"

echo "Getting video title..."
TITLE=$(yt-dlp --get-filename --restrict-filenames -o "%(title)s" "$URL" | sed 's/\.[^.]*$//' | tr ' ' '_')

echo "Sanitized video title: $TITLE"

VIDEO_FILE="$DOWNLOAD_DIR/${TITLE}.mp4"
AUDIO_FILE="$DOWNLOAD_DIR/${TITLE}.m4a"

if [[ -f "$VIDEO_FILE" && -f "$AUDIO_FILE" ]]; then
    echo "Merging video and audio..."
    ffmpeg -i "$VIDEO_FILE" -i "$AUDIO_FILE" -c:v libx264 -pix_fmt yuv420p -profile:v baseline -level 3.0 -c:a aac -b:a 192k -movflags +faststart "$OUTPUT_DIR/${TITLE}_output.mp4"

    echo "Cleaning up snatched files..."
    rm "$VIDEO_FILE"
    rm "$AUDIO_FILE"
else
    echo "Error: Snatched files not found for $URL"
fi

echo "VidVortex process completed successfully!"

# Open the log file (cross-platform)
if [[ "$OST
