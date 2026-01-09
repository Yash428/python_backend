"""
Speaker diarization using Silero VAD + SpeechBrain ECAPA-TDNN embeddings.

Fully open-source pipeline with no gated models or authentication required.

Pipeline:
1. Load audio and resample to 16kHz mono
2. Voice Activity Detection (Silero VAD)
3. Extract speaker embeddings (SpeechBrain ECAPA-TDNN)
4. Cluster embeddings (agglomerative clustering, cosine distance)
5. Merge with transcription segments

Requirements:
    - pip install silero-vad
    - pip install speechbrain
    - pip install torchaudio
    - pip install torch
    - pip install scikit-learn
"""

import json
import os
import sys
import time
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import numpy as np

try:
    import torch
    import torchaudio
except ImportError:
    torch = None
    torchaudio = None

try:
    from speechbrain.pretrained import SpeakerRecognition
except ImportError:
    SpeakerRecognition = None

try:
    from silero_vad import load_silero_vad, get_speech_timestamps
except ImportError:
    load_silero_vad = None
    get_speech_timestamps = None

try:
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.preprocessing import StandardScaler
    from scipy.spatial.distance import pdist, squareform
except ImportError:
    AgglomerativeClustering = None
    StandardScaler = None
    pdist = None
    squareform = None

from utils import setup_logger, ensure_directory, seconds_to_timestamp, validate_file_exists


logger = setup_logger(__name__)

# Set deterministic random seed
np.random.seed(42)
if torch is not None:
    torch.manual_seed(42)

class SpeakerDiarizer:
    """
    Perform speaker diarization using Silero VAD + SpeechBrain ECAPA-TDNN.
    
    This is a fully open-source, free, no-license-required implementation.
    """
    
    def __init__(self, device: str = None):
        """
        Initialize speaker diarizer.
        
        Args:
            device: "cuda" or "cpu". Auto-detects if None.
            
        Raises:
            ImportError: If required dependencies are not installed
        """
        if torch is None or torchaudio is None:
            raise ImportError(
                "PyTorch and torchaudio are required. "
                "Install with: pip install torch torchaudio"
            )
        
        if load_silero_vad is None:
            raise ImportError(
                "silero-vad is required. Install with: pip install silero-vad"
            )
        
        if SpeakerRecognition is None:
            raise ImportError(
                "SpeechBrain is required. Install with: pip install speechbrain"
            )
        
        if AgglomerativeClustering is None:
            raise ImportError(
                "scikit-learn is required. Install with: pip install scikit-learn"
            )
        
        # Setup device
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device.upper()}")
        
        # Models (lazy-loaded)
        self.vad_model = None
        self.speaker_model = None
        
        self._load_models()
    
    def _load_models(self) -> bool:
        """Load VAD and speaker embedding models."""
        try:
            # Load Silero VAD (device handling is automatic)
            logger.info("Loading Silero VAD model...")
            self.vad_model = load_silero_vad()
            logger.info("✓ Silero VAD loaded")
            
            # Load SpeechBrain ECAPA-TDNN
            logger.info("Loading SpeechBrain ECAPA-TDNN speaker embeddings...")
            self.speaker_model = SpeakerRecognition.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                savedir="pretrained_models/spkrec-ecapa-voxceleb",
                run_opts={"device": self.device}
            )
            logger.info("✓ SpeechBrain ECAPA-TDNN loaded")
            
            return True
        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            return False
    
    def load_model(self) -> bool:
        """
        Load diarization models (VAD + speaker embedding).
        
        Returns:
            True if successful
        """
        return self.vad_model is not None and self.speaker_model is not None
    
    def unload_model(self):
        """Unload models to free memory."""
        if self.vad_model is not None:
            del self.vad_model
            self.vad_model = None
        if self.speaker_model is not None:
            del self.speaker_model
            self.speaker_model = None
        if torch is not None:
            torch.cuda.empty_cache()
        logger.info("Diarization models unloaded")
    
    def _load_and_resample_audio(self, audio_path: Path, target_sr: int = 16000) -> Optional[torch.Tensor]:
        """
        Load audio file and resample to target sample rate (16kHz).
        
        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
            target_sr: Target sample rate (default 16000 Hz)
            
        Returns:
            Audio tensor (1D, float32) or None if error
        """
        try:
            # Load audio
            waveform, sr = torchaudio.load(str(audio_path))
            
            # Convert to mono if needed
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            
            # Resample if needed
            if sr != target_sr:
                resampler = torchaudio.transforms.Resample(sr, target_sr)
                waveform = resampler(waveform)
            
            # Ensure float32 and return as 1D
            return waveform.squeeze(0).float()
        
        except Exception as e:
            logger.error(f"Failed to load audio {audio_path}: {e}")
            return None
    
    def _get_speech_segments(self, waveform: torch.Tensor, sr: int = 16000, 
                             min_duration: float = 0.5) -> List[Tuple[float, float]]:
        """
        Detect speech segments using Silero VAD.
        
        Args:
            waveform: Audio tensor (1D)
            sr: Sample rate
            min_duration: Minimum segment duration in seconds
            
        Returns:
            List of (start_sec, end_sec) tuples
        """
        if self.vad_model is None:
            logger.error("VAD model not loaded")
            return []
        
        try:
            # Get VAD timestamps (returns dict with 'start' and 'end' in milliseconds)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                speech_ts = get_speech_timestamps(
                    waveform, 
                    self.vad_model, 
                    sampling_rate=sr,
                    threshold=0.5,
                    min_speech_duration_ms=int(min_duration * 1000),
                    min_silence_duration_ms=200,
                    return_seconds=True  # Return in seconds
                )
            
            segments = [(ts['start'], ts['end']) for ts in speech_ts]
            logger.info(f"Found {len(segments)} speech segments")
            return segments
        
        except Exception as e:
            logger.error(f"VAD failed: {e}")
            return []
    
    def _merge_nearby_segments(self, segments: List[Tuple[float, float]], 
                               merge_gap: float = 0.2) -> List[Tuple[float, float]]:
        """
        Merge speech segments that are very close together.
        This helps create longer chunks for better speaker embedding quality.
        
        Args:
            segments: List of (start, end) tuples
            merge_gap: Maximum gap in seconds to merge segments
            
        Returns:
            List of merged (start, end) tuples
        """
        if not segments:
            return []
        
        merged = []
        current_start, current_end = segments[0]
        
        for i in range(1, len(segments)):
            start, end = segments[i]
            gap = start - current_end
            
            if gap <= merge_gap:
                # Merge segments
                current_end = end
            else:
                # Save current segment and start new one
                merged.append((current_start, current_end))
                current_start, current_end = start, end
        
        # Don't forget the last segment
        merged.append((current_start, current_end))
        
        return merged
    
    def _extract_embedding(self, waveform: torch.Tensor, sr: int = 16000) -> Optional[np.ndarray]:
        """
        Extract speaker embedding from audio segment using SpeechBrain ECAPA-TDNN.
        
        Args:
            waveform: Audio tensor (1D)
            sr: Sample rate
            
        Returns:
            Embedding vector (numpy array) or None if error
        """
        if self.speaker_model is None:
            logger.error("Speaker model not loaded")
            return None
        
        try:
            # Move to device
            waveform = waveform.to(self.device).unsqueeze(0)  # Add batch dimension
            
            # Extract embedding
            with torch.no_grad():
                embeddings = self.speaker_model.encode_batch(waveform)
            
            # Return as numpy (1D vector)
            return embeddings.squeeze(0).cpu().numpy()
        
        except Exception as e:
            logger.error(f"Embedding extraction failed: {e}")
            return None
    
    def _cluster_embeddings(self, embeddings: np.ndarray, 
                           max_speakers: int = 10) -> np.ndarray:
        """
        Cluster speaker embeddings using agglomerative clustering (cosine distance).
        
        Args:
            embeddings: Shape (n_segments, embedding_dim)
            max_speakers: Maximum number of speakers to detect
            
        Returns:
            Cluster labels (array of speaker IDs)
        """
        if embeddings.shape[0] < 2:
            logger.warning("Too few segments for clustering, returning single speaker")
            return np.array([0] * embeddings.shape[0])
        
        try:
            # Ensure embeddings is 2D
            if embeddings.ndim == 1:
                embeddings = embeddings.reshape(1, -1)
            
            # Normalize embeddings for cosine distance
            embeddings_norm = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
            
            # Compute square distance matrix for clustering
            from scipy.spatial.distance import cdist
            distance_matrix = cdist(embeddings_norm, embeddings_norm, metric='cosine')
            
            # Determine optimal number of clusters using silhouette score and distance threshold
            best_n_clusters = 1
            best_score = -1.0
            
            from sklearn.metrics import silhouette_score
            from scipy.cluster.hierarchy import linkage, fcluster
            
            # Use hierarchical clustering to find optimal cut
            Z = linkage(distance_matrix, method='average', metric='cosine')
            
            max_k = min(max_speakers, embeddings.shape[0])
            distance_threshold = 0.5  # Cosine distance threshold for different speakers
            
            # Try different numbers of clusters
            for n_clusters in range(1, max_k + 1):
                try:
                    if n_clusters == 1:
                        # Single cluster case
                        labels = np.zeros(embeddings.shape[0], dtype=int)
                        best_n_clusters = 1
                        best_score = 0.0
                    else:
                        clusterer = AgglomerativeClustering(
                            n_clusters=n_clusters,
                            linkage='average',
                            metric='precomputed'
                        )
                        labels = clusterer.fit_predict(distance_matrix)
                        
                        # Calculate silhouette score
                        if n_clusters > 1 and len(np.unique(labels)) > 1:
                            score = silhouette_score(distance_matrix, labels, metric='precomputed')
                        else:
                            score = 0.0
                        
                        logger.debug(f"n_clusters={n_clusters}: silhouette={score:.3f}")
                        
                        if score > best_score:
                            best_score = score
                            best_n_clusters = n_clusters
                except Exception as e:
                    logger.debug(f"Failed to cluster with {n_clusters} clusters: {e}")
                    continue
            
            # Final clustering with best n_clusters
            if best_n_clusters == 1:
                labels = np.zeros(embeddings.shape[0], dtype=int)
                logger.info(f"Single speaker detected (silhouette: {best_score:.3f})")
            else:
                clusterer = AgglomerativeClustering(
                    n_clusters=best_n_clusters,
                    linkage='average',
                    metric='precomputed'
                )
                labels = clusterer.fit_predict(distance_matrix)
                logger.info(f"Detected {best_n_clusters} speakers (silhouette: {best_score:.3f})")
            
            return labels
        
        except Exception as e:
            logger.error(f"Clustering failed: {e}", exc_info=True)
            # Fallback: assign all to speaker 0
            return np.zeros(embeddings.shape[0], dtype=int)
    
    def diarize_audio(self, audio_path: Path, 
                     min_speech_duration: float = 0.5,
                     max_speakers: int = 10) -> Optional[Dict[str, Any]]:
        """
        Perform speaker diarization on audio file.
        
        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
            min_speech_duration: Minimum speech segment duration in seconds
            max_speakers: Maximum expected speakers
            
        Returns:
            Dictionary with speaker segments, or None if error
        """
        if not validate_file_exists(audio_path):
            return None
        
        if self.vad_model is None or self.speaker_model is None:
            logger.error("Models not loaded. Call load_model() first.")
            return None
        
        try:
            logger.info(f"Diarizing audio: {audio_path.name}")
            start_time = time.time()
            
            # Step 1: Load and resample audio
            logger.info("Loading and resampling audio to 16kHz...")
            waveform = self._load_and_resample_audio(audio_path, target_sr=16000)
            if waveform is None:
                return None
            
            # Step 2: Voice Activity Detection
            logger.info("Detecting speech segments...")
            speech_segments = self._get_speech_segments(
                waveform, 
                sr=16000,
                min_duration=min_speech_duration
            )
            if not speech_segments:
                logger.warning("No speech detected")
                return None
            
            # Step 3: Extract embeddings for each segment
            logger.info(f"Extracting embeddings for {len(speech_segments)} segments...")
            embeddings = []
            segment_info = []
            
            # Merge nearby segments and create longer chunks for better embedding quality
            merged_segments = self._merge_nearby_segments(speech_segments, merge_gap=0.2)
            logger.info(f"Merged {len(speech_segments)} segments into {len(merged_segments)} chunks")
            
            for start_sec, end_sec in merged_segments:
                start_idx = int(start_sec * 16000)
                end_idx = int(end_sec * 16000)
                
                segment_waveform = waveform[start_idx:end_idx]
                
                # Skip very short segments
                if segment_waveform.shape[0] < 16000 * 0.5:  # Less than 0.5 seconds
                    continue
                    
                embedding = self._extract_embedding(segment_waveform, sr=16000)
                
                if embedding is not None:
                    embeddings.append(embedding)
                    segment_info.append({
                        'start': start_sec,
                        'end': end_sec,
                        'duration': end_sec - start_sec
                    })
            
            if not embeddings:
                logger.warning("No embeddings extracted")
                return None
            
            embeddings_array = np.array(embeddings)
            logger.info(f"Extracted {len(embeddings)} embeddings")
            
            # Step 4: Cluster embeddings
            logger.info("Clustering speaker embeddings...")
            speaker_labels = self._cluster_embeddings(embeddings_array, max_speakers=max_speakers)
            
            # Step 5: Build output
            speakers_map = {}
            segments = []
            
            for label, info in zip(speaker_labels, segment_info):
                speaker_name = f"SPEAKER_{int(label):02d}"
                if speaker_name not in speakers_map:
                    speakers_map[speaker_name] = len(speakers_map)
                
                segments.append({
                    "speaker": speaker_name,
                    "speaker_id": speakers_map[speaker_name],
                    "start": info['start'],
                    "end": info['end'],
                    "duration": info['duration']
                })
            
            elapsed = time.time() - start_time
            
            result = {
                "file": str(audio_path),
                "total_speakers": len(speakers_map),
                "speakers": speakers_map,
                "segments": segments,
                "processing_time": elapsed
            }
            
            logger.info(f"✓ Diarization complete: {len(speakers_map)} speakers, {len(segments)} segments in {elapsed:.1f}s")
            return result
        
        except Exception as e:
            logger.error(f"Diarization failed: {e}", exc_info=True)
            return None
    
    def merge_with_transcription(self, diarization: Dict[str, Any], 
                                transcription: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge diarization results with transcription segments.
        
        Args:
            diarization: Output from diarize_audio()
            transcription: Output from Whisper transcription
            
        Returns:
            Combined result with speaker labels on each segment
        """
        try:
            diar_segments = diarization.get("segments", [])
            trans_segments = transcription.get("segments", [])
            
            if not diar_segments or not trans_segments:
                logger.warning("Missing diarization or transcription segments")
                return transcription
            
            # For each transcription segment, find overlapping speaker
            for trans_seg in trans_segments:
                trans_start = trans_seg.get("start", 0)
                trans_end = trans_seg.get("end", 0)
                
                # Find speaker with maximum overlap
                speaker = None
                speaker_id = None
                max_overlap = 0
                
                for diar_seg in diar_segments:
                    diar_start = diar_seg["start"]
                    diar_end = diar_seg["end"]
                    
                    # Calculate overlap
                    overlap_start = max(trans_start, diar_start)
                    overlap_end = min(trans_end, diar_end)
                    overlap = max(0, overlap_end - overlap_start)
                    
                    if overlap > max_overlap:
                        max_overlap = overlap
                        speaker = diar_seg["speaker"]
                        speaker_id = diar_seg["speaker_id"]
                
                # Add speaker info if found
                if speaker:
                    trans_seg["speaker"] = speaker
                    trans_seg["speaker_id"] = speaker_id
                    trans_seg["speaker_overlap"] = max_overlap
            
            # Combine metadata
            result = {
                "metadata": transcription.get("metadata", {}),
                "language": transcription.get("language", "unknown"),
                "duration_seconds": transcription.get("duration_seconds", 0),
                "total_speakers": diarization["total_speakers"],
                "speakers": diarization["speakers"],
                "diarization_time": diarization["processing_time"],
                "segments": trans_segments
            }
            
            logger.info("✓ Successfully merged diarization with transcription")
            return result
        
        except Exception as e:
            logger.error(f"Failed to merge results: {e}")
            return transcription
    
    def save_diarization_json(self, result: Dict[str, Any], output_path: Path) -> bool:
        """Save diarization result as JSON."""
        try:
            ensure_directory(output_path.parent)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ Saved diarization JSON: {output_path.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save diarization JSON: {e}")
            return False
    
    def save_speaker_timeline(self, result: Dict[str, Any], output_path: Path) -> bool:
        """Save speaker timeline as readable text."""
        try:
            ensure_directory(output_path.parent)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("SPEAKER TIMELINE\n")
                f.write("=" * 60 + "\n\n")
                
                f.write(f"File: {result.get('file', 'unknown')}\n")
                f.write(f"Total Speakers: {result.get('total_speakers', 0)}\n")
                if 'diarization_time' in result:
                    f.write(f"Processing Time: {result['diarization_time']:.1f}s\n")
                f.write("\n")
                
                # Write speaker list
                speakers = result.get("speakers", {})
                if speakers:
                    f.write("Speakers:\n")
                    for speaker, speaker_id in sorted(speakers.items(), key=lambda x: x[1]):
                        f.write(f"  [{speaker_id}] {speaker}\n")
                    f.write("\n")
                
                f.write("-" * 60 + "\n\n")
                
                # Write segments
                for segment in result.get("segments", []):
                    start = seconds_to_timestamp(segment.get("start", 0))
                    speaker = segment.get("speaker", "UNKNOWN")
                    text = segment.get("text", "").strip()
                    if text:
                        f.write(f"{start} - {speaker}:\n")
                        f.write(f"  {text}\n\n")
                    else:
                        f.write(f"{start} - {speaker} (speech detected)\n\n")
            
            logger.info(f"✓ Saved speaker timeline: {output_path.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save speaker timeline: {e}")
            return False
    
    def save_speaker_srt(self, result: Dict[str, Any], output_path: Path) -> bool:
        """Save speaker-labeled transcript as SRT format."""
        try:
            ensure_directory(output_path.parent)
            with open(output_path, "w", encoding="utf-8") as f:
                for idx, segment in enumerate(result.get("segments", []), 1):
                    start = seconds_to_timestamp(segment.get("start", 0))
                    end = seconds_to_timestamp(segment.get("end", 0))
                    speaker = segment.get("speaker", "UNKNOWN")
                    text = segment.get("text", "").strip()
                    
                    f.write(f"{idx}\n")
                    f.write(f"{start} --> {end}\n")
                    if text:
                        f.write(f"[{speaker}]\n{text}\n\n")
                    else:
                        f.write(f"[{speaker}]\n(speech segment)\n\n")
            
            logger.info(f"✓ Saved speaker SRT: {output_path.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save speaker SRT: {e}")
            return False


if __name__ == "__main__":
    logger.info("Speaker Diarization Module - Ready")
    logger.info("=" * 50)
    logger.info("Using Silero VAD + SpeechBrain ECAPA-TDNN")
    logger.info("No HuggingFace authentication required")
