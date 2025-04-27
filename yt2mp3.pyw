from tkinter import filedialog, BooleanVar, ttk, messagebox
from threading import Thread
from PIL import Image, ImageTk
from io import BytesIO
from urllib.parse import urlparse
import yt_dlp
import urllib.request
import time
import tkinter as tk
import os
import webbrowser
import validators
import string
import re

class GUI:
    def __init__(self) -> None:
        """
        Initializes the GUI window.
        """
        # Info
        self.version = '2.1.0'
        self.window = tk.Tk()
        self.window.title(f"Youtube to MP3/MP4 V{self.version}")
        self.window.minsize(550, 320)

        #misc
        self.current_info = None
        self.size_cache: dict[tuple[str,bool,str], int] = {}
        # State
        self.in_link_entry = tk.StringVar()
        self.photo = None
        self.current_info = None
        self.is_mp3 = BooleanVar(value=True)

        # --- Labels ---
        self.link         = tk.Label(self.window, text="YouTube Link:",   font=('Helvetica',12,'bold'))
        self.link_status  = tk.Label(self.window, text="Waiting for link...", font=('Helvetica',10), fg='gray')
        self.selection    = tk.Label(self.window, text="Preferred Output", font=('Helvetica',12,'bold'))
        self.quality_label= tk.Label(self.window, text="Audio Quality",    font=('Helvetica',12,'bold'))
        self.filesize_label = tk.Label(self.window, text="",               font=('Helvetica',10))
        self.directory    = tk.Label(self.window, text="Directory",        font=('Helvetica',12,'bold'))
        self.filename_label = tk.Label(self.window, text="Filename",       font=('Helvetica',12,'bold'))
        self.status_text  = tk.Label(self.window, text="Idle",             font=('Helvetica',12,'bold'))
        self.download_status = tk.Label(self.window, font=('Helvetica',10), wraplength=250)
        self.video_title  = tk.Label(self.window, text="",                 font=('Helvetica',12,'bold'))

        # --- Inputs ---
        self.in_link        = tk.Entry(self.window, textvariable=self.in_link_entry, width=40)
        self.in_directory   = tk.Entry(self.window, width=40)
        self.filename_entry = tk.Entry(self.window, width=40)

        # --- Radio Buttons ---
        self.mp3_butt = tk.Radiobutton(self.window, text="MP3", variable=self.is_mp3, value=True,  font=('Helvetica',12,'bold'))
        self.mp4_butt = tk.Radiobutton(self.window, text="MP4", variable=self.is_mp3, value=False, font=('Helvetica',12,'bold'))

        # --- Quality OptionMenu ---
        self.quality_var  = tk.StringVar(value='Medium')
        # supply at least one entry so __init__ is happy; we'll rebuild it immediately
        initial_opts     = ('Low','Medium','High')
        self.quality_menu = tk.OptionMenu(self.window, self.quality_var, *initial_opts)
        self.quality_menu.config(width=10)

        # --- Buttons & Progress ---
        self.browse  = tk.Button(self.window, text="Browse",  command=self.get_dir,       font=('Helvetica',12,'bold'))
        self.convert = tk.Button(self.window, text="Convert", command=self.start_convert, font=('Helvetica',12,'bold'))
        self.pb      = ttk.Progressbar(self.window, orient="horizontal", mode='indeterminate', length=250)
        self.thumbnail = tk.Canvas(self.window, width=400, height=200)

        # --- Layout ---
        # Row 0
        self.link.grid(        row=0, column=0, padx=5, pady=5, sticky='w')
        self.in_link.grid(     row=0, column=1, padx=5, pady=5)
        self.video_title.grid( row=0, column=2, padx=5, pady=5)

        # Row 1: link status
        self.link_status.grid( row=1, column=0, columnspan=2, pady=(0,10))

        # Row 2
        self.selection.grid(   row=2, column=0, columnspan=2, padx=5, pady=5)
        self.thumbnail.grid(   row=2, column=2, rowspan=5, padx=5, pady=5)

        # Row 3
        self.mp3_butt.grid(    row=3, column=0, padx=5, pady=5)
        self.mp4_butt.grid(    row=3, column=1, padx=5, pady=5)

        # Row 4
        self.quality_label.grid(row=4, column=0, padx=5, pady=5)
        self.quality_menu.grid(row=4, column=1, padx=5, pady=5)
        # Row 5
        self.filesize_label.grid(row=5, column=0, columnspan=2, padx=5, pady=(0,10))

        # Row 6
        self.directory.grid(   row=6, column=0, columnspan=2, padx=5, pady=5)
        self.browse.grid(      row=7, column=0, padx=5, pady=5)
        self.in_directory.grid(row=7, column=1, padx=5, pady=5)

        # Row 8
        self.filename_label.grid(row=8, column=0, padx=5, pady=5)
        self.filename_entry.grid(row=8, column=1, padx=5, pady=5)

        # Row 9
        self.convert.grid(     row=9, column=0, columnspan=2, padx=5, pady=10)

        # Row 10
        self.pb.grid(          row=10, column=0, padx=5, pady=5)
        self.status_text.grid( row=10, column=1, padx=1, pady=5)

        # Row 11
        self.download_status.grid(row=11, column=0, columnspan=2, pady=5)

        # --- Traces & Bindings ---
        self.quality_var.trace_add('write', lambda *a: self._refresh_quality_menu())
        self.in_link_entry.trace_add('write', lambda *a: self.start_wait_link_thread())
        self.is_mp3.trace_add('write',    lambda *a: self.update_quality_options())
        self.update_quality_options()

    def get_thumbnail(self, thumbnail_url: str) -> ImageTk.PhotoImage:
        """
        Gets the thumbnail of the YouTube video.

        Args:
            thumbnail_url (str): The YouTube URL that we will obtain the thumbnail.
        
        Returns:
            thumbnail (ImageTk.PhotoImage): The thumbnail image.
        """
        try:
            open_url = urllib.request.urlopen(thumbnail_url)
            raw_data = open_url.read()

            im = Image.open(BytesIO(raw_data))
            im = im.resize((400, 200))
            thumbnail = ImageTk.PhotoImage(im)
            return thumbnail
        except Exception as e:
            messagebox.showerror(f"Error Processing Thumbnail! {e}")

    def start_wait_link_thread(self, *args):
        """
        Starts the thread for capturing events in the entry for YouTube links.
        """
        Thread(target=self.wait_link, args=(self.in_link_entry.get(),)).start()

    def wait_link(self, url: str) -> None:
        """
        Updates the video panel with the video's title, thumbnail, and drives
        the link status sequence (verify → fetch → fetched).
        """
        # 1) Empty? back to waiting
        # 1) No URL yet?
        if not url:
            self.window.after(0, lambda: self.link_status.config(text="Waiting for link..."))
            self.window.after(0, self.reset_video_info_panel)
            return

        # 2) Verifying
        self.window.after(0, lambda: self.link_status.config(text="Verifying link..."))

        # 3) Is it syntactically a URL?
        if not validators.url(url):
            self.window.after(0, lambda: self.link_status.config(text="Please enter a valid link."))
            self.window.after(3000, lambda: self.link_status.config(text="Waiting for link..."))
            self.window.after(0, self.reset_video_info_panel)
            return

        # 4) Is it actually a YouTube URL?
        if not self._is_youtube_url(url):
            self.window.after(0, lambda: self.link_status.config(text="Please enter a valid YouTube link."))
            self.window.after(3000, lambda: self.link_status.config(text="Waiting for link..."))
            self.window.after(0, self.reset_video_info_panel)
            return

        # 5) Looks good!
        self.window.after(0, lambda: self.link_status.config(text="Link correct..."))
        # after 1s switch to “Fetching…”
        self.window.after(1000, lambda: self.link_status.config(text="Fetching link..."))

        # 6) Pull metadata
        opts = {'quiet': True, 'skip_download': True, 'extract_flat': False}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception:
            self.window.after(0, lambda: self.link_status.config(text="Error fetching link."))
            return

        # 7) Display title + thumbnail
        self.current_info = info
        title = info.get('title', '')
        thumb = info.get('thumbnail')
        def upd():
            self.video_title.config(text=title)
            self.thumbnail.delete('all')
            if thumb:
                self.photo = self.get_thumbnail(thumb)
                if self.photo:
                    self.thumbnail.create_image(0,0,anchor='nw',image=self.photo)
        self.window.after(0, upd)
        self.current_info = info
        self.size_cache.clear()    # <-- flush old entries
        # 8) Done
        self.window.after(0, self._refresh_quality_menu)
        self.window.after(0, self.update_filesize_display)
        self.window.after(0, lambda: self.link_status.config(text="Link fetched!"))
    def reset_video_info_panel(self):
        """
        Resets the video info panel widgets.
        """
        self.video_title.config(text="")
        self.photo = None
        self.thumbnail.delete('all')
        self.current_info = None
        # also clear filesize
        self.filesize_label.config(text="")

    def update_quality_options(self, *args):
        """
        Switches the Quality menu entries when MP3/MP4 is toggled,
        then gray-out anything unsupported.
        """
        # set the label
        if self.is_mp3.get():
            self.quality_label.config(text="Audio Quality")
            opts = [('Low',96), ('Medium',192), ('High',320)]
        else:
            self.quality_label.config(text="Video Quality")
            opts = [('480p',480), ('720p',720), ('1080p',1080), ('4K',2160)]

        # rebuild the menu
        menu = self.quality_menu['menu']
        menu.delete(0, 'end')
        for label, _ in opts:
            menu.add_command(
                label=label,
                command=lambda v=label: self.quality_var.set(v),
            )
        default_label = opts[len(opts)//2][0]
        self.quality_var.set(default_label)
        # now gray-out unsupported entries
        self._refresh_quality_menu()

    def change_widgets(self, mode: str) -> None:
        """
        Enables/disables the necessary widgets while converting.

        Args:
            mode (str): Takes in either the arguments 'on' or 'off' to state the mode of the widgets.
        """
        try:
            if mode == 'on':
                state = 'normal'
            elif mode == 'off':
                state = 'disabled'
            else:
                raise ValueError
        except ValueError:
            messagebox.showerror("Widget Error", "change_widgets() only takes 'on' or 'off'")

        to_change = [
            self.in_link, self.in_directory,
            self.mp3_butt,  self.mp4_butt,
            self.quality_menu, self.filename_entry,
            self.browse,     self.convert
        ]
        for w in to_change:
            w.config(state=state)
    
    @staticmethod
    def _strip_ansi(s: str) -> str:
        """
        Removes ANSI‐style escape sequences (e.g. '\x1b[0;94m') from a string.
        """
        ansi_re = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        return ansi_re.sub('', s)
    
    def yt_dlp_hook(self, d: dict):
        """
        Hook for yt-dlp to update download_status label.

        Args:
            d (dict): status dict from yt-dlp progress hook.
        """
        status   = d.get('status')
        # raw percent might have ANSI codes in it
        raw_pct  = d.get('_percent_str', '').strip()
        clean_pct = self._strip_ansi(raw_pct)
        filename = os.path.basename(d.get('filename', ''))

        if status == 'downloading':
            text = f"Downloading {filename} {clean_pct}"
        elif status == 'finished':
            text = f"Finished {filename}"
        else:
            return

        # update your label on the UI thread
        self.window.after(0, lambda: self.download_status.config(text=text))
    def update_filesize_display(self, *args):
        """
        Kicks off a background metadata-only size estimation
        so it will always be correct — but reuses any previously cached result.
        """
        url     = self.in_link_entry.get().strip()
        to_mp3  = self.is_mp3.get()
        quality = self.quality_var.get()
        key     = (url, to_mp3, quality)

        # no URL? blank out
        if not url:
            return self.filesize_label.config(text="")

        # cache hit → instant update
        if key in self.size_cache:
            mb = self.size_cache[key] / (1024*1024)
            return self.filesize_label.config(text=f"Estimated size: {mb:.2f} MB")

        # cache miss → show placeholder & fire off thread
        self.filesize_label.config(text="Estimating size…")
        Thread(
            target=self._estimate_and_update_size,
            args=(url, to_mp3, quality)
        ).start()

    def _estimate_and_update_size(self, url: str, is_mp3: bool, quality: str):
        """
        Background thread: runs yt_dlp.extract_info with the same format
        string we’d use to download, then sums the requested_formats sizes
        and updates the label.
        """
        # build the same format specifier you use for download
        if is_mp3:
            fmt = 'bestaudio/best'
        else:
            height_map = {'480p':480, '720p':720, '1080p':1080, '4K':2160}
            max_h = height_map.get(quality, 720)
            fmt = f'bestvideo[height<={max_h}]+bestaudio/best'

        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'noplaylist': True,
            'format': fmt,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception:
            self.window.after(0, lambda: self.filesize_label.config(text="Size unknown"))
            return

        total = 0
        if 'requested_formats' in info:
            for f in info['requested_formats']:
                total += f.get('filesize') or f.get('filesize_approx') or 0
        else:
            total = info.get('filesize') or info.get('filesize_approx') or 0

        # *** cache it ***
        key = (url, is_mp3, quality)
        self.size_cache[key] = total

        mb = total / (1024*1024)
        self.window.after(0, lambda:
            self.filesize_label.config(text=f"Estimated size: {mb:.2f} MB")
        )

    @staticmethod
    def _is_youtube_url(url: str) -> bool:
        """
        Returns True if the URL’s hostname is youtube.com or youtu.be.
        """
        try:
            net = urlparse(url).netloc.lower()
            return 'youtube.com' in net or 'youtu.be' in net
        except:
            return False
    def _refresh_quality_menu(self):
        """
        Rebuild the Quality menu, disabling any entries
        that self.current_info does not actually support.
        """
        if not self.current_info:
            return

        menu = self.quality_menu['menu']
        menu.delete(0, 'end')

        if self.is_mp3.get():
            # audio targets (kbps)
            opts = [('Low',96), ('Medium',192), ('High',320)]
            # what bitrates are available?
            abr_list = [f.get('abr') or 0
                        for f in self.current_info['formats']
                        if f.get('vcodec')=='none']
            max_abr = max(abr_list) if abr_list else 0

            for label, kbps in opts:
                state = 'normal' if kbps <= max_abr else 'disabled'
                menu.add_command(
                    label=label,
                    command=lambda v=label: self.quality_var.set(v),
                    state=state
                )
        else:
            # video targets (height)
            opts = [('480p',480), ('720p',720), ('1080p',1080), ('4K',2160)]
            heights = [f.get('height') or 0
                       for f in self.current_info['formats']
                       if f.get('vcodec')!='none']
            max_h = max(heights) if heights else 0

            for label, h in opts:
                state = 'normal' if h <= max_h else 'disabled'
                menu.add_command(
                    label=label,
                    command=lambda v=label: self.quality_var.set(v),
                    state=state
                )

        # ensure the selected value is valid
        cur = self.quality_var.get()
        entries = [ menu.entrycget(i,'label') for i in range(menu.index('end')+1) ]
        states  = [ menu.entrycget(i,'state') for i in range(menu.index('end')+1) ]
        if cur not in entries or states[entries.index(cur)]=='disabled':
            for lbl, st in zip(entries, states):
                if st=='normal':
                    self.quality_var.set(lbl)
                    break

        # finally, re-estimate size for the new selection
        self.update_filesize_display()
    def start_convert(self):
        """
        Starts the conversion process thread.
        """
        Thread(target=self.convert_now).start()

    def convert_now(self):
        """
        Converts the YouTube link provided into either MP3 or MP4.
        """
        # Start the progress bar.
        self.pb.start()
        self.status_text.config(text="Converting...")
        self.change_widgets('off')

        url        = self.in_link.get().strip()
        directory  = self.in_directory.get().strip()
        to_mp3     = self.is_mp3.get()
        quality    = self.quality_var.get()
        noplay     = 'list=' not in url

        # Determine base filename
        base_name = self.filename_entry.get().strip()
        if not base_name and self.current_info:
            base_name = self.current_info.get('title', '')
        if not base_name:
            base_name = 'download'
        outtmpl = os.path.join(directory, base_name) + '.%(ext)s'

        if to_mp3:
            # map Low/Med/High → kbps
            kbps_map = {'Low':'96', 'Medium':'192', 'High':'320'}
            ydl_opts = {
                'format':       'bestaudio/best',
                'outtmpl':      outtmpl,
                'postprocessors':[{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec':'mp3',
                    'preferredquality': kbps_map.get(quality, '192'),
                }],
                'progress_hooks':[self.yt_dlp_hook],
                'noplaylist':   noplay,
            }
        else:
            # map 480p/720p/1080p/4K → max height
            height_map = {'480p':480, '720p':720, '1080p':1080, '4K':2160}
            max_h = height_map.get(quality, 720)
            ydl_opts = {
                'format':              f'bestvideo[height<={max_h}]+bestaudio/best',
                'outtmpl':             outtmpl,
                'merge_output_format': 'mp4',
                'recode-video':        'mp4',
                'progress_hooks':      [self.yt_dlp_hook],
                'noplaylist':          noplay,
            }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            messagebox.showerror("Download Error", str(e))

        # Restore UI
        self.change_widgets('on')
        self.pb.stop()
        self.status_text.config(text="Done!")
        webbrowser.open(os.path.realpath(directory))
        Thread(target=self.reset_dl_status).start()

    def reset_dl_status(self):
        """
        Resets the download status.
        """
        time.sleep(5)
        self.window.after(0, lambda: self.download_status.config(text=''))
        self.window.after(0, lambda: self.status_text.config(text='Idle'))

    def get_dir(self):
        """
        Asks for the directory. This will be used as a location to save the MP3 or MP4 files.
        """
        file_location = filedialog.askdirectory()
        if file_location:
            self.in_directory.delete(0, tk.END)
            self.in_directory.insert(0, file_location)
        return file_location


    def run(self):
        """
        Runs the main window.
        """
        self.window.resizable(False, False)
        self.window.mainloop()

if __name__ == '__main__':
    GUI().run()
