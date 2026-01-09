"""
Configuration example for Jitsi Transcription Pipeline.

Copy this file and modify settings for your deployment.
"""

# ============================================================================
# TRANSCRIPTION SETTINGS
# ============================================================================

# Whisper model: tiny (39MB), base (141MB), small (244MB), medium (769MB), large (2.9GB)
# Recommendation: 'base' for good balance of speed and accuracy
WHISPER_MODEL = "base"

# Language code for transcription
# Set to None for automatic language detection
# Examples: 'en' (English), 'es' (Spanish), 'fr' (French), 'de' (German)
LANGUAGE = None

# Temperature for transcription (0.0 = deterministic, 1.0 = random)
# Lower values = more consistent, higher values = more variation
TEMPERATURE = 0.0

# Beam size for beam search (higher = slower but potentially better quality)
BEAM_SIZE = 5

# ============================================================================
# AUDIO SETTINGS
# ============================================================================

# Audio sample rate (Whisper requires 16kHz)
SAMPLE_RATE = 16000

# Number of audio channels (Whisper requires mono)
CHANNELS = 1

# Audio codec
AUDIO_CODEC = "pcm_s16le"

# ============================================================================
# OUTPUT SETTINGS
# ============================================================================

# Generate multiple output formats
GENERATE_TEXT = True      # Plain text transcript
GENERATE_JSON = True      # JSON with timestamps
GENERATE_SRT = True       # SRT subtitle format
GENERATE_TIMESTAMPS = True  # Human-readable timestamps
GENERATE_EDL = True       # EDL markers for video editing

# ============================================================================
# PROCESSING SETTINGS
# ============================================================================

# Remove intermediate WAV files after transcription
CLEANUP_AUDIO = False

# Verbose logging output
VERBOSE = False

# Maximum audio file size (bytes) - for safety
MAX_AUDIO_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# Processing timeout (seconds)
PROCESSING_TIMEOUT = 3600  # 1 hour

# ============================================================================
# BATCH PROCESSING
# ============================================================================

# Process multiple files in parallel
PARALLEL_PROCESSING = False

# Number of parallel workers (if enabled)
NUM_WORKERS = 2

# Batch size for processing
BATCH_SIZE = 10

# ============================================================================
# PATHS (Optional overrides)
# ============================================================================

# Leave empty to use default structure
PROJECT_ROOT = None  # Defaults to script directory

RECORDINGS_DIR = None  # Defaults to ./recordings
TRANSCRIPTS_DIR = None  # Defaults to ./transcripts

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = None     # Set to filename to also log to file

# ============================================================================
# ADVANCED OPTIONS
# ============================================================================

# Device to use: 'cpu', 'cuda', 'mps'
# Default: 'cpu' (most compatible)
DEVICE = "cpu"

# Use 16-bit floating point (faster but less accurate on some systems)
# Windows CPU: typically False
USE_FP16 = False

# Model download root
# Leave None to use default cache directory
MODEL_DOWNLOAD_ROOT = None

# ============================================================================
# SPEAKER DIARIZATION (Future)
# ============================================================================

# Enable speaker diarization (identify different speakers)
ENABLE_DIARIZATION = False

# Maximum number of speakers to detect
MAX_SPEAKERS = None  # Auto-detect

# ============================================================================
# NER (Named Entity Recognition) - Future
# ============================================================================

# Extract names, organizations, locations
ENABLE_NER = False

# ============================================================================
# SENTIMENT ANALYSIS - Future
# ============================================================================

# Analyze sentiment per segment
ENABLE_SENTIMENT = False

# ============================================================================
# CUSTOM VOCABULARY
# ============================================================================

# Custom words/phrases to boost recognition
# Useful for domain-specific terms, names, products
CUSTOM_VOCABULARY = {
    # "product_name": "Acme Corp",
    # "feature": "AI Integration",
    # "person": "John Doe",
}

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

"""
Using this configuration file:

1. In your Python code:
   import config
   
   pipeline = JitsiTranscriptionPipeline()
   pipeline.run(
       input_mp4=Path("video.mp4"),
       model=config.WHISPER_MODEL,
       language=config.LANGUAGE
   )

2. From command line:
   python run_pipeline.py video.mp4 --model base --language en

3. For batch processing:
   python batch_transcribe.py recordings/ --model base --cleanup
"""
