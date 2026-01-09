"""
Batch transcription processor.

Process multiple MP4 files in a directory with a single command.

Usage:
    python batch_transcribe.py recordings/ --model base --cleanup
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from run_pipeline import JitsiTranscriptionPipeline
from utils import setup_logger, format_duration


logger = setup_logger(__name__)


class BatchTranscriber:
    """Process multiple MP4 files in batch."""
    
    def __init__(self, input_dir: Path, model: str = "base", cleanup: bool = False):
        """
        Initialize batch transcriber.
        
        Args:
            input_dir: Directory containing MP4 files
            model: Whisper model to use
            cleanup: Clean up temporary files
        """
        self.input_dir = Path(input_dir)
        self.model = model
        self.cleanup = cleanup
        self.pipeline = JitsiTranscriptionPipeline()
        
        if not self.input_dir.exists():
            raise ValueError(f"Input directory not found: {input_dir}")
    
    def find_video_files(self) -> List[Path]:
        """
        Find all MP4 files in input directory.
        
        Returns:
            List of MP4 file paths
        """
        video_extensions = {".mp4", ".mov", ".avi", ".mkv"}
        videos = []
        
        for ext in video_extensions:
            videos.extend(self.input_dir.glob(f"*{ext}"))
            videos.extend(self.input_dir.glob(f"*{ext.upper()}"))
        
        # Sort by file size (smaller first for quicker processing)
        videos.sort(key=lambda x: x.stat().st_size)
        
        return videos
    
    def process_batch(self) -> dict:
        """
        Process all video files in batch.
        
        Returns:
            Dictionary with statistics
        """
        logger.info("=" * 80)
        logger.info("BATCH TRANSCRIPTION PROCESSOR")
        logger.info("=" * 80)
        logger.info("")
        
        # Find videos
        videos = self.find_video_files()
        
        if not videos:
            logger.error(f"No video files found in {self.input_dir}")
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "total_time": 0,
                "results": []
            }
        
        logger.info(f"Found {len(videos)} video file(s)")
        logger.info(f"Model: {self.model}")
        logger.info(f"Cleanup: {self.cleanup}")
        logger.info("")
        
        # Process each video
        batch_start = time.time()
        results = []
        
        for i, video_path in enumerate(videos, 1):
            logger.info(f"[{i}/{len(videos)}] Processing: {video_path.name}")
            logger.info("-" * 80)
            
            try:
                start_time = time.time()
                
                success = self.pipeline.run(
                    input_mp4=video_path,
                    model=self.model,
                    language=None,
                    cleanup_wav=self.cleanup
                )
                
                elapsed = time.time() - start_time
                
                results.append({
                    "file": video_path.name,
                    "status": "SUCCESS" if success else "FAILED",
                    "time": elapsed,
                    "error": None
                })
                
                logger.info(f"Status: {'✓ SUCCESS' if success else '✗ FAILED'}")
                logger.info(f"Time: {format_duration(elapsed)}")
                logger.info("")
                
            except Exception as e:
                logger.error(f"Error: {e}")
                results.append({
                    "file": video_path.name,
                    "status": "ERROR",
                    "time": 0,
                    "error": str(e)
                })
                logger.info("")
        
        batch_elapsed = time.time() - batch_start
        
        # Summary
        logger.info("=" * 80)
        logger.info("BATCH PROCESSING COMPLETE")
        logger.info("=" * 80)
        logger.info("")
        
        successful = sum(1 for r in results if r["status"] == "SUCCESS")
        failed = sum(1 for r in results if r["status"] != "SUCCESS")
        
        logger.info("SUMMARY:")
        logger.info(f"  Total files: {len(videos)}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Failed: {failed}")
        logger.info(f"  Total time: {format_duration(batch_elapsed)}")
        logger.info("")
        
        logger.info("DETAILED RESULTS:")
        logger.info("-" * 80)
        for result in results:
            status_symbol = "✓" if result["status"] == "SUCCESS" else "✗"
            time_str = format_duration(result["time"]) if result["time"] > 0 else "N/A"
            logger.info(f"{status_symbol} {result['file']:40s} [{time_str:>10s}]")
            if result["error"]:
                logger.info(f"  Error: {result['error']}")
        logger.info("")
        
        return {
            "total": len(videos),
            "successful": successful,
            "failed": failed,
            "total_time": batch_elapsed,
            "results": results
        }


def main():
    """Main entry point for batch transcription."""
    parser = argparse.ArgumentParser(
        description="Batch transcribe multiple Jitsi recordings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all MP4 files in recordings folder
  python batch_transcribe.py recordings/
  
  # With smaller model for faster processing
  python batch_transcribe.py recordings/ --model tiny
  
  # Clean up WAV files after transcription
  python batch_transcribe.py recordings/ --cleanup
  
  # Custom directory
  python batch_transcribe.py /path/to/videos/ --model base --cleanup
        """
    )
    
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing MP4 video files"
    )
    
    parser.add_argument(
        "--model",
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model to use (default: base)"
    )
    
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove temporary WAV files after transcription"
    )
    
    args = parser.parse_args()
    
    # Create batch transcriber
    try:
        transcriber = BatchTranscriber(
            input_dir=args.directory,
            model=args.model,
            cleanup=args.cleanup
        )
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        sys.exit(1)
    
    # Process batch
    stats = transcriber.process_batch()
    
    # Exit with appropriate code
    sys.exit(0 if stats["failed"] == 0 else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n✗ Batch processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}", exc_info=True)
        sys.exit(1)
