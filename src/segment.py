"""
Segment-level timestamp generation from transcription results.

This module creates human-readable timestamp files with segment boundaries
and speaker turn information for easy navigation through transcripts.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils import setup_logger, ensure_directory, seconds_to_timestamp


logger = setup_logger(__name__)


class SegmentProcessor:
    """Process and generate timestamped segments from transcription."""
    
    def __init__(self):
        """Initialize segment processor."""
        self.segments = []
    
    def load_transcription_result(self, result: Dict[str, Any]):
        """
        Load segments from Whisper transcription result.
        
        Args:
            result: Dictionary from Whisper transcription
        """
        self.segments = result.get("segments", [])
        logger.info(f"Loaded {len(self.segments)} segments from transcription")
    
    def load_from_json(self, json_path: Path) -> bool:
        """
        Load segments from JSON transcript file.
        
        Args:
            json_path: Path to JSON transcript
            
        Returns:
            True if successful
        """
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.segments = data.get("segments", [])
            logger.info(f"Loaded {len(self.segments)} segments from {json_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load JSON: {e}")
            return False
    
    def generate_timestamped_transcript(self) -> str:
        """
        Generate human-readable timestamped transcript.
        
        Format:
        [HH:MM:SS.mmm - HH:MM:SS.mmm] Segment text
        
        Returns:
            Formatted transcript string
        """
        lines = []
        
        for segment in self.segments:
            start = seconds_to_timestamp(segment.get("start", 0))
            end = seconds_to_timestamp(segment.get("end", 0))
            text = segment.get("text", "").strip()
            
            if text:  # Skip empty segments
                line = f"[{start} - {end}] {text}"
                lines.append(line)
        
        return "\n".join(lines)
    
    def generate_compact_timeline(self) -> str:
        """
        Generate compact timeline with just timestamps and beginning of text.
        
        Format:
        HH:MM:SS | First 80 characters of segment...
        
        Returns:
            Formatted timeline string
        """
        lines = ["TIMELINE VIEW", "=" * 80, ""]
        
        for segment in self.segments:
            timestamp = seconds_to_timestamp(segment.get("start", 0))
            text = segment.get("text", "").strip()
            
            # Get first 80 characters
            preview = text[:80]
            if len(text) > 80:
                preview += "..."
            
            if preview:
                line = f"{timestamp} | {preview}"
                lines.append(line)
        
        return "\n".join(lines)
    
    def generate_speaker_timeline(self) -> str:
        """
        Generate timeline focused on speaker changes (for future diarization).
        
        Returns:
            Speaker timeline string
        """
        lines = ["SPEAKER TIMELINE", "=" * 80, ""]
        
        current_speaker = "Speaker 1"
        silence_threshold = 0.5  # 500ms silence between turns
        
        for i, segment in enumerate(self.segments):
            start = segment.get("start", 0)
            text = segment.get("text", "").strip()
            
            # Check for long pause (indicates speaker change)
            if i > 0:
                prev_end = self.segments[i-1].get("end", 0)
                gap = start - prev_end
                if gap > silence_threshold:
                    # Potential speaker change
                    current_speaker = f"Speaker {len(set(range(1, i//5 + 2)))}"
            
            timestamp = seconds_to_timestamp(start)
            preview = text[:70] if text else "[silence]"
            
            line = f"{timestamp} | {current_speaker}: {preview}"
            lines.append(line)
        
        return "\n".join(lines)
    
    def save_timestamps_file(
        self,
        output_path: Path,
        include_timeline: bool = True,
        include_speaker: bool = True
    ) -> bool:
        """
        Save comprehensive timestamps file with multiple views.
        
        Args:
            output_path: Path to output file
            include_timeline: Include compact timeline view
            include_speaker: Include speaker timeline (placeholder)
            
        Returns:
            True if successful
        """
        try:
            ensure_directory(output_path.parent)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("TRANSCRIPTION TIMESTAMPS\n")
                f.write("=" * 80 + "\n\n")
                
                # Timestamped transcript
                f.write("DETAILED TRANSCRIPT\n")
                f.write("=" * 80 + "\n")
                f.write(self.generate_timestamped_transcript())
                f.write("\n\n")
                
                # Compact timeline
                if include_timeline:
                    f.write(self.generate_compact_timeline())
                    f.write("\n\n")
                
                # Speaker timeline
                if include_speaker:
                    f.write(self.generate_speaker_timeline())
                    f.write("\n\n")
                
                # Summary statistics
                f.write("STATISTICS\n")
                f.write("=" * 80 + "\n")
                f.write(f"Total segments: {len(self.segments)}\n")
                
                if self.segments:
                    total_duration = self.segments[-1].get("end", 0)
                    f.write(f"Total duration: {seconds_to_timestamp(total_duration)}\n")
                    f.write(f"Average segment duration: {total_duration / len(self.segments):.2f}s\n")
            
            logger.info(f"✓ Saved timestamps file: {output_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save timestamps file: {e}")
            return False
    
    def get_segment_at_timestamp(
        self,
        timestamp_seconds: float
    ) -> Optional[Dict[str, Any]]:
        """
        Find segment containing given timestamp.
        
        Args:
            timestamp_seconds: Time in seconds
            
        Returns:
            Segment dictionary or None
        """
        for segment in self.segments:
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            
            if start <= timestamp_seconds <= end:
                return segment
        
        return None
    
    def get_segments_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Find all segments containing keyword (case-insensitive).
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of matching segments
        """
        keyword_lower = keyword.lower()
        matches = []
        
        for segment in self.segments:
            text = segment.get("text", "").lower()
            if keyword_lower in text:
                matches.append(segment)
        
        return matches
    
    def export_segment_markers(self, output_path: Path) -> bool:
        """
        Export segment boundaries for video editing software.
        
        Format: EDL (Edit Decision List)
        
        Args:
            output_path: Path to output EDL file
            
        Returns:
            True if successful
        """
        try:
            ensure_directory(output_path.parent)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# EDL Segment Markers\n")
                f.write("# Timecode format: HH:MM:SS:FF (25fps)\n\n")
                
                for i, segment in enumerate(self.segments, 1):
                    start = seconds_to_timestamp(segment.get("start", 0)).replace(".", ":")
                    end = seconds_to_timestamp(segment.get("end", 0)).replace(".", ":")
                    text = segment.get("text", "").strip()[:60]
                    
                    f.write(f"{i:03d}  SEG_{i:04d}     V     C        {start}    {end}\n")
                    f.write(f"* TEXT: {text}\n")
            
            logger.info(f"✓ Saved EDL markers: {output_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save EDL: {e}")
            return False


def process_segments(
    transcription_json_path: Path,
    output_dir: Path
) -> bool:
    """
    Convenience function to process segments and generate all output files.
    
    Args:
        transcription_json_path: Path to JSON transcription
        output_dir: Directory for output files
        
    Returns:
        True if successful
    """
    processor = SegmentProcessor()
    
    # Load transcription
    if not processor.load_from_json(transcription_json_path):
        return False
    
    # Generate outputs
    base_name = transcription_json_path.stem
    ensure_directory(output_dir)
    
    success = True
    success &= processor.save_timestamps_file(
        output_dir / f"{base_name}_timestamps.txt"
    )
    success &= processor.export_segment_markers(
        output_dir / f"{base_name}_markers.edl"
    )
    
    return success


if __name__ == "__main__":
    logger.info("Segment Processor Module - Ready")
    logger.info("=" * 50)
    logger.info("Use this module to generate timestamps from transcription JSON")
