# yt2mp3mp4

A simple and user-friendly desktop application for downloading YouTube videos as MP4 or audio as MP3, with quality selection and filesize estimation.

**Current Version:** `3.0.1` (Corresponds to `config.APP_VERSION`)

## Features

*   Download YouTube videos in MP4 format.
*   Extract and convert audio to MP3 format.
*   Selectable video quality (480p, 720p, 1080p, 4K where available).
*   Selectable audio quality for MP3 (Low, Medium, High bitrate).
*   Displays video title and thumbnail.
*   Estimates download/conversion filesize before starting.
    *   Provides direct estimates when available from YouTube.
    *   Uses bitrate-based heuristics as a fallback (clearly marked as "Rough est: ~").
*   User-friendly interface with progress display:
    *   Indeterminate (bouncing) progress bar for preparatory stages or when download size is unknown.
    *   Determinate (filling) progress bar with percentage display during active downloads with known sizes.
*   Option to specify output directory and filename.
*   Prompts to overwrite if the output file already exists.
*   Opens the output directory upon successful download.
*   Informative status messages and error handling.
*   Debug logging for troubleshooting (creates `debug.log`).

## Installation

This application is written in Python and requires a few dependencies.

### Prerequisites

1.  **Python:** Version 3.10 or higher is required. You can download Python from [python.org](https://www.python.org/).
    *   Ensure Python is added to your system's PATH during installation.
2.  **pip:** Python's package installer. It usually comes with Python. If not, see [pip installation guide](https://pip.pypa.io/en/stable/installation/).
3.  **FFmpeg (for MP3 conversion):** `yt-dlp` (which this application uses) requires FFmpeg to be installed and accessible in your system's PATH for converting video to MP3 and for merging separate video/audio streams into MP4.
    *   **Windows:** Download from [FFmpeg Official Builds](https://ffmpeg.org/download.html#build-windows) (e.g., gyan.dev or BtbN). Extract the `bin` folder contents (like `ffmpeg.exe`, `ffprobe.exe`) to a directory and add that directory to your system's PATH environment variable.
    *   **macOS:** Use Homebrew: `brew install ffmpeg`
    *   **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install ffmpeg`
    *   **Linux (Fedora):** `sudo dnf install ffmpeg`

### Steps

1.  **Clone or Download the Repository:**
    If this project is hosted on a Git repository (e.g., GitHub):
    ```bash
    git clone https://github.com/Lolfaceftw/yt2mp3mp4
    cd yt2mp3mp4
    ```
    Alternatively, download the project files (e.g., as a ZIP) and extract them to a folder on your computer.

2.  **Navigate to the Project Directory:**
    Open your terminal or command prompt and navigate to the folder where you placed the project files (e.g., `yt2mp3`).
    ```bash
    cd path/to/your/project/yt2mp3mp4
    ```

3.  **Create a Virtual Environment (Recommended):**
    This creates an isolated environment for the project's dependencies.
    ```bash
    python -m venv .venv 
    ```
    Activate the virtual environment:
    *   Windows: `.venv\Scripts\activate`
    *   macOS/Linux: `source .venv/bin/activate`

4.  **Install Dependencies:**
    The application uses a `run.py` script that will check for and offer to install missing Python packages. Run:
    ```bash
    python run.py
    ```
    The script will check for:
    *   `Pillow` (for image handling)
    *   `yt-dlp` (the core YouTube downloader)
    *   `validators` (for URL validation)
    *   `Tkinter` (GUI library, usually part of Python standard library but verified)

    If any are missing (and are pip-installable), it will prompt you:
    `Install missing packages now? [Y/n]`
    Press `Y` (or Enter) to allow automatic installation.

    If you prefer to install them manually (especially if the automatic script fails or if you don't want to run it with install privileges directly):
    ```bash
    pip install Pillow yt-dlp validators
    ```

## Usage

1.  **Ensure your virtual environment is activated** (if you created one):
    *   Windows: `path\to\your\project\yt2mp3mp4\.venv\Scripts\activate`
    *   macOS/Linux: `source path/to/your/project/yt2mp3mp4/.venv/bin/activate`

2.  **Run the Application:**
    From the project's root directory (e.g., `yt2mp3mp4`), execute:
    ```bash
    python run.py
    ```
    This will launch the `gui.py` script, which is the main application window.

3.  **Using the GUI:**
    *   **YouTube Link:** Paste the full URL of the YouTube video you want to download. The application will attempt to fetch video information (title, thumbnail).
    *   **Preferred Output:**
        *   **MP3 Audio:** Select this to extract audio and convert it to MP3.
        *   **MP4 Video:** Select this to download the video.
    *   **Quality:**
        *   Based on your output choice, a quality dropdown will be populated.
        *   For MP3, this refers to the target bitrate (e.g., 192 kbps).
        *   For MP4, this refers to the maximum video resolution (e.g., 720p, 1080p). Options are only enabled if the source video offers that quality or higher.
    *   **Filesize Estimate:** After selecting a quality, an estimated filesize will be displayed.
        *   `Est. size:` - Based on direct information, usually accurate.
        *   `Rough est: ~` - Based on bitrate calculations, can vary significantly.
        *   `Size: Unknown` - Information couldn't be determined.
    *   **Save to Directory:** Shows the current output directory. Click "Browse..." to choose a different folder.
    *   **Filename (optional):** You can specify a custom filename (without extension). If left blank, the video's title will be used.
    *   **Download & Convert:** Click this button to start the process.
        *   The progress bar will indicate activity. If download percentage is available, it will fill up, and the percentage will be shown below it.
        *   Status messages will update you on the progress.
    *   **File Exists Prompt:** If the target output file already exists, you will be prompted to either overwrite it or skip the download.
    *   **Completion:** Upon successful download, a message will confirm, and the output folder should open automatically.

## Project Structure

The project is organized into several Python files:

*   **`run.py`**: The main entry point. Handles Python version checks and dependency management before launching the GUI.
*   **`gui.py`**: Contains the main `YoutubeDownloaderApp` class, which defines the entire graphical user interface, event handling, and orchestrates the download process.
*   **`config.py`**: Stores all application-wide constants and settings (e.g., version, fonts, quality lists, default paths). This makes customization easier.
*   **`logger.py`**: Provides a simple singleton logger for logging messages to the console and a `debug.log` file (if `DEBUG_MODE` is True in `config.py`).
*   **`utils.py`**: Contains general utility functions used across the application (e.g., `sanitize_filename`, `is_youtube_url`, `get_default_output_dir`, `strip_ansi`).
*   **`estimator.py`**: Handles the logic for estimating video/audio filesize before download, using direct metadata or bitrate-based heuristics.
*   **`gui_tooltip.py`**: A simple class to create and manage tooltips for GUI widgets.
*   **`gui_widgets.py`** (If used, based on previous refactoring iterations): Could contain helper functions to create logical groups of UI widgets, aiming to make `gui.py` cleaner. *(Note: The current iteration of `gui.py` might be creating widgets directly if the horizontal layout was prioritized over this specific modularization step).*

## Troubleshooting

*   **"FFmpeg not found" error during MP3 conversion:** Ensure FFmpeg is installed correctly and its `bin` directory (containing `ffmpeg.exe` or `ffmpeg`) is added to your system's PATH environment variable. Restart your terminal/command prompt after updating PATH.
*   **Download errors / "Video unavailable":**
    *   Check if the YouTube link is correct and the video is publicly accessible.
    *   Your internet connection might be down.
    *   `yt-dlp` might need an update if YouTube changes its site structure. You can try updating it within your virtual environment: `pip install --upgrade yt-dlp`
*   **GUI doesn't start / Tkinter errors:**
    *   Ensure you have a compatible Python version (3.10+).
    *   Make sure Tkinter is properly installed with your Python distribution. This is usually standard, but on some Linux systems, you might need to install it separately (e.g., `sudo apt install python3-tk`).
*   **Debug Log:** If you encounter issues, the `debug.log` file (created in the same directory as the scripts when `DEBUG_MODE` is `True` in `config.py`) can provide detailed information about the application's operations and any errors.

