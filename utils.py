import re
from urllib.parse import urlparse

def strip_ansi(s: str) -> str:
    """
    Removes ANSI‐style escape sequences (e.g. '\x1b[0;94m') from a string.
    """
    ansi_re = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_re.sub('', s)

def is_youtube_url(url: str) -> bool:
    """
    Returns True if the URL’s hostname is youtube.com or youtu.be.
    """
    try:
        net = urlparse(url).netloc.lower()
        return 'youtube.com' in net or 'youtu.be' in net
    except:
        return False