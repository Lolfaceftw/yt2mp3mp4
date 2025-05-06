# config.py
"""
Configuration constants for the YouTube Downloader application.

This module centralizes settings for easier management and modification,
including application metadata, UI styling, quality definitions, file handling
preferences, and operational timeouts.
"""

APP_NAME = "YouTube Downloader"
APP_VERSION = '3.0.1' # Version indicating docstring and progress bar refinements

# --- Debugging ---
DEBUG_MODE = True # Enables detailed logging and debug features.
DEBUG_LOG_FILE_NAME = "debug.log" # Name of the debug log file.

# --- UI Fonts ---
# Defines standard font configurations used throughout the application.
FONT_DEFAULT_FAMILY = 'Helvetica'
FONT_BOLD = (FONT_DEFAULT_FAMILY, 12, 'bold')
FONT_NORMAL = (FONT_DEFAULT_FAMILY, 10)
FONT_STATUS_ERROR = (FONT_DEFAULT_FAMILY, 10, 'italic')
FONT_INFO_NOTE = (FONT_DEFAULT_FAMILY, 9, 'italic')
FONT_TOOLTIP = ("tahoma", "8", "normal") # Specific font for tooltips.

# --- Quality Settings ---
# Defines available audio and video quality options.
# Each tuple: (Display Label, yt-dlp Parameter, Numeric Value for internal logic/comparison)
AUDIO_QUALITIES: list[tuple[str, str, int]] = [
    ('Low',    '96',  96),
    ('Medium', '192', 192), # Default audio quality
    ('High',   '320', 320)
]
VIDEO_QUALITIES: list[tuple[str, str, int]] = [
    ('480p',  '480',  480),
    ('720p',  '720',  720), # Default video quality
    ('1080p', '1080', 1080),
    ('4K',    '2160', 2160)
]
DEFAULT_AUDIO_QUALITY_IDX: int = 1 # Index in AUDIO_QUALITIES (Medium)
DEFAULT_VIDEO_QUALITY_IDX: int = 1 # Index in VIDEO_QUALITIES (720p)
NO_QUALITY_AVAILABLE_STR: str = "Not available" # String for when no quality options are applicable.

# --- UI Texts ---
# Predefined text for UI elements, promoting consistency and easy modification.
TOOLTIP_TEXT_SIZE_ESTIMATE: str = (
    "Size Estimate Guide:\n--------------------------------\n"
    "• 'Est. size: X MB':\n  Based on direct info from video source. Usually accurate.\n\n"
    "• 'Rough est: ~X MB (bitrate based)':\n  Calculated from video duration & reported bitrate. Actual size may vary, sometimes significantly.\n\n"
    "• 'Size: Unknown':\n  Detailed size info could not be determined."
)

# --- File Handling ---
# Settings related to file and directory management.
DEFAULT_OUTPUT_SUBDIR: str = "YouTube Downloads" # Subdirectory within user's Documents or home.
FALLBACK_OUTPUT_DIR_NAME: str = "YT_Downloader_Output" # Fallback directory name if default fails.
ILLEGAL_FILENAME_CHARS_PATTERN: str = r'[\\/*?:"<>|]' # Regex pattern for characters illegal in filenames.
DEFAULT_FILENAME_BASE: str = "youtube_video" # Default base for downloaded files if no title is available.
TIMESTAMP_FILENAME_FORMAT: str = "%Y%m%d_%H%M%S" # Format for timestamped filenames.

# --- Download Settings ---
USER_CONFIRMATION_TIMEOUT_SECONDS: int = 300 # Timeout for user prompts (e.g., overwrite) in seconds.

# --- Discrepancy Check for Estimates ---
# Defines thresholds for noting significant difference between estimate and actual size.
# Used to inform the user if a heuristic estimate was far off.
DISCREPANCY_LOWER_RATIO: float = 0.5 # Actual size is less than 50% of estimate.
DISCREPANCY_UPPER_RATIO: float = 2.0 # Actual size is more than 200% of estimate.

# --- Thumbnail ---
THUMBNAIL_WIDTH: int = 320
THUMBNAIL_HEIGHT: int = 180
THUMBNAIL_FETCH_TIMEOUT: int = 10 # Seconds for thumbnail download timeout.

# --- yt-dlp options ---
# Base options for yt-dlp calls. Specific format options are added dynamically.
YDL_BASE_OPTS: dict[str, any] = {
    'quiet': True, # Suppress yt-dlp console output.
    'verbose': False, # Set to True for extreme yt-dlp debugging if needed.
    'ignoreerrors': False, # Stop on download errors by default.
    # 'nocheckcertificate': True, # Uncomment if SSL certificate issues are frequent.
    # 'ffmpeg_location': '/path/to/your/ffmpeg', # Optional: if ffmpeg is not in system PATH.
}

# --- UI State Reset Delays ---
SUCCESS_RESET_DELAY_SECONDS: int = 3  # How long "Conversion Complete!" message and bar stay before resetting to Idle.
NON_SUCCESS_RESET_DELAY_SECONDS: int = 5 # How long "Error!" or "Skipped" messages stay before resetting to Idle.