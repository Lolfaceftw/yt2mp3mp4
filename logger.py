# logger.py
"""
Handles logging for the YouTube Downloader application.

This module provides a singleton Logger class that can log messages to both
the console and a specified log file (if DEBUG_MODE in config is True).
It timestamps log entries and allows for conditional logging based on flags.
"""
import sys
import os
import datetime
from typing import Optional, TextIO, Any # For type hinting

import config # Application configuration

class Logger:
    """
    Singleton class for application-wide logging.
    
    Logs messages with timestamps to the console and, if DEBUG_MODE is enabled,
    to a log file specified in the application's config. This ensures consistent
    logging behavior throughout the application.
    """
    _instance: Optional['Logger'] = None
    _log_file_handle: Optional[TextIO] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> 'Logger':
        """Ensures only one instance of Logger is created (Singleton pattern)."""
        if not cls._instance:
            cls._instance = super(Logger, cls).__new__(cls)
            # Initialize attributes that should only be set once.
            cls._instance._initialized_file = False 
        return cls._instance

    def __init__(self) -> None:
        """
        Initializes the Logger. The log file setup is called here but
        is guarded to run only once for the singleton instance.
        """
        if not hasattr(self, '_initialized_file') or not self._initialized_file:
            self._initialize_log_file()
            self._initialized_file = True # Mark as initialized

    def _initialize_log_file(self) -> None:
        """
        Initializes the log file if DEBUG_MODE is enabled in the config.
        This method is called once when the Logger instance is first created.
        """
        if config.DEBUG_MODE and self._log_file_handle is None:
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                log_file_path = os.path.join(script_dir, config.DEBUG_LOG_FILE_NAME)
                
                self._log_file_handle = open(log_file_path, 'w', encoding='utf-8')
                self._log_to_file_only(f"--- Log Session Start: {self._get_timestamp()} ---")
                self._log_to_file_only(f"Logging to: {log_file_path}")
            except Exception as e:
                sys.stderr.write(f"CRITICAL: Failed to open debug log file '{config.DEBUG_LOG_FILE_NAME}': {e}\n")
                self._log_file_handle = None

    def _get_timestamp(self) -> str:
        """Returns a consistently formatted timestamp string for log entries."""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def _log_to_file_only(self, message: str) -> None:
        """
        Internal method to log messages exclusively to the file, bypassing console output.
        Used for initial log file messages like session start.
        """
        if config.DEBUG_MODE and self._log_file_handle and not self._log_file_handle.closed:
            try:
                self._log_file_handle.write(f"[{self._get_timestamp()}] {message}\n")
                self._log_file_handle.flush()
            except Exception as e:
                sys.stderr.write(f"ERROR: Writing initial log entry to file failed: {e}\n")

    def log(self, *args: Any, console_only: bool = False, file_only: bool = False, **kwargs_for_print: Any) -> None:
        """
        Logs a message to the console and/or the log file based on flags and DEBUG_MODE.

        Args:
            *args: Message parts to be logged, which will be space-separated.
            console_only: If True, logs only to the console.
            file_only: If True, logs only to the file (effective only if DEBUG_MODE is True).
            **kwargs_for_print: Additional keyword arguments for the built-in print() function.
        """
        if not config.DEBUG_MODE and file_only:
            return # Do not log file_only messages if DEBUG_MODE is off

        timestamp = self._get_timestamp()
        message_str = ' '.join(str(arg) for arg in args)
        log_entry = f"[{timestamp}] {message_str}"

        if not file_only:
            try:
                print(log_entry, **kwargs_for_print)
            except Exception as e: 
                sys.stderr.write(f"ERROR: Console logging failed: {e}\nOriginal log: {log_entry}\n")

        if config.DEBUG_MODE and not console_only:
            if self._log_file_handle and not self._log_file_handle.closed:
                try:
                    self._log_file_handle.write(log_entry + "\n")
                    self._log_file_handle.flush()
                except Exception as e: 
                    sys.stderr.write(f"ERROR: File logging failed: {e}\nOffending log: {log_entry}\n")

    def close(self) -> None:
        """Closes the log file if it is open, writing a session end message."""
        if self._log_file_handle and not self._log_file_handle.closed:
            self.log(f"--- Log Session End: {self._get_timestamp()} ---", file_only=True)
            try:
                self._log_file_handle.close()
            except Exception as e: 
                 sys.stderr.write(f"ERROR: Closing debug log file failed: {e}\n")
            self._log_file_handle = None

# Create a single, globally accessible logger instance for use across modules.
logger = Logger()