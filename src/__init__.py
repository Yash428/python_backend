"""
Jitsi Transcription Pipeline - Source Package

Modules:
- extract_audio: MP4 to WAV conversion using FFmpeg
- transcribe: OpenAI Whisper transcription
- segment: Timestamp and segment processing
- utils: Helper utilities and logging
"""

__version__ = "1.0.0"
__author__ = "Backend Team"

from .extract_audio import AudioExtractor, extract_audio_from_mp4
from .transcribe import WhisperTranscriber, transcribe_file
from .segment import SegmentProcessor, process_segments
from .utils import (
    setup_logger,
    seconds_to_timestamp,
    timestamp_to_seconds,
    ensure_directory,
    get_project_root,
)

__all__ = [
    "AudioExtractor",
    "extract_audio_from_mp4",
    "WhisperTranscriber",
    "transcribe_file",
    "SegmentProcessor",
    "process_segments",
    "setup_logger",
    "seconds_to_timestamp",
    "timestamp_to_seconds",
    "ensure_directory",
    "get_project_root",
]
