"""
Speech-to-text transcription using OpenAI Whisper.

This module handles local Whisper transcription with automatic language detection
and produces outputs in multiple formats (text, JSON, timestamped).
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import whisper
except ImportError:
    whisper = None

from utils import setup_logger, ensure_directory, seconds_to_timestamp, validate_file_exists


logger = setup_logger(__name__)


class WhisperTranscriber:
    """Transcribe audio files using OpenAI Whisper."""
    
    # Supported models: tiny, base, small, medium, large
    # For production: base or small (balance of quality and speed)
    # Windows CPU: disable fp16
    SUPPORTED_MODELS = ["tiny", "base", "small", "medium", "large"]
    DEFAULT_MODEL = "medium"
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Initialize Whisper transcriber.
        
        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large)
            
        Raises:
            ImportError: If Whisper is not installed
            ValueError: If model name is not supported
        """
        if whisper is None:
            raise ImportError(
                "Whisper is not installed. Run: pip install openai-whisper"
            )
        
        if model_name not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model: {model_name}. Choose from: {self.SUPPORTED_MODELS}"
            )
        
        self.model_name = "small"
        self.model = None
        self.device = None
        self._is_windows = sys.platform == "win32"
    
    def load_model(self) -> bool:
        """
        Load Whisper model into memory.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Loading Whisper '{self.model_name}' model...")
            
            # Determine device and fp16 setting
            # Windows CPU doesn't support fp16 efficiently
            use_fp16 = not self._is_windows
            
            self.model = whisper.load_model(
                self.model_name,
                device="cpu",  # Use CPU for compatibility
                download_root=None,  # Use default cache directory
                in_memory=False
            )
            
            logger.info(f"✓ Model loaded successfully (fp16={use_fp16})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def unload_model(self):
        """Unload model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
            logger.info("Model unloaded from memory")
    
    def transcribe_audio(
        self,
        audio_path: Path,
        language: Optional[str] = None,
        verbose: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio file using Whisper.
        
        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
            language: Language code (e.g., 'en', 'es'). None for auto-detect.
            verbose: Print Whisper output
            
        Returns:
            Dictionary with transcription results, or None if error
        """
        if not validate_file_exists(audio_path):
            return None
        
        if self.model is None:
            logger.error("Model not loaded. Call load_model() first.")
            return None
        
        try:
            logger.info(f"Transcribing: {audio_path.name}")
            if language:
                logger.info(f"Language: {language}")
            else:
                logger.info("Language: auto-detect")
            
            start_time = time.time()
            
            # Transcribe with Whisper
            # fp16=False for Windows CPU compatibility
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                verbose=verbose,
                fp16=False,  # Disabled for Windows CPU
                temperature=0.0,  # More deterministic
                beam_size=5,  # Good balance of quality/speed
            )
            
            elapsed = time.time() - start_time
            logger.info(f"✓ Transcription complete in {elapsed:.1f} seconds")
            
            # Add metadata
            result["metadata"] = {
                "model": self.model_name,
                "audio_file": str(audio_path),
                "language": result.get("language", "unknown"),
                "duration": result.get("duration", 0),
                "processing_time": elapsed
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return False
    
    def save_transcript_text(
        self,
        result: Dict[str, Any],
        output_path: Path
    ) -> bool:
        """
        Save full transcript as plain text.
        
        Args:
            result: Transcription result from transcribe_audio()
            output_path: Path to output text file
            
        Returns:
            True if successful
        """
        try:
            ensure_directory(output_path.parent)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(result["text"])
            
            logger.info(f"✓ Saved transcript: {output_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save transcript: {e}")
            return False
    
    def save_transcript_json(
        self,
        result: Dict[str, Any],
        output_path: Path
    ) -> bool:
        """
        Save transcript with segment-level timestamps as JSON.
        
        Args:
            result: Transcription result from transcribe_audio()
            output_path: Path to output JSON file
            
        Returns:
            True if successful
        """
        try:
            ensure_directory(output_path.parent)
            
            # Build structured output
            output = {
                "metadata": result.get("metadata", {}),
                "language": result.get("language", "unknown"),
                "duration_seconds": result.get("duration", 0),
                "segments": []
            }
            
            # Process segments
            for segment in result.get("segments", []):
                segment_data = {
                    "id": segment.get("id"),
                    "start": segment.get("start"),
                    "end": segment.get("end"),
                    "text": segment.get("text", "").strip(),
                    "confidence": segment.get("confidence", None)
                }
                output["segments"].append(segment_data)
            
            # Save to JSON
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            num_segments = len(output["segments"])
            logger.info(f"✓ Saved JSON transcript: {output_path.name} ({num_segments} segments)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save JSON transcript: {e}")
            return False
    
    def save_transcript_srt(
        self,
        result: Dict[str, Any],
        output_path: Path
    ) -> bool:
        """
        Save transcript as SRT (SubRip) format.
        
        Args:
            result: Transcription result from transcribe_audio()
            output_path: Path to output SRT file
            
        Returns:
            True if successful
        """
        try:
            ensure_directory(output_path.parent)
            
            with open(output_path, "w", encoding="utf-8") as f:
                for idx, segment in enumerate(result.get("segments", []), 1):
                    start = seconds_to_timestamp(segment.get("start", 0))
                    end = seconds_to_timestamp(segment.get("end", 0))
                    text = segment.get("text", "").strip()
                    
                    f.write(f"{idx}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{text}\n")
                    f.write("\n")
            
            logger.info(f"✓ Saved SRT transcript: {output_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save SRT transcript: {e}")
            return False


def transcribe_file(
    audio_path: Path,
    output_dir: Path,
    model: str = "medium",
    language: Optional[str] = None
) -> bool:
    """
    Convenience function to transcribe audio file and save all formats.
    
    Args:
        audio_path: Path to audio file
        output_dir: Directory to save output files
        model: Whisper model to use
        language: Language code (None for auto-detect)
        
    Returns:
        True if successful
    """
    transcriber = WhisperTranscriber(model)
    
    # Load model
    if not transcriber.load_model():
        return False
    
    try:
        # Transcribe
        result = transcriber.transcribe_audio(audio_path, language=language)
        if result is None:
            return False
        
        # Save outputs
        base_name = audio_path.stem
        ensure_directory(output_dir)
        
        success = True
        success &= transcriber.save_transcript_text(
            result,
            output_dir / f"{base_name}.txt"
        )
        success &= transcriber.save_transcript_json(
            result,
            output_dir / f"{base_name}.json"
        )
        success &= transcriber.save_transcript_srt(
            result,
            output_dir / f"{base_name}.srt"
        )
        
        return success
        
    finally:
        transcriber.unload_model()


if __name__ == "__main__":
    logger.info("Whisper Transcriber Module - Ready")
    logger.info("=" * 50)
    
    if whisper is None:
        logger.error("Whisper not installed: pip install openai-whisper")
        sys.exit(1)
    
    logger.info("Whisper is available")
    logger.info(f"Available models: {WhisperTranscriber.SUPPORTED_MODELS}")
