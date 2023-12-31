from pytube import YouTube
from pytube import Playlist
from tkinter import filedialog, BooleanVar, ttk, messagebox
from threading import Thread
from PIL import Image, ImageTk
from io import BytesIO
import urllib.request
import time
import tkinter as tk
import os, webbrowser

class GUI:
    def __init__(self) -> None:
        """
        Initializes the GUI window.
        """
        # Info
        self.version = '1.2.0'
        # Initializes the window.
        self.window = tk.Tk()
        self.window.title(f"Youtube to MP3/MP4 V{self.version}")
        self.window.minsize(550, 200)

        # To trace
        self.in_link_entry = tk.StringVar()
        self.photo = None

        # Boolean variables
        self.is_vid = True
        self.is_mp3 = BooleanVar(value=True)

        # Labels
        self.link = tk.Label(self.window, text="YouTube Link:", font=('Helvetica', 12, 'bold'))
        self.selection = tk.Label(self.window, text="Preferred Output", font=('Helvetica', 12, 'bold'))
        self.directory = tk.Label(self.window, text="Directory", font=('Helvetica', 12, 'bold'))
        self.status_text = tk.Label(self.window, text="Idle", font=('Helvetica', 12, 'bold'))
        self.download_status = tk.Label(self.window, font=('Helvetica', 10), wraplength=250)
        self.video_title = tk.Label(self.window, text="YouTube Video Title", font=('Helvetica', 12, 'bold'))
        self.file_size = tk.Label(self.window, font=('Helvetica', 12, 'bold'))

        # Text boxes
        self.in_link = tk.Entry(self.window, textvariable=self.in_link_entry, width=40)
        self.in_directory = tk.Entry(self.window, width=40)

        # Radio Buttons
        self.mp3_butt = tk.Radiobutton(self.window, text="MP3", variable=self.is_mp3, value = True, font=('Helvetica', 12, 'bold'))
        self.mp4_butt = tk.Radiobutton(self.window, text="MP4", variable=self.is_mp3, value = False, font=('Helvetica', 12, 'bold'))

        # Normal Buttons
        self.browse = tk.Button(self.window, text="Browse", command=self.get_dir, font=('Helvetica', 12, 'bold'))
        self.convert = tk.Button(self.window, text="Convert", command = self.start_convert, font=('Helvetica', 12, 'bold'))

        # Progress Bar
        self.pb = ttk.Progressbar(self.window, orient="horizontal", mode='indeterminate', length=250)

        # Canvas Image
        self.thumbnail = tk.Canvas(self.window, width=400, height=200)

        #* Grid Settings
        # Row 0
        self.link.grid(row=0, column=0, padx=5, pady=5)
        self.in_link.grid(row=0, column=1, padx=5, pady=5)
        self.video_title.grid(row=0, column=2, padx=5, pady=5)

        # Row 1
        self.selection.grid(row=1, columnspan=2, padx=5, pady=5)
        self.thumbnail.grid(row=1, column=2, rowspan=3, padx=5, pady=5)

        # Row 2
        self.mp3_butt.grid(row=2, column=0, padx=5, pady=5)
        self.mp4_butt.grid(row=2, column=1, padx=5, pady=5)

        # Row 3
        self.directory.grid(row=3, columnspan=2, padx=5,pady=5)

        # Row 4
        self.browse.grid(row=4,column=0)
        self.in_directory.grid(row=4,column=1)
        self.file_size.grid(row=4, column=2)

        # Row 5
        self.convert.grid(row=5,columnspan=2,padx=5,pady=5)

        # Row 6
        self.pb.grid(row=6,column=0,padx=5,pady=5)
        self.status_text.grid(row=6,column=1,padx=1,pady=1)

        # Row 7
        self.download_status.grid(row=7,columnspan=2,pady=1)

        # Initial threads
        self.in_link_entry.trace_add('write', callback=self.start_wait_link_thread)

    def get_thumbnail(self, yt_object):
        """
        Gets the thumbnail of the YouTube video.

        Args:
            yt_object (YouTube/Playlist): YouTube or Playlist object from Pytube.
        """
        open_url = urllib.request.urlopen(yt_object.thumbnail_url)
        raw_data = open_url.read()


        im = Image.open(BytesIO(raw_data))
        im = im.resize((400, 200))
        return ImageTk.PhotoImage(im)

    def start_wait_link_thread(self, *args):
        """
        Starts the thread for capturing events in the entry for YouTube links.
        """
        Thread(target=self.wait_link, args=(self.get_input_link(),)).start()

    def get_file_size(self, link, mode: str):
        """
        Returns the file size of both MP3 and MP4 of the video.

        Args:
            object (YouTube/Playlist): YouTube or Playlist object from pytube.
            mode (str): mp3 or mp4
        """
        try:
            if mode == 'mp3':
                return round(int(self.object_filter(link, mode).filesize) / 1000000, 2)
            elif mode == 'mp4':
                return round(int(self.object_filter(link, mode).filesize) / 1000000, 2)
            else: raise ValueError
        except ValueError:
            messagebox.showerror("get_file_size() only accepts mp3 or mp4 as arguments for the mode.")

    def reset_video_info_panel(self):
        """
        Resets the video info panel widgets.
        """
        self.video_title.config(text="YouTube Video Title")
        self.photo = None
        self.file_size.config(text = '')
        self.thumbnail.delete('all')

    def wait_link(self, youtube_object):
        """
        Updates the video panel with the video's title, thumbnail, and file size.

        Args:
            youtube_object (YouTube/Playlist): YouTube or Playlist object from pytube.
        """
        try:
            self.video_title.config(text=youtube_object.streams[0].title)
            self.photo = self.get_thumbnail(youtube_object)
            self.thumbnail.create_image(1, 1, image=self.photo, anchor='nw')
            self.file_size.config(text=f"Filesize: {self.get_file_size(youtube_object, 'mp3')}MB (MP3) and {self.get_file_size(youtube_object, 'mp4')}MB (MP4)")

        except:
            self.reset_video_info_panel()

    def start_convert(self):
        """
        Starts the conversion process thread.
        """
        Thread(target=self.convert_now).start()

    def check_in_link(self):
        """
        Checks the input link whether it is under a playlist or not.
        """
        if 'list' in self.in_link.get():
            self.is_vid = False
        else: 
            self.is_vid = True

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
            else: raise ValueError
        except ValueError:
            messagebox.showerror(f'change_widgets() only takes in either on or off as arguments!')

        to_change_state = [self.in_link, self.in_directory, self.mp3_butt, self.mp4_butt, self.browse, self.convert]
        for variables in to_change_state:
            variables.config(state=state)

    def get_input_link(self):
        """
        Gets the input link data. Returns a Youtube or Playlist object.
        """
        self.check_in_link()
        try:
            
            if self.is_vid:
                return YouTube(self.in_link.get())
            else:
                return Playlist(self.in_link.get())
        except: pass

    def download_status_update(self, state: int, string: str):
        """
        Prints the download status of the specific video or audio file.

        Args:
            state (int): 0 - downloading; 1 - downloaded; 2 - file exists
            string (str): title/directory of the video or audio file.
        """
        try:
            if state == 0:
                self.download_status.config(text=f'Downloading {string}')
            elif state == 1:
                self.download_status.config(text=f'Downloaded @ {string}')
            elif state == 2:
                self.download_status.config(text=f'File exists @ {string}')
            else: 
                raise ValueError
        except ValueError:
            print('download_status_update() only takes in 0-2 for the state!')

    def download_file(self, streams_object: str, directory: str, mode: str):
        """
        Downloads the stream object file and saves it.

        Args:
            streams_object (YouTube/Playlist): Streams object from Pytube either YouTube or Playlist
            directory (str): Directory where the file will be saved.
            mode (str): Accepts 'mp3' or 'mp4'
        """
        # Check if file exists before downloading
        to_check = f'{directory}\\{streams_object.title}.{mode}'
        print(to_check, "exists", os.path.isfile(to_check))
        if os.path.isfile(to_check):
            self.download_status_update(2, streams_object.title)
        else:
            self.download_status_update(0, streams_object.title)
            temp = streams_object.download(output_path=directory)
            base, _ = os.path.splitext(temp)
            output = base + '.' + mode
            if mode == 'mp3': 
                os.rename(temp, output)
            self.download_status_update(1, output)

    def object_filter(self, link, mode: str) -> None:
        """
        Returns the filtered object.

        Args:
            link (Youtube/Playlist): YouTube or Playlist object from link. 
            mode (str): mp4 or mp3.
        """
        try:
            if mode == 'mp3':
                return link.streams.filter(adaptive=True, only_audio=True).order_by('abr').desc().first()
            elif mode == 'mp4':
                return link.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            else: raise ValueError
        except ValueError:
            messagebox.showerror("Value Error!", "object_filter() takes in only mp3 or mp4 for the mode.")

    def start_download(self, link, type: str, directory: str, is_mp3: bool):
        """
        Starts the download process of the YouTube video or playlist.

        Args:
            link (Youtube/Playlist): YouTube or Playlist Object from link.
            type (str): Accepts either 'vid' or 'playlist'.
            directory (str): The directory to save.
            is_mp3 (bool): Checks if the object will be converted to mp3 or mp4.
        """
        if is_mp3: mode = 'mp3'
        else: mode = 'mp4'

        try:
            if type == 'vid':
                streams_object_mp3 = self.object_filter(link, mode)
                self.download_file(streams_object_mp3, directory, mode)
                self.window.update()
            elif type == 'playlist':
                for video in link.videos:
                    playlist_object_mp3 = self.object_filter(video, mode)
                    Thread(target=self.wait_link, args=(video,)).start()
                    self.download_file(playlist_object_mp3, directory, 'mp3')
                    self.window.update()

        except Exception as e:
            messagebox.showerror("YT Streams Error!", str(e))
    def convert_now(self):
        """
        Converts the YouTube link provided into either MP3 or MP4.
        """
        # Start the progress bar.
        self.pb.start()

        # Adjust initial window.
        self.status_text.config(text="Converting...")
        self.change_widgets('off')

        # Capture directory
        directory = self.in_directory.get()
        
        if self.is_vid:
            yt_link = self.get_input_link()
            self.start_download(yt_link, 'vid', directory, self.is_mp3.get())
        else:
            playlist_link = self.get_input_link()
            self.start_download(playlist_link, 'playlist', directory, self.is_mp3.get())

        # Done
        self.change_widgets('on')

        # Start timer for status deletion.
        Thread(target=self.reset_dl_status).start()
        webbrowser.open(os.path.realpath(directory))
        self.status_text.config(text="Done!")
        self.pb.stop()

    def reset_dl_status(self):
        """
        Resets the download status.
        """
        time.sleep(5)
        self.download_status.config(text='')
        self.status_text.config(text = 'Idle')

    def get_dir(self):
        """
        Asks for the directory. This will be used as a location to save the MP3 or MP4 files.
        """
        self.in_directory.delete('0', tk.END)
        file_location = filedialog.askdirectory()
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