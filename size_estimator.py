# estimator.py
import yt_dlp

def estimate_size(url: str, is_mp3: bool, quality: str) -> int:
    """
    Returns the estimated download size in bytes for the given
    url / mp3-vs-mp4 / quality triple, by doing a metadata-only
    yt_dlp.extract_info() with the same format string you’d later download.
    """
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
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    total = 0
    if 'requested_formats' in info:
        for f in info['requested_formats']:
            total += f.get('filesize') or f.get('filesize_approx') or 0
    else:
        total = info.get('filesize') or info.get('filesize_approx') or 0

    return total
