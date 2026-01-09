"""
Audio extraction from MP4 files.

This module extracts mono audio from MP4 video files using FFmpeg.
The audio is converted to 16kHz WAV format for speech recognition.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

from utils import setup_logger, ensure_directory, format_duration, validate_file_exists


logger = setup_logger(__name__)


class AudioExtractor:
    """Extract audio from video files using FFmpeg."""
    
    def __init__(self):
        """Initialize the audio extractor."""
        self.sample_rate = 16000  # 16kHz for Whisper
        self.channels = 1  # Mono
        self.audio_codec = "pcm_s16le"
    
    def check_ffmpeg_installed(self) -> bool:
        """
        Check if FFmpeg is installed and accessible.
        
        Returns:
            True if FFmpeg is available, False otherwise
        """
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                check=True,
                timeout=10
            )
            logger.info("✓ FFmpeg is installed and accessible")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error(
                "✗ FFmpeg is not installed or not in PATH\n"
                "  Install from: https://ffmpeg.org/download.html"
            )
            return False
    
    def get_video_duration(self, video_path: Path) -> Optional[float]:
        """
        Get the duration of a video file using FFprobe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds, or None if error occurs
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1:noprint_wrappers=1",
                    str(video_path)
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=True
            )
            duration = float(result.stdout.strip())
            return duration
        except Exception as e:
            logger.warning(f"Could not determine video duration: {e}")
            return None
    
    def extract_audio(
        self,
        video_path: Path,
        output_path: Path,
        verbose: bool = False
    ) -> bool:
        """
        Extract audio from video file to WAV format.
        
        Args:
            video_path: Path to input video file (MP4)
            output_path: Path for output WAV file
            verbose: Print FFmpeg output
            
        Returns:
            True if successful, False otherwise
        """
        if not validate_file_exists(video_path):
            return False
        
        # Ensure output directory exists
        ensure_directory(output_path.parent)
        
        # Get video duration for progress indication
        duration = self.get_video_duration(video_path)
        if duration:
            logger.info(f"Video duration: {format_duration(duration)}")
        
        logger.info(f"Extracting audio from: {video_path.name}")
        logger.info(f"Output format: {self.channels}ch, {self.sample_rate}Hz, 16-bit WAV")
        logger.info(f"Saving to: {output_path.name}")
        
        try:
            # FFmpeg command to extract audio
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-vn",  # No video
                "-acodec", self.audio_codec,  # PCM 16-bit
                "-ar", str(self.sample_rate),  # Sample rate
                "-ac", str(self.channels),  # Channels (mono)
                "-y",  # Overwrite output
                str(output_path)
            ]
            
            if verbose:
                logger.info(f"Command: {' '.join(cmd)}")
            
            # Run FFmpeg
            result = subprocess.run(
                cmd,
                capture_output=not verbose,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
            
            # Verify output file exists and has content
            if not output_path.exists():
                logger.error("Output WAV file was not created")
                return False
            
            file_size = output_path.stat().st_size
            if file_size < 1000:  # Less than 1KB is suspicious
                logger.error(f"Output file is too small ({file_size} bytes)")
                return False
            
            logger.info(f"✓ Audio extraction successful")
            logger.info(f"  Output size: {file_size / (1024*1024):.2f} MB")
            
            return True
            
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg extraction timed out")
            return False
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return False


def extract_audio_from_mp4(
    mp4_path: Path,
    wav_path: Optional[Path] = None,
    verbose: bool = False
) -> Optional[Path]:
    """
    Convenience function to extract audio from MP4.
    
    Args:
        mp4_path: Path to MP4 video file
        wav_path: Output WAV path (if None, uses same name with .wav extension)
        verbose: Print FFmpeg output
        
    Returns:
        Path to output WAV file if successful, None otherwise
    """
    if wav_path is None:
        wav_path = mp4_path.with_suffix(".wav")
    
    extractor = AudioExtractor()
    
    # Check FFmpeg first
    if not extractor.check_ffmpeg_installed():
        return None
    
    success = extractor.extract_audio(mp4_path, wav_path, verbose=verbose)
    
    if success:
        return wav_path
    return None


if __name__ == "__main__":
    # Example usage
    logger.info("Audio Extraction Module - Demonstration")
    logger.info("=" * 50)
    
    # Example paths (adjust to your test file)
    example_mp4 = Path(__file__).parent.parent / "recordings" / "meeting.mp4"
    example_wav = Path(__file__).parent.parent / "recordings" / "meeting.wav"
    
    extractor = AudioExtractor()
    
    # Check FFmpeg installation
    if not extractor.check_ffmpeg_installed():
        logger.info("Please install FFmpeg to use this module")
        sys.exit(1)
    
    logger.info("FFmpeg is ready for audio extraction")
