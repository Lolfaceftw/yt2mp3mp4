# estimator.py
"""
Estimates the download size of a YouTube video based on metadata.

This module provides functionality to estimate the file size of a YouTube video
before downloading. It prioritizes direct filesize information from yt-dlp if available.
If direct sizes are missing, it falls back to heuristics:
1. For video streams without size, it attempts to find an H.264 (AVC1) encoded
   stream of the same resolution. If this "proxy" stream has size information
   (direct or from its own bitrate heuristic), that is used.
2. If no suitable proxy is found or the proxy also lacks size, it uses the
   bitrate (VBR or TBR) of the originally selected video stream.
3. For audio streams without size, it uses their ABR (Average BitRate).

The estimate is returned along with a flag indicating if it's "incomplete"
(i.e., based on heuristics or missing components).
"""
import yt_dlp
import traceback
from typing import Tuple, Optional, Dict, List, Any # For type hinting

from logger import logger # Use the centralized logger
import config # Use centralized configuration

# Version for internal tracking of heuristic logic, can be useful for debugging.
ESTIMATOR_LOGIC_VERSION = "4.1.1_docstrings" # Updated version

def _calculate_heuristic_size(duration_seconds: Optional[float],
                              bitrate_kbps: Optional[float],
                              stream_id_for_log: str,
                              stream_type_for_log: str) -> Tuple[int, str]:
    """
    Helper function to calculate estimated size from duration and bitrate.

    Args:
        duration_seconds: Video/audio duration in seconds.
        bitrate_kbps: Stream bitrate in kilobits per second.
        stream_id_for_log: Format ID for logging purposes.
        stream_type_for_log: Description of the stream type for logging.

    Returns:
        A tuple (estimated_size_bytes, source_description_string).
        Returns (0, "error_string") if calculation is not possible.
    """
    if duration_seconds is None or bitrate_kbps is None:
        logger.log(f"    - HEURISTIC CALC (ID: {stream_id_for_log}): Cannot calculate, "
                   f"duration ({duration_seconds}) or bitrate ({bitrate_kbps}) is None.", file_only=True)
        return 0, "heuristic_missing_data"
    try:
        calc_bitrate = float(bitrate_kbps)
        calc_duration = float(duration_seconds)
        
        estimated_size_float = calc_duration * (calc_bitrate / 8.0) * 1000.0
        chosen_size = int(estimated_size_float) 
        
        source_description = f"heuristic ({stream_type_for_log} @ {bitrate_kbps}kbps)"
        logger.log(f"  >>> HEURISTIC CALC (ID: {stream_id_for_log}). Duration: {calc_duration:.2f}s, "
                   f"Bitrate: {calc_bitrate:.3f}kbps. Estimated bytes: {chosen_size}.", file_only=True)
        return chosen_size, source_description
    except ValueError as ve:
        logger.log(f"  !!! HEURISTIC CALC FAILED (ValueError on ID: {stream_id_for_log}). "
                   f"Bitrate: {bitrate_kbps}. Error: {ve}", file_only=True)
        return 0, "heuristic_value_error"
    except Exception as ex: 
        logger.log(f"  !!! HEURISTIC CALC FAILED (Exception on ID: {stream_id_for_log}). Error: {ex}", file_only=True)
        return 0, "heuristic_exception"

def estimate_size(url: str, is_mp3: bool, quality_param_input: str) -> Tuple[int, bool]:
    """
    Estimates download size in bytes and indicates if the estimate is incomplete.

    Args:
        url: The YouTube video URL.
        is_mp3: True if estimating for MP3, False for MP4.
        quality_param_input: The quality parameter string (e.g., '192' for MP3 ABR,
                             '1080' for MP4 video height).

    Returns:
        A tuple containing:
            - estimated_size_bytes (int): Estimated size in bytes.
            - size_is_incomplete (bool): True if any component's size was derived
                                         from heuristics or was missing.
    """
    logger.log(f"--- Size Estimation (Estimator v{ESTIMATOR_LOGIC_VERSION}) ---", file_only=True)
    logger.log(f"Input: url='{url}', is_mp3={is_mp3}, quality_param='{quality_param_input}'", file_only=True)

    format_string = 'bestaudio/best' if is_mp3 else \
                    f'bestvideo[height<={str(quality_param_input)}]+bestaudio/best[height<={str(quality_param_input)}]/best'
    logger.log(f"Format string for yt-dlp: '{format_string}'", file_only=True)

    ydl_opts = {**config.YDL_BASE_OPTS, 'skip_download': True, 'format': format_string}

    total_size_bytes: int = 0
    size_is_incomplete: bool = False 

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info: Dict[str, Any] = ydl.extract_info(url, download=False)

        duration_seconds: Optional[float] = info.get('duration')
        all_available_formats: List[Dict[str, Any]] = info.get('formats', [])
        requested_formats: Optional[List[Optional[Dict[str, Any]]]] = info.get('requested_formats')

        logger.log(f"Video duration: {duration_seconds}s. Total available formats: {len(all_available_formats)}.", file_only=True)

        if requested_formats:
            logger.log(f"Processing {len(requested_formats)} 'requested_formats':", file_only=True)
            for i, f_info in enumerate(requested_formats):
                if f_info is None:
                    logger.log(f"  - Req.Format {i}: IS NONE (SKIPPING)", file_only=True)
                    size_is_incomplete = True; continue

                f_id, vcodec, acodec = str(f_info.get('format_id','N/A')), str(f_info.get('vcodec','none')), str(f_info.get('acodec','none'))
                f_height, vbr, abr = f_info.get('height'), f_info.get('vbr'), f_info.get('abr')
                f_size, f_approx = f_info.get('filesize'), f_info.get('filesize_approx')

                logger.log(f"  - Req.Format {i} (ID: {f_id}, v:{vcodec}, a:{acodec}, h:{f_height}, "
                           f"vbr:{vbr}, abr:{abr}, size:{f_size}, approx:{f_approx})", file_only=True)

                chosen_size: int = 0
                source_of_size: str = "N/A"

                if f_size is not None: chosen_size, source_of_size = int(f_size), "filesize"
                elif f_approx is not None: chosen_size, source_of_size = int(f_approx), "filesize_approx"
                else: 
                    size_is_incomplete = True
                    logger.log(f"    - INFO (Req.Format {i}, ID: {f_id}): No direct size. Heuristic required.", file_only=True)
                    if vcodec != 'none': 
                        logger.log(f"    - Video Component (ID: {f_id}). Target height: {f_height}.", file_only=True)
                        proxy_size, proxy_source = 0, "no_h264_proxy"
                        for alt_f in all_available_formats:
                            if str(alt_f.get('vcodec','none')).startswith('avc1') and alt_f.get('height') == f_height and str(alt_f.get('acodec','none')) == 'none':
                                alt_id, alt_vbr = str(alt_f.get('format_id','N/A')), alt_f.get('vbr')
                                logger.log(f"      - H264_PROXY: Found (ID: {alt_id}, vbr: {alt_vbr})", file_only=True)
                                if alt_f.get('filesize') is not None: proxy_size, proxy_source = int(alt_f['filesize']), f"h264_proxy_filesize (ID:{alt_id})"; break
                                if alt_f.get('filesize_approx') is not None: proxy_size, proxy_source = int(alt_f['filesize_approx']), f"h264_proxy_approx (ID:{alt_id})"; break
                                if duration_seconds and alt_vbr:
                                    ps, p_src = _calculate_heuristic_size(duration_seconds, float(alt_vbr), alt_id, "H264_Proxy_VBR")
                                    if ps > 0: proxy_size, proxy_source = ps, p_src; break
                        if proxy_size > 0: chosen_size, source_of_size = proxy_size, proxy_source; logger.log(f"    >>> Using H.264 Proxy: {source_of_size}, Size: {chosen_size}", file_only=True)
                        else: logger.log(f"    - H.264 proxy not found/usable. Using original (ID: {f_id}).", file_only=True); chosen_size, source_of_size = _calculate_heuristic_size(duration_seconds, vbr or f_info.get('tbr'), f_id, "Orig_Video(vbr/tbr)")
                    elif acodec != 'none': 
                        logger.log(f"    - Audio Component (ID: {f_id}). Using ABR ({abr}).", file_only=True); chosen_size, source_of_size = _calculate_heuristic_size(duration_seconds, abr, f_id, "Audio(abr)")
                    else: logger.log(f"    - WARN (Req.Format {i}, ID: {f_id}): No vcodec or acodec.", file_only=True)
                logger.log(f"  - Req.Format {i} (ID: {f_id}): CHOSEN_SIZE={chosen_size} (from {source_of_size})", file_only=True)
                total_size_bytes += chosen_size
        
        elif info and (info.get('filesize') is not None or info.get('filesize_approx') is not None): 
            logger.log("Estimator: Processing direct info (no 'requested_formats')", file_only=True)
            f_size, f_approx = info.get('filesize'), info.get('filesize_approx')
            chosen_size, source_of_size = 0, "N/A"
            if f_size is not None: chosen_size, source_of_size = int(f_size), "filesize (direct)"
            elif f_approx is not None: chosen_size, source_of_size = int(f_approx), "filesize_approx (direct)"
            else: # Should not be reached if outer if is true, but defensive
                size_is_incomplete = True; source_of_size = "no_direct_size_or_bitrate" 
            total_size_bytes = chosen_size
            logger.log(f"  - Direct Info: CHOSEN_SIZE={total_size_bytes} (from {source_of_size})", file_only=True)
            if chosen_size == 0 and (info.get('vcodec','none') != 'none' or info.get('acodec','none') != 'none'): size_is_incomplete = True
        else:
            logger.log(f"Warning: Could not determine filesize for {url}. No 'requested_formats' or direct filesize.", console_only=True)
            size_is_incomplete = True

    except yt_dlp.utils.DownloadError as e:
        logger.log(f"Error during size estimation (yt_dlp DownloadError) for {url}: {e}", console_only=True)
        size_is_incomplete = True 
    except Exception as e: 
        logger.log(f"Generic exception during size estimation for {url}: {e}\n{traceback.format_exc()}", console_only=True)
        size_is_incomplete = True 
        total_size_bytes = 0 

    logger.log(f"Estimator: Final estimated size: {total_size_bytes} bytes, Incomplete: {size_is_incomplete}", file_only=True)
    return total_size_bytes, size_is_incomplete