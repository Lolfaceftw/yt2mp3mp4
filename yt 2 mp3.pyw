from pytube import YouTube
from pytube import Playlist
from tkinter import filedialog, BooleanVar, ttk, messagebox
from threading import Thread
import time
import tkinter as tk
import os, webbrowser

class GUI:
    def __init__(self) -> None:
        """
        Initializes the GUI window.
        """
        # Info
        self.version = '1.0'
        # Initializes the window.
        self.window = tk.Tk()
        self.window.title(f"Youtube to MP3/MP4 V{self.version}")
        self.window.minsize(550, 200)

        # Boolean variables
        self.is_vid = BooleanVar(value=True)
        self.is_mp3 = BooleanVar(value=True)

        # Labels
        self.link = tk.Label(self.window, text="YouTube Link:", font=('Helvetica', 12, 'bold'))
        self.selection = tk.Label(self.window, text="Preferred Output", font=('Helvetica', 12, 'bold'))
        self.directory = tk.Label(self.window, text="Directory", font=('Helvetica', 12, 'bold'))
        self.status_text = tk.Label(self.window, text="Idle", font=('Helvetica', 12, 'bold'))
        self.download_status = tk.Label(self.window, font=('Helvetica', 10))

        # Text boxes
        self.in_link = tk.Entry(self.window, width=40)
        self.in_directory = tk.Entry(self.window, width=40)

        # Radio Buttons
        self.video_butt = tk.Radiobutton(self.window, text="Video", variable=self.is_vid, value=True, font=('Helvetica', 12, 'bold'))
        self.ps_butt = tk.Radiobutton(self.window, text="Playlist", variable=self.is_vid, value=False, font=('Helvetica', 12, 'bold'))
        self.mp3_butt = tk.Radiobutton(self.window, text="MP3", variable=self.is_mp3, value = True, font=('Helvetica', 12, 'bold'))
        self.mp4_butt = tk.Radiobutton(self.window, text="MP4", variable=self.is_mp3, value = False, font=('Helvetica', 12, 'bold'))

        # Normal Buttons
        self.browse = tk.Button(self.window, text="Browse", command=self.get_dir, font=('Helvetica', 12, 'bold'))
        self.convert = tk.Button(self.window, text="Convert", command = self.convert_now, font=('Helvetica', 12, 'bold'))

        # Progress Bar
        self.pb = ttk.Progressbar(self.window, orient="horizontal", mode='indeterminate', length=250)

        #* Grid Settings
        # Row 0
        self.link.grid(row=0, column=0, padx=5, pady=5)
        self.in_link.grid(row=0, column=1, padx=5, pady=5)

        # Row 1
        self.video_butt.grid(row=1, column=0, padx=5, pady=5)
        self.ps_butt.grid(row=1, column=1, padx=5, pady=5)

        # Row 2
        self.selection.grid(row=2, columnspan=2, padx=5, pady=5)

        # Row 3
        self.mp3_butt.grid(row=3, column=0, padx=5, pady=5)
        self.mp4_butt.grid(row=3, column=1, padx=5, pady=5)

        # Row 4
        self.directory.grid(row=4, columnspan=2, padx=5,pady=5)

        # Row 5
        self.browse.grid(row=5,column=0)
        self.in_directory.grid(row=5,column=1)

        # Row 6
        self.convert.grid(row=6,columnspan=2,padx=5,pady=5)

        # Row 7
        self.pb.grid(row=7,column=0,padx=5,pady=5)
        self.status_text.grid(row=7,column=1,padx=1,pady=1)

        # Row 8
        self.download_status.grid(row=8,columnspan=2,pady=1)

    def convert_now(self):
        # Start the progress bar.
        self.pb.start()
        self.status_text.config(text="Converting...")
        self.window.minsize(550, 325)

        # Capture directory
        directory = self.in_directory.get()
        if self.is_vid.get():
            try:
                yt_link = YouTube(self.in_link.get())
            except Exception as e:
                messagebox.showerror("Link Error!", str(e))
        
            try:
                if self.is_mp3.get():
                    x = yt_link.streams.filter(adaptive=True, only_audio=True).order_by('abr').desc().first().download(output_path=directory)
                    base, _ = os.path.splitext(x)
                    new = base + '.mp3'
                    if not os.path.isfile(new):
                        self.download_status.config(text=f'Downloaded @ {new}')
                        os.rename(x, new)
                    else:
                        self.download_status.config(text=f'File exists @ {new}')
                    self.window.update()
                else:
                    download_location = yt_link.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download(output_path=directory)
                    if not os.path.isfile(download_location):
                        self.download_status.config(text=f'Downloaded @ {download_location}')
                    else:
                        self.download_status.config(text=f'Downloaded @ {download_location}')
                    self.window.update()
            except Exception as e:
                print(str(e))
                messagebox.showerror("YT Streams Error!", str(e))
        else:
            try:
                playlist_link = Playlist(self.in_link.get())
            except Exception as e:
                messagebox.showerror("Link Error!", str(e))
            try:
                if self.is_mp3.get():
                    for audio in playlist_link.videos:
                        y = audio.streams.filter(adaptive=True, only_audio=True).order_by('abr').desc().first().download(output_path=directory)
                        base, _ = os.path.splitext(y)
                        new = base + '.mp3'
                        if not os.path.isfile(new):
                            self.download_status.config(text=f'Downloaded @ {new}')
                            os.rename(y, new)
                        else:
                            self.download_status.config(text=f'File exists @ {new}')
                        self.window.update()
                else:
                    for video in playlist_link.videos:
                        dl_loc = video.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').download(output_path=directory)
                        if not os.path.isfile(dl_loc):
                            self.download_status.config(text=f'Downloaded @ {dl_loc}')
                        else:
                            self.download_status.config(text=f'File exists @ {dl_loc}')
                        self.window.update()
            except Exception as e:
                messagebox.showerror("YT Streams Error!", str(e))
        Thread(target=self.reset_dl_status).start()
        self.window.minsize(550, 250)
        webbrowser.open(os.path.realpath(directory))
        
        self.status_text.config(text="Done!")
        self.pb.stop()

    def reset_dl_status(self):
        time.sleep(2)
        self.download_status.config(text='')

    def get_dir(self):
        self.in_directory.delete('0', tk.END)
        file_location = filedialog.askdirectory()
        self.in_directory.insert(0, file_location)
        return file_location

    def run(self):
        self.window.resizable(False, False)
        self.window.deiconify()
        self.window.mainloop()
if __name__ == '__main__':
    GUI().run()