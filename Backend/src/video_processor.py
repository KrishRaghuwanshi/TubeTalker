import os
import yt_dlp
from moviepy.editor import VideoFileClip
import time
import tempfile
import shutil
import uuid

def download_video(url: str, output_dir: str) -> str:
    """
    Downloads a YouTube video using yt-dlp and returns the absolute file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_template = os.path.join(output_dir, '%(id)s.%(ext)s')

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_template,
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        downloaded_file_path = ydl.prepare_filename(info_dict)

    # Ensure the file exists and has content
    if not os.path.exists(downloaded_file_path) or os.path.getsize(downloaded_file_path) == 0:
        raise RuntimeError(f"Video download failed or empty file: {downloaded_file_path}")

    return os.path.abspath(downloaded_file_path)


def extract_audio(video_path: str, audio_path: str) -> None:
    """
    Extract audio from video using MoviePy safely on Windows.
    Copies video to temp location to avoid PermissionError.
    """
    video_path = os.path.abspath(video_path)
    audio_path = os.path.abspath(audio_path)

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Copy to temporary file to avoid Windows file lock issues
    temp_video_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp4")
    shutil.copy(video_path, temp_video_path)

    try:
        with VideoFileClip(temp_video_path) as video:
            if video.audio is None:
                raise RuntimeError("Video has no audio stream")
            video.audio.write_audiofile(audio_path, logger=None)
    except Exception as e:
        raise RuntimeError(f"Failed to extract audio: {e}")
    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)


def extract_frames(video_path: str, frames_dir: str, fps: int = 1) -> list[str]:
    """
    Extract frames from video safely on Windows.
    Copies video to temp location to avoid PermissionError.
    Returns list of frame file paths.
    """
    video_path = os.path.abspath(video_path)
    frames_dir = os.path.abspath(frames_dir)
    os.makedirs(frames_dir, exist_ok=True)

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    temp_video_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.mp4")
    shutil.copy(video_path, temp_video_path)
    frame_files = []

    try:
        with VideoFileClip(temp_video_path) as video:
            total_frames = int(video.duration * fps)
            for i, t in enumerate([x / fps for x in range(total_frames)]):
                frame_file = os.path.join(frames_dir, f"frame_{i}.jpg")
                video.save_frame(frame_file, t)
                frame_files.append(frame_file)
    except Exception as e:
        raise RuntimeError(f"Failed to extract frames: {e}")
    finally:
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)

    return frame_files
