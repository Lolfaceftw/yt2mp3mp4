# gui.py
"""
Main GUI application class for the YouTube Downloader.

Handles UI setup, event binding, and orchestrates the download/conversion
process, providing feedback to the user via status messages, progress bars,
and filesize estimates.
"""
import os
import tkinter as tk
from tkinter import filedialog, BooleanVar, messagebox, ttk
from threading import Thread
from io import BytesIO
import urllib.request
import webbrowser
import traceback
from queue import Queue, Empty
import sys # Not strictly needed by this file after refactor, but often kept.
from typing import Optional, Dict, Tuple, List, Any # For type hinting

# Third-party library imports
import validators
import yt_dlp
from PIL import Image, ImageTk

# Local application imports
import config # Application-wide constants and settings
from logger import logger # Centralized logging
from utils import (strip_ansi, is_youtube_url, get_default_output_dir,
                   sanitize_filename) # Utility functions
from estimator import estimate_size # Filesize estimation logic
from gui_tooltip import ToolTip # Custom tooltip class

class YoutubeDownloaderApp:
    """
    Main application class for the YouTube Downloader GUI.
    Manages UI elements, user interactions, metadata fetching, filesize estimation,
    and download/conversion operations via yt-dlp.
    """

    def __init__(self) -> None:
        """Initializes the application, sets up UI, and binds events."""
        logger.log(f"YoutubeDownloaderApp __init__ (Version: {config.APP_VERSION}) started.")
        self._setup_main_window()
        self._init_state_variables()
        self._create_widgets()
        self._layout_widgets()
        self._bind_events()
        self._update_quality_options_ui() # Set initial quality state
        logger.log("YoutubeDownloaderApp __init__ finished.")
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing_application)

    # --- Initialization & Setup Methods ---

    def _setup_main_window(self) -> None:
        """Sets up the main Tkinter window properties and geometry."""
        logger.log("Setting up main window.", file_only=True)
        self.window = tk.Tk()
        self.window.title(f"{config.APP_NAME} V{config.APP_VERSION}")
        self.window.minsize(600, 480) # Min size accommodates percentage label
        self.window.columnconfigure(1, weight=1) 
        self.window.columnconfigure(2, weight=1)
        logger.log("Main window setup finished.", file_only=True)

    def _init_state_variables(self) -> None:
        """Initializes application state variables and Tkinter control variables."""
        logger.log("Initializing state variables.", file_only=True)
        self.current_video_info: Optional[Dict[str, Any]] = None
        self.filesize_cache: Dict[Tuple[str, bool, str], Dict[str, Any]] = {}
        self.thumbnail_photo_image: Optional[ImageTk.PhotoImage] = None
        
        self.link_entry_var = tk.StringVar(master=self.window)
        self.is_mp3_var = BooleanVar(master=self.window, value=True)
        self.quality_var = tk.StringVar(master=self.window, value=config.NO_QUALITY_AVAILABLE_STR)
        self.output_directory_var = tk.StringVar(master=self.window, value=get_default_output_dir())
        self.filename_var = tk.StringVar(master=self.window)
        
        self.link_label: Optional[tk.Label] = None; self.link_entry: Optional[tk.Entry] = None; self.link_status_label: Optional[tk.Label] = None
        self.video_title_label: Optional[tk.Label] = None; self.thumbnail_canvas: Optional[tk.Canvas] = None
        self.output_format_label: Optional[tk.Label] = None; self.mp3_radio_button: Optional[tk.Radiobutton] = None; self.mp4_radio_button: Optional[tk.Radiobutton] = None
        self.quality_label: Optional[tk.Label] = None; self.quality_option_menu: Optional[tk.OptionMenu] = None
        self.filesize_info_label: Optional[tk.Label] = None; self.mp3_size_info_label: Optional[tk.Label] = None
        self.directory_label: Optional[tk.Label] = None; self.directory_entry: Optional[tk.Entry] = None; self.browse_button: Optional[tk.Button] = None
        self.filename_label: Optional[tk.Label] = None; self.filename_entry: Optional[tk.Entry] = None
        self.convert_button: Optional[tk.Button] = None; self.progress_bar: Optional[ttk.Progressbar] = None
        self.conversion_status_label: Optional[tk.Label] = None; self.download_details_label: Optional[tk.Label] = None
        self.download_percentage_label: Optional[tk.Label] = None
        self.filesize_tooltip: Optional[ToolTip] = None
        logger.log("State variables initialized.", file_only=True)

    def _create_widgets(self) -> None:
        """Creates all GUI widgets and assigns them to instance attributes."""
        logger.log("Creating widgets.", file_only=True)
        self.link_label = tk.Label(self.window, text="YouTube Link:", font=config.FONT_BOLD)
        self.link_entry = tk.Entry(self.window, textvariable=self.link_entry_var, width=50)
        self.link_status_label = tk.Label(self.window, text="Waiting for link...", font=config.FONT_NORMAL, fg='gray')
        self.video_title_label = tk.Label(self.window, text="", font=config.FONT_BOLD, wraplength=300, justify="left")
        self.thumbnail_canvas = tk.Canvas(self.window, width=config.THUMBNAIL_WIDTH, height=config.THUMBNAIL_HEIGHT, 
                                          bg="lightgrey", relief=tk.SUNKEN, borderwidth=1)
        self.output_format_label = tk.Label(self.window, text="Preferred Output:", font=config.FONT_BOLD)
        self.mp3_radio_button = tk.Radiobutton(self.window, text="MP3 Audio", variable=self.is_mp3_var, value=True, font=config.FONT_NORMAL)
        self.mp4_radio_button = tk.Radiobutton(self.window, text="MP4 Video", variable=self.is_mp3_var, value=False, font=config.FONT_NORMAL)
        self.quality_label = tk.Label(self.window, text="Quality:", font=config.FONT_BOLD)
        self.quality_option_menu = tk.OptionMenu(self.window, self.quality_var, self.quality_var.get()) 
        self.quality_option_menu.config(width=12)
        self.filesize_info_label = tk.Label(self.window, text="", font=config.FONT_NORMAL, wraplength=300) 
        self.filesize_tooltip = ToolTip(self.filesize_info_label, config.TOOLTIP_TEXT_SIZE_ESTIMATE)
        self.mp3_size_info_label = tk.Label(self.window, text="", font=config.FONT_INFO_NOTE, fg="darkblue", wraplength=300, justify="left")
        self.directory_label = tk.Label(self.window, text="Save to Directory:", font=config.FONT_BOLD)
        self.directory_entry = tk.Entry(self.window, textvariable=self.output_directory_var, width=50)
        self.browse_button = tk.Button(self.window, text="Browse...", command=self._browse_for_directory, font=config.FONT_NORMAL)
        self.filename_label = tk.Label(self.window, text="Filename (optional):", font=config.FONT_BOLD)
        self.filename_entry = tk.Entry(self.window, textvariable=self.filename_var, width=50)
        self.convert_button = tk.Button(self.window, text="Download & Convert", command=self._start_conversion_thread, font=config.FONT_BOLD)
        self.progress_bar = ttk.Progressbar(self.window, orient="horizontal", mode='determinate', length=300, maximum=100)
        self.download_percentage_label = tk.Label(self.window, text="", font=config.FONT_NORMAL) 
        self.conversion_status_label = tk.Label(self.window, text="Idle", font=config.FONT_BOLD)
        self.download_details_label = tk.Label(self.window, font=config.FONT_NORMAL, wraplength=580, justify="left") 
        logger.log("Widgets created.", file_only=True)

    def _layout_widgets(self) -> None:
        """Arranges widgets in the main window using the desired grid layout."""
        logger.log("Laying out widgets.", file_only=True)
        self.link_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.link_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky='ew')
        self.link_status_label.grid(row=1, column=0, columnspan=4, padx=5, pady=(0,5), sticky='w')
        self.thumbnail_canvas.grid(row=2, column=0, rowspan=5, padx=10, pady=10, sticky='nw') 
        self.video_title_label.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky='nw') 
        self.output_format_label.grid(row=3, column=1, padx=5, pady=(10,2), sticky='sw') 
        self.mp3_radio_button.grid(row=4, column=1, padx=15, pady=2, sticky='w')
        self.mp4_radio_button.grid(row=4, column=2, padx=5, pady=2, sticky='w')
        self.quality_label.grid(row=5, column=1, padx=5, pady=5, sticky='sw')
        self.quality_option_menu.grid(row=5, column=2, padx=5, pady=5, sticky='w')
        self.filesize_info_label.grid(row=6, column=1, columnspan=2, padx=5, pady=(2,0), sticky='w')
        self.mp3_size_info_label.grid(row=7, column=0, columnspan=3, padx=10, pady=(0,5), sticky='w') 
        self.directory_label.grid(row=8, column=0, padx=5, pady=5, sticky='w')
        self.directory_entry.grid(row=8, column=1, columnspan=2, padx=5, pady=5, sticky='ew')
        self.browse_button.grid(row=8, column=3, padx=5, pady=5, sticky='e') 
        self.filename_label.grid(row=9, column=0, padx=5, pady=5, sticky='w')
        self.filename_entry.grid(row=9, column=1, columnspan=2, padx=5, pady=5, sticky='ew')
        self.convert_button.grid(row=10, column=0, columnspan=4, padx=5, pady=10)
        self.progress_bar.grid(row=11, column=0, columnspan=2, padx=5, pady=(5,0), sticky='ew') 
        self.download_percentage_label.grid(row=12, column=0, columnspan=2, padx=5, pady=(0,5), sticky='ew') 
        self.conversion_status_label.grid(row=11, column=2, columnspan=2, rowspan=2, padx=5, pady=5, sticky='w') 
        self.download_details_label.grid(row=13, column=0, columnspan=4, padx=5, pady=5, sticky='w') 

    def _bind_events(self) -> None:
        """Binds Tkinter variable traces to handler methods."""
        logger.log("Binding events.", file_only=True)
        self.link_entry_var.trace_add('write', self._on_link_entry_change)
        self.is_mp3_var.trace_add('write', self._on_output_type_or_metadata_change)
        self.quality_var.trace_add('write', self._on_quality_selection_change)

    # --- UI Update Helper Methods ---
    def _schedule_ui_update(self, widget: Optional[tk.Widget], **kwargs: Any) -> None:
        if self.window and widget: 
            try: self.window.after(0, lambda w=widget, k=kwargs: w.config(**k))
            except tk.TclError as e: logger.log(f"TclError scheduling UI update for {widget}: {e}", file_only=True)
            except Exception as e: logger.log(f"Unexpected error scheduling UI update for {widget}: {e}", file_only=True)
    def _update_link_status_message(self, text: str, color: str = 'gray') -> None:
        self._schedule_ui_update(self.link_status_label, text=text, fg=color)
    def _update_video_title_display(self, title: str = "") -> None:
        self._schedule_ui_update(self.video_title_label, text=title)
    def _update_filesize_display_text(self, text: str) -> None:
        self._schedule_ui_update(self.filesize_info_label, text=text)
    def _update_download_details_text(self, text: str) -> None:
        self._schedule_ui_update(self.download_details_label, text=text)
    def _update_conversion_status_text(self, text: str) -> None:
        self._schedule_ui_update(self.conversion_status_label, text=text)
    def _update_mp3_note_text(self, text: str) -> None:
         self._schedule_ui_update(self.mp3_size_info_label, text=text)
    def _update_quality_label_text(self, text: str) -> None:
        self._schedule_ui_update(self.quality_label, text=text)
    def _update_download_percentage_text(self, text: str) -> None:
        self._schedule_ui_update(self.download_percentage_label, text=text)

    def _display_thumbnail_image(self, thumbnail_url: str) -> None:
        logger.log(f"Fetching thumbnail: {thumbnail_url}", file_only=True)
        def _fetch_and_render_in_thread() -> None:
            try:
                with urllib.request.urlopen(thumbnail_url, timeout=config.THUMBNAIL_FETCH_TIMEOUT) as response: raw_data = response.read()
                image = Image.open(BytesIO(raw_data)); image.thumbnail((config.THUMBNAIL_WIDTH, config.THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)
                self.thumbnail_photo_image = ImageTk.PhotoImage(image) 
                if self.window and self.thumbnail_canvas : self.window.after(0, lambda: self._draw_thumbnail_on_canvas(self.thumbnail_photo_image))
            except Exception as e:
                logger.log(f"Error in thumbnail fetch/render thread: {e}", file_only=True); logger.log(traceback.format_exc(), file_only=True) 
                if self.window and self.thumbnail_canvas: self.window.after(0, self._clear_thumbnail_canvas)
        Thread(target=_fetch_and_render_in_thread, daemon=True).start()
    def _draw_thumbnail_on_canvas(self, photo_image: ImageTk.PhotoImage) -> None:
        if self.thumbnail_canvas: self.thumbnail_canvas.delete('all'); self.thumbnail_canvas.create_image(0, 0, anchor='nw', image=photo_image)
    def _clear_thumbnail_canvas(self) -> None:
        if self.thumbnail_canvas: self.thumbnail_canvas.delete('all')
        self.thumbnail_photo_image = None 
    def _set_interactive_widgets_enabled(self, enabled: bool) -> None:
        state = 'normal' if enabled else 'disabled'
        widgets = [self.link_entry, self.directory_entry, self.filename_entry, self.mp3_radio_button, self.mp4_radio_button, self.quality_option_menu, self.browse_button, self.convert_button]
        for widget in widgets:
            if widget: self._schedule_ui_update(widget, state=state)

    # --- Event Handlers & Core Logic ---
    def _on_link_entry_change(self, *_: Any) -> None:
        url = self.link_entry_var.get().strip()
        logger.log(f"Link entry changed. Processing URL: '{url}'")
        Thread(target=self._process_youtube_link_async, args=(url,), daemon=True).start()
    def _process_youtube_link_async(self, url: str) -> None:
        logger.log(f"Async processing link: '{url}'", file_only=True)
        if not url: self._update_link_status_message("Waiting for link..."); self._reset_video_info_ui_elements(); return
        self._update_link_status_message("Verifying link...")
        is_valid, msg = self._validate_url_input(url)
        if not is_valid: self._update_link_status_message(msg, color='red'); self._reset_video_info_ui_elements(); return
        self._update_link_status_message("Link format correct. Fetching info...")
        video_info = self._fetch_video_metadata_from_url(url) 
        if video_info:
            self.current_video_info = video_info; self.filesize_cache.clear() 
            self._update_ui_with_video_info(video_info); self._update_link_status_message("Link fetched!", color='green')
        else: self._reset_video_info_ui_elements()
        logger.log(f"Async link processing finished for: '{url}'", file_only=True)
    def _validate_url_input(self, url: str) -> Tuple[bool, str]:
        if not validators.url(url): return False, "Invalid URL format."
        if not is_youtube_url(url): return False, "Not a valid YouTube link."
        return True, ""
    def _fetch_video_metadata_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        logger.log(f"Fetching metadata for: '{url}' (blocking call)", file_only=True)
        opts = {**config.YDL_BASE_OPTS, 'skip_download': True, 'extract_flat': False, 'noplaylist': True}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl: info = ydl.extract_info(url, download=False)
            logger.log(f"Metadata fetched successfully for: '{url}'", file_only=True); return info
        except yt_dlp.utils.DownloadError as e:
            err = strip_ansi(str(e)); logger.log(f"yt-dlp DownloadError for '{url}': {err[:150]}", file_only=True)
            self._update_link_status_message(f"Error fetching: {err[:100]}", color='red'); return None
        except Exception as e: 
            logger.log(f"Unexpected Exception fetching metadata for '{url}': {e}", file_only=True); logger.log(traceback.format_exc(), file_only=True)
            self._update_link_status_message(f"Unexpected error fetching info: {str(e)[:100]}", color='red'); return None
    def _update_ui_with_video_info(self, info: Dict[str, Any]) -> None:
        title = info.get('title', config.DEFAULT_FILENAME_BASE); logger.log(f"Updating UI with video info. Title: '{title}'", file_only=True)
        self._update_video_title_display(title)
        if tn_url := info.get('thumbnail'): self._display_thumbnail_image(tn_url)
        else: self._clear_thumbnail_canvas()
        self._on_output_type_or_metadata_change() 
    def _reset_video_info_ui_elements(self) -> None:
        logger.log("Resetting video info UI elements.", file_only=True)
        self.current_video_info = None; self._update_video_title_display(""); self._clear_thumbnail_canvas()
        self._update_filesize_display_text(""); self._update_quality_options_ui() 
    def _on_output_type_or_metadata_change(self, *_: Any) -> None: 
        self._update_quality_options_ui()
    def _update_quality_options_ui(self) -> None:
        is_mp3 = self.is_mp3_var.get(); logger.log(f"Updating quality options UI. Format: {'MP3' if is_mp3 else 'MP4'}", file_only=True)
        options_config, default_idx = (config.AUDIO_QUALITIES, config.DEFAULT_AUDIO_QUALITY_IDX) if is_mp3 else (config.VIDEO_QUALITIES, config.DEFAULT_VIDEO_QUALITY_IDX)
        self._update_quality_label_text("Audio Quality:" if is_mp3 else "Video Quality:"); self._update_mp3_note_text("") 
        options_with_state: List[Tuple[str, str, bool]] = []
        if self.current_video_info and 'formats' in self.current_video_info:
            formats = self.current_video_info['formats']
            if is_mp3:
                audio_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none' and f.get('abr')]
                source_audio_exists = bool(audio_formats)
                if source_audio_exists:
                    try: max_abr = max(float(f['abr']) for f in audio_formats); self._update_mp3_note_text(f"Note: Best audio source is ~{max_abr:.0f}kbps. Final MP3 is re-encoded."); logger.log(f"Source Audio ABRs found. Max: {max_abr:.0f}kbps", file_only=True)
                    except (ValueError, TypeError): logger.log("Could not determine max ABR from formats.", file_only=True)
                for label, param, _ in options_config: options_with_state.append((label, param, source_audio_exists))
            else: 
                available_heights = {int(f['height']) for f in formats if f.get('vcodec') != 'none' and f.get('height')}
                logger.log(f"Available Video Heights: {sorted(list(available_heights))}", file_only=True)
                for label, param, target_h in options_config: options_with_state.append((label, param, any(h >= target_h for h in available_heights)))
        else: options_with_state = [(label, param, False) for label, param, _ in options_config]
        self._populate_quality_menu(options_with_state, default_idx)
    def _populate_quality_menu(self, options_with_state: List[Tuple[str, str, bool]], default_option_idx: int) -> None:
        logger.log(f"Populating quality menu. Options: {options_with_state}", file_only=True)
        if not self.quality_option_menu: logger.log("Quality option menu widget is None.", file_only=True); return
        menu = self.quality_option_menu['menu'] 
        if not menu: logger.log("Quality option menu's internal menu is None.", file_only=True); return 
        menu.delete(0, 'end')
        current_selection = self.quality_var.get(); new_selection = config.NO_QUALITY_AVAILABLE_STR
        first_enabled = None; has_options = bool(options_with_state)
        if has_options:
            for label, _, enabled in options_with_state:
                if enabled and first_enabled is None: first_enabled = label
                menu.add_command(label=label, command=lambda l=label: self.quality_var.set(l), state='normal' if enabled else 'disabled')
            is_current_valid = any(lbl == current_selection and enabled for lbl, _, enabled in options_with_state)
            if is_current_valid: new_selection = current_selection
            elif first_enabled: new_selection = first_enabled
            else: 
                if default_option_idx < len(options_with_state): new_selection = options_with_state[default_option_idx][0]
                elif options_with_state: new_selection = options_with_state[0][0]
        if self.quality_var.get() != new_selection: self.quality_var.set(new_selection) 
        else: self._on_quality_selection_change()
        logger.log(f"Quality menu populated. Selected quality: '{self.quality_var.get()}'", file_only=True)
    def _on_quality_selection_change(self, *_: Any) -> None: 
        selected_quality = self.quality_var.get(); logger.log(f"Quality selection changed to: '{selected_quality}'")
        if selected_quality == config.NO_QUALITY_AVAILABLE_STR: self._update_filesize_display_text(""); return
        self._estimate_and_update_filesize_async()
    def _estimate_and_update_filesize_async(self) -> None:
        url = self.link_entry_var.get().strip()
        if not url or not self.current_video_info: self._update_filesize_display_text(""); return
        is_mp3, quality_key = self.is_mp3_var.get(), self.quality_var.get() 
        logger.log(f"Async filesize estimation for: URL='{url}', MP3={is_mp3}, QualityKey='{quality_key}'", file_only=True)
        cache_key = (url, is_mp3, quality_key)
        if cached_data := self.filesize_cache.get(cache_key):
            logger.log(f"Filesize cache hit for {cache_key}. Data: {cached_data}", file_only=True); self._display_estimated_filesize(cached_data['bytes'], cached_data['incomplete']); return
        self._update_filesize_display_text("Estimating size…")
        Thread(target=self._get_estimate_cache_and_display_size_worker, args=(url, is_mp3, quality_key), daemon=True).start()
    def _get_estimate_cache_and_display_size_worker(self, url: str, is_mp3: bool, quality_key_label: str) -> None:
        logger.log(f"Worker thread: Estimating size for QualityLabel='{quality_key_label}'", file_only=True)
        try:
            options_source = config.AUDIO_QUALITIES if is_mp3 else config.VIDEO_QUALITIES
            quality_param_for_estimator = next((p_val for lbl, p_val, _ in options_source if lbl == quality_key_label), None)
            if quality_param_for_estimator is None: logger.log(f"Error: Could not map QKey '{quality_key_label}' to param.", file_only=True); self._display_filesize_error_on_ui("Error (internal map)"); return
            total_bytes, is_incomplete = estimate_size(url, is_mp3, quality_param_for_estimator)
            self.filesize_cache[(url,is_mp3,quality_key_label)] = {'bytes':total_bytes, 'incomplete':is_incomplete}
            logger.log(f"Estimation complete: {total_bytes} bytes, Incomplete: {is_incomplete}. Cached.", file_only=True)
            self._display_estimated_filesize(total_bytes, is_incomplete)
        except Exception as e: 
            logger.log(f"Exception in estimation thread: {e}", file_only=True); logger.log(traceback.format_exc(), file_only=True) 
            self._display_filesize_error_on_ui("Error (estimation failed)")
    def _display_estimated_filesize(self, total_bytes: int, is_incomplete: bool) -> None:
        mb = total_bytes / (1024*1024); text = ""
        if not is_incomplete: text = f"Est. size: {mb:.2f} MB" if total_bytes >= 0 else "Size: Error"
        elif is_incomplete and total_bytes > 0: text = f"Rough est: ~{mb:.2f} MB (bitrate based)"
        elif is_incomplete and total_bytes == 0: text = "Size: Unknown (detailed info unavailable)"
        else: text = "Size: Error (unexpected state)"; logger.log(f"Unexpected filesize state: bytes={total_bytes}, incomplete={is_incomplete}", file_only=True)
        self._update_filesize_display_text(text)
    def _display_filesize_error_on_ui(self, message: str) -> None: self._update_filesize_display_text(message)

    # --- Conversion Process ---
    def _start_conversion_thread(self) -> None:
        url = self.link_entry_var.get().strip(); directory = self.output_directory_var.get().strip()
        is_mp3 = self.is_mp3_var.get(); quality_label = self.quality_var.get(); filename_input = self.filename_var.get().strip()
        logger.log(f"Initiating conversion: URL='{url}', MP3={is_mp3}, Quality='{quality_label}', Dir='{directory}', Filename='{filename_input}'")
        if not self.current_video_info: messagebox.showerror("Error", "No video information loaded."); logger.log("Conv aborted: No video info.", file_only=True); return
        if not directory or not os.path.isdir(directory): messagebox.showerror("Error", "Select valid output directory."); logger.log(f"Conv aborted: Invalid dir '{directory}'.", file_only=True); return
        if quality_label == config.NO_QUALITY_AVAILABLE_STR: messagebox.showerror("Error", "Selected quality not available."); logger.log("Conv aborted: Quality not available.", file_only=True); return
        Thread(target=self._perform_conversion_worker, args=(url, directory, is_mp3, quality_label, filename_input), daemon=True).start()

    def _perform_conversion_worker(self, url: str, directory: str, is_mp3_target: bool, 
                                 quality_label: str, base_filename_input: str) -> None:
        logger.log("Conversion worker thread started.", file_only=True)
        self._set_interactive_widgets_enabled(False) 
        
        if self.window and self.progress_bar:
            self.window.after(0, lambda: self.progress_bar.config(mode='indeterminate', value=0))
            self.window.after(0, self.progress_bar.start) 
            logger.log("Progress bar: Indeterminate (Preparing).", file_only=True)

        self._update_download_details_text("") 
        self._update_conversion_status_text("Preparing...")
        self._update_download_percentage_text("") 

        base_filename = sanitize_filename(base_filename_input or (self.current_video_info.get('title') if self.current_video_info else None))
        expected_ext = ".mp3" if is_mp3_target else ".mp4"; final_filename_only = f"{base_filename}{expected_ext}"
        final_filepath = os.path.join(directory, final_filename_only)
        logger.log(f"Target output file: '{final_filepath}'", file_only=True)

        should_proceed = self._check_and_handle_overwrite(final_filepath, final_filename_only)
        
        if not should_proceed:
             self._finalize_conversion_ui_state(current_status=self.conversion_status_label.cget("text")) 
             return 

        self._update_conversion_status_text("Downloading...") 
        output_template = os.path.join(directory, f"{base_filename}.%(ext)s")
        download_successful = False; error_message = ""
        final_operation_status = "Error!" 

        try:
            ydl_opts = self._build_yt_dlp_options(output_template, is_mp3_target, quality_label, url)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
            download_successful = True 
            final_operation_status = "Conversion Complete!"
        except yt_dlp.utils.DownloadError as de: 
            error_message = strip_ansi(str(de)); logger.log(f"yt-dlp DownloadError: {error_message}"); logger.log(traceback.format_exc(), file_only=True)
        except Exception as e: 
            error_message = strip_ansi(str(e)); logger.log(f"Generic exception during download: {error_message}"); logger.log(traceback.format_exc(), file_only=True)
        
        if self.window and self.progress_bar and self.progress_bar.cget("mode") == "indeterminate":
            self.window.after(0, self.progress_bar.stop)
            logger.log("Progress bar: Stopped indeterminate after download attempt.", file_only=True)

        if download_successful:
            self._handle_successful_download_outcome(final_filepath, final_filename_only, url, is_mp3_target, quality_label)
        else:
            self._update_conversion_status_text("Error!")
            self._update_download_details_text(f"Download Failed: {error_message[:200]}")
            if self.window: messagebox.showerror("Download Error", f"An error occurred during download:\n{error_message}")
            if self.window and self.progress_bar: self.window.after(0, lambda: self.progress_bar.config(value=0, mode='determinate'))
            if self.window and self.download_percentage_label: self.window.after(0, lambda: self._update_download_percentage_text("Error"))
        
        self._finalize_conversion_ui_state(current_status=final_operation_status)

    def _check_and_handle_overwrite(self, filepath: str, filename: str) -> bool:
        if not os.path.exists(filepath): return True 
        logger.log(f"File '{filepath}' exists. Prompting user.", file_only=True); response_queue = Queue()
        
        if self.window and self.progress_bar:
            current_mode = self.progress_bar.cget("mode")
            if current_mode != "indeterminate":
                self.window.after(0, lambda: self.progress_bar.config(mode='indeterminate', value=0))
            self.window.after(0, self.progress_bar.start)
            logger.log("Progress bar: Indeterminate (Waiting for user overwrite).", file_only=True)

        def _ask_on_main() -> None: response_queue.put(messagebox.askyesno("File Exists", f"File '{filename}' already exists.\nOverwrite?"))
        
        if self.window: self.window.after(0, _ask_on_main)
        else: response_queue.put(False); logger.log("Window closed, cannot prompt. Skipping.", file_only=True)
        
        user_response: Optional[bool] = None; proceed = False
        try:
            self._update_conversion_status_text("Waiting for user input...")
            user_response = response_queue.get(timeout=config.USER_CONFIRMATION_TIMEOUT_SECONDS)
            if user_response:
                try: os.remove(filepath); logger.log("Deleted existing file for overwrite."); proceed = True
                except OSError as e: 
                    logger.log(f"Error deleting file '{filepath}': {e}", file_only=True); self._update_conversion_status_text("Error (delete failed)")
                    self._update_download_details_text(f"Could not delete existing file: {e}");
                    if self.window: messagebox.showerror("Overwrite Error", f"Failed to delete file:\n{e}"); proceed = False 
            else: 
                logger.log("User chose not to overwrite. Skipping.", file_only=True); self._update_conversion_status_text("Skipped (file exists)")
                self._update_download_details_text(f"File '{filename}' exists. Skipped by user."); proceed = False 
        except Empty: 
            logger.log("Timeout waiting for user response. Skipping.", file_only=True); self._update_conversion_status_text("Skipped (timeout)")
            self._update_download_details_text(f"File '{filename}' exists. Skipped (no response)."); proceed = False 
        
        if not proceed: # If not proceeding, ensure bar is reset now
            if self.window and self.progress_bar:
                if self.progress_bar.cget("mode") == "indeterminate": self.window.after(0, self.progress_bar.stop)
                self.window.after(0, lambda: self.progress_bar.config(value=0, mode='determinate'))
                self.window.after(0, lambda: self._update_download_percentage_text(""))
        return proceed

    def _build_yt_dlp_options(self, output_template: str, is_mp3: bool, quality_label: str, url: str) -> Dict[str, Any]:
        options_source = config.AUDIO_QUALITIES if is_mp3 else config.VIDEO_QUALITIES
        quality_param = next((p for lbl, p, _ in options_source if lbl == quality_label), None)
        if quality_param is None: err = f"Invalid quality label '{quality_label}'"; logger.log(f"ERROR building options: {err}", file_only=True); raise ValueError(err)
        noplaylist = 'list=' not in url.lower()
        logger.log(f"Building ydl_opts: mp3={is_mp3}, q_param='{quality_param}' (from '{quality_label}'), noplaylist={noplaylist}", file_only=True)
        common_opts = {**config.YDL_BASE_OPTS, 'outtmpl': output_template, 'progress_hooks': [self._yt_dlp_progress_hook], 'noplaylist': noplaylist}
        if is_mp3: return {**common_opts, 'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': quality_param}]}
        else: return {**common_opts, 'format': f'bestvideo[height<={quality_param}]+bestaudio/best[height<={quality_param}]/best', 'merge_output_format': 'mp4'}

    def _yt_dlp_progress_hook(self, d: Dict[str, Any]) -> None:
        status = d.get('status')
        if status == 'downloading':
            total_bytes_est_str = d.get('total_bytes_estimate'); downloaded_bytes_str = d.get('downloaded_bytes')
            if total_bytes_est_str is not None and downloaded_bytes_str is not None:
                try:
                    total_b, downloaded_b = float(total_bytes_est_str), float(downloaded_bytes_str)
                    if total_b > 0: 
                        percent = min(100.0, (downloaded_b / total_b) * 100)
                        if self.window and self.progress_bar:
                            if self.progress_bar.cget("mode") != 'determinate': self.window.after(0, self.progress_bar.stop); self.window.after(0, lambda: self.progress_bar.config(mode='determinate'))
                            self.window.after(0, lambda p=percent: self.progress_bar.config(value=p))
                        if self.window and self.download_percentage_label: self.window.after(0, lambda p=percent: self._update_download_percentage_text(f"{p:.1f}%"))
                except (ValueError, TypeError): logger.log("Progress hook: Invalid byte values.", file_only=True)
                except Exception as e: logger.log(f"Progress hook: UI update error: {e}", file_only=True)
            else: 
                if self.window and self.progress_bar and self.progress_bar.cget("mode") != "indeterminate":
                    self.window.after(0, lambda: self.progress_bar.config(mode='indeterminate', value=0)); self.window.after(0, self.progress_bar.start) 
                    self.window.after(0, lambda: self._update_download_percentage_text("Downloading... (size unknown)"))
        elif status == 'finished':
            logger.log("yt-dlp hook: 'finished'.", file_only=True)
            if self.window and self.progress_bar:
                if self.progress_bar.cget("mode") == "indeterminate": self.window.after(0, self.progress_bar.stop)
                self.window.after(0, lambda: self.progress_bar.config(value=100, mode='determinate'))
            if self.window and self.download_percentage_label: self.window.after(0, lambda: self._update_download_percentage_text("100.0%"))
        elif status == 'error':
            logger.log("yt-dlp hook: ERROR.", file_only=True)
            if self.window and self.progress_bar:
                 if self.progress_bar.cget("mode") == "indeterminate": self.window.after(0, self.progress_bar.stop)
                 self.window.after(0, lambda: self.progress_bar.config(value=0, mode='determinate')) 
            if self.window and self.download_percentage_label: self.window.after(0, lambda: self._update_download_percentage_text("Error"))

    def _handle_successful_download_outcome(self, filepath: str, filename: str, url: str, is_mp3: bool, quality_label: str) -> None:
        if os.path.exists(filepath):
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            success_msg = f"Downloaded: {filename} ({file_size_mb:.2f} MB)"
            self._update_download_details_text(success_msg); logger.log(f"Verified final file: '{filepath}', Size: {file_size_mb:.2f} MB"); self._update_conversion_status_text("Conversion Complete!")
            discrepancy_note = self._check_estimate_discrepancy(url, is_mp3, quality_label, os.path.getsize(filepath))
            if discrepancy_note: self._update_download_details_text(success_msg + discrepancy_note)
            final_user_msg = f"Download finished! Saved to:\n{os.path.realpath(os.path.dirname(filepath))}"
            if self.window: messagebox.showinfo("Success", final_user_msg)
            self._open_output_directory(filepath)
        else:
            logger.log(f"Error: Expected file '{filepath}' not found post-success.", file_only=True)
            self._update_download_details_text(f"Error: Final file '{filename}' missing."); self._update_conversion_status_text("Error (File Missing)")
            if self.window: messagebox.showerror("Error", f"Download complete, but final file '{filename}' missing.")

    def _check_estimate_discrepancy(self, url: str, is_mp3: bool, quality_label: str, actual_bytes: int) -> str:
        cache_key = (url, is_mp3, quality_label); cached_info = self.filesize_cache.get(cache_key); note = ""
        if cached_info:
            est_bytes, incomplete = cached_info.get('bytes', -1), cached_info.get('incomplete', False)
            if incomplete and est_bytes > 0 and not (est_bytes*config.DISCREPANCY_LOWER_RATIO <= actual_bytes <= est_bytes*config.DISCREPANCY_UPPER_RATIO):
                note = (f"\nNote: Initial rough estimate (~{est_bytes/(1024*1024):.2f} MB) "
                        "differed significantly from actual size. This can happen with some videos.")
                logger.log(f"Discrepancy noted: {note.strip()}", file_only=True)
        return note

    def _open_output_directory(self, filepath: str) -> None:
        try: directory = os.path.dirname(os.path.realpath(filepath)); logger.log(f"Attempting to open directory: {directory}", file_only=True); webbrowser.open(directory)
        except Exception as e: logger.log(f"Could not open output directory '{directory}': {e}", file_only=True)

    def _finalize_conversion_ui_state(self, current_status: str = "Idle") -> None:
        logger.log(f"Finalizing conversion UI. Status before reset: '{current_status}'", file_only=True)
        if self.window and self.progress_bar:
            if current_status == "Conversion Complete!":
                logger.log("Progress bar: Indeterminate (post-success visual cue).", file_only=True)
                self.window.after(0, lambda: self.progress_bar.config(mode='indeterminate', value=0))
                self.window.after(0, self.progress_bar.start)
            else: 
                logger.log("Progress bar: Empty determinate (error/skip/other).", file_only=True)
                if self.progress_bar.cget("mode") == "indeterminate": self.window.after(0, self.progress_bar.stop)
                self.window.after(0, lambda: self.progress_bar.config(value=0, mode='determinate'))
        self._set_interactive_widgets_enabled(True) 
        self._schedule_status_label_reset(final_status_before_idle=current_status)

    def _schedule_status_label_reset(self, delay_seconds: int = 5, final_status_before_idle: str = "Idle") -> None:
        actual_delay_ms = (config.SUCCESS_RESET_DELAY_SECONDS if final_status_before_idle == "Conversion Complete!" 
                           else config.NON_SUCCESS_RESET_DELAY_SECONDS) * 1000
        logger.log(f"Scheduling final UI reset to Idle in {actual_delay_ms}ms.", file_only=True)
        def _reset_ui_to_idle() -> None:
            if self.window: 
                logger.log("Executing scheduled UI reset to Idle state.", file_only=True)
                self._update_download_details_text(''); self._update_conversion_status_text('Idle')
                self._update_download_percentage_text('') 
                if self.progress_bar:
                    logger.log("Progress bar: Reset to empty determinate for Idle state.", file_only=True)
                    if self.progress_bar.cget("mode") == "indeterminate": self.progress_bar.stop() 
                    self.progress_bar.config(value=0, mode='determinate') 
        if self.window: self.window.after(actual_delay_ms, _reset_ui_to_idle)

    def _browse_for_directory(self) -> None:
        logger.log("Browse for directory action initiated.", file_only=True)
        current_dir = self.output_directory_var.get(); initial_dir = current_dir if os.path.isdir(current_dir) else get_default_output_dir()
        chosen_directory = filedialog.askdirectory(initialdir=initial_dir, title="Select Output Directory")
        if chosen_directory: self.output_directory_var.set(chosen_directory); logger.log(f"Output directory set to: '{chosen_directory}'")

    # --- Application Lifecycle ---
    def run(self) -> None:
        logger.log(f"Starting {config.APP_NAME} GUI main event loop.")
        try: self.window.mainloop()
        except KeyboardInterrupt: logger.log("Application interrupted by user (KeyboardInterrupt).")
        finally: logger.log("Application mainloop exited.", console_only=True); logger.close()
    def _on_closing_application(self) -> None:
        logger.log("Application window closing sequence initiated by user.")
        if self.window: self.window.destroy()

# --- Main Execution Guard ---
if __name__ == '__main__':
    logger.log(f"Starting application {config.APP_NAME} V{config.APP_VERSION} from __main__.", console_only=True)
    try:
        app = YoutubeDownloaderApp()
        app.run()
    except Exception as main_app_error: 
        logger.log(f"CRITICAL UNHANDLED EXCEPTION in __main__: {main_app_error}", console_only=True)
        logger.log(traceback.format_exc(), console_only=True)
        try:
            root = tk.Tk(); root.withdraw() 
            messagebox.showerror("Fatal Application Error", f"A critical error occurred: {main_app_error}\n\nPlease check the logs for more details.\nApplication will now exit.")
            root.destroy()
        except Exception: pass 
        sys.exit(1) 