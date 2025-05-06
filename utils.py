# utils.py
"""
General utility functions for the YouTube Downloader application.
Includes functions for string manipulation (ANSI stripping), URL validation,
default directory retrieval, and filename sanitization.
"""
import re
import os
import datetime
from urllib.parse import urlparse, ParseResult
from typing import Tuple # For type hinting

import config # Application configuration
from logger import logger # Application logger

def strip_ansi(text: str) -> str:
    """
    Removes ANSI escape sequences (e.g., color codes) from a string.

    Args:
        text: The input string, potentially containing ANSI codes.

    Returns:
        The string with ANSI codes removed. If input is not a string,
        it's converted to string.
    """
    if not isinstance(text, str):
        return str(text) 
    ansi_escape_pattern = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape_pattern.sub('', text)

def is_youtube_url(url: str) -> bool:
    """
    Checks if the URL's hostname is a recognized YouTube domain.

    Args:
        url: The URL string to validate.

    Returns:
        True if the URL is a valid YouTube domain, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    try:
        parsed_url: ParseResult = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            return False 
        
        hostname = parsed_url.netloc.lower()
        youtube_domains = [
            'youtube.com', 'www.youtube.com', 'm.youtube.com',
            'music.youtube.com', 'youtu.be'
        ]
        return any(domain == hostname for domain in youtube_domains)
    except ValueError: 
        logger.log(f"ValueError parsing URL for YouTube check: {url}", file_only=True)
        return False
    except Exception as e: 
        logger.log(f"Unexpected error validating YouTube URL '{url}': {e}", file_only=True)
        return False

def get_default_output_dir() -> str:
    """
    Determines and returns the default output directory for downloads.
    Attempts to create `config.DEFAULT_OUTPUT_SUBDIR` within the user's
    Documents or home directory. Falls back to a directory in the current
    working path if user-specific directories are not accessible/creatable.

    Returns:
        The absolute path to the determined default output directory.
    """
    preferred_base_dir: str
    try:
        home_dir = os.path.expanduser("~")
        documents_dir = os.path.join(home_dir, "Documents")
        preferred_base_dir = documents_dir if os.path.isdir(documents_dir) else home_dir
        default_dir_path = os.path.join(preferred_base_dir, config.DEFAULT_OUTPUT_SUBDIR)
    except Exception: # pylint: disable=broad-except
        # Fallback if user home/documents determination fails
        default_dir_path = os.path.join(os.getcwd(), config.FALLBACK_OUTPUT_DIR_NAME)
        logger.log(f"Could not determine user-specific default directory. Using fallback: {default_dir_path}", file_only=True)

    try:
        os.makedirs(default_dir_path, exist_ok=True) 
        logger.log(f"Ensured output directory exists: {default_dir_path}", file_only=True)
        return os.path.abspath(default_dir_path)
    except OSError as e:
        logger.log(f"OSError creating/accessing directory '{default_dir_path}': {e}. Using CWD as last resort.", file_only=True)
        # Final fallback: current working directory (absolute path)
        return os.path.abspath(".")


def sanitize_filename(filename_base: str) -> str:
    """
    Sanitizes a base filename by removing illegal characters, stripping whitespace,
    and handling empty or None inputs by using a default name. If sanitization
    results in an empty string, a timestamped default name is generated.

    Args:
        filename_base: The proposed base name for the file. Can be None or empty.

    Returns:
        A sanitized, safe filename string (without file extension).
    """
    if not filename_base: # Handle None or empty string
        base_to_sanitize = config.DEFAULT_FILENAME_BASE
        logger.log(f"Input filename_base was empty, using default: '{base_to_sanitize}'", file_only=True)
    else:
        base_to_sanitize = filename_base

    # Remove characters matched by the regex pattern from config
    sanitized = re.sub(config.ILLEGAL_FILENAME_CHARS_PATTERN, "", base_to_sanitize)
    # Remove leading/trailing whitespace
    sanitized = sanitized.strip()

    # If, after sanitization, the string is empty, generate a default name with timestamp
    if not sanitized:
        timestamp = datetime.datetime.now().strftime(config.TIMESTAMP_FILENAME_FORMAT)
        sanitized = f"{config.DEFAULT_FILENAME_BASE}_{timestamp}"
        logger.log(f"Original filename '{base_to_sanitize}' was empty/invalid after sanitization. Generated: {sanitized}", file_only=True)
        
    return sanitized