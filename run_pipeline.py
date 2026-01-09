"""
Main pipeline orchestrator for Jitsi transcription.

This module coordinates the entire workflow:
1. Extract audio from MP4 using FFmpeg
2. Transcribe audio using OpenAI Whisper
3. Generate timestamped segments
4. Save all output formats

Usage:
    python run_pipeline.py <path/to/meeting.mp4> [--model base] [--language en]
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from extract_audio import extract_audio_from_mp4
from transcribe import transcribe_file
from segment import process_segments
from diarize import SpeakerDiarizer
from utils import setup_logger, get_project_root, format_duration, ensure_directory


logger = setup_logger(__name__)


class JitsiTranscriptionPipeline:
    """Orchestrate the complete transcription pipeline."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the pipeline.
        
        Args:
            project_root: Root directory of project
        """
        self.project_root = project_root or get_project_root()
        self.recordings_dir = self.project_root / "recordings"
        self.transcripts_dir = self.project_root / "transcripts"
        
        # Ensure directories exist
        ensure_directory(self.recordings_dir)
        ensure_directory(self.transcripts_dir)
    
    def run(
        self,
        input_mp4: Path,
        model: str = "base",
        language: Optional[str] = None,
        cleanup_wav: bool = False,
        enable_diarization: bool = True
    ) -> bool:
        """
        Run the complete transcription pipeline.
        
        Args:
            input_mp4: Path to input MP4 video file
            model: Whisper model to use (tiny, base, small, medium, large)
            language: Optional language code (e.g., 'en', 'es')
            cleanup_wav: Remove intermediate WAV file after transcription
            enable_diarization: Include speaker diarization in results
            
        Returns:
            True if pipeline completed successfully
        """
        logger.info("=" * 80)
        logger.info("JITSI TRANSCRIPTION PIPELINE")
        logger.info("=" * 80)
        
        pipeline_start = time.time()
        
        # Validate input
        if not input_mp4.exists():
            logger.error(f"Input file not found: {input_mp4}")
            return False
        
        logger.info(f"Input video: {input_mp4.name}")
        logger.info(f"Whisper model: {model}")
        if language:
            logger.info(f"Language: {language}")
        else:
            logger.info("Language: auto-detect")
        logger.info(f"Diarization: {'Enabled' if enable_diarization else 'Disabled'}")
        logger.info("")
        
        # ======== STEP 1: EXTRACT AUDIO ========
        logger.info("STEP 1: EXTRACTING AUDIO FROM VIDEO")
        logger.info("-" * 80)
        
        wav_path = input_mp4.with_suffix(".wav")
        
        audio_result = extract_audio_from_mp4(
            input_mp4,
            wav_path=wav_path,
            verbose=False
        )
        
        if audio_result is None:
            logger.error("✗ Audio extraction failed. Exiting.")
            return False
        
        logger.info("")
        
        # ======== STEP 2: TRANSCRIBE AUDIO ========
        logger.info("STEP 2: TRANSCRIBING AUDIO")
        logger.info("-" * 80)
        
        transcribe_start = time.time()
        
        transcribe_success = transcribe_file(
            wav_path,
            self.transcripts_dir,
            model=model,
            language=language
        )
        
        if not transcribe_success:
            logger.error("✗ Transcription failed. Exiting.")
            return False
        
        transcribe_elapsed = time.time() - transcribe_start
        logger.info(f"Transcription time: {format_duration(transcribe_elapsed)}")
        logger.info("")
        
        # ======== STEP 3: SPEAKER DIARIZATION (Optional) ========
        base_name = input_mp4.stem
        diarization_result = None
        
        if enable_diarization:
            logger.info("STEP 3: PERFORMING SPEAKER DIARIZATION")
            logger.info("-" * 80)
            logger.info("Using: Silero VAD + SpeechBrain ECAPA-TDNN")
            
            try:
                # Initialize and load diarization models
                diarizer = SpeakerDiarizer()
                
                if diarizer.load_model():
                    diarize_start = time.time()
                    
                    # Perform diarization on audio
                    diarization_result = diarizer.diarize_audio(wav_path)
                    
                    if diarization_result:
                        # Load transcription for merging
                        json_path = self.transcripts_dir / f"{base_name}.json"
                        with open(json_path, "r", encoding="utf-8") as f:
                            import json as json_module
                            transcription = json_module.load(f)
                        
                        # Merge diarization with transcription
                        merged_result = diarizer.merge_with_transcription(
                            diarization_result,
                            transcription
                        )
                        
                        # Save speaker-labeled outputs
                        diarizer.save_diarization_json(
                            merged_result,
                            self.transcripts_dir / f"{base_name}_with_speakers.json"
                        )
                        diarizer.save_speaker_timeline(
                            merged_result,
                            self.transcripts_dir / f"{base_name}_speaker_timeline.txt"
                        )
                        diarizer.save_speaker_srt(
                            merged_result,
                            self.transcripts_dir / f"{base_name}_with_speakers.srt"
                        )
                        
                        diarize_elapsed = time.time() - diarize_start
                        logger.info(f"Diarization time: {format_duration(diarize_elapsed)}")
                    else:
                        logger.warning("Diarization did not produce results")
                else:
                    logger.error("Failed to load diarization models")
                
                diarizer.unload_model()
            
            except Exception as e:
                logger.error(f"Diarization failed: {e}", exc_info=True)
            
            logger.info("")
        
        # ======== STEP 4: GENERATE TIMESTAMPS ========
        logger.info("STEP 4: GENERATING TIMESTAMPS")
        logger.info("-" * 80)
        
        json_path = self.transcripts_dir / f"{base_name}.json"
        
        segment_success = process_segments(json_path, self.transcripts_dir)
        
        if not segment_success:
            logger.warning("✗ Timestamp generation had issues")
        
        logger.info("")
        
        # ======== CLEANUP ========
        if cleanup_wav and wav_path.exists():
            logger.info("STEP 5: CLEANUP")
            logger.info("-" * 80)
            wav_path.unlink()
            logger.info(f"Removed temporary WAV file: {wav_path.name}")
            logger.info("")
        
        # ======== SUMMARY ========
        logger.info("=" * 80)
        logger.info("PIPELINE COMPLETE")
        logger.info("=" * 80)
        
        total_elapsed = time.time() - pipeline_start
        
        logger.info("")
        logger.info("OUTPUT FILES:")
        logger.info(f"  Text transcript:        {base_name}.txt")
        logger.info(f"  JSON with timestamps:   {base_name}.json")
        logger.info(f"  SRT subtitles:          {base_name}.srt")
        logger.info(f"  Timestamped file:       {base_name}_timestamps.txt")
        logger.info(f"  EDL markers:            {base_name}_markers.edl")
        if diarization_result:
            logger.info(f"  With speakers (JSON):   {base_name}_with_speakers.json")
            logger.info(f"  With speakers (SRT):    {base_name}_with_speakers.srt")
            logger.info(f"  Speaker timeline:       {base_name}_speaker_timeline.txt")
        logger.info("")
        logger.info(f"Location: {self.transcripts_dir}")
        logger.info("")
        logger.info(f"Total pipeline time: {format_duration(total_elapsed)}")
        logger.info("")
        
        # Print sample of transcript
        try:
            txt_path = self.transcripts_dir / f"{base_name}.txt"
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Show first 500 characters
            preview = content[:500]
            if len(content) > 500:
                preview += "\n\n[... transcript continues ...]"
            
            logger.info("TRANSCRIPT PREVIEW:")
            logger.info("-" * 80)
            logger.info(preview)
            logger.info("")
        except Exception as e:
            logger.warning(f"Could not read transcript preview: {e}")
        
        return True


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Jitsi Meeting Transcription Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (auto-detect language, use 'base' model)
  python run_pipeline.py recordings/meeting.mp4
  
  # With specific language and smaller model
  python run_pipeline.py recordings/meeting.mp4 --language en --model small
  
  # Clean up intermediate WAV file after completion
  python run_pipeline.py recordings/meeting.mp4 --cleanup
        """
    )
    
    parser.add_argument(
        "video",
        type=Path,
        help="Path to input MP4 video file (Jitsi recording)"
    )
    
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)"
    )
    
    parser.add_argument(
        "--language",
        default=None,
        help="Language code (e.g., 'en', 'es', 'fr'). Leave blank for auto-detect."
    )
    
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove intermediate WAV file after transcription"
    )
    
    parser.add_argument(
        "--no-diarization",
        action="store_true",
        help="Skip speaker diarization (faster, no speaker labels)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed processing information"
    )
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = JitsiTranscriptionPipeline()
    
    # Run pipeline
    success = pipeline.run(
        input_mp4=args.video,
        model=args.model,
        language=args.language,
        cleanup_wav=args.cleanup,
        enable_diarization=not args.no_diarization
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n✗ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}", exc_info=True)
        sys.exit(1)
